# -*- coding: utf-8 -*-
"""两件事：
1) 给新建的新闻采集任务指定模型（create 不继承默认模型）
2) 给三个写作任务加「素材来源」指令：先读知识库最近7天新闻摘要再写
备份 → 改 → 验证
"""
import json
import shutil
from pathlib import Path

J = Path(r"C:\Users\Administrator\AppData\Local\hermes\cron\jobs.json")
BAK = J.with_suffix(J.suffix + ".bak_20261117_newssource")
shutil.copy2(J, BAK)
print(f"备份: {BAK.name}\n")

COLLECT_ID = "398ca98e3c8d"
WRITERS = {
    "5ca6766a19a8": "茶叶-07晨语茶事",
    "29c356765d6d": "凤凰单丛-04做青篇",
    "e07a2152c955": "茶叶-19健康养生",
}

NEWS_BLOCK = """

【素材来源 · 必须遵守】
写作前先用 read_file 读知识库最近 7 天的新闻摘要（目录见下，取最新的 1–2 个文件）：
C:/Users/Administrator/Desktop/MianAI知识库/MianAI知识库/vault/茶叶知识库/12-新闻素材/
把里面的**真实行业动态**融进文章（写成阿凤姐茶桌上跟客人聊的话），并遵守：
- 标「已核」的数字可以用，但要注明是谁公布的
- 标「待核」的一律降级表述：只写趋势（如"量减价增""上新基地"），不写精确数字
- 新闻目录里没有的内容，宁可只写店里真实场景，绝不得自己编造行业数据"""

data = json.loads(J.read_text(encoding="utf-8"))
jobs = data["jobs"] if isinstance(data, dict) and "jobs" in data else data

for j in jobs:
    jid = j.get("id")
    if jid == COLLECT_ID:
        j["model"] = "deepseek-flash"
        j["provider"] = "deepseek"
        j["base_url"] = "https://api.deepseek.com/v1"
        j["pinned"] = True
        print(f"✓ 采集任务已绑定模型: deepseek-flash / deepseek")
    if jid in WRITERS:
        p = j.get("prompt") or ""
        if "【素材来源 · 必须遵守】" in p:
            print(f"  ↺ {j['name']} 已含素材来源块，跳过")
            continue
        j["prompt"] = p.rstrip() + NEWS_BLOCK
        print(f"✓ {j['name']}：已加「先读知识库新闻」指令（{len(p)} → {len(j['prompt'])} 字符）")

J.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

# 验证
data2 = json.loads(J.read_text(encoding="utf-8"))
jobs2 = data2["jobs"] if isinstance(data2, dict) and "jobs" in data2 else data2
print("\n=== 验证 ===")
for j in jobs2:
    if j.get("id") == COLLECT_ID:
        print(f"  采集任务: model={j.get('model')} provider={j.get('provider')} "
              f"{(j.get('schedule') or {}).get('expr')} toolsets={j.get('enabled_toolsets')}")
    if j.get("id") in WRITERS:
        ok = "【素材来源 · 必须遵守】" in (j.get("prompt") or "")
        print(f"  {'✓' if ok else '✗'} {j['name']:20s} 已读知识库新闻={ok}")
