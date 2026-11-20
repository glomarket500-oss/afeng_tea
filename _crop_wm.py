# -*- coding: utf-8 -*-
"""裁掉样张底部 9% 的「AI生成」水印（正式流水线本来就裁 16:9，同理）"""
from pathlib import Path

from PIL import Image

D = Path(r"C:\Users\Administrator\AppData\Local\hermes\cache\scratch\teapot_demo")
for p in sorted(D.glob("scene_person_*.webp")):
    with Image.open(p) as im:
        im = im.convert("RGB")
        w, h = im.size
        # 底部 9% 连水印一起去掉，再压回 869×489
        im = im.crop((0, 0, w, int(h * 0.91))).resize((869, 489), Image.LANCZOS)
        out = D / f"{p.stem}_clean.webp"
        im.save(out, "WEBP", quality=88)
        print(f"{out.name}  {out.stat().st_size // 1024}KB")
