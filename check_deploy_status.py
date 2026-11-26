import json
import re
import urllib.request

# 获取最近提交的部署状态 - Vercel 部署通过 GitHub webhook 触发
# 检查 Vercel API (需要 token, 但先试公开端点看能否获取部署列表)
# 实际用 GitHub API 检查 commit status 里是否有 Vercel 的部署状态
import urllib.request

req = urllib.request.Request(
    "https://api.github.com/repos/glomarket500-oss/afeng_tea/commits/df0843d6bd816c021cb8f28d87cf7c4e4796d457/status",
    headers={"Accept": "application/vnd.github+json", "User-Agent": "Mozilla/5.0"}
)
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode())
    statuses = data.get("statuses", [])
    print("状态数:", len(statuses))
    for s in statuses:
        print("  ", s.get("context"), "->", s.get("state"), s.get("description", "")[:80])
    print("总状态:", data.get("state"))
except Exception as e:
    print("ERROR:", e)