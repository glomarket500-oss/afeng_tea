# -*- coding: utf-8 -*-
"""把已生成但未推送的文章页按规范书修到合规（不改正文，只修元数据/标签）：
 - JSON-LD image → 本篇封面（原来指向 homepage-hero 通用图）
 - 顶部 chips / article-tags / xhs-tags / 首页卡片 四处标签同一套、顺序一致
 - meta keywords 与 JSON-LD keywords 同步
用法: python _fix_compliance.py <slug> <prefix>
"""
import re
import json
import sys
from pathlib import Path

sys.path.insert(0, r"C:\afeng_tea")
import publish_new as P   # 复用 rebuild_jsonld / CASE_TAGS / SITE / REPO

slug = sys.argv[1] if len(sys.argv) > 1 else "20261115三泡就淡的鸭屎香的两只盖碗阿凤姐"
prefix = sys.argv[2] if len(sys.argv) > 2 else "a202611154d957b"

art = P.REPO / "articles" / f"{slug}.html"
if not art.exists():
    raise SystemExit(f"❌ 文章页不存在: {art}")
html = art.read_text(encoding="utf-8")
before = html

# ---- 1. 以底部 xhs-tags 为基准重建统一标签 ----
m = re.search(r'<p class="xhs-tags">(.*?)</p>', html, re.S)
tags = re.findall(r"#[^\s#<>\"，,。]+", re.sub(r"<[^>]*>", " ", m.group(1))) if m else []
for t in P.CASE_TAGS:
    if t not in tags:
        tags.append(t)
tags = tags[:10]

title = re.search(r"<h1>🍵 (.*?)</h1>", html, re.S).group(1).strip()
desc = re.search(r'<meta name="description" content="([^"]*)"', html).group(1)
date = re.search(r'<time datetime="(\d{4}-\d{2}-\d{2})"', html).group(1)
url = f"{P.SITE}/articles/{slug}.html"
cover = f"{P.SITE}/images/full/{prefix}-cover.webp"
kw = ",".join(x.lstrip("#") for x in tags)

# ---- 2. JSON-LD 重建 ----
html = P.rebuild_jsonld(html, title, desc, url, date, cover, kw)

# 若原 LD 块是坏 JSON（描述里有未转义换行/引号），json.loads 会失败 → 上面等于没改，这里整段重建
if "homepage-hero" in html or f'"{cover}"' not in html:
    clean_desc = re.sub(r"[\r\n\t]+", " ", desc).strip()
    new_ld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": f"🍵 {title}",
        "description": clean_desc,
        "image": [cover],
        "url": url,
        "datePublished": date,
        "dateModified": date,
        "author": {"@type": "Person", "name": "阿凤姐"},
        "publisher": {
            "@type": "Organization",
            "name": "溢豐堂 · 阿凤姐的故事",
            "address": {"@type": "PostalAddress", "addressLocality": "惠城區",
                        "addressRegion": "廣東省", "addressCountry": "CN"},
        },
        "articleSection": "茶文化",
        "inLanguage": "zh-Hant",
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
        "keywords": kw.split(","),
    }
    html = re.sub(r'(<script type="application/ld\+json">).*?(</script>)',
                  lambda m: m.group(1) + "\n" + json.dumps(new_ld, ensure_ascii=False, indent=2) + "\n" + m.group(2),
                  html, count=1, flags=re.S)
    print("  ⓘ 原 LD 块非合法 JSON，已整段重建")

# ---- 3. meta keywords ----
if '<meta name="keywords"' in html:
    html = re.sub(r'(<meta name="keywords" content=")[^"]*(")', lambda m: m.group(1) + kw + m.group(2),
                  html, count=1)
else:
    html = html.replace('<meta name="description"',
                        f'<meta name="keywords" content="{kw}">\n<meta name="description"', 1)

# ---- 4. 顶部 chips + article-tags ----
chips = "".join(f'<a class="tag" href="../index.html#knowledge">{x}</a>' for x in tags)
html = re.sub(r'<div class="tags">.*?</div>',
              f'<div class="tags">{chips}</div>\n<div class="article-tags">'
              + "".join(f'<span class="tag">{x}</span>' for x in tags) + "</div>",
              html, count=1, flags=re.S)
# ---- 5. 底部 xhs-tags ----
html = re.sub(r'<p class="xhs-tags">.*?</p>',
              f'<p class="xhs-tags">{"".join(tags)}</p>', html, count=1, flags=re.S)

art.write_text(html, encoding="utf-8")

# ---- 6. 首页卡片标签对齐 ----
idx_p = P.REPO / "index.html"
idx = idx_p.read_text(encoding="utf-8")
mcard = re.search(r'(id="article-' + re.escape(slug) + r'".*?</article>)', idx, re.S)
card_note = "首页无此卡片"
if mcard:
    card = mcard.group(1)
    new_card = re.sub(r'<div class="tags">.*?</div>',
                      '<div class="tags">' + "".join(f'<span class="tag">{x}</span>' for x in tags) + "</div>",
                      card, count=1, flags=re.S)
    if new_card != card:
        idx = idx.replace(card, new_card, 1)
        idx_p.write_text(idx, encoding="utf-8")
        card_note = "首页卡片标签已对齐"

# ---- 7. 自检 ----
print(f"标题: {title}")
print(f"标签({len(tags)}): {' '.join(tags)}")
print(f"封面: {cover}")
print(f"{card_note}")
checks = {
    "JSON-LD image = 本篇封面": f'"image": [\n    "{cover}"' in html or f'"{cover}"' in html,
    "全文无 homepage-hero": "homepage-hero" not in html,
    "meta keywords": kw in html,
    "article-tags 存在": 'class="article-tags"' in html,
    "有改动": html != before or card_note != "首页无此卡片",
}
for k, v in checks.items():
    print(f"  {'✓' if v else '✗'} {k}")
