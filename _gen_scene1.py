import requests, sys, os

API_KEY = os.environ.get("SILICONFLOW_KEY", "")
if not API_KEY:
    print("MISSING_KEY")
    sys.exit(1)

url = "https://api.siliconflow.cn/v1/images/generations"

prompts = [
    {
        "name": "scene1",
        "prompt": "Inside a traditional Chinese tea workshop, a refined 30-35 year old Chinese woman in a stylish dark blue modern Chinese blouse with mandarin collar, opening the lid of a bamboo tea roasting cage, releasing fragrant steam. Wudong mountain misty tea garden visible through open wooden window. Warm morning daylight, bamboo trays with dried tea leaves on the side. Photorealistic, no fire flame, no candle, no text, no watermark."
    },
    {
        "name": "scene2",
        "prompt": "Close-up shot of a female hand holding a smartphone on a wooden tea table, with a small bamboo canister labeled for Mid-Autumn tea gift beside it. Background is a softly blurred traditional Chinese tea shop interior with daylight from window. Modern urban young woman perspective, candid photo style. Photorealistic, no fire flame, no text, no watermark, no labels."
    },
    {
        "name": "scene3",
        "prompt": "Inside a traditional Chinese tea shop, an elderly tea master in a blue cloth jacket holding a teacup, conversing with a refined 30-35 year old Chinese woman in a dark blue modern blouse with mandarin collar. Bamboo tea canisters on wooden shelves in the background, soft daylight from side window. Two generations of tea people discussing. Photorealistic, no fire flame, no candle, no text, no watermark."
    },
    {
        "name": "scene4",
        "prompt": "Cantonese qilou arcade building exterior at night in Guangzhou, warm yellow lanterns hanging, an elderly 82 year old Chinese woman sitting by a window holding a mooncake and a small tea cup. Soft moonlight glow on her face. Family warmth, nostalgic feeling, Mid-Autumn Festival night. Photorealistic, no fire flame, no candle, no text, no watermark."
    },
]

out_dir = "C:/Users/a/Desktop/afeng_tea_repo/images"
os.makedirs(out_dir, exist_ok=True)

for item in prompts:
    fname = f"2026-09-22-1000-{item['name']}.png"
    out_path = os.path.join(out_dir, fname)
    # 跳过已存在的
    if os.path.exists(out_path):
        print(f"SKIP_EXIST: {fname}")
        continue
    try:
        resp = requests.post(
            url,
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            json={"model": "Tongyi-MAI/Z-Image-Turbo", "prompt": item["prompt"], "image_size": "1024x576"},
            timeout=90,
        )
        data = resp.json()
        if "images" in data and len(data["images"]) > 0:
            img_url = data["images"][0]["url"]
            img_data = requests.get(img_url, timeout=30).content
            with open(out_path, "wb") as f:
                f.write(img_data)
            print(f"OK: {fname} ({len(img_data)} bytes)")
        else:
            print(f"FAIL_NO_IMG: {fname} -> {data}")
    except Exception as e:
        print(f"ERROR: {fname} -> {e}")

print("DONE")
