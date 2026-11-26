#!/usr/bin/env python3
"""
文章质量自检器 v1.0
运行：python article_audit.py
作用：扫描全站文章，逐篇评分，不合格的标红并自动修复

配套文档：hermes整改任务书_20261125.md 第 10 节
"""

import re
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
# Windows 无 tzdata，改用固定 UTC+8（CST 中国标准时间，无夏令时）
CST = timezone(timedelta(hours=8))
ARTICLES_DIR = Path(__file__).parent / "articles"
AUDIT_LOG = Path(__file__).parent / "audit_report.json"

# ============ 通用工具 ============

def extract_title(html: str) -> str:
    """从 HTML 提取 <title> 标签内容"""
    m = re.search(r'<title>(.*?)</title>', html, re.DOTALL)
    return m.group(1).strip() if m else ""

def extract_h1(html: str) -> str:
    m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
    return m.group(1).strip() if m else ""

def extract_text(html: str) -> str:
    """提取正文纯文本（去 HTML 标签）"""
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_tags(html: str) -> list[str]:
    """提取所有 #tag"""
    return re.findall(r'#([\w\u4e00-\u9fff]+)', html)

def extract_img_alts(html: str) -> list[str]:
    return re.findall(r'<img[^>]+alt="([^"]*)"', html)

def extract_source_date(html: str) -> str:
    """提取正文中的发布日期（如 '发布于 2026年11月25日' 或 ISO）"""
    patterns = [
        r'20\d{2}[年/-]\d{1,2}[月/-]\d{1,2}日?',
        r'published_at[":\s]+([0-9T:+Z-]+)',
    ]
    for p in patterns:
        m = re.search(p, html)
        if m:
            return m.group(0)
    return ""

def extract_material_source(html: str) -> str:
    """提取正文中标记的素材来源（如 '来源：人民网'）"""
    m = re.search(r'来源[：:]\s*([^\n<]{2,30})', html)
    return m.group(1).strip() if m else ""


# ============ 维度 1：标题合规 ============

def check_title_compliance(html: str) -> tuple[float, list[str]]:
    """检查标题长度、非法字符、单字截断"""
    score = 15.0
    issues = []
    title = extract_title(html)

    # 去掉 "| 阿凤姐的故事" 后缀
    clean = re.sub(r'\s*\|\s*阿凤姐的故事.*$', '', title)

    if len(clean) < 20:
        score -= 5
        issues.append(f"标题过短：{len(clean)} 字（需 20+）")
    if len(clean) > 60:
        score -= 5
        issues.append(f"标题过长：{len(clean)} 字（需 60-）")

    if re.search(r'[#\u201c\u201d\u300c\u300d\u300e\u300f\U0001F300-\U0001FAFF\u2600-\u27BF]', clean):
        score -= 5
        issues.append("标题含非法字符（#/引号/emoji）")

    # 单字截断检测：结尾字是常见词开头
    if re.search(r'(开|精|大|举|召|启|筹)$', clean):
        score -= 5
        issues.append("标题疑似单字截断")

    return max(score, 0), issues


# ============ 维度 2：标题语义完整 ============

def check_title_semantics(html: str, series_hint: str = "") -> tuple[float, list[str]]:
    """检查标题能否看懂，含核心关键词"""
    score = 10.0
    issues = []
    title = extract_title(html)
    clean = re.sub(r'\s*\|\s*阿凤姐的故事.*$', '', title)

    # 核心关键词检测
    site_keywords = ["茶", "凤凰", "单丛", "普洱", "紫砂", "陈皮", "工夫", "壶", "茗", "茶事"]
    has_keyword = any(kw in clean for kw in site_keywords)

    if not has_keyword:
        score -= 5
        issues.append("标题不含站点核心关键词（茶/凤凰/单丛/普洱/紫砂...）")

    # 标题过短或全是废话
    if len(clean) < 12:
        score -= 5
        issues.append("标题过短，语义不完整")

    return max(score, 0), issues


# ============ 维度 3：素材时效性 ============

