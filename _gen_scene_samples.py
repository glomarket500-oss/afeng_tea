# -*- coding: utf-8 -*-
"""用新的「场景 + 人物」提示词生成 3 张样图给站方看"""
import os
import sys
from pathlib import Path

REPO = Path(r"C:\afeng_tea")
sys.path.insert(0, str(REPO))
import publish_new as P
import teapot_daily as TP
from PIL import Image

OUT = Path(r"C:\Users\Administrator\AppData\Local\hermes\cache\scratch\teapot_demo")
OUT.mkdir(parents=True, exist_ok=True)

key = P.load_key() if hasattr(P, "load_key") else os.environ.get("SILICONFLOW_API_KEY", "")
if not key:
    # publish_new 里的取 key 方式
    key = getattr(P, "SILICONFLOW_API_KEY", "") or os.environ.get("SILICONFLOW_API_KEY", "")
print("key 就绪:", bool(key))

scene = TP.scene_pool(3)
for i, desc in enumerate(scene, 1):
    print(f"\n[{i}/3] {desc[:46]}…")
    try:
        u = P.gen_image(key, desc)             # 返回的是图片 URL
        if not u:
            print("  ✗ 生成失败")
            continue
        import io
        import urllib.request
        with urllib.request.urlopen(u, timeout=120) as r:
            raw = r.read()
        img = Image.open(io.BytesIO(raw))
        fp = OUT / f"scene_person_{i}.webp"
        img.convert("RGB").resize((869, 489), Image.LANCZOS).save(fp, "WEBP", quality=88)
        print(f"  ✓ {fp}  {fp.stat().st_size // 1024}KB")
    except Exception as e:
        print(f"  ✗ {type(e).__name__}: {str(e)[:120]}")
