#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""摸清站点惯例：标签模块命名、锚点、img 尺寸、meta keywords"""
import re, glob, json
from pathlib import Path
REPO = Path(r"C:\afeng_tea")
SLUG = "20261115立冬之后换一壶秋茶阿凤姐教你顺时而饮"

# 1) 各文章页用的标签 class
cls = {}
for f in glob.glob(str(REPO / "articles" / "*.html")):
    t = Path(f).read_text(encoding="utf-8")
    has = tuple(sorted(set(re.findall(r'class="(article-tags|xhs-tags|tags)"', t))))
    cls[has] = cls.get(has, 0) + 1
print("=== 各文章页标签 class 组合统计 ===")
for k, v in sorted(cls.items(), key=lambda x: -x[1]):
    print(f"  {v:3d} 篇  {k}")

# 2) 参考文章（最近正式上线）
ref = REPO / "articles" / "20261112立冬过了雪片还没到阿凤姐教你一眼看穿单丛秋茶换皮的价差.html"
r = ref.read_text(encoding="utf-8")
print("\n=== 参考文章 20261112 ===")
for pat in [r'<meta name="keywords" content="[^"]*"', r'<meta property="og:image" content="[^"]*"',
            r'<meta name="twitter:image" content="[^"]*"', r'"keywords"\s*:\s*\[[^\]]*\]',
            r'"image"\s*:\s*\[[^\]]*\]']:
    m = re.search(pat, r)
    print(f"  {pat[:38]:40s} -> {m.group(0)[:160] if m else '无'}")
for m in re.finditer(r'<div class="(article-tags|tags)">.*?</div>', r, re.S):
    print("  TAGS DIV:", m.group(0)[:400]); break
m = re.search(r'<p class="xhs-tags">(.*?)</p>', r, re.S)
print("  XHS:", m.group(1)[:300] if m else "无")

# 3) index.html 的锚点
idx = (REPO / "index.html").read_text(encoding="utf-8")
print("\n=== index.html 锚点 id ===")
print(sorted(set(re.findall(r'id="([a-z\-]+)"', idx))))
print("=== data-category 取值 ===")
print(sorted(set(re.findall(r'data-category="([a-z]+)"', idx))))

# 4) 首页卡片：参考文章的卡片标签 & description
m = re.search(r'<article class="article-card.*?id="article-20261112[^"]*".*?</article>', idx, re.S)
if m:
    c = m.group(0)
    md = re.search(r'<meta itemprop="description" content="([^"]*)"', c)
    mt = re.search(r'<div class="tags">(.*?)</div>', c, re.S)
    print("\n=== 参考卡片 description ===\n ", (md.group(1)[:120] if md else "无"))
    print("=== 参考卡片 tags ===\n ", (mt.group(1)[:400] if mt else "无"))

# 5) 本文图片真实像素 vs 标注
print("\n=== 本文 7 图真实像素 vs 页面标注 ===")
from PIL import Image
art = (REPO / "articles" / f"{SLUG}.html").read_text(encoding="utf-8")
for src, w, h in re.findall(r'<figure class="scene-fig"><img src="([^"]+)"[^>]*?width="(\d+)" height="(\d+)"', art):
    p = REPO / src.replace("../", "").replace("images/", "images/")
    real = Image.open(p).size if p.exists() else None
    okk = real == (int(w), int(h))
    print(f"  {'OK ' if okk else 'BAD'} {src.split('/')[-1]:22s} 标注={w}x{h} 真实={real}")
for src, w, h in re.findall(r'<img src="(images/full/[^"]+)"[^>]*?width="(\d+)" height="(\d+)"', idx):
    p = REPO / src
    real = Image.open(p).size if p.exists() else None
    print(f"  首页 {src.split('/')[-1]:22s} 标注={w}x{h} 真实={real}")