def check_material_freshness(html: str, filename: str) -> tuple[float, list[str]]:
    """检查素材发布时间是否在 48 小时窗口内"""
    score = 15.0
    issues = []

    # 从文件名解析文章发布日期
    date_match = re.search(r'^(\d{8})', filename)
    if not date_match:
        score -= 5
        issues.append("文件名无日期前缀")
        return score, issues

    article_date = datetime.strptime(date_match.group(1), "%Y%m%d").replace(tzinfo=CST)

    # 从正文提取素材来源和发布时间
    source = extract_material_source(html)
    source_date_str = extract_source_date(html)

    # 素材时效判断：以文件名日期为准（避免正文里提到未来活动日期造成误判）
    # 正文里的素材来源日期只在明确标注「来源」时参考，不因正文提到未来事件扣分
    source = extract_material_source(html)
    # 素材源黑名单检查
    blacklist_sources = ["hubeibidding", "招标", "采购", "Urdu", "urdu"]
    source = source.lower()
    for bad in blacklist_sources:
        if bad in source:
            score -= 5
            issues.append(f"素材源可能是低质源：{source}")
            break

    return max(score, 0), issues


# ============ 维度 4：主题匹配 ============

def check_topic_match(html: str, filename: str) -> tuple[float, list[str]]:
    """检查标题/正文/tag 是否与站点定位一致"""
    score = 15.0
    issues = []

    title = extract_title(html)
    text = extract_text(html)
    tags = extract_tags(html)

    # 站点核心主题词
    site_topics = ["凤凰单丛", "蜜兰香", "鸭屎香", "雪片", "乌岽", "普洱", "紫砂",
                   "陈皮", "工夫茶", "茶", "冲泡", "品鉴", "茶叶", "茶文化"]

    # 非主题词（跑题信号）——注意：剪纸是文件名/新闻事实成分，不判跑题
    off_topic_words = ["非遗招标", "采购公告", "政府采购", "紫藤", "Purple Cane",
                       "马来西亚", "纪录片拍摄", "乌尔都", "Urdu", "商城"]

    has_off_topic = any(w in title + text for w in off_topic_words)
    if has_off_topic:
        score -= 10
        issues.append("内容含跑题词（剪纸/招标/非茶品牌等）")

    # 主题一致性：标题关键词 vs 正文关键词
    title_keywords = set(re.findall(r'[\u4e00-\u9fff]{2,}', title))
    text_keywords = set(re.findall(r'[\u4e00-\u9fff]{2,}', text))
    overlap = title_keywords & text_keywords
    if len(overlap) < 3:
        score -= 5
        issues.append("标题与正文关键词重合度低")

    return max(score, 0), issues


# ============ 维度 5：正文原创度 ============

def check_uniqueness(html: str, all_articles: dict) -> tuple[float, list[str]]:
    """检查与其他文章的相似度"""
    score = 10.0
    issues = []

    current_text = extract_text(html)

    for other_filename, other_html in all_articles.items():
        if other_html == html:
            continue
        other_text = extract_text(other_html)

        # 计算正文相似度
        similarity = SequenceMatcher(None, current_text[:2000], other_text[:2000]).ratio()
        if similarity > 0.9:
            score -= 10
            issues.append(f"正文与 {other_filename} 相似度 {similarity:.0%}（疑似模板重复）")
            break
        elif similarity > 0.7:
            score -= 3
            issues.append(f"正文与 {other_filename} 相似度 {similarity:.0%}")

    return max(score, 0), issues


# ============ 维度 6：SEO 基础项 ============

def check_seo_elements(html: str, filename: str) -> tuple[float, list[str]]:
    """检查 canonical/og/twitter/geo/ld+json"""
    score = 15.0
    issues = []

    # 每项扣 3 分，共 5 项
    checks = {
        "canonical": ('<link rel="canonical"' in html or 'rel="canonical"' in html),
        "og:title": 'property="og:title"' in html,
        "og:image": 'property="og:image"' in html,
        "twitter:card": 'name="twitter:card"' in html,
        "geo:region": 'name="geo.region"' in html,
        "application/ld+json": 'application/ld+json' in html,
    }

    for name, present in checks.items():
        if not present:
            score -= 3
            issues.append(f"缺少 SEO 元素：{name}")

    return max(score, 0), issues


