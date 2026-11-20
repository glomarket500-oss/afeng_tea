#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿凤姐茶站 · 配图生成（SiliconFlow 免费模型 Kwai-Kolors/Kolors）
用法: python _gen_images_20261115.py
产物: images/full/qiuchu-{cover,s1..s6}.webp  +  images/thumb/{slug}-hero.webp
"""
import os, sys, time, io, json, urllib.request, urllib.error
from pathlib import Path
from PIL import Image, ImageOps

REPO = Path(r"C:\afeng_tea")
MODEL = "Kwai-Kolors/Kolors"          # 免费
API = "https://api.siliconflow.cn/v1/images/generations"
KEY = os.environ.get("SILICONFLOW_API_KEY", "")

SLUG = "20261115立冬之后换一壶秋茶阿凤姐教你顺时而饮"
PREFIX = "qiuchu"

# ---- 规范书 §3.2 图片禁令（逐条追加到每条提示词）----
BAN = """畫面中絕對不可以出現任何文字、漢字、英文字母、數字、字幕、招牌、標籤、包裝文字、水印、標誌或logo。
所有罐子、玻璃瓶、包裝袋、紙袋、木牌都必須是素面空白，完全沒有任何標籤或印刷字樣。
器物必須素面無字。純寫實攝影，自然光或暖色燈光，構圖乾淨。"""

NEG = """文字, 漢字, 字母, 数字, 字幕, 招牌, 標籤, 标签, 包装文字, 水印, logo, 标志, 印章, 书法, 书法字, 书法作品,
包装有字, 瓶身有字, 罐身有字, 木牌有字, 招牌有字, watermark, text, letters, numbers, signature, caption,
distorted face, deformed hands, extra fingers, blurry, lowres, jpeg artifacts, oversaturated"""

# ---- 规范书 §3.4 角色锁定（含阿凤姐的画面必须逐字使用，一字不改）----
ROLE = """一位三十多歲的中國女性茶店主理人：鵝蛋臉、皮膚白皙、細長眉、單眼皮微雙、鼻樑秀氣、唇色自然；
黑色齊肩直髮、自然垂落或低馬尾；身穿墨綠色中式立領棉麻上衣，袖口挽起，手腕戴一只細銀手鐲；
神情溫和自信，淡妝。"""

# 7 张图：(key, 场景描述, 是否含阿凤姐, 图说)
SCENES = [
    ("cover",
     "惠州东平江边老街的茶店门口傍晚景，竹匾上晾着深褐色条索紧结的乌龙茶叶，暖黄灯光从半开的卷闸门里透出来，"
     "门口一张小茶桌上一只紫砂壶和两只白瓷杯，远处是西江水面和暮色天空，安静温暖，中景广角",
     False,
     "惠州东平的江边，秋茶晾在竹匾上"),

    ("s1",
     "横向构图 16:9 横幅照片，十一月傍晚的沿江商铺门口，风吹动门帘，"
     "一位" + ROLE + "站在门槛上把竹匾上的茶叶收进屋里，"
     "她身穿的必须是墨绿色中式立领棉麻上衣，袖口挽起，手腕戴一只细银手镯，黑色齐肩直发自然垂落；"
     "背景是江边老街与暖黄店灯，中景，纪实摄影，人物居中偏左",
     True,
     "十一月的傍晚，江风起，阿凤姐在收茶"),

    ("s2",
     "横向构图 16:9 横幅照片，茶店柜台前，一位" + ROLE + "正在用盖碗冲泡凤凰单丛，"
     "她身穿的必须是墨绿色中式立领棉麻上衣，袖口挽起，黑色齐肩直发自然垂落；"
     "面前柜台上并排放着两只素面无字的深色锡罐，盖碗冒着热气，玻璃公道杯里是琥珀色茶汤，"
     "暖色室内光，中景，单一连续场景，人物半身在画面右侧",
     True,
     "柜台前两罐秋茶，一泡功夫茶"),

    ("s3",
     "功夫茶具特写，一只小盖碗刚出汤，茶汤注入玻璃公道杯呈透亮琥珀色，旁边是竹制茶则和茶针，"
     "背景虚化的茶室暖光，俯拍微距，无人物",
     False,
     "第二泡快出汤，汤色像兑了蜜的琥珀"),

    ("s4",
     "茶店门口停着一辆面包车，后备箱打开装满编织袋装的茶叶，二十来斤一袋堆叠，"
     "旁边一位年轻女性店员抱着一个纸箱准备上车，白天自然光，中景纪实",
     False,
     "陈老板的三十斤，装了满满一后备箱"),

    ("s5",
     "傍晚茶室内的长条茶桌，桌上摆着一只紫砂壶、一只盖碗、几个白瓷杯，旁边散放几片陈皮、"
     "几粒麦冬和两个雪梨，窗外暮色透进来，暖黄灯光，无人物",
     False,
     "秋冬润燥，陈皮麦冬雪梨都能搭"),

    ("s6",
     "入夜的茶店里，柜台上几只封好的素面无字深色茶叶罐整齐排成一排，一只手正把一只罐子轻轻放稳，"
     "旁边有一支铅笔和一叠空白无字纸片，暖黄灯光，夜色氛围",
     False,
     "天黑透了，最后一罐秋茶封好"),
]


def postprocess(raw_bytes, out_full, out_thumb=None):
    im = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
    raw_size = im.size
    w, h = im.size
    im = im.crop((0, 0, w, int(h * 0.85)))            # ① 裁掉底部 15%（去水印）
    # ② 等比缩放 + 居中裁成 16:9（ImageOps.fit 不拉伸，竖版源图也不会变形）
    im = ImageOps.fit(im, (869, 489), method=Image.LANCZOS, centering=(0.5, 0.5))
    print(f"      源图 {raw_size[0]}x{raw_size[1]} -> 869x489", flush=True)
    quality = 82
    out_full.parent.mkdir(parents=True, exist_ok=True)
    im.save(out_full, "WEBP", quality=quality, method=5)
    kb = out_full.stat().st_size / 1024
    if kb > 200:                                        # ③ >200KB 降质 / 缩到 900 宽
        im.save(out_full, "WEBP", quality=72, method=5)
        kb = out_full.stat().st_size / 1024
    if out_thumb:
        t = im.copy()
        t.thumbnail((400, 400), Image.LANCZOS)
        out_thumb.parent.mkdir(parents=True, exist_ok=True)
        t.save(out_thumb, "WEBP", quality=82, method=5)
    return im.size, round(kb, 1)


def call_api(prompt, attempts=4):
    payload = {
        "model": MODEL,
        "prompt": prompt + "\n" + BAN,
        "negative_prompt": NEG,
        "image_size": "1024x576",
        "batch_size": 1,
        "num_inference_steps": 20,
        "guidance_scale": 7.5,
    }
    body = json.dumps(payload).encode("utf-8")
    last = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(
                API, data=body,
                headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=180) as r:
                data = json.loads(r.read().decode("utf-8"))
            url = data["images"][0]["url"]
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=120) as r2:
                return r2.read()
        except Exception as e:
            last = e
            print(f"    ! 第 {i+1} 次失败: {e}", flush=True)
            time.sleep(5 * (i + 1))
    raise RuntimeError(f"生图失败: {last}")


def main():
    if not KEY:
        print("!! SILICONFLOW_API_KEY 未设置")
        sys.exit(1)
    only = set(sys.argv[1:]) or None
    print(f"模型: {MODEL} (免费)")
    results = []
    for key, scene, has_role, caption in SCENES:
        if only and key not in only:
            continue
        full = REPO / "images" / "full" / f"{PREFIX}-{key}.webp"
        thumb = (REPO / "images" / "thumb" / f"{SLUG}-hero.webp") if key == "cover" else None
        if full.exists() and not only:
            print(f"  {key}: 已存在，跳过")
            continue
        prompt = scene if has_role else scene
        print(f"  [{key}] 生图中... {caption}", flush=True)
        raw = call_api(prompt)
        size, kb = postprocess(raw, full, thumb)
        print(f"  [{key}] OK {size} {kb}KB -> {full.name}", flush=True)
        results.append((key, caption, full))
    print("\n完成。生成清单:")
    for k, c, f in results:
        print(f"  {k}: {c}  ({f.stat().st_size//1024}KB)")


if __name__ == "__main__":
    main()
