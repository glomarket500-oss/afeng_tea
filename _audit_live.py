#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""线上文章体检：标签份数 / JSON-LD 合法性 / 分享图 / 模块完整性"""
import re
import json
import urllib.parse
import urllib.request

SLUG = "20261115三泡就淡的鸭屎香的两只盖碗阿凤姐"
URL = f"https://feng-tea.com/articles/{urllib.parse.quote(SLUG)}.html"

req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=40) as r:
    html = r.read().decode("utf-8", "ignore")
print(f"HTTP 200  {len(html)} 字节\n")

m = re.search(r'application/ld\+json">(.*?)</script>', html, re.S)
if m:
    try:
        d = json.loads(m.group(1))
        print("JSON-LD: ✅ 合法")
        print(f"  headline = {d.get('headline')}")
        print(f"  image    = {d.get('image')}")
        print(f"  keywords = {len(d.get('keywords') or [])} 个")
        print(f"  datePublished = {d.get('datePublished')}")
    except Exception as e:
        print(f"JSON-LD: ❌ 非法 —— {e}")
else:
    print("JSON-LD: ❌ 未找到")

print(f"\narticle-tags 份数: {html.count('class=\"article-tags\"')}  (应为 1)")
print(f"头部 tags 份数:    {html.count('class=\"tags\"')}  (应为 1)")
print(f"xhs-tags:          {'✅' if 'xhs-tags' in html else '❌'}")
print(f"场景图:            {html.count('scene-fig')} 张")

og = re.search(r'og:image" content="([^"]+)"', html)
tw = re.search(r'twitter:image" content="([^"]+)"', html)
print(f"\nog:image      = {og.group(1) if og else '缺失'}")
print(f"twitter:image = {tw.group(1) if tw else '缺失'}")
print(f"指向本篇封面:  {'✅' if og and 'a202611154d957b-cover' in og.group(1) else '❌'}")

desc = re.search(r'<meta name="description" content="([^"]*)"', html)
print(f"\n描述({len(desc.group(1)) if desc else 0}字): {desc.group(1)[:120] if desc else '缺失'}")
