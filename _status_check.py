#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查：git 推送状态 / .env 全部键名 / cron jobs.json 结构"""
import subprocess, json, re
from pathlib import Path

HERMES = Path(r"C:\Users\Administrator\AppData\Local\hermes")
REPO = Path(r"C:\afeng_tea")


def run(cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.stdout + r.stderr


print("=== 1) git 状态：我的提交是否已推送 ===")
print(run(["git", "log", "--oneline", "-4"], cwd=str(REPO)).strip())
print("--- 本地 vs 远程 ---")
print(run(["git", "status", "-sb"], cwd=str(REPO)).strip().split("\n")[0])
print("--- 远程 HEAD ---")
print(run(["git", "log", "--oneline", "-3", "origin/main"], cwd=str(REPO)).strip())

print("\n=== 2) .env 全部键名（只列名字，不打印值） ===")
env = HERMES / ".env"
if env.exists():
    for line in env.read_text(encoding="utf-8").split("\n"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            print(f"  {k.strip():38s} {'(有值, 长度%d)' % len(v.strip()) if v.strip() else '(空)'}")

print("\n=== 3) cron jobs.json 结构 ===")
jf = HERMES / "cron" / "jobs.json"
if jf.exists():
    data = json.loads(jf.read_text(encoding="utf-8"))
    jobs = data if isinstance(data, list) else data.get("jobs", [])
    print(f"  总任务数: {len(jobs)}")
    if jobs:
        print("  单条任务的字段:")
        for k in sorted(jobs[0].keys()):
            v = jobs[0][k]
            t = type(v).__name__
            show = ""
            if isinstance(v, (str, int, float, bool)) and k not in ("prompt",):
                show = f" = {str(v)[:60]}"
            print(f"    {k:22s} ({t}){show}")
    # 统计 model/provider 分布
    from collections import Counter
    cm = Counter((j.get("model"), j.get("provider"), j.get("base_url")) for j in jobs)
    print("\n  model/provider/base_url 分布:")
    for k, v in cm.most_common():
        print(f"    {v:3d} × {k}")
else:
    print("  未找到 jobs.json")
