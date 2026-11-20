# -*- coding: utf-8 -*-
"""把茶叶知识库注册进 Obsidian 的 vault 列表，并设为打开时自动加载"""
import json
import re
import time
import subprocess
from pathlib import Path

APP = Path(r"C:\Users\Administrator\AppData\Local\Programs\Obsidian\Obsidian.exe")
CFG_DIR = Path(r"C:\Users\Administrator\AppData\Roaming\obsidian")
CFG = CFG_DIR / "obsidian.json"
VAULT = Path(r"C:\Users\Administrator\Desktop\MianAI知识库\MianAI知识库\vault")

print(f"Obsidian: {'✓ 存在' if APP.exists() else '✗ 缺失'}  {APP}")

# 版本
try:
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        f"(Get-Item '{APP}').VersionInfo.ProductVersion"],
                       capture_output=True, text=True, timeout=30)
    print(f"版本: {r.stdout.strip() or '(未取到)'}")
except Exception as e:
    print(f"版本读取失败: {e}")

print(f"Vault: {'✓ 存在' if VAULT.exists() else '✗ 缺失'}  {VAULT}")

CFG_DIR.mkdir(parents=True, exist_ok=True)
cfg = {}
if CFG.exists():
    try:
        cfg = json.loads(CFG.read_text(encoding="utf-8"))
        print(f"已有配置: {len(cfg.get('vaults', {}))} 个 vault")
    except Exception:
        cfg = {}

vaults = cfg.setdefault("vaults", {})
target = str(VAULT)
existing = [k for k, v in vaults.items() if str(v.get("path", "")).lower() == target.lower()]

if existing:
    vid = existing[0]
    print("已注册过，更新为默认打开")
else:
    vid = format(int(time.time() * 1000), "x")[-16:].rjust(16, "0")
    print(f"新注册 vault id: {vid}")

vaults[vid] = {"path": target, "ts": int(time.time() * 1000), "open": True}
for k, v in vaults.items():
    v.pop("open", None) if k != vid else None
vaults[vid]["open"] = True

CFG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n✓ 已写入 {CFG}")
print(f"  vault 列表: {len(vaults)} 个")
for k, v in vaults.items():
    mark = " ← 默认打开" if v.get("open") else ""
    print(f"  · {v.get('path')}{mark}")

# 校验：知识库目录里有多少笔记
kb = VAULT / "茶叶知识库"
if kb.exists():
    n = len(list(kb.glob("*.md")))
    print(f"\n知识库笔记: {n} 篇")