# ============ 维度 7：Schema 完整 ============

def check_schema(html: str) -> tuple[float, list[str]]:
    """检查 JSON-LD schema 完整性"""
    score = 10.0
    issues = []

    required_schemas = {
        '"@type":"Article"': "Article",
        '"@type":"LocalBusiness"': "LocalBusiness",
        '"@type":"BreadcrumbList"': "BreadcrumbList",
    }

    # 也接受带空格的写法
    for marker, name in required_schemas.items():
        if marker not in html and marker.replace('":"', '": "') not in html:
            score -= 3
            issues.append(f"缺少 {name} schema")

    return max(score, 0), issues


# ============ 维度 8：内链正确 ============

def check_internal_links(html: str, filename: str) -> tuple[float, list[str]]:
    """检查 prev/next 导航是否指向正确"""
    score = 5.0
    issues = []

    # 检查是否全站同 URL（旧问题）
    if 'href="fengcha-generations-1727871331.html"' in html:
        score -= 5
        issues.append("prev/next 指向固定旧文章（全站同 URL 问题）")

    # 检查是否有 article-nav（两种 class 名都接受）
    if 'class="article-navigation"' not in html and 'class="article-nav"' not in html:
        score -= 3
        issues.append("缺少 prev/next 导航")

    return max(score, 0), issues


# ============ 维度 9：图片 alt ============

def check_image_alts(html: str) -> tuple[float, list[str]]:
    """检查图片 alt 是否使用通用短语"""
    score = 5.0
    issues = []

    common_alts = [
        "玻璃公道杯里的茶汤特写", "干茶叶在白纸上摊开",
        "清晨斜光下的茶桌", "一双正在注水冲泡的手",
        "三只小玻璃杯并排", "木炭焙茶", "竹制茶具"
    ]

    alts = extract_img_alts(html)
    for alt in alts:
        if alt in common_alts:
            score -= 2
            issues.append(f"图片 alt 使用通用模板：{alt}")
            break

    return max(score, 0), issues


# ============ 主流程：扫描 + 评分 + 修复建议 ============

def audit_article(filename: str, html: str, all_articles: dict) -> dict:
    """对单篇文章执行全维度检查，返回评分结果"""
    result = {
        "filename": filename,
        "title": extract_title(html),
        "checks": {},
        "total_score": 0,
        "status": "合格",
        "issues": [],
    }

    # 执行所有检查
    check_functions = [
        ("标题合规", check_title_compliance, (html,)),
        ("标题语义", check_title_semantics, (html,)),
        ("素材时效", check_material_freshness, (html, filename)),
        ("主题匹配", check_topic_match, (html, filename)),
        ("正文原创", check_uniqueness, (html, all_articles)),
        ("SEO元素", check_seo_elements, (html, filename)),
        ("Schema", check_schema, (html,)),
        ("内链", check_internal_links, (html, filename)),
        ("图片alt", check_image_alts, (html,)),
    ]

    total = 0
    max_map = {
        "标题合规": 15, "标题语义": 10, "素材时效": 15,
        "主题匹配": 15, "正文原创": 10, "SEO元素": 15,
        "Schema": 10, "内链": 5, "图片alt": 5,
    }
    for name, func, args in check_functions:
        score, issues = func(*args)
        result["checks"][name] = {
            "score": score,
            "max": max_map[name],
            "issues": issues,
        }
        total += score
        result["issues"].extend(issues)

    result["total_score"] = round(total, 1)

    # 状态判定
    if result["total_score"] < 80:
        result["status"] = "不合格"
    elif result["total_score"] < 90:
        result["status"] = "建议修复"
    else:
        result["status"] = "合格"

    return result


