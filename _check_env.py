#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查发布环境：Python 依赖 / SILICONFLOW_API_KEY / 仓库状态（不打印密钥明文）"""
import os, sys, glob, subprocess

def mask(v):
    if not v:
        return "(空)"
    return v[:6] + "***" + v[-4:] + f" (len={len(v)})"

print("=== Python ===")
print("version:", sys.version.split()[0])

print("\n=== 依赖 ===")
for mod in ("PIL", "requests"):
    try:
        m = __import__(mod)
        print(f"  {mod}: OK", getattr(m, "__version__", ""))
    except Exception as e:
        print(f"  {mod}: 缺失 -> {e}")

print("\n=== SILICONFLOW_API_KEY ===")
key = os.environ.get("SILICONFLOW_API_KEY")
src = "环境变量"
if not key:
    src = "未找到(环境变量)"
    for cand in (
        r"C:\Users\Administrator\AppData\Local\hermes\.env",
        r"C:\Users\Administrator\.hermes\.env",
        r"C:\afeng_tea\.env",
    ):
        if os.path.exists(cand):
            try:
                for line in open(cand, encoding="utf-8", errors="ignore"):
                    line = line.strip()
                    if line.startswith("SILICONFLOW_API_KEY"):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val:
                            key, src = val, cand
                            break
            except Exception:
                pass
            if key:
                break
print(f"  来源: {src}")
print(f"  密钥: {mask(key)}")

print("\n=== 仓库 ===")
print(subprocess.run(["git", "log", "--oneline", "-1"], capture_output=True, text=True).stdout.strip())
print("articles/*.html =", len(glob.glob("articles/*.html")))
print("products/*.html =", len(glob.glob("products/*.html")))
print("images/full     =", len(glob.glob("images/full/*.webp")))
print("images/thumb    =", len(glob.glob("images/thumb/*.webp")))
print("模板 laocha.html 存在:", os.path.exists("articles/laocha.html"))
print("作者基准图存在:", os.path.exists("images/author/afeng-portrait.webp"))
