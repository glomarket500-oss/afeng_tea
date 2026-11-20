#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿凤姐茶站 · 文章发布流水线（规范书 §4 九步，步骤 1-7 落地）
文章: 立冬之后，换一壶秋茶
用法: python _publish_20261115.py
"""
import re, os, glob, sys, json
from pathlib import Path
from datetime import datetime

REPO = Path(r"C:\afeng_tea")
DRAFT = Path(r"C:\Users\Administrator\Desktop\MianAI知识库\MianAI知识库\vault\资料库\素材材料\茶叶素材\2026-11-14-立冬之后换一壶秋茶.md")

DATE = datetime.now().strftime("%Y-%m-%d")
DATE_COMPACT = datetime.now().strftime("%Y%m%d")
TIME_HM = datetime.now().strftime("%H:%M")
NEW_DT = f"{DATE}T{TIME_HM}:00"
ZH_DATE = f"{datetime.now().strftime('%Y年%m月%d日')} {TIME_HM}:00"
ZH_DATE_ONLY = datetime.now().strftime("%Y年%m月%d日")

TITLE = "立冬之后，换一壶秋茶"
SLUG = f"{DATE_COMPACT}立冬之后换一壶秋茶阿凤姐教你顺时而饮"
PREFIX = "qiuchu"
CATEGORY = "chaye"
LEAD = ("立冬一过，惠州东平的江风就凉得钻骨气。街上老街坊开始往我这儿跑——" +
        "「凤姐，天冷了，有没有养生的茶？」\n\n" +
        "我做了二十多年凤凰单丛，答案其实很简单：<strong>养生茶不是药，是把燥气先收一收。</strong> " +
        "立冬前后的单丛要焙得透，火气沉下去，胃就不难受；香，反而是焙过之后才出得来。")
DESC = ("立冬之后怎么喝凤凰单丛才不燥？阿凤姐讲透秋茶三件事：焙火要透、顺时而饮、秋茶老丛怎么配着喝。惠州买茶去哪，东湖花园沿江商铺89-136，电话13435567385。")
TAGS = ["#凤凰单丛", "#立冬养生", "#潮州工夫茶", "#惠州茶馆", "#老丛鸭屎香", "#秋茶批发", "#顺时而饮"]
TAG_CHIPS = ["#凤凰单丛", "#立冬养生", "#秋茶老丛", "#顺时而饮", "#惠州茶叶店", "#惠州买茶去哪"]

# 章节 -> 场景图
SCENES = [
    ("【场景开头】", "s1", "十一月的傍晚，江风起，阿凤姐在收茶"),
    ("【第一幕 · 姚老师来问养生茶】", "s2", "柜台前两罐秋茶，一泡功夫茶"),
    ("【第二幕 · 一泡茶的功夫】", "s3", "第二泡快出汤，汤色像兑了蜜的琥珀"),
    ("【第三幕 · 陈老板的三十斤】", "s4", "陈老板的三十斤，装了满满一后备箱"),
    ("【第四幕 · 顺时而饮】", "s5", "秋冬润燥，陈皮麦冬雪梨都能搭"),
    ("【尾声】", "s6", "天黑透了，最后一罐秋茶封好"),
]

QA = [
    ("Q1：立冬后喝凤凰单丛燥不燥？",
     "阿凤姐一句话讲透：「<strong>不燥的前提，是焙火足。</strong>」立冬前后的秋茶要走老火，"
     "火力沉进茶里，入口温厚不冲；配上陈皮、雪梨、麦冬，更润。怕燥的茶友，选<strong>老丛鸭屎香、蜜兰香</strong>这类高香但火气沉的，比清香的绿茶、香片更适合这个季节。"),
    ("Q2：惠州哪里能买到正宗的凤凰单丛秋茶？",
     "来 <strong>阿凤姐茶叶店（惠州凤凰茶业）</strong>！地址：<strong>惠州市惠城区东湖花园一区沿江商铺89-136</strong>，"
     "每天 <strong>9:00-21:00</strong> 营业。电话：<strong>13435567385</strong>（微信同号，支持全国快递）。"
     "店里秋茶、老丛常年有货，批发零售都做，可以先来喝一杯再定。"),
    ("Q3：怎么挑一泡焙火到位、不燥的秋茶？",
     "阿凤姐教你四招：①<strong>看干茶</strong>，条索紧结、色泽乌褐带枣红；②<strong>闻干香</strong>，是焙火香与果香交织，不是清飘的花香；"
     "③<strong>看汤色</strong>，琥珀透亮、挂壁明显；④<strong>问批号</strong>，每一罐都写清采摘季与焙火日期。"),
]


def scrub(text):
    """规范书 §2.4 隐私红线"""
    for a, b in [("林玉凤（阿凤姐）", "阿凤姐"), ("林玉鳳（阿鳳姐）", "阿鳳姐"),
                 ("林玉凤", "阿凤姐"), ("林玉鳳", "阿鳳姐")]:
        text = text.replace(a, b)
    text = re.sub(r"[ \t]*(?:💬\s*)?QQ\s*[：:]\s*107[-‑]?9790[-‑]?744", "", text)
    text = text.replace("1079790744", "")
    return text


def parse_draft(raw):
    """解析草稿：标题 / 导语 / 各幕 / FAQ / 标签"""
    lines = raw.split("\n")
    title = ""
    lead = ""
    sections = []       # [(标题, [段落...])]
    faq = []
    tags = ""
    cur = None
    buf = []
    mode = None
    pre = []            # 第一个 ## 之前的段落 = 场景开头

    for ln in lines:
        s = ln.strip()
        if s.startswith("# ") and not title:
            title = s[2:].strip()
            continue
        if s.startswith("📌"):
            mode = "lead"
            lead = s.replace("📌", "").replace("开篇回答：", "").strip()
            continue
        if re.match(r"^##\s*(FAQ|常见问题)", s, re.I):
            mode = "faq"
            continue
        if re.match(r"^##\s*(标签|话题)", s):
            mode = "tags"
            continue
        if re.match(r"^##\s*(联系方式|联系)", s):
            mode = "skip"
            continue
        if re.match(r"^##\s*(下回预告|预告)", s):
            mode = "skip"
            continue
        if s.startswith("## "):
            if cur:
                sections.append((cur, [b for b in buf if b]))
            elif pre:
                sections.append(("【场景开头】", list(pre)))
            cur = s[3:].strip()
            buf = []
            mode = "body"
            continue
        if not s:
            continue
        if mode == "lead":
            lead += " " + s
        elif mode == "faq":
            if s.startswith("**Q") or s.startswith("Q："):
                faq.append([s.replace("**", "").strip(), ""])
            elif faq:
                faq[-1][1] = s
        elif mode == "tags":
            tags += " " + s
        elif mode == "body":
            buf.append(s)
        elif mode is None:
            pre.append(s)
    if cur:
        sections.append((cur, [b for b in buf if b]))
    elif pre:
        sections.append(("【场景开头】", list(pre)))

    # 标题规范化：'第一幕 · 姚老师来问养生茶' -> '【第一幕：姚老师来问养生茶】'
    norm = []
    for h, ps in sections:
        if not (h.startswith("【") and h.endswith("】")):
            m = re.match(r"^(第[一二三四五六七八九十]+幕|场景开头|尾声)\s*[·:：\-]?\s*(.*)$", h)
            if m:
                core = m.group(1)
                sub = m.group(2).strip()
                h = f"【{core}：{sub}】" if sub else f"【{core}】"
        norm.append((h, ps))
    return title, lead, norm, faq, tags


def build_body(sections):
    """组装正文：导语 + 开篇Q&A + 各幕(每段后插场景图) + GEO + 标签"""
    out = []
    out.append(f'<p class="lead" style="font-size:1.06em;color:#4a7023;font-weight:600;line-height:1.95">{LEAD}</p>')
    out.append('<h2>🌿 开篇问答：立冬之后，凤凰单丛怎么喝才养人？</h2>')
    for q, a in QA:
        out.append(f'<p><strong>{q}</strong></p>')
        out.append(f'<p>{a}</p>')

    scene_iter = iter(SCENES)
    for head, paras in sections:
        try:
            _, key, cap = next(scene_iter)
        except StopIteration:
            key, cap = "s6", ""
        out.append(f"<h2>{head}</h2>")
        for p in paras:
            p = p.replace("**", "")
            out.append(f"<p>{p}</p>")
        out.append(
            f'<figure class="scene-fig"><img src="../images/full/{PREFIX}-{key}.webp" alt="{cap}" '
            f'width="869" height="489" loading="lazy" decoding="async">'
            f'<figcaption>{cap}</figcaption></figure>'
        )
    return "\n".join(out)


def build_page(lead, sections, faq):
    """基于模板 articles/laocha.html 生成新文章页"""
    tpl = (REPO / "articles" / "laocha.html").read_text(encoding="utf-8")

    # --- head 区替换 ---
    tpl = tpl.replace(
        "<title>🍵 老茶 | 时光的礼物 | 阿凤姐的故事</title>",
        f"<title>🍵 {TITLE} | 阿凤姐的故事</title>")
    tpl = re.sub(r'(<meta name="description" content=")[^"]*(")',
                 lambda m: m.group(1) + DESC + m.group(2), tpl)
    tpl = re.sub(r'(<meta property="og:title" content=")[^"]*(")',
                 lambda m: m.group(1) + TITLE + m.group(2), tpl)
    tpl = re.sub(r'(<meta property="og:description" content=")[^"]*(")',
                 lambda m: m.group(1) + DESC + m.group(2), tpl)
    tpl = re.sub(r'(<meta property="og:url" content=")[^"]*(")',
                 lambda m: m.group(1) + f"https://feng-tea.com/articles/{SLUG}.html" + m.group(2), tpl)
    tpl = re.sub(r'(<meta name="twitter:title" content=")[^"]*(")',
                 lambda m: m.group(1) + TITLE + m.group(2), tpl)
    tpl = re.sub(r'(<meta name="twitter:description" content=")[^"]*(")',
                 lambda m: m.group(1) + DESC + m.group(2), tpl)
    tpl = re.sub(r'(<meta property="article:published_time" content=")[^"]*(")',
                 lambda m: m.group(1) + DATE + m.group(2), tpl)
    # canonical
    tpl = re.sub(r'(<link rel="canonical" href=")[^"]*(")',
                 lambda m: m.group(1) + f"https://feng-tea.com/articles/{SLUG}.html" + m.group(2), tpl)
    # JSON-LD
    tpl = re.sub(r'("headline":\s*")[^"]*(")', lambda m: m.group(1) + TITLE + m.group(2), tpl)
    tpl = re.sub(r'("description":\s*")[^"]*(")', lambda m: m.group(1) + DESC + m.group(2), tpl)
    tpl = re.sub(r'("url":\s*")[^"]*(")',
                 lambda m: m.group(1) + f"https://feng-tea.com/articles/{SLUG}.html" + m.group(2), tpl)
    tpl = re.sub(r'("datePublished":\s*")[^"]*(")', lambda m: m.group(1) + DATE + m.group(2), tpl)
    tpl = re.sub(r'("dateModified":\s*")[^"]*(")', lambda m: m.group(1) + DATE + m.group(2), tpl)
    tpl = re.sub(r'("mainEntityOfPage":\s*\{\s*"@type":\s*"WebPage",\s*"@id":\s*")[^"]*(")',
                 lambda m: m.group(1) + f"https://feng-tea.com/articles/{SLUG}.html" + m.group(2), tpl)

    # --- 面包屑 / h1 / 时间 / 标签 ---
    tpl = re.sub(r'(<span>)[^<]*(</span>\s*</div>\s*<article>)',
                 lambda m: m.group(1) + f"🍵 {TITLE[:18]}" + m.group(2), tpl)
    tpl = re.sub(r'<h1>.*?</h1>', f"<h1>🍵 {TITLE}</h1>", tpl, flags=re.S)
    tpl = re.sub(r'<p class="article-meta-time">.*?</p>',
                 f'<p class="article-meta-time">📅 发布于 <time datetime="{DATE}">{ZH_DATE_ONLY}</time>　✍️ 阿凤姐</p>',
                 tpl, flags=re.S)
    chips = "".join(f'<a class="tag" href="../index.html#knowledge">{t}</a>' for t in TAG_CHIPS)
    tpl = re.sub(r'<div class="tags">.*?</div>',
                 f'<div class="tags">{chips}</div>', tpl, count=1, flags=re.S)

    # --- 封面图 ---
    tpl = re.sub(r'<figure class="article-hero">.*?</figure>',
                 f'<figure class="article-hero"><img src="../images/full/{PREFIX}-cover.webp" '
                 f'alt="🍵 {TITLE}" width="869" height="489" decoding="async"></figure>',
                 tpl, count=1, flags=re.S)

    # --- 正文整块替换 ---
    body = build_body(sections)
    if faq:
        body += '\n<div class="faq-section">\n<h4>📌 FAQ 常见问题</h4>\n'
        for q, a in faq:
            body += (f'<div class="faq-item">\n<p class="faq-q">{q}</p>\n'
                     f'<p class="faq-a">A：{a}</p>\n</div>\n')
        body += "</div>"

    body += (
        f'\n<h2>📍 惠州买茶去哪？阿凤姐茶叶店欢迎你</h2>\n'
        f'<p>🏪 <strong>店铺</strong>：阿凤姐茶叶店（惠州凤凰茶业）<br>\n'
        f'📍 <strong>地址</strong>：惠州市惠城区东湖花园一区沿江商铺89-136<br>\n'
        f'📱 <strong>电话</strong>：13435567385（微信同号，支持全国快递）<br>\n'
        f'⏰ <strong>营业时间</strong>：每天 9:00-21:00，全年无休<br>\n'
        f'🚗 <strong>停车</strong>：东湖花园沿街有停车位，导航搜索「凤凰茶业」即可</p>\n'
        f'<p>🍵 <strong>店内主营</strong>：潮州凤凰单丛全系列（鸭屎香、蜜兰香、老丛、芝兰香等）、新会陈皮、茶礼定制；'
        f'<strong>批发零售均可，先来喝一杯再定</strong>。</p>\n'
        f'<p class="xhs-tags">{"".join(TAGS)}</p>'
    )

    tpl = re.sub(r'<div class="article-body">.*?</div>\s*\n\s*<div class="cta-box">',
                 lambda m: f'<div class="article-body">\n{body}\n</div>\n\n<div class="cta-box">',
                 tpl, count=1, flags=re.S)

    # --- xhs-tags 样式（规范书 §4 步骤4 要求）---
    if ".xhs-tags{" not in tpl:
        tpl = tpl.replace("</style>",
                          ".xhs-tags{color:#4a7023;font-size:.9em;line-height:2;border-top:1px dashed #e2d9cb;padding-top:12px;margin-top:6px}</style>")

    # --- 上一篇/下一篇 ---
    prev = "20261112立冬过了雪片还没到阿凤姐教你一眼看穿单丛秋茶换皮的价差.html"
    nav = (f'<div class="article-nav"><span></span>'
           f'<a href="{prev}" style="text-align:right">立冬过了，雪片还没到：阿凤姐教你一眼看穿单丛秋茶换皮的价差 →</a></div>')
    tpl = re.sub(r'<div class="article-nav">.*?</div>', nav, tpl, count=1, flags=re.S)

    return tpl


def main():
    raw = DRAFT.read_text(encoding="utf-8")
    raw = scrub(raw)
    assert "林玉凤" not in raw and "林玉鳳" not in raw, "真名残留"
    assert "1079790744" not in raw, "QQ 残留"
    print("✓ 步骤1 scrub 完成，隐私红线通过")

    title, lead, sections, faq, tags = parse_draft(raw)
    print(f"✓ 步骤2 解析完成：{len(sections)} 段 / {len(faq)} 组FAQ")
    for h, ps in sections:
        print(f"    - {h}  ({len(ps)} 段)")

    page = build_page(lead, sections, faq)
    assert "林玉凤" not in page and "1079790744" not in page, "页面隐私残留"
    assert "Q1：" in page and "惠州买茶去哪" in page, "缺少Q1或GEO板块"
    assert page.count("scene-fig") == len(sections), f"场景图数不符: {page.count('scene-fig')} vs {len(sections)}"
    assert "xhs-tags" in page, "缺少话题标签"
    print(f"✓ 步骤4 文章页生成：scene-fig={page.count('scene-fig')} Q1✓ GEO✓ 标签✓")

    art_path = REPO / "articles" / f"{SLUG}.html"
    art_path.write_text(page, encoding="utf-8")
    print(f"  → {art_path.name}")

    # ---------- 步骤5 首页卡片（第1位）----------
    idx = (REPO / "index.html").read_text(encoding="utf-8")
    card = (
        f'<article class="article-card has-thumb" id="article-{SLUG}" data-category="{CATEGORY}" '
        f'data-url="articles/{SLUG}.html" itemscope itemtype="https://schema.org/Article">\n'
        f'<a class="article-thumb" href="articles/{SLUG}.html">'
        f'<img src="images/thumb/{SLUG}-hero.webp" alt="{TITLE}" width="400" height="225" '
        f'loading="lazy" decoding="async"></a>\n'
        f'<div class="card-body">\n'
        f'<h3 itemprop="headline"><a href="articles/{SLUG}.html">{TITLE}</a></h3>\n'
        f'<p class="article-meta-time">📅 发布于 <time itemprop="datePublished" datetime="{DATE}">{ZH_DATE_ONLY}</time></p>\n'
        f'<meta itemprop="description" content="{TITLE}">\n'
        f'<p class="article-excerpt" itemprop="abstract">{DESC}</p>\n'
        f'<a class="read-more" href="articles/{SLUG}.html">阅读全文 →</a>\n'
        f'<div class="tags">' + "".join(f'<span class="tag">{t}</span>' for t in TAG_CHIPS[:4]) + '</div>\n'
        f'</div>\n</article>\n'
    )
    marker = '<div class="article-list">\n'
    assert marker in idx, "找不到 article-list 标记"
    if f'id="article-{SLUG}"' not in idx:
        idx = idx.replace(marker, marker + card, 1)
        (REPO / "index.html").write_text(idx, encoding="utf-8")
    print(f"✓ 步骤5 首页卡片已插入第1位（卡片总数 {idx.count('class=\"article-card')+1}）")

    # ---------- 步骤6 sitemap ----------
    sm = (REPO / "sitemap.xml").read_text(encoding="utf-8")
    if f"{SLUG}.html" not in sm:
        entry = (f'  <url><loc>https://feng-tea.com/articles/{SLUG}.html</loc>'
                 f'<lastmod>{DATE}</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>\n')
        sm = sm.replace("</urlset>", entry + "</urlset>")
        (REPO / "sitemap.xml").write_text(sm, encoding="utf-8")
    print(f"✓ 步骤6 sitemap 已追加（<loc> 总数 {sm.count('<loc>')+1}）")

    # ---------- 步骤7 全站页脚同步 ----------
    COUNT = str(len(glob.glob(str(REPO / "articles" / "*.html"))))
    changed = 0
    for p in glob.glob(str(REPO / "articles" / "*.html")) + glob.glob(str(REPO / "products" / "*.html")):
        fp = Path(p)
        s = fp.read_text(encoding="utf-8"); o = s
        s = re.sub(r'(🔄 上次更新：[^<]*<time datetime=")[^"]*(">)[^<]*(</time>)',
                   lambda m: m.group(1) + NEW_DT + m.group(2) + ZH_DATE + m.group(3), s)
        s = re.sub(r'(共 <span id="article-count">)\d+(</span>)',
                   lambda m: m.group(1) + COUNT + m.group(2), s)
        if s != o:
            fp.write_text(s, encoding="utf-8"); changed += 1
    print(f"✓ 步骤7 页脚同步完成：{changed} 个页面更新为 {NEW_DT} / 共{COUNT}篇")

    print("\n=== 本地产物就绪，待提交 ===")
    print(f"  articles/{SLUG}.html")
    print(f"  images/full/{PREFIX}-*.webp (7张)")
    print(f"  images/thumb/{SLUG}-hero.webp")
    print(f"  index.html / sitemap.xml / 全站页脚")
    print(f"\nSLUG={SLUG}")


if __name__ == "__main__":
    main()
