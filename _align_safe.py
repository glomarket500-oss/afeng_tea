# -*- coding: utf-8 -*-
"""非破坏式对齐：备份脚本改动 → stash → 切到 origin/main → 放回脚本
不使用 reset --hard / clean -fd。
"""
import shutil
import subprocess
from pathlib import Path

REPO = Path(r"C:\afeng_tea")
BK = Path(r"C:\Users\Administrator\AppData\Local\hermes\cache\scratch\afeng_scripts_20261116")
BK.mkdir(parents=True, exist_ok=True)


def sh(cmd, check=False):
    r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    print(f"$ {' '.join(cmd)}\n  rc={r.returncode} {(r.stdout + r.stderr).strip()[:260]}")
    if check and r.returncode != 0:
        raise SystemExit("中止")
    return r


print("=== 1) 备份我在用的脚本 ===")
for f in ("publish_new.py", "publish_weekly.py", "publish_daily.py", "next_draft.py"):
    src = REPO / f
    if src.exists():
        shutil.copy2(src, BK / f)
        print(f"  ✓ {f} → {BK}")

print("\n=== 2) 备份当前未推送提交的分支标记 ===")
sh(["git", "branch", "-f", "backup-regen-20261116", "HEAD"])

print("\n=== 3) 暂存已跟踪改动 ===")
sh(["git", "stash", "push", "-m", "20261116-对齐远程前的脚本改动（已另存文件备份）"])

print("\n=== 4) 切到 origin/main ===")
sh(["git", "checkout", "-B", "main", "origin/main"], check=True)

print("\n=== 5) 把脚本放回（保持我的改进可用）===")
for f in ("publish_new.py", "publish_weekly.py"):
    src = BK / f
    if src.exists():
        shutil.copy2(src, REPO / f)
        print(f"  ✓ 恢复 {f}")

print("\n=== 6) 核对 ===")
head = sh(["git", "rev-parse", "HEAD"]).stdout.split()[-1]
origin = sh(["git", "rev-parse", "origin/main"]).stdout.split()[-1]
print(f"  本地 {head[:12]} / 远程 {origin[:12]} → {'✅ 一致' if head == origin else '❌ 不一致'}")
sh(["git", "status", "--porcelain"])