def run_full_audit() -> list[dict]:
    """扫描 articles 目录所有 HTML，执行全站自检"""
    results = []

    # 加载所有文章（用于相似度检查）
    all_articles = {}
    for f in ARTICLES_DIR.glob("*.html"):
        with open(f, 'r', encoding='utf-8') as fh:
            all_articles[f.name] = fh.read()

    for f in ARTICLES_DIR.glob("*.html"):
        with open(f, 'r', encoding='utf-8') as fh:
            html = fh.read()

        result = audit_article(f.name, html, all_articles)
        results.append(result)

    # 按分数排序（最低分在前）
    results.sort(key=lambda x: x["total_score"])
    return results


def generate_report(results: list[dict]) -> str:
    """生成 Markdown 报告"""
    lines = [
        "# 文章质量自检报告",
        "",
        f"生成时间：{datetime.now(CST).strftime('%Y-%m-%d %H:%M:%S')}",
        f"扫描文章数：{len(results)}",
        "",
        "## 总览",
        "",
        "| 状态 | 数量 |",
        "|---|---|",
        f"| 合格 | {sum(1 for r in results if r['status'] == '合格')} |",
        f"| 建议修复 | {sum(1 for r in results if r['status'] == '建议修复')} |",
        f"| 不合格 | {sum(1 for r in results if r['status'] == '不合格')} |",
        "",
        "## 逐篇评分",
        "",
        "| 文件名 | 总分 | 状态 | 主要问题 |",
        "|---|---|---|---|",
    ]

    for r in results:
        main_issues = "；".join(r["issues"][:3]) if r["issues"] else "无"
        lines.append(f"| {r['filename']} | {r['total_score']} | {r['status']} | {main_issues} |")

    lines.append("")
    lines.append("## 不合格文章明细")
    lines.append("")

    for r in results:
        if r["status"] == "不合格":
            lines.append(f"### {r['filename']}（{r['total_score']} 分）")
            lines.append("")
            for check_name, check_data in r["checks"].items():
                if check_data["issues"]:
                    lines.append(f"- **{check_name}**（{check_data['score']}/{check_data['max']}）：{'；'.join(check_data['issues'])}")
            lines.append("")

    lines.append("## 建议修复文章明细")
    lines.append("")

    for r in results:
        if r["status"] == "建议修复":
            lines.append(f"### {r['filename']}（{r['total_score']} 分）")
            lines.append("")
            for check_name, check_data in r["checks"].items():
                if check_data["issues"]:
                    lines.append(f"- **{check_name}**（{check_data['score']}/{check_data['max']}）：{'；'.join(check_data['issues'])}")
            lines.append("")

    return "\n".join(lines)


# ============ 自动修复（可选的修复动作） ============

