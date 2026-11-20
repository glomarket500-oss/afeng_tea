# -*- coding: utf-8 -*-
"""单测：真实照片取材 + 裁切转换"""
import sys
from pathlib import Path

REPO = Path(r"C:\afeng_tea")
sys.path.insert(0, str(REPO))
import real_photos as RP

TITLE = "清晨六点半的惠州东平，阿凤姐一壶凤凰单丛理年货单"
BODY = "泡茶 茶架 茶具 干茶 店内 客人 工夫茶 年货 礼盒"
out = Path(r"C:\Users\Administrator\AppData\Local\hermes\cache\scratch\realph_test")

items = RP.load_manifest()
print(f"清单 {len(items)} 张，可用 {len([i for i in items if i.get('suitable_for_article')])} 张\n")

picked = RP.pick(TITLE, BODY, need=7)
print(f"为这篇文章挑出 {len(picked)} 张：")
for i, m in enumerate(picked, 1):
    print(f"  {i}. {RP.describe(m)}  质量={m.get('quality')}  {m['w']}×{m['h']}")

out.mkdir(parents=True, exist_ok=True)
print("\n裁切转换测试：")
for idx, m in enumerate(picked):
    try:
        w, h, sz = RP.prepare(m, out / f"test-{idx:02d}.webp")
        print(f"  ✓ {idx}. {m['file'][:16]} → {w}×{h} {sz//1024}KB")
    except Exception as e:
        print(f"  ✗ {m['file'][:14]} → {type(e).__name__}: {e}")
try:
    sz = RP.prepare_thumb(picked[0], out / "thumb.webp")
    print(f"  ✓ 缩略图 {sz//1024}KB")
except Exception as e:
    print(f"  ✗ 缩略图 {e}")

from PIL import Image
for p in sorted(out.glob("*.webp"))[:3]:
    with Image.open(p) as im:
        print(f"  校验 {p.name}: {im.size} {im.format}")
