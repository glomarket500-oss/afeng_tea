# -*- coding: utf-8 -*-
"""线上复核：抓取指定文章 URL，核对隐私/分享图/JSON-LD/标签/场景图"""
import re
import sys
import json
import urllib.request
import urllib.parse

url = sys.argv[1]
_p = urllib.parse.urlsplit(url)
url = urllib.parse.urlunsplit((_p.scheme, _p.netloc, urllib.parse.quote(_p.path), _p.query, _p.fragment))
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    code = r.status
    html = r.read().decode("utf-8", "ignore")

print(f"HTTP {code}  {len(html)} bytes")
print(f"URL: {url}\n")

ld_ok, ld_img, ld_kw = None, "", 0
for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
    try:
        d = json.loads(m.group(1))
        ld_ok = True
        img = d.get("image")
        ld_img = img[0] if isinstance(img, list) and img else img
        kw = d.get("keywords")
        ld_kw = len(kw) if isinstance(kw, list) else 0
    except Exception as e:
        ld_ok = False
        ld_img = f"(非法 JSON: {e})"

og = re.search(r'<meta property="og:image" content="([^"]*)"', html)
tw = re.search(r'<meta name="twitter:image" content="([^"]*)"', html)
top = re.search(r'<div class="tags">(.*?)</div>', html, re.S)
mid = re.search(r'<div class="article-tags">(.*?)</div>', html, re.S)
bot = re.search(r'<p class="xhs-tags">(.*?)</p>', html, re.S)


def tg(m):
    if not m:
        return []
    seg = re.sub(r"<[^>]*>", " ", m.group(1))
    seg = re.sub(r'href="[^"]*"', " ", seg)
    return re.findall(r"#[^\s#<>\"，,。]+", seg)


t_top, t_mid, t_bot = tg(top), tg(mid), tg(bot)

checks = {
    "JSON-LD 合法": ld_ok is True,
    "JSON-LD 分享图 = 本篇封面": "cover.webp" in str(ld_img),
    "og:image = 本篇封面": bool(og) and "cover.webp" in og.group(1),
    "twitter:image = 本篇封面": bool(tw) and "cover.webp" in tw.group(1),
    "全文无 homepage-hero": "homepage-hero" not in html,
    "三处标签一致": t_top == t_mid == t_bot and len(t_bot) > 0,
    "含惠州茶叶店/惠州买茶去哪": "#惠州茶叶店" in t_bot and "#惠州买茶去哪" in t_bot,
    "meta keywords": 'name="keywords"' in html,
    "开篇 Q1/Q2/Q3": all(f"Q{i}：" in html for i in (1, 2, 3)),
    "GEO 板块": "惠州买茶去哪" in html,
    "导语 lead": 'class="lead"' in html,
    "场景图 ≥4": html.count("scene-fig") >= 4,
    "真名=0": "林玉凤" not in html and "林玉鳳" not in html,
    "QQ=0": "1079790744" not in html,
    "旧域名=0": "vercel.app" not in html and "netlify.app" not in html,
}
for k, v in checks.items():
    print(f"  {'✓' if v else '✗'} {k}")
print(f"\n  JSON-LD keywords: {ld_kw} 个｜标签数: {len(t_bot)}")
bad = [k for k, v in checks.items() if not v]
print("\n" + ("✅ 线上全部通过" if not bad else "❌ 未通过: " + ", ".join(bad)))
sys.exit(0 if not bad else 1)
