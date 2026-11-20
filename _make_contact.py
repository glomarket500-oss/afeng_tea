# -*- coding: utf-8 -*-
"""把 7 张配图拼成一张总览图，供视觉复核（含原位标注顺序）"""
from PIL import Image
from pathlib import Path

PREFIX = "a2026111679b460"
SRC = Path(r"C:\afeng_tea\images\full")
OUT = Path(r"C:\Users\Administrator\AppData\Local\hermes\cache\scratch\img_test\contact_20261116.png")
OUT.parent.mkdir(parents=True, exist_ok=True)

keys = ["cover", "s1", "s2", "s3", "s4", "s5", "s6"]
CW, CH = 520, 293          # 每格尺寸（保持 16:9）
COLS = 2
rows = (len(keys) + COLS - 1) // COLS
sheet = Image.new("RGB", (CW * COLS + 12 * (COLS + 1), (CH + 12) * rows + 12), (24, 24, 24))

for i, k in enumerate(keys):
    fp = SRC / f"{PREFIX}-{k}.webp"
    if not fp.exists():
        print(f"缺 {k}")
        continue
    im = Image.open(fp).convert("RGB").resize((CW, CH), Image.LANCZOS)
    c, r = i % COLS, i // COLS
    x = 12 + c * (CW + 12)
    y = 12 + r * (CH + 12)
    sheet.paste(im, (x, y))
    print(f"格位 {i + 1} = {k}")

sheet.save(OUT, "PNG")
print(f"\n总览图: {OUT}  ({sheet.size[0]}×{sheet.size[1]})")
print("顺序：左上 cover → 右上 s1 → 第二行 s2 / s3 → 第三行 s4 / s5 → 第四行左 s6")
