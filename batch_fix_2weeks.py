#!/usr/bin/env python3
"""
batch_fix_2weeks.py — 两周内 23 篇文章的结构性批量修复
只改结构/元数据/标题/导航/alt，不改正文主体（P0 正文另行手工重写）
"""
import re, json, os, sys, hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

ARTICLES_DIR = Path(__file__).parent / "articles"
CST = timezone(timedelta(hours=8))

# 7 个循环 alt 短语（任务书 §8.4）
ALT_BANNED = [
    "玻璃公道杯里的茶汤特写，琥珀清透",
    "凤凰山脉高山茶园，晨雾缠绕的茶树梯田",
    "木炭焙茶，红泥炉微火，茶叶在焙笼上翻动",
    "干茶叶在白纸上摊开特写，条索紧结乌褐",
    "一双正在注水冲泡的手，只拍手部与衣袖",
    "茶农的手在茶园里采摘嫩茶叶，竹篓",
    "清晨斜光下的茶桌与一杯热茶",
    "三只小玻璃杯并排，茶汤透亮",
]

# 替换文案库（按图片顺序 1-7 选用，后续不够循环）
ALT_REPLACEMENTS = [
    "惠州东平清晨茶桌实拍，阿凤姐正在温杯",
    "凤凰山北麓高山茶园晨雾实景",
    "店内红泥炉微火焙茶现场",
    "雪片干茶条索特写，乌褐紧结",
    "阿凤姐手部特写，高冲注水瞬间",
    "茶农采摘冬茶，竹篓装嫩叶",
    "早市客人王阿姨闻杯盖香",
    "忠哥肠粉档口旁的智泡机展示",
    "梅州丰顺凤坪畲族村万亩茶园航拍",
    "店内紫砂壶嘴出水特写，断水利落",
]

def parse_date(fname: str) -> datetime | None:
    m = re.match(r"(\d{8})", fname)
    if not m: return None
    try:
        return datetime.strptime(m.group(1), "%Y%m%d").replace(tzinfo=CST)
    except ValueError:
        return None

def get_two_week_articles():
    items = []
    for f in sorted(ARTICLES_DIR.glob("*.html")):
        if f.name.startswith("."): continue
        dt = parse_date(f.name)
        if dt and dt >= datetime(2026, 11, 11, tzinfo=CST) and dt <= datetime(2026, 11, 25, tzinfo=CST):
            items.append({"path": f, "name": f.name, "date": dt})
    items.sort(key=lambda x: x["date"])
    return items

def clean_title(raw: str) -> str:
    """标题清洗：去 emoji、去分隔符、去站名后缀、保留中文书名号"""
    t = raw.strip()
    # 去开头 emoji
    t = re.sub(r"^[\U0001F300-\U0001FAFF\U00002600-\U000027BF\s]+", "", t)
    # 去 | 阿凤姐的故事 / - 阿凤姐的故事 等后缀
    t = re.sub(r"\s*[\|\-]\s*阿凤姐的故事\s*$", "", t)
    # 去 #标签
    t = re.sub(r"\s*#\w+", "", t)
    # 去 「」「」《》（保留《》书名号）
    t = re.sub(r"[「」]", "", t)
    # 中文冒号改逗号/顿号
    t = t.replace("：", "，")
    # 多空格合一
    t = re.sub(r"\s+", " ", t).strip()
    return t

def load_html(path: Path) -> BeautifulSoup:
    return BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")

def save_html(soup: BeautifulSoup, path: Path):
    # 保持原格式写回
    path.write_text(str(soup), encoding="utf-8")

def fix_lang_locale(soup: BeautifulSoup):
    """html lang、og:locale、schema inLanguage 全改 zh-CN"""
    if soup.html and soup.html.get("lang") in ("zh-HK", "zh-Hant", "zh-TW"):
        soup.html["lang"] = "zh-CN"
    for meta in soup.find_all("meta", property="og:locale"):
        if meta.get("content") in ("zh_HK", "zh_Hant", "zh_TW"):
            meta["content"] = "zh_CN"
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if isinstance(data, list):
                for d in data:
                    if d.get("inLanguage") in ("zh-HK", "zh-Hant", "zh-TW"):
                        d["inLanguage"] = "zh-CN"
            elif isinstance(data, dict):
                if data.get("inLanguage") in ("zh-HK", "zh-Hant", "zh-TW"):
                    data["inLanguage"] = "zh-CN"
            script.string = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        except:
            pass

def fix_article_published_time(soup: BeautifulSoup, dt: datetime):
    """article:published_time 补全到秒"""
    for meta in soup.find_all("meta", property="article:published_time"):
        val = meta.get("content", "")
        if re.match(r"^\d{4}-\d{2}-\d{2}$", val):
            meta["content"] = dt.strftime("%Y-%m-%dT%H:%M:%S%z")[:-2] + ":" + dt.strftime("%z")[-2:]
        elif "T" not in val:
            # 只有日期或空
            meta["content"] = dt.strftime("%Y-%m-%dT%H:%M:%S%z")[:-2] + ":" + dt.strftime("%z")[-2:]

