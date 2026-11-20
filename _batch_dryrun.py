#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量 dry-run 今天所有素材，验证发布脚本兼容性"""
import subprocess, sys, glob
from pathlib import Path

DRAFTS = Path(r"C:\Users\Administrator\Desktop\MianAI知识库\MianAI知识库\vault\资料库\素材材料\茶叶素材")
REPO = Path(r"C:\afeng_tea")
files = sorted(glob.glob(str(DRAFTS / "2026-11-15-*.md")))

ok, fail = [], []
for i, f in enumerate(files, 1):
    p = Path(f)
    r = subprocess.run([sys.executable, str(REPO / "publish_new.py"), f, "--dry-run"],
                       cwd=str(REPO), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    out = r.stdout + r.stderr
    if r.returncode == 0:
        # 抽取统计
        acts = faq = tags = ""
        for line in out.split("\n"):
            if "[2/9] 解析" in line:
                acts = line.split("解析:")[-1].strip()
            if "场景图" in line and "[4/9]" in line:
                tags = line.split(":")[-1].strip()
        synth = "合成导语" if "自动合成导语" in out else "自带导语"
        ok.append((p.name, acts, synth))
        print(f"  ✓ {i:2d}. {p.name[:44]:46s} {acts}  [{synth}]")
    else:
        err = [l for l in out.split("\n") if l.startswith("❌")]
        fail.append((p.name, err[0] if err else "unknown"))
        print(f"  ✗ {i:2d}. {p.name[:44]:46s} {err[0] if err else ''}")

print(f"\n{'='*70}")
print(f"通过 {len(ok)} / {len(files)}　失败 {len(fail)}")
if fail:
    print("\n失败清单:")
    for n, e in fail:
        print(f"  - {n}\n      {e}")
