# -*- coding: utf-8 -*-
"""全站扫描：JSON-LD 结构化数据健康状况
统计每篇文章的：
 - ld+json 是否合法 JSON
 - image 指向：本篇封面 / 首页通用图 homepage-hero / 其它 / 缺失
 - meta keywords 是否存在
只读，不修改任何文件。
"""
import re
import json
import collections
from pathlib import Path

REPO = Path(r"C:\afeng_tea")
SITE = "https://feng-tea.com"

rows = []
for p in sorted((REPO / "articles").glob("*.html")):
    html = p.read_text(encoding="utf-8")
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    valid = None
    img_kind = "无ld+json"
    detail = ""
    for b in blocks:
        try:
            d = json.loads(b)
        except Exception as e:
            valid = False
            detail = str(e)[:60]
            continue
        valid = True if valid is None else valid
        img = d.get("image")
        u = img[0] if isinstance(img, list) and img else (img if isinstance(img, str) else "")
        if not u:
            img_kind = "image缺失"
        elif "homepage-hero" in u:
            img_kind = "首页通用图"
        elif "/images/full/" in u or "/images/thumb/" in u:
            img_kind = "本篇封面"
        else:
            img_kind = "其它:" + u[-30:]
    kw = 'name="keywords"' in html
    rows.append((p.name, valid, img_kind, kw, detail))

total = len(rows)
c_img = collections.Counter(r[2] for r in rows)
c_valid = collections.Counter(r[1] for r in rows)
no_kw = sum(1 for r in rows if not r[3])

print(f"文章总数: {total}\n")
print("=== JSON-LD 是否合法 ===")
for k, v in c_valid.items():
    print(f"  {str(k):8s}: {v}")
print("\n=== 分享图 image 指向 ===")
for k, v in c_img.most_common():
    print(f"  {k:12s}: {v}")
print(f"\n=== 缺 meta keywords: {no_kw} 篇 ===")

bad = [r for r in rows if r[1] is False or r[2] != "本篇封面"]
print(f"\n=== 需要处理的: {len(bad)} 篇 ===")
for name, valid, kind, kw, detail in bad[:15]:
    flag = "坏JSON" if valid is False else kind
    print(f"  [{flag}] {name[:44]}  {detail}")
if len(bad) > 15:
    print(f"  …另有 {len(bad) - 15} 篇")

# 坏 JSON 的原因归类
errs = collections.Counter()
for name, valid, kind, kw, detail in rows:
    if valid is False:
        if "Expecting ',' delimiter" in detail or "Invalid \\escape" in detail or "Unterminated" in detail:
            errs["字符串里有未转义的引号/换行"] += 1
        else:
            errs[detail] += 1
if errs:
    print("\n=== 坏 JSON 原因 ===")
    for k, v in errs.most_common():
        print(f"  {v:3d} 篇  {k}")
