# -*- coding: utf-8 -*-
"""对照交接书 §6 检查清单，逐项核对刚生成的测试文章"""
import re, os, json
from pathlib import Path
from PIL import Image

REPO = Path(r"C:\afeng_tea")
SLUG = "20261115一周茶事从凤凰山到惠州茶桌这周茶友最关心的三件事阿凤姐"
PREFIX = "a2026111562fca1"
art = REPO / "articles" / f"{SLUG}.html"
html = art.read_text(encoding="utf-8")
ok = lambda b: "✓" if b else "✗"

def tags_in(s, pat):
    m = re.search(pat, s, re.S)
    if not m:
        return []
    seg = re.sub(r"<[^>]*>", " ", m.group(1))      # 剥掉标签与属性
    seg = re.sub(r'href="[^"]*"', " ", seg)        # 否则 href 里的 #knowledge 会被误当标签
    return re.findall(r"#[^\s#<>\"，,。]+", seg)

top = tags_in(html, r'<div class="tags">(.*?)</div>')
mid = tags_in(html, r'<div class="article-tags">(.*?)</div>')
bot = tags_in(html, r'<p class="xhs-tags">(.*?)</p>')
idx = (REPO / "index.html").read_text(encoding="utf-8")
card = re.search(r'id="article-' + re.escape(SLUG) + r'".*?</article>', idx, re.S)
card_tags = tags_in(card.group(0), r'<div class="tags">(.*?)</div>') if card else []

print("=== 三处标签一致性（规范书检查项13）===")
print(f"  顶部 chips   {len(top)}: {top}")
print(f"  article-tags {len(mid)}: {mid}")
print(f"  xhs-tags     {len(bot)}: {bot}")
print(f"  首页卡片     {len(card_tags)}: {card_tags}")
same = top == mid == bot == card_tags
print(f"  {ok(same)} 四处完全一致（顺序也一致）  数量合规(6-10): {ok(6 <= len(bot) <= 10)}")
print(f"  {ok('#惠州茶叶店' in bot and '#惠州买茶去哪' in bot)} 含「惠州茶叶店」「惠州买茶去哪」")

print("\n=== 分享图（检查项15）===")
og = re.search(r'<meta property="og:image" content="([^"]+)"', html)
tw = re.search(r'<meta name="twitter:image" content="([^"]+)"', html)
ld_url = "(缺失)"
for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
    try:
        d = json.loads(m.group(1))
        img = d.get("image")
        ld_url = img[0] if isinstance(img, list) and img else (img if isinstance(img, str) else "(缺失)")
    except Exception as e:
        ld_url = f"(解析失败 {e})"
for n, v in (("og:image", og.group(1) if og else "(缺失)"),
             ("twitter:image", tw.group(1) if tw else "(缺失)"),
             ("JSON-LD image", ld_url)):
    print(f"  {ok(v.endswith(f'{PREFIX}-cover.webp'))} {n}: {v}")
print(f"  {ok('homepage-hero' not in html)} 全文无 homepage-hero 通用图")

print("\n=== keywords（检查项14）===")
kw = re.search(r'<meta name="keywords" content="([^"]*)"', html)
print(f"  {ok(bool(kw))} meta keywords: {(kw.group(1)[:90] if kw else '(缺失)')}")

print("\n=== 图片真实像素 vs 页面标注（检查项17 / 坑17）===")
imgs = re.findall(r'<img src="\.\./images/full/([^"]+)"[^>]*width="(\d+)" height="(\d+)"', html)
allok = True
for fn, w, h in imgs:
    fp = REPO / "images" / "full" / fn
    if fp.exists():
        real = Image.open(fp).size
        good = (int(w), int(h)) == real
        allok &= good
        sz = fp.stat().st_size // 1024
        print(f"  {ok(good)} {fn}: 标注{w}×{h} 实际{real[0]}×{real[1]} {sz}KB {'✓≤200KB' if sz<=200 else '✗超限'}")
    else:
        print(f"  ✗ {fn}: 文件不存在")
print(f"  {ok(allok)} 全部标注与真实像素一致")

print("\n=== 其余检查项 ===")
checks = {
    "开篇 Q1/Q2/Q3": all(f"Q{i}：" in html for i in (1, 2, 3)),
    "Q2 含地址+电话+营业时间": "东湖花园一区沿江商铺89-136" in html and "13435567385" in html and "9:00-21:00" in html,
    "导语 lead": 'class="lead"' in html,
    "GEO 板块": "惠州买茶去哪" in html,
    "场景图数(6幕)": html.count("scene-fig") == 6,
    "FAQ 无 A：A：": "A：A：" not in html and "A:A:" not in html,
    "真名残留=0": "林玉凤" not in html and "林玉鳳" not in html,
    "QQ 残留=0": "1079790744" not in html,
    "旧域名=0": "vercel.app" not in html and "netlify.app" not in html,
    "首页卡片在第1位": bool(re.search(r'<div class="article-list">\s*<article class="article-card[^>]*id="article-' + re.escape(SLUG), idx)),
    "卡片 description=摘要": bool(card and 'itemprop="description" content="这周我在店里' in card.group(0)),
}
sm = (REPO / "sitemap.xml").read_text(encoding="utf-8")
checks["sitemap 含 YYYYMMDD 前缀且逐字一致"] = f"/articles/{SLUG}.html" in sm

foot = re.findall(r'共 <span id="article-count">(\d+)</span>', html)
print(f"  页脚篇数: {foot[0] if foot else '(无)'} | articles 实际文件数: {len(list((REPO/'articles').glob('*.html')))}")
for k, v in checks.items():
    print(f"  {ok(v)} {k}")

bad = [k for k, v in checks.items() if not v]
print(f"\n{'✅ 全部通过' if not bad and same and allok else '❌ 未通过: ' + ', '.join(bad)}")
