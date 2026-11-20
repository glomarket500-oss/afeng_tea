#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""步骤 8：一次原子提交并推送（规范书 §4 步骤8 / §7 坑2）"""
import subprocess, sys
from pathlib import Path

REPO = Path(r"C:\afeng_tea")
SLUG = "20261115立冬之后换一壶秋茶阿凤姐教你顺时而饮"
TMP = " _tmp_ "


def run(cmd):
    r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    print(f"$ {' '.join(cmd)}\n{r.stdout}{r.stderr}")
    return r


# 只 add 本次真正改动的文件；临时脚本一律不 add
run(["git", "add", "index.html"])
run(["git", "add", f"articles/{SLUG}.html"])
run(["git", "add", "images/full/qiuchu-s1.webp", "images/full/qiuchu-s2.webp"])

r = run(["git", "status", "--short"])
lines = [l for l in r.stdout.split("\n") if l.strip()]
staged = [l for l in lines if not l.startswith("??")]
untracked = [l for l in lines if l.startswith("??")]
print(f"\n暂存 {len(staged)} 个文件；未跟踪 {len(untracked)} 个（临时脚本，不会提交）")
for l in staged:
    print("  S", l)
if not staged:
    print("!! 无暂存内容，中止"); sys.exit(1)

r = run(["git", "diff", "--cached", "--stat"])
msg = ("修補《立冬之后，换一壶秋茶》：補 .article-tags 模組與三處統一標籤；"
       "meta/JSON-LD keywords；og/twitter/JSON-LD image 改本篇封面；"
       "卡片 description 改摘要；FAQ 去重複前綴；"
       "s1/s2 用免費 Kolors 重生為干茶葉/茶湯微距並同步圖說與圖片寬高")
r = run(["git", "commit", "-m", msg])
if r.returncode != 0:
    print("!! commit 失败"); sys.exit(1)
run(["git", "log", "--oneline", "-2"])
r = run(["git", "push", "origin", "main"])
print("\npush 退出码:", r.returncode)
sys.exit(r.returncode)
