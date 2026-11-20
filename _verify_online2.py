#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""线上验证（中文 slug 百分号编码）"""
import sys
import re
import time
import urllib.request
import urllib.parse

SLUG = "20261115三泡就淡的鸭屎香的两只盖碗阿凤姐"
SITE = "https://feng-tea.com"
STORE_ADDR = "东湖花园一区沿江商铺89-136"
STORE_TEL = "13435567385"

enc = urllib.parse.quote(SLUG)
url = f"{SITE}/articles/{enc}.html"
print(f"URL: {url}\n")

html = None
for att in range(6):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            html = r.read().decode("utf-8", "ignore")
        print(f"✓ HTTP 200（第 {att+1} 次尝试），{len(html)} 字节")
        break
    except urllib.error.HTTPError as e:
        print(f"  第 {att+1} 次: HTTP {e.code}")
    except Exception as e:
        print(f"  第 {att+1} 次: {type(e).__name__}")
    time.sleep(15)

if not html:
    print("\n❌ 页面不可达")
    sys.exit(1)

checks = {
    "h1 标题": "三泡就淡的鸭屎香" in html,
    "lead 导语": 'class="lead"' in html,
    "开篇 Q1": "Q1：" in html,
    "开篇 Q2 本地转化": STORE_ADDR in html and STORE_TEL in html,
    "GEO 板块": "惠州买茶去哪" in html,
    "xhs-tags 话题标签": "xhs-tags" in html,
    "article-tags 模块": 'class="article-tags"' in html,
    "场景图 ≥4": html.count("scene-fig") >= 4,
    "og:image 本篇封面": "a202611154d957b-cover.webp" in html,
    "canonical 正确": f"{SLUG}.html" in html or enc in html,
    "FAQ 区块": "faq-section" in html,
}
print("\n=== 模块校验 ===")
bad = []
for k, v in checks.items():
    print(f"  {'✓' if v else '✗'} {k}")
    if not v:
        bad.append(k)

print("\n=== 隐私红线（必须全 0）===")
for k in ["林玉凤", "林玉鳳", "1079790744", "vercel.app", "netlify.app"]:
    n = html.count(k)
    print(f"  {'✓' if n == 0 else '✗'} {k}: {n}")

print("\n=== 配图可达性 ===")
imgs = re.findall(r'src="\.\./images/full/([^"]+)"', html)
for im in dict.fromkeys(imgs):
    iu = f"{SITE}/images/full/{urllib.parse.quote(im)}"
    try:
        req = urllib.request.Request(iu, headers={"User-Agent": "Mozilla/5.0"}, method="HEAD")
        with urllib.request.urlopen(req, timeout=20) as r:
            print(f"  ✓ {im}  HTTP {r.status}")
    except Exception as e:
        print(f"  ✗ {im}  {e}")

print("\n" + "=" * 60)
if bad:
    print(f"⚠ 未通过 {len(bad)} 项: {', '.join(bad)}")
else:
    print("✅ 线上验证全部通过")
print(f"文章地址: {url}")
