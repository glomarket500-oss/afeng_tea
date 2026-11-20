# -*- coding: utf-8 -*-
"""查 SiliconFlow 有哪些可用的图像模型（找支持参考图/编辑的免费模型）"""
import json
import os
import urllib.request
from pathlib import Path

ENV = Path(r"C:\Users\Administrator\AppData\Local\hermes\.env")
key = ""
for line in ENV.read_text(encoding="utf-8", errors="replace").splitlines():
    if line.strip().startswith("SILICONFLOW_API_KEY") and "=" in line:
        key = line.split("=", 1)[1].strip().strip('"').strip("'")
key = key or os.environ.get("SILICONFLOW_API_KEY", "")

req = urllib.request.Request("https://api.siliconflow.cn/v1/models?sub_type=text-to-image",
                             headers={"Authorization": f"Bearer {key}"})
try:
    with urllib.request.urlopen(req, timeout=40) as r:
        data = json.loads(r.read().decode())
    ids = [m.get("id", "") for m in data.get("data", [])]
    print(f"text-to-image 模型 {len(ids)} 个：")
    for i in ids:
        print("  ", i)
except Exception as e:
    print("查询失败:", type(e).__name__, str(e)[:120])

# 再查图生图/编辑类
for sub in ("image-to-image",):
    try:
        req = urllib.request.Request(f"https://api.siliconflow.cn/v1/models?sub_type={sub}",
                                     headers={"Authorization": f"Bearer {key}"})
        with urllib.request.urlopen(req, timeout=40) as r:
            data = json.loads(r.read().decode())
        ids = [m.get("id", "") for m in data.get("data", [])]
        print(f"\n{sub} 模型 {len(ids)} 个：")
        for i in ids:
            print("  ", i)
    except Exception as e:
        print(f"\n{sub} 查询失败:", type(e).__name__, str(e)[:100])
