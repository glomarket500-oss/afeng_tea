# -*- coding: utf-8 -*-
"""修正三个生成任务的 prompt：
1) 章节标记必须是流水线能解析的 ## 【第X幕：xxx】 格式（现在有的写成 **第一幕·xxx**，发布时会被自动重切、结构失真）
2) 严禁真名「林玉凤」——草稿会以 md 附件直接发到飞书群，写真名等于把老板真名发进群
按 cron-jobs-bulk-admin 技能：备份 → 改 → 验证
"""
import json
import shutil
from pathlib import Path

J = Path(r"C:\Users\Administrator\AppData\Local\hermes\cron\jobs.json")
BAK = J.with_suffix(J.suffix + ".bak_20261117_genformat")
shutil.copy2(J, BAK)
print(f"备份: {BAK.name}\n")

TARGETS = {
    "5ca6766a19a8": "茶叶-07晨语茶事",
    "29c356765d6d": "凤凰单丛-04做青篇",
    "e07a2152c955": "茶叶-19健康养生",
}

BLOCK = """

【硬性格式 · 流水线按此解析，符号一个字都不能改】
# 标题（含关键词，15–30字）

📌 开篇回答：100–200字导语，含关键词 + 一句金句

## 【场景开头】
## 【第一幕：xxx】
## 【第二幕：xxx】
## 【第三幕：xxx】
## 【第四幕：xxx】
## 【尾声】

## FAQ
**Q：……**
A：……
（5 组）

## 标签
（8–10 个，必须含 #惠州茶叶店 #惠州买茶去哪）

【红线 · 违反即作废】
- 全文一律写「阿凤姐」，**绝不能出现"林玉凤""林玉鳳"**（这篇会以附件直接发到飞书群，写真名就是把老板真名发进群）
- 不写手机号、电话号码、微信号、QQ 号
- 本站是茶叶站，不写陈皮 / 新会 / 柑普 / 小青柑题材"""

data = json.loads(J.read_text(encoding="utf-8"))
jobs = data["jobs"] if isinstance(data, dict) and "jobs" in data else data

done = []
for j in jobs:
    if j.get("id") not in TARGETS:
        continue
    p = j.get("prompt") or ""
    if "硬性格式 · 流水线按此解析" in p:
        print(f"  ↺ {j['name']} 已含格式块，跳过")
        continue
    j["prompt"] = p.rstrip() + BLOCK
    done.append((TARGETS[j["id"]], len(p), len(j["prompt"])))

J.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"已更新 {len(done)} 个：")
for n, a, b in done:
    print(f"  ✓ {n}  prompt {a} → {b} 字符")

# 验证
data2 = json.loads(J.read_text(encoding="utf-8"))
jobs2 = data2["jobs"] if isinstance(data2, dict) and "jobs" in data2 else data2
print("\n=== 验证 ===")
for j in jobs2:
    if j.get("id") not in TARGETS:
        continue
    p = j.get("prompt") or ""
    ok_fmt = all(k in p for k in ("## 【场景开头】", "## 【第一幕：xxx】", "## 【尾声】", "## FAQ", "## 标签"))
    ok_name = "绝不能出现" in p and "林玉凤" in p
    ok_chenpi = "不写陈皮" in p
    print(f"  {'✓' if ok_fmt else '✗'} {j['name']:16s} 格式块 | "
          f"{'✓' if ok_name else '✗'} 真名禁令 | {'✓' if ok_chenpi else '✗'} 陈皮禁令")
