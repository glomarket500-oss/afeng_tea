# -*- coding: utf-8 -*-
import os, re, json, urllib.request, glob

def load_env():
    cands = [r"C:\Users\Administrator\AppData\Local\hermes\.env",
             r"C:\Users\Administrator\AppData\Local\hermes\config\.env",
             r"C:\afeng_tea\.env"]
    d = {}
    for p in cands:
        if os.path.exists(p):
            for line in open(p, encoding="utf-8", errors="ignore"):
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                d[k.strip()] = v.strip().strip('"').strip("'")
    return d

env = load_env()
app_id = os.environ.get("FEISHU_APP_ID") or env.get("FEISHU_APP_ID") or env.get("LARK_APP_ID")
app_secret = os.environ.get("FEISHU_APP_SECRET") or env.get("FEISHU_APP_SECRET") or env.get("LARK_APP_SECRET")
print("env keys found:", [k for k in env if "FEISHU" in k or "LARK" in k])
print("app_id set:", bool(app_id), "secret set:", bool(app_secret))
if not (app_id and app_secret):
    raise SystemExit("missing credentials")

def post(url, body, token=None):
    hdr = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        hdr["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=hdr, method="POST")
    return json.loads(urllib.request.urlopen(req, timeout=40).read().decode())

def get(url, token):
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token})
    return json.loads(urllib.request.urlopen(req, timeout=40).read().decode())

tk = post("https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
          {"app_id": app_id, "app_secret": app_secret})
print("token code:", tk.get("code"))
token = tk["tenant_access_token"]
r = get("https://open.feishu.cn/open-apis/im/v1/chats?page_size=50", token)
print("chats code:", r.get("code"))
for it in r.get("data", {}).get("items", []):
    print(" -", it.get("chat_id"), it.get("name"))
