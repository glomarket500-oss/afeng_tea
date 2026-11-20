# -*- coding: utf-8 -*-
"""开工前三样前提自检：只打印是否存在，绝不打印密钥内容"""
import os, re, sys, subprocess
from pathlib import Path

HERMES = Path(r"C:\Users\Administrator\AppData\Local\hermes")

def read_env(path):
    env = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8", errors="replace").split("\n"):
            m = re.match(r"^\s*([A-Z_][A-Z0-9_]*)\s*=\s*(.*)$", line)
            if m:
                env.setdefault(m.group(1), m.group(2).strip().strip('"').strip("'"))
    return env

print("=== 1. SILICONFLOW_API_KEY ===")
for p in [HERMES / ".env", Path(r"C:\Users\Administrator\.hermes\.env")]:
    e = read_env(p)
    if "SILICONFLOW_API_KEY" in e:
        v = e["SILICONFLOW_API_KEY"]
        print(f"  FOUND in {p}  len={len(v)}  prefix={v[:6]}...  suffix=...{v[-4:]}")
        break
else:
    print("  MISSING in .env files; os.environ has it:", bool(os.environ.get("SILICONFLOW_API_KEY")))

print("=== 2. Pillow ===")
try:
    import PIL
    from PIL import Image
    print("  OK Pillow", PIL.__version__)
except Exception as ex:
    print("  FAIL", ex)

print("=== 3. git push 凭据 ===")
r = subprocess.run(["git", "remote", "get-url", "origin"], cwd=r"C:\afeng_tea",
                   capture_output=True, text=True)
u = (r.stdout or "").strip()
masked = re.sub(r"//[^@]*@", "//***TOKEN***@", u)
print("  remote:", masked)
print("  has_token_in_url:", ("@" in u and "github.com" in u))
r2 = subprocess.run(["git", "ls-remote", "origin", "-h", "refs/heads/main"], cwd=r"C:\afeng_tea",
                    capture_output=True, text=True)
print("  ls-remote rc:", r2.returncode, "|", (r2.stdout or r2.stderr).strip()[:80])

print("=== 4. gh CLI ===")
try:
    r3 = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
    print("  rc:", r3.returncode, "|", (r3.stdout or r3.stderr).strip().split("\n")[0][:100])
except Exception as ex:
    print("  gh not available:", ex)

print("=== 5. 仓库状态 ===")
for args in (["log", "--oneline", "-1"], ["status", "--porcelain"]):
    r4 = subprocess.run(["git"] + args, cwd=r"C:\afeng_tea", capture_output=True, text=True)
    print("  git", args[0], "->", (r4.stdout or "").strip()[:200] or "(empty=clean)")
