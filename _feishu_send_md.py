# -*- coding: utf-8 -*-
import os, json, uuid, urllib.request, urllib.parse

PATH = r"C:\Users\Administrator\Desktop\MianAI知识库\MianAI知识库\vault\资料库\素材材料\茶叶素材\2026-11-23-惠州东平周一清晨阿凤姐一壶蜜兰香先暖了晨练人的手.md"
CHAT = "oc_47f80b14f92c85c277075cc6d1d78d6a"

def load_env():
    d = {}
    for p in [r"C:\Users\Administrator\AppData\Local\hermes\.env"]:
        if os.path.exists(p):
            for line in open(p, encoding="utf-8", errors="ignore"):
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    d[k.strip()] = v.strip().strip('"').strip("'")
    return d

env = load_env()
app_id, app_secret = env["FEISHU_APP_ID"], env["FEISHU_APP_SECRET"]

def post_json(url, body, token=None):
    hdr = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        hdr["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=hdr, method="POST")
    return json.loads(urllib.request.urlopen(req, timeout=40).read().decode())

token = post_json("https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
                  {"app_id": app_id, "app_secret": app_secret})["tenant_access_token"]

fname = os.path.basename(PATH)
content = open(PATH, "rb").read()
b = "----" + uuid.uuid4().hex
def part(s):
    return s.encode("utf-8") if isinstance(s, str) else s
body = b""
body += part("--%s\r\n" % b)
body += part('Content-Disposition: form-data; name="file_type"\r\n\r\nstream\r\n')
body += part("--%s\r\n" % b)
body += part('Content-Disposition: form-data; name="file_name"\r\n\r\n%s\r\n' % fname)
body += part("--%s\r\n" % b)
body += part('Content-Disposition: form-data; name="file"; filename="%s"\r\n' % fname)
body += part("Content-Type: application/octet-stream\r\n\r\n")
body += content
body += part("\r\n--%s--\r\n" % b)

req = urllib.request.Request("https://open.feishu.cn/open-apis/im/v1/files", data=body,
                             headers={"Authorization": "Bearer " + token,
                                      "Content-Type": "multipart/form-data; boundary=" + b},
                             method="POST")
up = json.loads(urllib.request.urlopen(req, timeout=90).read().decode())
print("upload:", up.get("code"), up.get("msg"), up.get("data"))

fk = up["data"]["file_key"]
msg = post_json("https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
                {"receive_id": CHAT, "msg_type": "file",
                 "content": json.dumps({"file_key": fk})}, token)
print("send:", msg.get("code"), msg.get("msg"), msg.get("data", {}).get("message_id"))

mid = msg["data"]["message_id"]
url = "https://open.feishu.cn/open-apis/im/v1/messages/" + urllib.parse.quote(mid)
req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token})
back = json.loads(urllib.request.urlopen(req, timeout=40).read().decode())
items = back.get("data", {}).get("items", [])
print("verify code:", back.get("code"), "msg_type:", items[0]["msg_type"] if items else None)
print("body:", items[0]["body"]["content"][:200] if items else None)
