# -*- coding: utf-8 -*-
"""用阿凤姐实拍做参考图，让 Qwen-Image-Edit 把人物放进紫砂茶席场景（测是否可用/免费）"""
import base64
import io
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image

ENV = Path(r"C:\Users\Administrator\AppData\Local\hermes\.env")
OUT = Path(r"C:\Users\Administrator\AppData\Local\hermes\cache\scratch\teapot_demo")
OUT.mkdir(parents=True, exist_ok=True)

key = ""
for line in ENV.read_text(encoding="utf-8", errors="replace").splitlines():
    if line.strip().startswith("SILICONFLOW_API_KEY") and "=" in line:
        key = line.split("=", 1)[1].strip().strip('"').strip("'")
key = key or os.environ.get("SILICONFLOW_API_KEY", "")

# 阿凤姐实拍：旗袍、店内、有茶架那张
REF = Path(r"C:\茶叶素材\紫砂壶图片\1119_10.jpg")
if not REF.exists():
    cands = sorted(Path(r"C:\茶叶素材\图片文件夹").glob("*.jpg"))
    REF = cands[0] if cands else None
print("参考图:", REF.name if REF else "无")

# 压到 1024 内，转 base64 data URL
with Image.open(REF) as im:
    im = im.convert("RGB")
    im.thumbnail((1024, 1024), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=90)
b64 = base64.b64encode(buf.getvalue()).decode()
data_url = f"data:image/jpeg;base64,{b64}"

PROMPT = ("保持参考图里这位女士的面部特征与身形不变，把她放到茶店场景中："
          "她侧身坐在木质茶桌前低头斟茶，桌上摆着一把紫红色宜兴紫砂壶和两只白瓷小杯，"
          "背景是虚化的木质货架与暖黄灯光，晨光从侧面照进来，画面为横向16:9构图，"
          "不出现任何文字、汉字、水印")

for model in ("Qwen/Qwen-Image-Edit-2509", "Qwen/Qwen-Image-Edit"):
    print(f"\n=== {model} ===")
    payload = {"model": model, "prompt": PROMPT, "image": data_url, "image_size": "1024x576"}
    req = urllib.request.Request("https://api.siliconflow.cn/v1/images/generations",
                                 data=json.dumps(payload).encode(),
                                 headers={"Authorization": f"Bearer {key}",
                                          "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            js = json.loads(r.read().decode())
        imgs = js.get("data") or js.get("images") or []
        if not imgs:
            print("  空响应:", str(js)[:200])
            continue
        it = imgs[0]
        u = it["url"] if isinstance(it, dict) else it
        with urllib.request.urlopen(u, timeout=120) as r2:
            raw = r2.read()
        img = Image.open(io.BytesIO(raw))
        fp = OUT / f"afeng_scene_{model.split('/')[-1]}.webp"
        img.convert("RGB").resize((869, 489), Image.LANCZOS).save(fp, "WEBP", quality=88)
        print(f"  ✓ 成功 {fp}  {fp.stat().st_size // 1024}KB")
        break
    except urllib.error.HTTPError as e:
        print(f"  ✗ HTTP {e.code}: {e.read(300).decode('utf-8', 'ignore')[:220]}")
    except Exception as e:
        print(f"  ✗ {type(e).__name__}: {str(e)[:150]}")
