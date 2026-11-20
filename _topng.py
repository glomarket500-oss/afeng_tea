#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""导出 webp → png 供视觉复核，并跑客观检测"""
from PIL import Image
from pathlib import Path
import glob

REPO = Path(r"C:\afeng_tea")
PNG = REPO / "_png"
PNG.mkdir(exist_ok=True)
for f in sorted(glob.glob(str(REPO / "images" / "full" / "qiuchu-*.webp"))):
    im = Image.open(f)
    out = PNG / (Path(f).stem + ".png")
    im.convert("RGB").save(out)
    print(f"{Path(f).name:24s} {im.size} -> {out.name}")
