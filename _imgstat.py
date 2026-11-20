#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""配图客观体检：亮度/色彩分布/边缘复杂度 + 导出唯一名副本供视觉复核"""
import hashlib
from PIL import Image, ImageStat
from pathlib import Path

REPO = Path(r"C:\afeng_tea")
OUT = Path(r"C:\Users\Administrator\AppData\Local\hermes\cache\scratch\imgcheck2")
OUT.mkdir(parents=True, exist_ok=True)

names = ["qiuchu-cover", "qiuchu-s1", "qiuchu-s2", "qiuchu-s3", "qiuchu-s4", "qiuchu-s5", "qiuchu-s6"]
for n in names:
    f = REPO / "images" / "full" / f"{n}.webp"
    im = Image.open(f).convert("RGB")
    st = ImageStat.Stat(im)
    r, g, b = st.mean
    gray = im.convert("L")
    gstd = ImageStat.Stat(gray).stddev[0]
    colors = im.resize((120, 68)).getcolors(120 * 68)
    uniq = len(colors) if colors else ">8160"
    # 边缘密度（信息量粗略指标）
    edge = gray.filter(__import__("PIL.ImageFilter", fromlist=["FIND_EDGES"]).FIND_EDGES)
    estat = ImageStat.Stat(edge)
    print(f"{n:14s} {im.size} 均值RGB=({r:.0f},{g:.0f},{b:.0f}) 灰度std={gstd:.1f} "
          f"边缘std={estat.stddev[0]:.1f} 颜色数={uniq} {f.stat().st_size//1024}KB")

# 唯一名副本（规避可能的缓存）
for n in names:
    f = REPO / "images" / "full" / f"{n}.webp"
    h = hashlib.md5(f.read_bytes()).hexdigest()[:8]
    Image.open(f).convert("RGB").save(OUT / f"{n}_{h}.jpg", "JPEG", quality=92)
print("\n唯一名副本:", OUT)
