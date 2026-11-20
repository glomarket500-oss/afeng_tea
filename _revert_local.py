#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""回退本地那次越界提交（远程本来就没收到，直接 reset 本地即可）"""
import subprocess
from pathlib import Path

REPO = Path(r"C:\afeng_tea")


def run(cmd):
    r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    print(f"$ {' '.join(cmd)}\n{r.stdout}{r.stderr}")
    return r


print("=== 回退前 ===")
run(["git", "log", "--oneline", "-2"])
run(["git", "status", "-sb"])

# 远程 HEAD 是 899e10b，本地多一个 6bb6c12。reset --hard 到远程即可
r = run(["git", "reset", "--hard", "origin/main"])
print("\n=== 回退后 ===")
run(["git", "log", "--oneline", "-2"])
run(["git", "status", "-sb"])
print("\n远程 HEAD:", run(["git", "log", "--oneline", "-1", "origin/main"]).stdout.strip())
print("→ 本地与远程已一致，站方版本未被改动")
