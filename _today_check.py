#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""确认 DeepSeek 官方 provider 已生效 + 盘点今天(2026-11-15)新生成的素材"""
import os, re, sys, json, glob
from pathlib import Path

HERMES = Path(r"C:\Users\Administrator\AppData\Local\hermes")
DRAFTS = Path(r"C:\Users\Administrator\Desktop\MianAI知识库\MianAI知识库\vault\资料库\素材材料\茶叶素材")
REPO = Path(r"C:\afeng_tea")

print("=" * 60)
print("1) DeepSeek 官方 provider 配置核实")
print("=" * 60)

# --- .env 里的 key（只看是否存在与形态，绝不打印明文）---
for envf in [HERMES / ".env", Path(r"C:\Users\Administrator\.hermes\.env")]:
    if envf.exists():
        txt = envf.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"^\s*(DEEPSEEK[A-Z_]*)\s*=\s*(\S*)", txt, re.M):
            k, v = m.group(1), m.group(2)
            v = v.strip().strip('"').strip("'")
            shape = f"{v[:6]}...{v[-4:]} len={len(v)}" if len(v) > 12 else ("空" if not v else "太短")
            print(f"  {envf.name}: {k} = {shape}")
        if "DEEPSEEK" not in txt:
            print(f"  {envf.name}: 无 DEEPSEEK 条目")

# 环境变量
for k in ["DEEPSEEK_API_KEY", "DEEPSEEK_BASE_URL"]:
    v = os.environ.get(k)
    print(f"  env {k}: {'已设置 len=' + str(len(v)) if v else '未设置'}")

# --- config.yaml 当前模型/provider ---
cfg = HERMES / "config.yaml"
if cfg.exists():
    txt = cfg.read_text(encoding="utf-8", errors="replace")
    print("\n  config.yaml 相关行:")
    for line in txt.split("\n"):
        if re.search(r"(provider|model|base_url|key_env|api_key)", line, re.I):
            s = line.strip()
            # 屏蔽可能的明文 key
            s = re.sub(r"(sk-[A-Za-z0-9]{4})[A-Za-z0-9\-_]+", r"\1[REDACTED]", s)
            print(f"    {s[:120]}")

print("\n" + "=" * 60)
print("2) 今天(2026-11-15)新生成的素材")
print("=" * 60)

if not DRAFTS.exists():
    print(f"  ❌ 素材目录不存在: {DRAFTS}")
    sys.exit(1)

allmd = sorted(DRAFTS.glob("*.md"))
print(f"  素材库总计: {len(allmd)} 篇")

today = [p for p in allmd if p.name.startswith("2026-11-15")]
print(f"  今天生成: {len(today)} 篇\n")

# 已发布的 slug 集合（从仓库 articles/ 提取）
published = set()
for f in glob.glob(str(REPO / "articles" / "*.html")):
    published.add(Path(f).stem)
print(f"  仓库已有文章页: {len(published)} 个\n")

rows = []
for p in today:
    raw = p.read_text(encoding="utf-8", errors="replace")
    # 标题
    m = re.search(r"^#\s+(.+)$", raw, re.M)
    title = m.group(1).strip() if m else p.stem
    # 是否含隐私字段
    privacy = []
    if "林玉凤" in raw or "林玉鳳" in raw: privacy.append("真名")
    if "1079790744" in raw: privacy.append("QQ")
    # 章节完整度
    acts = len(re.findall(r"^##\s*【?(?:第[一二三四五六七八九十]幕|场景开头|尾声)", raw, re.M))
    faq = len(re.findall(r"^\*\*Q", raw, re.M))
    size = len(raw)
    # 是否已发布（按标题关键词模糊匹配 slug）
    key = re.sub(r"[^\u4e00-\u9fa5A-Za-z0-9]", "", title)[:10]
    hit = [s for s in published if key and key in re.sub(r"[^\u4e00-\u9fa5A-Za-z0-9]", "", s)]
    rows.append({
        "file": p.name, "title": title, "size": size,
        "acts": acts, "faq": faq, "privacy": privacy,
        "published": bool(hit), "hit": hit[:1], "mtime": p.stat().st_mtime,
    })

rows.sort(key=lambda r: r["mtime"])
for i, r in enumerate(rows, 1):
    flag = "✅已发" if r["published"] else "🆕待发"
    pv = (" ⚠" + "+".join(r["privacy"])) if r["privacy"] else ""
    print(f"  {i:2d}. {flag} 幕{r['acts']} FAQ{r['faq']} {r['size']:5d}B{pv}")
    print(f"      {r['title'][:60]}")
    print(f"      {r['file']}")

ready = [r for r in rows if not r["published"] and r["acts"] >= 5]
print(f"\n  待发布且结构完整(>=5幕): {len(ready)} 篇")
print(json.dumps([r["file"] for r in ready], ensure_ascii=False, indent=2))
