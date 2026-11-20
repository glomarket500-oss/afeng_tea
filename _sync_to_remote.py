# -*- coding: utf-8 -*-
"""把本地 main 对齐到 origin/main（站方修复后的标准版面），未推送的提交存到备份分支。
不丢弃任何提交、不改远程。
"""
import subprocess

REPO = r"C:\afeng_tea"


def sh(cmd, check=False):
    r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    out = (r.stdout + r.stderr).strip()
    print(f"$ {' '.join(cmd)}\n  rc={r.returncode} {out[:300]}")
    if check and r.returncode != 0:
        raise SystemExit(f"中止：{' '.join(cmd)} 失败")
    return out


print("=== 对齐前 ===")
local_only = sh(["git", "log", "--oneline", "origin/main..HEAD"])
sh(["git", "status", "-sb"])

if local_only:
    tip = sh(["git", "rev-parse", "HEAD"]).split()[-1]
    branch = "backup-unpushed-20261115"
    print(f"\n=== 把未推送提交存到备份分支 {branch} ===")
    sh(["git", "branch", "-f", branch, tip], check=True)

print("\n=== 本地 main 对齐到 origin/main ===")
sh(["git", "checkout", "-B", "main", "origin/main"], check=True)

print("\n=== 对齐后 ===")
sh(["git", "log", "--oneline", "-1"])
sh(["git", "status", "-sb"])
head = sh(["git", "rev-parse", "HEAD"]).split()[-1]
origin = sh(["git", "rev-parse", "origin/main"]).split()[-1]
print(f"\n本地 HEAD = {head[:12]}")
print(f"origin/main = {origin[:12]}")
print("✅ 已对齐，今晚发布不会被安全闸拦" if head == origin else "❌ 仍未对齐")
print("\n备份分支内容（未推送的那篇，随时可取回）：")
sh(["git", "log", "--oneline", "-1", "backup-unpushed-20261115"])
