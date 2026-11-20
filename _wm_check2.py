#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""裁新图右下角，核对「AI生成」水印是否已消失"""
from PIL import Image
from pathlib import Path

RES = getattr(getattr(Image, "Resampling", Image), "LANCZOS")
FULL = Path(r"C:\afeng_tea\images\full")
REPO = Path(r"C:\afeng_tea")

for tag, prefix, key in [("new_cover", "a20261115e54200", "cover"),
                         ("new_s1", "a20261115e54200", "s1"),
                         ("old_s2", "a202611154d957b", "s2")]:
    p = FULL / f"{prefix}-{key}.webp"
    if not p.exists():
        print(f"{tag}: 文件不存在")
        continue
    im = Image.open(p).convert("RGB")
    w, h = im.size
    strip = im.crop((int(w * 0.5), int(h * 0.82), w, h))
    strip = strip.resize((strip.width * 3, strip.height * 3), RES)
    out = REPO / f"_wmchk_{tag}.png"
    strip.save(out)
    print(f"{tag}: {w}×{h} → {out.name}")