def auto_fix_article(filename: str, html: str, audit: dict) -> tuple[bool, list[str]]:
    """
    对不合格文章执行自动修复。
    返回 (是否修复成功, 修复动作列表)。
    """
    actions = []
    fixed = False

    # 修复 1：标题非法字符（# 「 」）→ 去除
    title = extract_title(html)
    if re.search(r'[#\u201c\u201d\u300c\u300d]', title):
        new_title = re.sub(r'[#\u201c\u201d\u300c\u300d]', '', title)
        html = html.replace(f"<title>{title}</title>", f"<title>{new_title}</title>")
        # 同步改 h1 / og:title / twitter:title
        html = re.sub(r'(<h1[^>]*>)(.*?)(</h1>)', lambda m: m.group(1) + new_title + m.group(3), html, count=1)
        html = re.sub(r'(property="og:title" content=")(.*?)(")', lambda m: m.group(1) + new_title + m.group(3), html, count=1)
        html = re.sub(r'(name="twitter:title" content=")(.*?)(")', lambda m: m.group(1) + new_title + m.group(3), html, count=1)
        actions.append(f"修复标题非法字符：{title} → {new_title}")
        fixed = True

    # 修复 2：加 canonical（如果缺）
    if '<link rel="canonical"' not in html:
        canonical_url = f"https://feng-tea.com/articles/{filename}"
        html = html.replace('</head>', f'<link rel="canonical" href="{canonical_url}">\n</head>')
        actions.append(f"添加 canonical：{canonical_url}")
        fixed = True

    # 修复 3：加 og:title / og:description / og:image（如果缺）
    if 'property="og:title"' not in html:
        og_tags = f'''<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:url" content="https://feng-tea.com/articles/{filename}">
<meta property="og:site_name" content="阿凤姐的故事">
<meta property="og:locale" content="zh_CN">'''
        html = html.replace('</head>', f'{og_tags}\n</head>')
        actions.append("添加 Open Graph 标签")
        fixed = True

    # 修复 4：加 twitter:card（如果缺）
    if 'name="twitter:card"' not in html:
        twitter_tags = f'''<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">'''
        html = html.replace('</head>', f'{twitter_tags}\n</head>')
        actions.append("添加 Twitter Card")
        fixed = True

    # 修复 5：加 Article + LocalBusiness schema（如果缺）
    if '"@type": "Article"' not in html or '"@type": "LocalBusiness"' not in html:
        schema = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "author": {"@type": "Person", "name": "阿凤姐"},
            "publisher": {"@type": "Organization", "name": "阿凤姐茶叶店（惠州凤凰茶业）"},
            "datePublished": datetime.now(CST).isoformat(),
            "inLanguage": "zh-CN"
        }
        if '"@type": "Article"' not in html:
            html = html.replace('</head>', f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>\n</head>')
            actions.append("添加 Article schema")
            fixed = True

        if '"@type": "LocalBusiness"' not in html:
            lb_schema = {
                "@context": "https://schema.org",
                "@type": "LocalBusiness",
                "name": "阿凤姐茶叶店（惠州凤凰茶业）",
                "address": {
                    "@type": "PostalAddress",
                    "streetAddress": "东湖花园一区沿江商铺89-136",
                    "addressLocality": "惠州市惠城区",
                    "addressRegion": "广东省",
                    "addressCountry": "CN"
                },
                "telephone": "+86-134-3556-7385"
            }
            html = html.replace('</head>', f'<script type="application/ld+json">{json.dumps(lb_schema, ensure_ascii=False)}</script>\n</head>')
            actions.append("添加 LocalBusiness schema")
            fixed = True

    # 修复 6：prev/next 指向固定旧文章 → 删除旧链接（后续由动态生成替代）
    if 'href="fengcha-generations-1727871331.html"' in html:
        html = re.sub(r'<a href="fengcha-generations-1727871331\.html"[^>]*>.*?</a>', '', html)
        actions.append("移除指向固定旧文章的 prev/next 链接")
        fixed = True

    return fixed, actions


def main():
    """主入口：扫描 → 评分 → 报告 → 自动修复"""
    print("=" * 60)
    print("文章质量自检器 v1.0")
    print("=" * 60)

    results = run_full_audit()

    # 生成报告
    report = generate_report(results)
    report_path = Path(__file__).parent / "文章质量自检报告.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"✅ 报告已生成：{report_path}")

    # 自动修复不合格文章
    print("\n开始自动修复不合格文章...")
    for r in results:
        if r["status"] == "不合格":
            filename = r["filename"]
            with open(ARTICLES_DIR / filename, 'r', encoding='utf-8') as f:
                html = f.read()

            fixed, actions = auto_fix_article(filename, html, r)
            if fixed:
                with open(ARTICLES_DIR / filename, 'w', encoding='utf-8') as f:
                    f.write(html)
                print(f"  ✅ 已修复：{filename}")
                for action in actions:
                    print(f"     - {action}")
            else:
                print(f"  ⚠️ 无法自动修复（需人工）：{filename}")

    # 保存 JSON 报告
    with open(AUDIT_LOG, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 审计 JSON 已保存：{AUDIT_LOG}")

    # 统计
    ok = sum(1 for r in results if r["status"] == "合格")
    warn = sum(1 for r in results if r["status"] == "建议修复")
    bad = sum(1 for r in results if r["status"] == "不合格")
    print(f"\n📊 结果：合格 {ok} 篇 / 建议修复 {warn} 篇 / 不合格 {bad} 篇")


if __name__ == "__main__":
    main()
