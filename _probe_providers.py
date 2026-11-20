#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探针：
1) DeepSeek 官方 API 端点是否可达（不带 key，只看网络层）
2) 旧 provider api2.aitoken521.com 是否还活着
3) 模型目录里有没有 deepseek 条目
4) Hermes 支持哪些 provider 名
"""
import json, urllib.request, urllib.error, socket, ssl
from pathlib import Path

HERMES = Path(r"C:\Users\Administrator\AppData\Local\hermes")


def probe(url, timeout=15, headers=None):
    try:
        req = urllib.request.Request(url, headers=headers or {"User-Agent": "probe"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read(400).decode("utf-8", "ignore")
            return f"HTTP {r.status}  {body[:200]}"
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}  {e.read(200).decode('utf-8','ignore')}"
    except Exception as e:
        return f"ERR {type(e).__name__}: {e}"


print("=== 1) DeepSeek 官方端点 ===")
for u in ["https://api.deepseek.com/v1/models",
          "https://api.deepseek.com/v1/chat/completions"]:
    print(f"  {u}\n     → {probe(u)}")

print("\n=== 2) 现役 provider（api2.aitoken521.com）===")
print(f"  https://api2.aitoken521.com/v1/models\n     → {probe('https://api2.aitoken521.com/v1/models')}")

print("\n=== 3) 用户资料里提到的另一个 base_url ===")
print(f"  https://ac2eaff62b1f.eicp.fun/v1/models\n     → {probe('https://ac2eaff62b1f.eicp.fun/v1/models')}")

print("\n=== 4) Hermes 内置 provider 名单 ===")
for p in ["hermes_cli", "hermes", "src", "hermes_cli"]:
    pass
# 从已安装包里找 provider 定义
import subprocess
r = subprocess.run(["bash", "-lc",
    "grep -rn --include=*.py -oE '\\\"(deepseek|openai|anthropic|moonshot|xai|openrouter|groq|together|fireworks|custom|nous|zai|minimax)\\\"\\s*:' "
    "/c/Users/Administrator/AppData/Local/hermes/hermes-agent/ 2>/dev/null | head -40"],
                   capture_output=True, text=True, errors="replace")
print(r.stdout.strip() or "  (grep 未命中)")

print("\n=== 5) 模型目录里的 deepseek 条目 ===")
cat = HERMES / "cache" / "model_catalog.json"
if cat.exists():
    try:
        d = json.loads(cat.read_text(encoding="utf-8"))
        items = d if isinstance(d, list) else d.get("models", d.get("data", []))
        hits = []
        for m in items:
            s = json.dumps(m, ensure_ascii=False).lower()
            if "deepseek" in s:
                hits.append(m.get("id") or m.get("name") or str(m)[:80])
        print(f"  命中 {len(hits)} 条:")
        for h in hits[:25]:
            print(f"    {h}")
    except Exception as e:
        print(f"  解析失败: {e}")
