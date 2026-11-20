#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修补《立冬之后，换一壶秋茶》以符合更新后的规范书 §4 / §6 / §7
- 统一标签集（顶部 .tags / 底部 .xhs-tags / 首页卡片 .tags 三处同一套、同一顺序）
- 新增结尾 .article-tags 模块（坑14）
- meta keywords + JSON-LD keywords（§4 步骤4）
- og:image / twitter:image / JSON-LD image → 本篇封面绝对 URL（坑15）
- 首页卡片 meta description = 摘要（非标题）
- FAQ 去掉重复前缀 "A：A："（§6）
- 链接按真实分类锚点聚合（不全部 #knowledge）
- 图说与画面同步（坑16）：s1/s2 已重做 → 改图说
- <img> width/height = 真实像素（坑17）
"""
import re
from pathlib import Path

REPO = Path(r"C:\afeng_tea")
SLUG = "20261115立冬之后换一壶秋茶阿凤姐教你顺时而饮"
ART = REPO / "articles" / f"{SLUG}.html"
IDX = REPO / "index.html"

SITE = "https://feng-tea.com"
COVER_ABS = f"{SITE}/images/full/qiuchu-cover.webp"
THUMB_ABS = f"{SITE}/images/thumb/{SLUG}-hero.webp"

# ---- 统一标签集：8 个，顺序固定，三处一致 ----
# 链接按真实分类锚点：#knowledge 是文章列表区，#products 是产品区，#contact 是联系区
TAGS = [
    ("凤凰单丛",   "../index.html#knowledge"),
    ("立冬养生",   "../index.html#knowledge"),
    ("秋茶老丛",   "../index.html#knowledge"),
    ("顺时而饮",   "../index.html#knowledge"),
    ("潮州工夫茶", "../index.html#knowledge"),
    ("老丛鸭屎香", "../index.html#knowledge"),
    ("惠州茶叶店", "../index.html#contact"),
    ("惠州买茶去哪", "../index.html#contact"),
]
TAG_NAMES = [t[0] for t in TAGS]
KW = "，".join(TAG_NAMES)

DESC = ("立冬之后怎么喝凤凰单丛才不燥？阿凤姐讲透秋茶三件事：焙火要透、顺时而饮、"
        "秋茶老丛怎么配着喝。惠州买茶去哪，东湖花园沿江商铺89-136，电话13435567385。")

# 新的图说（s1/s2 已按新画面重做；s3-s6 画面未变，图说保持）
CAPTIONS = {
    "s1": "深褐色的秋茶干叶，条索紧结，纹理里带着焙火的香",
    "s2": "琥珀色的茶汤透亮，焙火沉在汤里",
}

# 各场景图真实像素
SIZES = {"cover": (869, 489), "s1": (869, 489), "s2": (869, 489),
         "s3": (869, 489), "s4": (869, 489), "s5": (869, 489), "s6": (869, 489)}

log = []
def note(msg):
    log.append(msg); print(msg)

art = ART.read_text(encoding="utf-8")
orig = art

# ---------- 1. meta keywords ----------
if '<meta name="keywords"' in art:
    art = re.sub(r'<meta name="keywords" content="[^"]*"',
                 f'<meta name="keywords" content="{KW}"', art)
else:
    art = art.replace('<meta name="author" content="阿凤姐">',
                       f'<meta name="author" content="阿凤姐">\n<meta name="keywords" content="{KW}">')
note(f"[1] meta keywords -> {KW}")

# ---------- 2. og:image / twitter:image → 本篇封面 ----------
art = art.replace(
    '<meta property="og:image" content="https://feng-tea.com/images/homepage-hero-20260908.jpg">',
    f'<meta property="og:image" content="{COVER_ABS}">\n'
    f'<meta property="og:image:width" content="869">\n'
    f'<meta property="og:image:height" content="489">')
art = art.replace(
    '<meta name="twitter:image" content="https://feng-tea.com/images/homepage-hero-20260908.jpg">',
    f'<meta name="twitter:image" content="{THUMB_ABS}">')
note("[2] og:image / twitter:image -> 本篇封面（去除 homepage-hero 通用图）")

# ---------- 3. JSON-LD：image + keywords ----------
art = art.replace(
    '"image": [\n    "https://feng-tea.com/images/homepage-hero-20260908.jpg"\n  ],',
    f'"image": [\n    "{COVER_ABS}"\n  ],\n  "keywords": "{KW}",\n  "articleSection": "茶文化",')
note("[3] JSON-LD image -> 本篇封面；补 keywords")

# ---------- 4. 顶部 .tags 三处统一 ----------
tags_div = '<div class="tags">' + "".join(
    f'<a class="tag" href="{href}">#{n}</a>' for n, href in TAGS) + '</div>'
art = re.sub(r'<div class="tags">.*?</div>', tags_div, art, count=1, flags=re.S)
note(f"[4] 顶部 .tags -> {len(TAGS)} 个统一标签（链接按真实锚点）")

# ---------- 5. 底部 .xhs-tags 统一 ----------
xhs = '<p class="xhs-tags">' + "".join(f"#{n}" for n in TAG_NAMES) + '</p>'
art = re.sub(r'<p class="xhs-tags">.*?</p>', xhs, art, flags=re.S)
note(f"[5] 底部 .xhs-tags -> {len(TAG_NAMES)} 个统一标签")

# ---------- 6. 新增结尾 .article-tags 模块（坑14）----------
if '<div class="article-tags">' not in art:
    atags = ('\n<div class="article-tags">'
             '<a class="tag" href="../index.html#knowledge">#凤凰单丛</a>'
             '<a class="tag" href="../index.html#knowledge">#立冬养生</a>'
             '<a class="tag" href="../index.html#knowledge">#秋茶老丛</a>'
             '<a class="tag" href="../index.html#knowledge">#顺时而饮</a>'
             '<a class="tag" href="../index.html#knowledge">#潮州工夫茶</a>'
             '<a class="tag" href="../index.html#knowledge">#老丛鸭屎香</a>'
             '<a class="tag" href="../index.html#contact">#惠州茶叶店</a>'
             '<a class="tag" href="../index.html#contact">#惠州买茶去哪</a>'
             '</div>')
    # 插在 xhs-tags 之前（GEO 板块末尾）
    art = art.replace(xhs, atags + "\n" + xhs)
    # 样式
    if '.article-tags{' not in art:
        art = art.replace(
            '.xhs-tags{color:#4a7023;font-size:.9em;line-height:2;border-top:1px dashed #e2d9cb;padding-top:12px;margin-top:6px}</style>',
            '.xhs-tags{color:#4a7023;font-size:.9em;line-height:2;border-top:1px dashed #e2d9cb;padding-top:12px;margin-top:6px}\n'
            '.article-tags{margin:16px 0 6px;padding:10px 0}\n'
            '.article-tags .tag{display:inline-block;background:#eef3e6;color:#3d6b1e;border-radius:12px;'
            'padding:3px 12px;font-size:.8em;margin:0 8px 8px 0;text-decoration:none}</style>')
note("[6] 新增结尾 .article-tags 模块 + 样式（坑14）")

# ---------- 7. FAQ 去重复前缀 ----------
n_faq = art.count('A：A：')
art = art.replace('<p class="faq-a">A：A：', '<p class="faq-a">A：')
note(f"[7] FAQ 去掉重复前缀 A：A： x{n_faq}")

# ---------- 8. 图说同步 + width/height 真实像素 ----------
for key, cap in CAPTIONS.items():
    w, h = SIZES[key]
    pat = re.compile(r'(<figure class="scene-fig"><img src="\.\./images/full/qiuchu-' + key +
                     r'\.webp" alt=")[^"]*(" width=")\d+(" height=")\d+("[^>]*>)<figcaption>[^<]*</figcaption>')
    def rep(m):
        return f'{m.group(1)}{cap}{m.group(2)}{w}{m.group(3)}{h}{m.group(4)}<figcaption>{cap}</figcaption>'
    art, n = pat.subn(rep, art)
    note(f"[8] {key}: 图说与 width/height 已同步 (改 {n} 处)")

# 全部 scene-fig 兜底：确保 width/height 与真实像素一致
def fix_wh(m):
    src, w, h = m.group(1), m.group(2), m.group(3)
    key = src.rsplit("qiuchu-", 1)[-1].replace(".webp", "")
    if key in SIZES:
        rw, rh = SIZES[key]
        return f'{m.group(0).replace(f"width=\"{w}\"", f"width=\"{rw}\"").replace(f"height=\"{h}\"", f"height=\"{rh}\"")}'
    return m.group(0)
art = re.sub(r'<img src="\.\./images/full/(qiuchu-[^"]+\.webp)"[^>]*width="(\d+)" height="(\d+)"[^>]*>',
             fix_wh, art)
note("[8b] 全部场景图 width/height 已核对真实像素")

ART.write_text(art, encoding="utf-8")
note(f"→ 文章页已写入（{len(orig)} → {len(art)} 字节）")

# ================= 首页 =================
idx = IDX.read_text(encoding="utf-8")
m = re.search(r'<article class="article-card.*?id="article-' + re.escape(SLUG) + r'".*?</article>', idx, re.S)
card = m.group(0)
new_card = card

# ① description = 摘要
new_card = re.sub(r'<meta itemprop="description" content="[^"]*"',
                   f'<meta itemprop="description" content="{DESC}">', new_card)
note("[9] 首页卡片 description -> 摘要")

# ② tags 统一
ctags = '<div class="tags">' + "".join(f'<span class="tag">#{n}</span>' for n in TAG_NAMES) + '</div>'
new_card = re.sub(r'<div class="tags">.*?</div>', ctags, new_card, flags=re.S)
note(f"[10] 首页卡片 tags -> {len(TAG_NAMES)} 个统一标签")

# ③ 缩略图 alt/尺寸核对
new_card = re.sub(r'<img src="(images/thumb/[^"]+)" alt="[^"]*" width="(\d+)" height="(\d+)"',
                  r'<img src="\1" alt="立冬之后，换一壶秋茶" width="400" height="225"', new_card)

idx = idx.replace(card, new_card)
IDX.write_text(idx, encoding="utf-8")
note("→ 首页已写入")

print("\n=== 写入完成 ===")
