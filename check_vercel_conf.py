import json
import urllib.request

# Vercel 部署状态可以通过 GitHub 的 commit check-runs 查看
# 但需要 token。改用公开 Vercel 部署页尝试
# 更直接：检查 vercel.json 是否被提交（决定路由行为）
import urllib.request

# 尝试读取仓库根目录的 vercel.json
for f in ["vercel.json", "next.config.js", "next.config.mjs", "package.json"]:
    url = f"https://raw.githubusercontent.com/glomarket500-oss/afeng_tea/main/{f}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            content = r.read().decode(errors="replace")
            print(f"=== {f} ===")
            print(content[:800])
            print()
    except Exception as e:
        print(f"{f}: {e}")