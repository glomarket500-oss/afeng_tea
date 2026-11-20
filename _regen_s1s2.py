#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重做 s1 / s2 —— 规范书 §3.2 安全题材（干茶叶微距 / 茶汤微距），避开一切
可能长汉字的器物（罐/瓶/袋/招牌/灯笼/建筑），并把输出统一为 869x489。
仅免费模型 Kwai-Kolors/Kolors。
"""
import os, sys, time, io, json, urllib.request
from pathlib import Path
from PIL import Image, ImageOps

REPO = Path(r"C:\afeng_tea")
MODEL = "Kwai-Kolors/Kolors"          # 免费（规范书 §3.1 成本铁律）
API = "https://api.siliconflow.cn/v1/images/generations"
KEY = os.environ.get("SILICONFLOW_API_KEY", "")
PREFIX = "qiuchu"

BAN = ("畫面中絕對不可以出現任何文字、漢字、英文字母、數字、字幕、招牌、標籤、包裝文字、水印、標誌或logo。"
       "不要出現任何器皿、罐子、瓶子、紙袋、包裝盒、木牌、燈籠、對聯、建築物、人物。"
       "只有茶葉和茶湯本身。純寫實攝影，微距特寫，淺景深，暖色光線，主體充滿畫面。")

NEG = ("文字, 漢字, 字母, 数字, 字幕, 招牌, 標籤, 包装文字, 水印, logo, 标志, 印章, 书法, 灯笼, 对联, 建筑, 亭子, 庙宇, 招牌, 木牌, 罐, 瓶, 包装袋, 纸袋, 礼盒, 人脸, 人物, 手, watermark, text, letters, numbers, signature, caption, blurry, lowres")

SCENES = {
    # s1: 干茶叶微距（承接「场景开头」——十一月收茶季，茶园/竹匾上的秋茶）
    "s1": ("微距特写照片：一堆深褐色条索紧结的凤凰单丛干茶叶，茶叶表面带细微白毫，"
           "叶片相互堆叠形成自然纹理，背景是模糊的深色木桌面，"
           "暖色侧光从右上方照射，浅景深，画面中只有茶叶与木桌，无任何其他物体。"
           "超近距离微距，茶叶纹理清晰锐利，主体充满画面",
           "深褐色的秋茶干叶，条索紧结，纹理里带着焙火的香"),

    # s2: 琥珀色茶汤微距（承接「第一幕」——焙火足的老火秋茶，汤色沉而不燥）
    "s2": ("微距特写照片：琥珀色茶汤的液面特写，透亮的红褐色茶汤清澈见底，"
           "表面有极细微的茶汤纹理和一圈浅色边缘，背景是模糊的深色木桌面，"
           "暖色侧光穿透茶汤，茶汤呈蜜糖般的通透感，浅景深。"
           "画面中只有茶汤本身，没有杯子、没有碗、没有其他任何物体，超近距离微距，主体充满画面",
           "琥珀色的茶汤透亮，焙火沉在汤里"),
}


def call_api(prompt, attempts=4):
    payload = {"model": MODEL, "prompt": prompt + "\n" + BAN, "negative_prompt": NEG,
               "image_size": "1024x576", "batch_size": 1,
               "num_inference_steps": 20, "guidance_scale": 7.5}
    body = json.dumps(payload).encode("utf-8")
    last = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(API, data=body, headers={
                "Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=180) as r:
                data = json.loads(r.read().decode("utf-8"))
            url = data["images"][0]["url"]
            with urllib.request.urlopen(
                    urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=120) as r2:
                return r2.read()
        except Exception as e:
            last = e
            print(f"    ! 第 {i+1} 次失败: {e}", flush=True)
            time.sleep(5 * (i + 1))
    raise RuntimeError(f"生图失败: {last}")


def postprocess(raw, out_full):
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    src = im.size
    w, h = im.size
    im = im.crop((0, 0, w, int(h * 0.85)))          # 裁掉底部 15%（去水印）
    im = ImageOps.fit(im, (869, 489), method=Image.LANCZOS, centering=(0.5, 0.5))
    out_full.parent.mkdir(parents=True, exist_ok=True)
    im.save(out_full, "WEBP", quality=82, method=5)
    kb = out_full.stat().st_size / 1024
    if kb > 200:
        im.save(out_full, "WEBP", quality=72, method=5)
        kb = out_full.stat().st_size / 1024
    return src, im.size, round(kb, 1)


def main():
    if not KEY:
        print("!! SILICONFLOW_API_KEY 未设置"); sys.exit(1)
    only = set(sys.argv[1:]) or set(SCENES)
    print(f"模型: {MODEL}（免费）")
    for key in ["s1", "s2"]:
        if key not in only:
            continue
        prompt, caption = SCENES[key]
        out = REPO / "images" / "full" / f"{PREFIX}-{key}.webp"
        print(f"  [{key}] 生图中... {caption}", flush=True)
        raw = call_api(prompt)
        src, size, kb = postprocess(raw, out)
        print(f"  [{key}] OK 源{src[0]}x{src[1]} -> {size[0]}x{size[1]}  {kb}KB", flush=True)


if __name__ == "__main__":
    main()
