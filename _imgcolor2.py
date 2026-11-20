#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""轻量图像分析（纯 PIL，无 numpy）：红色占比/暗部/四角取色"""
from PIL import Image
import glob
from pathlib import Path

PNG = Path(r"C:\afeng_tea\_png")
for f in sorted(glob.glob(str(PNG / "qiuchu-*.png"))):
    im = Image.open(f).convert("RGB")
    w, h = im.size
    small = im.resize((217, 122), Image.BILINEAR)
    px = list(small.getdata())
    n = len(px)
    red = sum(1 for (R, G, B) in px if R > 120 and R - G > 45 and R - B > 45)
    dark = sum(1 for (R, G, B) in px if max(R, G, B) < 70)
    bright = sum(1 for (R, G, B) in px if min(R, G, B) > 240)
    mr = sum(p[0] for p in px) / n
    mg = sum(p[1] for p in px) / n
    mb = sum(p[2] for p in px) / n
    top = list(small.crop((0, 0, 217, 61)).getdata())
    bot = list(small.crop((0, 61, 217, 122)).getdata())
    tr = sum(1 for (R, G, B) in top if R > 120 and R - G > 45 and R - B > 45) / len(top) * 100
    br = sum(1 for (R, G, B) in bot if R > 120 and R - G > 45 and R - B > 45) / len(bot) * 100
    print(f"\n=== {Path(f).stem} {w}x{h} ===")
    print(f"  均值RGB=({mr:.0f},{mg:.0f},{mb:.0f})  红{red/n*100:.1f}%  暗{dark/n*100:.1f}%  亮{bright/n*100:.1f}%")
    print(f"  上半红{tr:.1f}%  下半红{br:.1f}%  差{tr-br:+.1f}")
    for nm, (x, y) in {"左上": (60, 60), "右上": (w - 60, 60), "左下": (60, h - 60),
                        "右下": (w - 60, h - 60), "正中": (w // 2, h // 2)}.items():
        print(f"    {nm} = {im.getpixel((x, y))}")
