#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抽查历史文章图片是否同样带「AI生成」水印（裁底部条带）"""
from PIL import Image
from pathlib import Path
import re

REPO = Path(r"C:\afeng_tea")
FULL = REPO / "images" / "full"

# 找几张非本次前缀的历史图
cands = [p for p in sorted(FULL.glob("*.webp")) if not p.name.startswith("a202611154d957b")][:3]
for p in cands:
    im = Image.open(p).convert("RGB")
    w, h = im.size
    strip = im.crop((int(w * 0.55), int(h * 0.85), w, h))
    strip = strip.resize((strip.width * 3, strip.height * 3), Image.LANCZOS)
    out = REPO / f"_wm_old_{p.stem[:18]}.png"
    strip.save(out)
    print(f"{p.name}: {w}×{h} → {out.name}  (右下角放大3倍)")

# 统计全站图片数量
allimg = list(FULL.glob("*.webp"))
print(f"\nimages/full 共 {len(allimg)} 张")
