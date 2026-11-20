#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查 .env 里各模型密钥是否存在（只打印是否存在，绝不打印值）"""
import os, re
from pathlib import Path

ENV = Path(r"C:\Users\Administrator\AppData\Local\hermes\.env")
text = ENV.read_text(encoding="utf-8") if ENV.exists() else ""
keys = {}
for line in text.split("\n"):
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    keys[k.strip()] = v.strip()

print(f"=== .env 密钥存在性（只列键名与是否存在，不打印值） ===")
print(f"共 {len(keys)} 个键\n")
want = [k for k in keys if re.search(r"DEEPSEEK|SILICONFLOW|OPENAI|ANTHROPIC|MOONSHOT|KIMI|MINIMAX|API_KEY|TOKEN|LLM|MODEL|BASE_URL", k, re.I)]
for k in sorted(want):
    v = keys[k]
    exists = bool(v)
    hint = ""
    if v.lower().startswith("sk-"):
        hint = f"sk-…（长度{len(v)}）"
    elif re.match(r"^https?://", v):
        hint = v
    else:
        hint = f"（长度{len(v)}）"
    print(f"  {'有' if exists else '空'}  {k:34s} {hint if exists else ''}")

print("\n=== DeepSeek 相关判定 ===")
ds = {k: v for k, v in keys.items() if "DEEPSEEK" in k.upper()}
if ds:
    for k, v in ds.items():
        print(f"  ✅ 找到 {k}，值前缀 {v[:6]!r}… 长度 {len(v)}")
else:
    print("  ❌ .env 中没有任何 DEEPSEEK* 密钥")

print("\n=== 当前生效的 Hermes 模型配置 ===")
cfg = Path(r"C:\Users\Administrator\AppData\Local\hermes\config.yaml").read_text(encoding="utf-8")
for line in cfg.split("\n")[:14]:
    if any(t in line for t in ("default:", "provider:", "base_url:", "name:", "model:")):
        print("  ", line.strip())
