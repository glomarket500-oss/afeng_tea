# -*- coding: utf-8 -*-
"""检查一篇文章页里所有 ld+json 块是否合法 JSON，并核对关键字段"""
import re
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
html = path.read_text(encoding="utf-8")
blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
print(f"文件: {path.name}")
print(f"ld+json 块数: {len(blocks)}")
allok = True
for i, b in enumerate(blocks, 1):
    try:
        d = json.loads(b)
        img = d.get("image")
        img = img[0] if isinstance(img, list) and img else img
        kw = d.get("keywords")
        print(f"  [{i}] ✓ 合法 JSON  image={img}")
        print(f"      headline={d.get('headline')}")
        print(f"      keywords={len(kw) if isinstance(kw, list) else kw}")
        print(f"      desc_len={len(d.get('description',''))}  首40字={d.get('description','')[:40]}")
        if "homepage-hero" in str(img):
            print("      ✗ 分享图仍是首页通用图"); allok = False
    except Exception as e:
        print(f"  [{i}] ✗ 非法 JSON: {e}")
        allok = False
print("\n" + ("✅ 全部合法，分享图正确" if allok else "❌ 有问题"))
sys.exit(0 if allok else 1)
