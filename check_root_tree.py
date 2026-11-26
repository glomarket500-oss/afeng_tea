import json
import urllib.request

# 获取仓库根目录的 tree，看是否有路由配置文件
req = urllib.request.Request(
    "https://api.github.com/repos/glomarket500-oss/afeng_tea/git/trees/main",
    headers={"Accept": "application/vnd.github+json", "User-Agent": "Mozilla/5.0"}
)
with urllib.request.urlopen(req, timeout=30) as r:
    data = json.loads(r.read().decode())

print("根目录文件:")
for t in data.get("tree", []):
    if t.get("type") == "blob":
        print("  ", t.get("path"))