#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""裁出图片底部条带，用来核对是否残留「AI生成」水印"""
from PIL import Image
from pathlib import Path

FULL = Path(r"C:\afeng_tea\images\full")
prefix = "a202611154d957b"
for k in ["cover", "s1", "s2"]:
    p = FULL / f"{prefix}-{k}.webp"
    if not p.exists():
        continue
    im = Image.open(p).convert("RGB")
    w, h = im.size
    strip = im.crop((0, int(h * 0.86), w, h))
    strip = strip.resize((w * 2, (h - int(h * 0.86)) * 2), Image.LANCZOS)
    out = Path(rf"C:\afeng_tea\_wm_{k}.png")
    strip.save(out)
    print(f"{k}: {w}×{h} → 底带裁出 {out.name} ({strip.width}×{strip.height})")
