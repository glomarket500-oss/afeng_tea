# -*- coding: utf-8 -*-
"""给真实照片打标签，生成 images/real_photos.json（流水线取材用）

用 SiliconFlow 的视觉模型（免费额度内），一次跑完全部照片；
以后往 C:\\茶叶素材\\图片文件夹 里丢新图，重跑本脚本即可增量补标签。
"""
import base64
import json
import os
import sys
import urllib.request
from pathlib import Path

SRC = Path(r"C:\茶叶素材\图片文件夹")
REPO = Path(r"C:\afeng_tea")
OUT = REPO / "images" / "real_photos.json"
MODEL = "Qwen/Qwen3-VL-8B-Instruct"
API = "https://api.siliconflow.cn/v1/chat/completions"

PROMPT = """你是茶叶店内容编辑。看这张照片，严格按 JSON 回答，不要多余文字：
{"subject":"person|tea|teaware|shop|teagarden|scenery|food|other",
 "has_person":true/false,
 "person":"无|女性单人正面|女性单人侧脸/背影|多人|男性",
 "scene":"一句话描述场景（20字内）",
 "shop_shelves":true/false,
 "quality":"good|ok|poor",
 "width_ok":true/false,
 "useful_tags":["从这些里选：人物,店内,茶架,茶具,泡茶,干茶,茶园,山景,礼盒,生活,街景"],
 "suitable_for_article":true/false,
 "reason":"一句话说明能不能用作茶叶文章配图"}"""


def load_key():
    for p in (Path(r"C:\Users\Administrator\AppData\Local\hermes\.env"), REPO / ".env"):
        if p.exists():
            for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
                if line.startswith("SILICONFLOW_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("SILICONFLOW_API_KEY")


def ask(key, path):
    b64 = base64.b64encode(path.read_bytes()).decode()
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": PROMPT},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
        ]}],
        "temperature": 0.1,
        "max_tokens": 300,
    }
    req = urllib.request.Request(API, data=json.dumps(payload).encode(),
                                 headers={"Authorization": f"Bearer {key}",
                                          "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=90) as r:
        js = json.loads(r.read())
    txt = js["choices"][0]["message"]["content"].strip()
    txt = txt[txt.find("{"): txt.rfind("}") + 1]
    return json.loads(txt)


def size_of(path):
    try:
        from PIL import Image
        with Image.open(path) as im:
            return im.size
    except Exception:
        return (0, 0)


key = load_key()
if not key:
    sys.exit("✗ 没有 SILICONFLOW_API_KEY")

files = sorted([p for p in SRC.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")])
print(f"共 {len(files)} 张待打标签\n")

manifest = {"source": str(SRC), "model": MODEL, "items": []}
if OUT.exists():
    try:
        old = json.loads(OUT.read_text(encoding="utf-8"))
        manifest["items"] = [i for i in old.get("items", []) if (SRC / i["file"]).exists()]
    except Exception:
        pass
known = {i["file"] for i in manifest["items"]}

for p in files:
    if p.name in known:
        print(f"  ↺ 已有标签 {p.name}")
        continue
    w, h = size_of(p)
    try:
        meta = ask(key, p)
    except Exception as e:
        print(f"  ✗ {p.name}: {type(e).__name__} {str(e)[:100]}")
        continue
    meta.update({"file": p.name, "w": w, "h": h, "size_kb": p.stat().st_size // 1024})
    manifest["items"].append(meta)
    print(f"  ✓ {p.name[:18]}  {meta.get('subject')}/{meta.get('person')}  "
          f"{w}×{h}  可用={meta.get('suitable_for_article')}  {str(meta.get('scene'))[:22]}")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n写出 {OUT}（{len(manifest['items'])} 条）")
ok = [i for i in manifest["items"] if i.get("suitable_for_article")]
print(f"可用于文章: {len(ok)} 张")
for i in ok:
    print(f"  · {i['file'][:16]}  {i.get('person')}  {i.get('scene','')[:26]}  tags={i.get('useful_tags')}")
