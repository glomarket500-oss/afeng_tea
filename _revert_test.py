# -*- coding: utf-8 -*-
"""撤销本地测试发布：回退本地提交 + 恢复已跟踪文件 + 删除未推送的新文章与配图。
用法: python _revert_test.py <slug> <prefix>
只动本地，不碰远程；先检查是否已推送，已推送则拒绝执行（避免把线上搞乱）。
"""
import subprocess, os, sys, glob, re

REPO = r"C:\afeng_tea"
slug = sys.argv[1] if len(sys.argv) > 1 else "20261115一周茶事从凤凰山到惠州茶桌这周茶友最关心的三件事阿凤姐"
prefix = sys.argv[2] if len(sys.argv) > 2 else "a2026111562fca1"


def run(c):
    r = subprocess.run(c, cwd=REPO, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    print(f"$ {' '.join(c)}\n  rc={r.returncode} {(r.stdout + r.stderr).strip()[:300]}")
    return r


print("=== 撤销前 ===")
run(["git", "log", "--oneline", "-2"])
run(["git", "status", "-sb"])

# 安全闸：只回退「HEAD 提交信息含本篇 slug」的那一个（可能还有第三方并行提交，绝不能连带撤销）
head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                      capture_output=True, text=True).stdout.strip()
msg = subprocess.run(["git", "log", "-1", "--format=%s"], cwd=REPO,
                     capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
origin = subprocess.run(["git", "rev-parse", "origin/main"], cwd=REPO,
                        capture_output=True, text=True).stdout.strip()
if head == origin:
    print("❌ HEAD 已与 origin/main 一致（已推送），拒绝撤销"); sys.exit(1)
marker = re.sub(r"^\d+", "", slug)[:4]     # 用标题头匹配（提交信息里是标题，不含日期前缀）
if marker not in msg:
    print(f"❌ HEAD 提交与本篇不符，拒绝撤销\n   HEAD: {msg.strip()[:90]}\n   期望含: {marker}"); sys.exit(1)
ahead = subprocess.run(["git", "rev-list", "--count", "origin/main..HEAD"], cwd=REPO,
                       capture_output=True, text=True).stdout.strip()
print(f"⚠ 本地领先 origin/main {ahead} 个提交；本次只回退 HEAD 这一个（其它提交原样保留）")

run(["git", "reset", "--mixed", "HEAD~1"])
run(["git", "checkout", "--", "."])

killed = []
for pat in (f"articles/{slug}.html", f"images/full/{prefix}-*.webp",
            f"images/thumb/{slug}-hero.webp", f"_preview_{slug[:20]}*.html"):
    for p in glob.glob(os.path.join(REPO, pat)):
        os.remove(p)
        killed.append(os.path.relpath(p, REPO).replace("\\", "/"))
print(f"\n删除测试产物 {len(killed)} 个:")
for k in killed:
    print("  -", k)

print("\n=== 撤销后 ===")
run(["git", "log", "--oneline", "-1"])
r = run(["git", "status", "--porcelain"])
tracked = [l for l in r.stdout.split("\n") if l.strip() and not l.startswith("??")]
print(f"已跟踪文件改动: {len(tracked)} 个 {'（应为 0）' if not tracked else tracked[:5]}")
