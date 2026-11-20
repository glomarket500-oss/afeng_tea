# -*- coding: utf-8 -*-
"""单图验收：真生成 1 张，验证「裁底部15%去水印 + 869×489 + 像素合规」"""
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, r"C:\afeng_tea")
import publish_new as P

OUT_DIR = Path(r"C:\Users\Administrator\AppData\Local\hermes\cache\scratch\img_test")
OUT_DIR.mkdir(parents=True, exist_ok=True)

env = P.load_env()
key = env.get("SILICONFLOW_API_KEY")
if not key:
    raise SystemExit("缺少 SILICONFLOW_API_KEY")

desc = "木质茶席上凤凰单丛干茶与白瓷盖碗，晨光斜射"
print(f"提示词: {desc}")
url = P.gen_image(key, desc)
raw = urllib.request.urlopen(url, timeout=120).read()

# 原始图的真实尺寸
from PIL import Image
import io
orig = Image.open(io.BytesIO(raw))
print(f"原始图尺寸: {orig.size}（Kolors 返回 1024x576 = 16:9，只做居中裁切等于没裁）")

out = OUT_DIR / "test-cover.webp"
w, h, sz = P.to_webp(raw, out, 869, 489)
print(f"输出: {w}×{h}  {sz // 1024}KB  → {out}")

warns = P.audit_image(out)
print(f"像素合规: {'⚠ ' + ';'.join(warns) if warns else '✓ 通过（无正脸 / 无汉字）'}")

# 图说预览
print(f"图说样例: {P.scene_caption(desc)}")
