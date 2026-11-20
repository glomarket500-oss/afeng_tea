#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查图片在位情况 + 转 PNG 供视觉复核 + 摸清首页分类锚点机制"""
import re, os
from pathlib import Path
from PIL import Image

REPO = Path(r"C:\afeng_tea")
SLUG = "20261115立冬之后换一壶秋茶阿凤姐教你顺时而饮"
OUT = REPO / "_png"
OUT.mkdir(exist_ok=True)

print("=== 图片在位 & 真实像素 ===")
files = [f"images/full/qiuchu-{k}.webp" for k in ["cover","s1","s2","s3","s4","s5","s6"]]
files.append(f"images/thumb/{SLUG}-hero.webp")
for f in files:
    p = REPO / f
    if p.exists():
        im = Image.open(p)
        print(f"  ✓ {f.split('/')[-1]:46s} {im.size}  {p.stat().st_size//1024}KB")
        im.convert("RGB").save(OUT / (Path(f).stem + ".png"))
    else:
        print(f"  ✗ {f}  不存在")

print("\n=== git 是否已跟踪这些文件 ===")
import subprocess
r = subprocess.run(["git","ls-files","images/full/qiuchu-cover.webp",
                    f"images/thumb/{SLUG}-hero.webp"], cwd=str(REPO),
                   capture_output=True, text=True)
print(r.stdout.strip() or "  (无输出 = 未跟踪)")

print("\n=== index.html 分类筛选机制 ===")
idx = (REPO / "index.html").read_text(encoding="utf-8")
for pat in [r'data-cat[a-z-]*="[^"]*"', r"filterCategory[^;\n]{0,120}",
            r"category[^;\n]{0,120}", r"#[a-z]{4,8}\b"]:
    found = re.findall(pat, idx)
    uniq = sorted(set(found))
    if uniq:
        print(f"  {pat[:34]:36s} -> {uniq[:12]}")

print("\n=== index.html 中 JS 过滤/锚点相关行 ===")
for m in re.finditer(r'<script[^>]*>(.*?)</script>', idx, re.S):
    s = m.group(1)
    for line in s.split("\n"):
        if re.search(r"cat|anchor|hash|filter|location\.hash", line, re.I):
            print("   ", line.strip()[:180])

print("\n=== 其他文章的 tags 链接指向统计 ===")
import glob
from collections import Counter
c = Counter()
for f in glob.glob(str(REPO/"articles"/"*.html")):
    t = Path(f).read_text(encoding="utf-8")
    m = re.search(r'<div class="tags">(.*?)</div>', t, re.S)
    if m:
        for h in re.findall(r'href="([^"]+)"', m.group(1)):
            c[h] += 1
for k, v in c.most_common(12):
    print(f"   {v:4d} × {k}")
