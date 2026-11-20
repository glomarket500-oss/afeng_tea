#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""盘点：素材库最新草稿 + 线上最新文章 + 发布流水线脚本现状"""
import os, glob, json, urllib.request, urllib.parse, re
from pathlib import Path

REPO = Path(r"C:\afeng_tea")
DRAFTS = Path(r"C:\Users\Administrator\Desktop\MianAI知识库\MianAI知识库\vault\资料库\素材材料\茶叶素材")
UA = {"User-Agent": "Mozilla/5.0"}

print("=== 1) 素材库 ===")
if DRAFTS.exists():
    files = sorted(DRAFTS.glob("*.md"))
    print(f"  路径存在，共 {len(files)} 篇 md")
    recent = sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)[:15]
    print("  最近 15 篇（按修改时间）:")
    for p in recent:
        print(f"    {p.stat().st_mtime:.0f}  {p.name}")
    today = [p for p in files if p.name.startswith("2026-11-15") or p.name.startswith("2026-11-14")]
    print(f"  11/14-11/15 的稿: {len(today)} 篇")
    for p in sorted(today):
        print(f"    - {p.name}")
else:
    print(f"  ❌ 路径不存在: {DRAFTS}")

print("\n=== 2) 线上最新文章 ===")
try:
    with urllib.request.urlopen(urllib.request.Request("https://feng-tea.com/sitemap.xml", headers=UA), timeout=30) as r:
        sm = r.read().decode("utf-8", "ignore")
    locs = re.findall(r"<loc>([^<]+)</loc>", sm)
    dates = re.findall(r"<lastmod>([^<]+)</lastmod>", sm)
    pairs = sorted(zip(dates, locs), reverse=True)
    print(f"  sitemap 共 {len(locs)} 条，最近 5 条:")
    for d, l in pairs[:5]:
        print(f"    {d}  {l.split('/')[-1]}")
except Exception as e:
    print(f"  ERR {e}")

print("\n=== 3) 仓库里的发布脚本 ===")
for pat in ["publish*.py", "_publish*.py", "gen_image*.py", "*publish*"]:
    for f in glob.glob(str(REPO / pat)):
        p = Path(f)
        head = p.read_text(encoding="utf-8", errors="replace")[:600]
        bad = []
        if "afeng-tea.vercel.app" in head: bad.append("旧域名")
        if "C:\\Users\Administrator\Desktop\\afeng_tea_repo" in head: bad.append("旧仓库路径")
        if "REPO_DIR" in head or "REPO =" in head:
            for line in head.split("\n"):
                if "REPO" in line and ("=" in line) and ("C:" in line or "Path" in line):
                    bad.append("REPO定义: " + line.strip()[:70])
        print(f"  {p.name:30s} {'⚠ ' + '; '.join(bad) if bad else 'OK'}")

print("\n=== 4) git 远程 HEAD ===")
import subprocess
r = subprocess.run(["git", "log", "--oneline", "-1", "origin/main"], cwd=str(REPO),
                   capture_output=True, text=True, errors="replace")
print("  " + r.stdout.strip())
