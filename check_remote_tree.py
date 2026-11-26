import json
import urllib.request

req = urllib.request.Request(
    "https://api.github.com/repos/glomarket500-oss/afeng_tea/git/trees/df0843d6bd816c021cb8f28d87cf7c4e4796d457?recursive=1",
    headers={"Accept": "application/vnd.github+json", "User-Agent": "Mozilla/5.0"}
)
with urllib.request.urlopen(req, timeout=30) as r:
    data = json.loads(r.read().decode())

articles = [t for t in data.get("tree", []) if t.get("path", "").startswith("articles/") and t.get("path", "").endswith(".html")]
print("远程 articles 总数:", len(articles))
for t in articles:
    if "202611" in t["path"]:
        print("  ", t["path"][:80])