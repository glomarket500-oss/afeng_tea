# -*- coding: utf-8 -*-
"""批量暂停冗余 cron（控费）。按 cron-jobs-bulk-admin 技能规程：备份→改→验证。
保留：生活提醒 8 个、茶叶资讯-8点、3 个生成轮换、周评 2 个、每日发文脚本。
"""
import json
import shutil
from datetime import datetime
from pathlib import Path

J = Path(r"C:\Users\Administrator\AppData\Local\hermes\cron\jobs.json")
BAK = J.with_suffix(J.suffix + ".bak_20261116_costcontrol")
shutil.copy2(J, BAK)
print(f"备份: {BAK.name}")

# 要停的：茶叶系列 13 个（保留 07晨语=5ca6766a19a8、19养生=e07a2152c955）
#         凤凰单丛系列 11 个（保留 04做青=29c356765d6d）
#         节日礼品送茶指南 1 个（与茶叶-19 重叠）
PAUSE = {
    # 茶叶系列
    "9db567035dd7": "茶叶-08茶山产地",
    "546e5a26c6ac": "茶叶-09茶界资讯",
    "c4c43b5af544": "茶叶-10社会观察",
    "40ec28b6497b": "茶叶-11品鉴技巧",
    "2bd26cb93d0d": "茶叶-12产业动态",
    "477c2ecac6bd": "茶叶-13文化传承",
    "a0fee16dbaec": "茶叶-14茶器美学",
    "756c5776f4a9": "茶叶-15茶禅一味",
    "281febc66715": "茶叶-16茶人故事",
    "88c361efa5eb": "茶叶-17海外茶缘",
    "cbc98db09137": "茶叶-18茶旅融合",
    "711a933261f6": "茶叶-20茶食搭配",
    "0fa4463fca16": "茶叶-21茶叶夜话",
    # 凤凰单丛系列
    "79740538ae2b": "凤凰单丛-01采茶篇",
    "0099b5c1d85f": "凤凰单丛-02晒青篇",
    "877ae50d3c6d": "凤凰单丛-03晾青篇",
    "6d604fcb698c": "凤凰单丛-05杀青篇",
    "6fcdcc0d1458": "凤凰单丛-06揉捻篇",
    "542aeb35888e": "凤凰单丛-07烘焙篇",
    "7318c2d1c4b4": "凤凰单丛-08老茶农篇",
    "1557900aafc7": "凤凰单丛-09传承篇",
    "21bc5cf753d1": "凤凰单丛-10茶季篇",
    "e78d5de0133a": "凤凰单丛-11品种篇",
    "d55e43e4c373": "凤凰单丛-12高山茶园篇",
    # 重叠任务
    "66e4ff2881da": "节日礼品送茶指南（与茶叶-19重叠）",
}

data = json.loads(J.read_text(encoding="utf-8"))
jobs = data["jobs"] if isinstance(data, dict) and "jobs" in data else data
now = datetime.now().astimezone().isoformat(timespec="seconds")

hit, miss = [], []
for j in jobs:
    jid = j.get("id")
    if jid in PAUSE:
        j["enabled"] = False
        j["state"] = "paused"
        j["paused_at"] = now
        j["paused_reason"] = "控费：素材库积压513篇、日产13.7篇而发布1篇/天，暂停生成侧冗余任务（可随时恢复）"
        hit.append(PAUSE[jid])
for k, name in PAUSE.items():
    if not any(j.get("id") == k for j in jobs):
        miss.append(name)

J.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\n已暂停 {len(hit)} 个：")
for h in hit:
    print(f"  - {h}")
if miss:
    print(f"\n⚠ 未找到（ID 可能已变）: {miss}")

# 验证
data2 = json.loads(J.read_text(encoding="utf-8"))
jobs2 = data2["jobs"] if isinstance(data2, dict) and "jobs" in data2 else data2
still_on = [j for j in jobs2 if j.get("id") in PAUSE and j.get("enabled")]
print(f"\n=== 验证 ===")
print(f"  应停 {len(PAUSE)}，实际停 {sum(1 for j in jobs2 if j.get('id') in PAUSE and not j.get('enabled'))}")
print(f"  仍启用（应为 0）: {len(still_on)}")

keep = [j for j in jobs2 if j.get("enabled") and not j.get("no_agent")]
print(f"\n仍启用的 LLM 任务（{len(keep)} 个）:")
for j in sorted(keep, key=lambda x: str(x.get("schedule", {}).get("expr", ""))):
    expr = (j.get("schedule") or {}).get("expr") or j.get("schedule_display")
    print(f"  {str(expr):16s} {j['name'][:24]}")
print(f"\n仍启用的脚本任务: {[j['name'] for j in jobs2 if j.get('enabled') and j.get('no_agent')]}")