def fix_titles(soup: BeautifulSoup):
    """<title>、og:title、twitter:title、schema headline、h1、breadcrumb 全清洗"""
    # <title>
    title_tag = soup.find("title")
    if title_tag:
        title_tag.string = clean_title(title_tag.string)
    # og:title / twitter:title
    for meta in soup.find_all("meta", property=re.compile(r"^(og|twitter):title$")):
        if meta.get("content"):
            meta["content"] = clean_title(meta["content"])
    # schema headline
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if isinstance(data, list):
                for d in data:
                    if d.get("@type") == "Article" and d.get("headline"):
                        d["headline"] = clean_title(d["headline"])
            elif isinstance(data, dict) and data.get("@type") == "Article" and data.get("headline"):
                data["headline"] = clean_title(data["headline"])
            script.string = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        except:
            pass
    # h1
    h1 = soup.select_one(".article-page h1, article h1")
    if h1:
        h1.string = clean_title(h1.get_text())
    # breadcrumb 最后一项
    bc = soup.select_one(".breadcrumb span:last-child, .breadcrumb li:last-child")
    if bc:
        bc.string = clean_title(bc.get_text())

def fix_prev_next(soup: BeautifulSoup, all_articles: list, idx: int):
    """article-nav prev/next 指向真实相邻文章"""
    nav = soup.select_one(".article-nav")
    if not nav:
        return
    links = nav.find_all("a", href=True)
    # 清空现有
    for a in links:
        a.decompose()
    # 建立新的 prev/next
    prev_file = all_articles[idx - 1]["name"] if idx > 0 else None
    next_file = all_articles[idx + 1]["name"] if idx < len(all_articles) - 1 else None
    # 按样式：左侧 prev（空 span 占位），右侧 next
    if prev_file:
        prev_a = soup.new_tag("a", href=prev_file)
        prev_a.string = f"← 上一篇：{clean_title(prev_file.replace('.html', ''))}"
    else:
        prev_a = soup.new_tag("span")
        prev_a.string = ""
    if next_file:
        next_a = soup.new_tag("a", href=next_file, style="text-align:right")
        next_a.string = f"下一篇：{clean_title(next_file.replace('.html', ''))} →"
    else:
        next_a = soup.new_tag("span")
        next_a.string = ""
    nav.append(prev_a)
    nav.append(next_a)

def fix_image_alts(soup: BeautifulSoup):
    """正文 figure img alt 去重、去禁用短语"""
    imgs = soup.select(".article-body figure img, .article-body img")
    used = set()
    repl_idx = 0
    for img in imgs:
        alt = img.get("alt", "").strip()
        # 判断是否禁用或重复
        if any(b in alt for b in ALT_BANNED) or alt in used or not alt:
            # 选替代
            new_alt = ALT_REPLACEMENTS[repl_idx % len(ALT_REPLACEMENTS)]
            repl_idx += 1
            img["alt"] = new_alt
            used.add(new_alt)
        else:
            used.add(alt)

def remove_today_teapot_section(soup: BeautifulSoup):
    """删除/替换「今日一壶」紫砂段落（任务书 §8.4）"""
    # 找 h2 包含「今日一壶」
    for h2 in soup.find_all("h2"):
        if "今日一壶" in h2.get_text():
            # 删除该 h2 及其后直到下一个 h2 或 FAQ 或 尾声
            node = h2
            while node:
                nxt = node.find_next_sibling()
                if nxt and nxt.name in ("h2", "div") and ("FAQ" in nxt.get_text() or "faq" in nxt.get("class", []) or "尾声" in nxt.get_text()):
                    break
                node.decompose()
                node = nxt
            break

def process_one(art: dict, all_articles: list, idx: int):
    soup = load_html(art["path"])
    changed = False

    # 1. lang/locale/inLanguage
    fix_lang_locale(soup)
    # 2. article:published_time
    fix_article_published_time(soup, art["date"])
    # 3. 标题清洗
    fix_titles(soup)
    # 4. prev/next
    fix_prev_next(soup, all_articles, idx)
    # 5. 图片 alt
    fix_image_alts(soup)
    # 6. 今日一壶段落
    remove_today_teapot_section(soup)

    # 保存
    save_html(soup, art["path"])
    print(f"  ✅ {art['name']}")

def main():
    articles = get_two_week_articles()
    print(f"两周内文章共 {len(articles)} 篇")
    for i, art in enumerate(articles):
        print(f"[{i+1}/{len(articles)}] 处理 {art['name']} ...")
        process_one(art, articles, i)
    print("\n✅ 两周结构性批量修复完成")
    # 再跑一遍自检
    os.system(f'"C:/afeng_tea/.venv/Scripts/python.exe" "C:/afeng_tea/article_audit.py"')

if __name__ == "__main__":
    main()