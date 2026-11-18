# -*- coding: utf-8 -*-
"""自动化发文自检 v2：完整流水线（--no-push 纯校验），精确回滚，并断言没有产生任何提交。

与 v1 的区别：
  - 只回滚「本次运行新产生/新修改」的文件（after - before），绝不碰测试前就存在的改动
  - 断言 HEAD 在测试前后一致（--no-push 不该提交）
  - 断言 index.html / sitemap.xml 确实被本次运行更新过
"""
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(r"C:\afeng_tea")
PY = REPO / ".venv" / "Scripts" / "python.exe"
TMP_DRAFT = Path(r"C:\Users\Administrator\AppData\Local\hermes\cache\scratch\_selftest_v2.md")
SOURCE_DRAFT = Path(r"C:\Users\Administrator\Desktop\MianAI知识库\MianAI知识库\vault\资料库\素材材料\茶叶素材\2026-11-16-三只杯摆成品字.md")


def git(*args):
    # core.quotepath=false：否则中文文件名会被转义成 \345\207... 导致路径匹配全错
    return subprocess.run(["git", "-c", "core.quotepath=false"] + list(args), cwd=str(REPO),
                          capture_output=True, text=True, encoding="utf-8", errors="replace").stdout


def snapshot():
    tracked, untracked = set(), set()
    for line in git("status", "--porcelain", "--untracked-files=all").splitlines():
        if not line.strip():
            continue
        path = line[3:].strip().strip('"')
        (untracked if line.startswith("??") else tracked).add(path)
    return tracked, untracked


fails = []
def check(name, ok, detail=""):
    print(f"  {'✓' if ok else '✗'} {name}" + (f"   {detail}" if detail else ""))
    if not ok:
        fails.append(name)


if not PY.exists():
    raise SystemExit("✗ 专用环境不存在")
if not SOURCE_DRAFT.exists():
    raise SystemExit(f"✗ 源草稿不存在: {SOURCE_DRAFT}")
if git("status", "--porcelain", "publish_new.py", "next_draft.py").strip():
    raise SystemExit("✗ publish_new.py / next_draft.py 有未提交改动，先提交再自检")

head_before = git("rev-parse", "--short", "HEAD").strip()
before_tracked, before_untracked = snapshot()

print("=" * 62)
print(f"自动化发文自检 v2 ｜ HEAD={head_before} ｜ 测试前改动 {len(before_tracked)} 个")
print("=" * 62)

TMP_DRAFT.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(SOURCE_DRAFT, TMP_DRAFT)
m = re.search(r"^#\s*(.+)$", TMP_DRAFT.read_text(encoding="utf-8"), re.M)
print(f"测试稿：{(m.group(1) if m else '')[:44]}")

print("\n[1] 跑完整流水线（--no-push）…")
t0 = time.time()
r = subprocess.run([str(PY), "publish_new.py", str(TMP_DRAFT), "--no-push"],
                   cwd=str(REPO), capture_output=True, text=True,
                   encoding="utf-8", errors="replace", timeout=900)
elapsed = time.time() - t0
out = (r.stdout or "") + (r.stderr or "")
print(f"    退出码 {r.returncode} ｜ 用时 {elapsed:.0f} 秒")
for line in [l for l in out.splitlines() if l.strip()][-12:]:
    print("    " + line[:118])

check("流水线退出码 0", r.returncode == 0, f"实际 {r.returncode}")
check("确实是纯校验（未提交）", "跳过 git add" in out)
check("未做线上验证（--no-push）", "线上验证通过" not in out)

after_tracked, after_untracked = snapshot()
changed = after_tracked - before_tracked
created = after_untracked - before_untracked

print("\n[2] 产物核对")
page = None
for rel in created:
    if rel.startswith("articles/") and rel.endswith(".html"):
        page = REPO / rel
if page is None:
    cands = sorted((REPO / "articles").glob("*.html"), key=lambda p: p.stat().st_mtime)
    if cands:
        page = cands[-1]

check("生成了文章页", page is not None and page.exists(), page.name if page else "无")
if page and page.exists():
    html = page.read_text(encoding="utf-8", errors="replace")
    check("含 H1 标题", "<h1>🍵" in html)
    check("幕结构 ≥3 幕", len(set(re.findall(r"第[一二三四五六]幕", html))) >= 3)
    t = re.search(r'发布于 <time datetime="([^"]+)">([^<]+)</time>', html)
    check("发布时间精确到秒", bool(t) and t.group(2).count(":") == 2, t.group(2) if t else "未找到")
    check("datetime 带 +08:00 时区", bool(t) and "+08:00" in t.group(1), t.group(1) if t else "")
    jl = re.search(r'"datePublished":\s*"([^"]+)"', html)
    check("JSON-LD 到秒", bool(jl) and len(jl.group(1)) >= 19, jl.group(1) if jl else "未找到")
    check("无真名", "林玉凤" not in html)
    check("无 QQ 号", "1079790744" not in html)
    # 陈皮限制只管"文章题材"：页脚/店铺信息块的「新会陈皮（经营范围）」是正常内容，不算违规
    # 判据 = 大标题 + 小标题（章节名），这才是"题材"
    heads = " ".join(re.findall(r"<h[12][^>]*>(.*?)</h[12]>", html, re.S))
    heads = re.sub(r"<[^>]+>", "", heads)
    check("文章题材（标题/小标题）无陈皮", not any(w in heads for w in ("陈皮", "新会", "柑普")),
          heads[:40] if any(w in heads for w in ("陈皮", "新会", "柑普")) else "")
    imgs = set(re.findall(r"images/full/(a[0-9a-f]+-\w+)\.webp", html))
    check("配图引用 7 张", len(imgs) >= 7, f"{len(imgs)} 张")
    missing = [n for n in imgs if not (REPO / "images" / "full" / f"{n}.webp").exists()]
    check("配图全部落盘", not missing, f"缺 {missing[:2]}" if missing else "")
    check("配图像素合规（无汉字/正脸）", "⚠ 图片合规" not in out or "全部通过" in out)

new_imgs = [c for c in created if c.startswith("images/")]
check("新增配图文件", len(new_imgs) >= 7, f"{len(new_imgs)} 个")
check("index.html 已更新", "index.html" in changed or "index.html" in created)
check("sitemap.xml 已更新", "sitemap.xml" in changed or "sitemap.xml" in created)
check("页脚同步（其他文章被改）", len([c for c in changed if c.startswith("articles/")]) >= 1,
      f"{len([c for c in changed if c.startswith('articles/')])} 篇")
check("没有产生新提交", git("rev-parse", "--short", "HEAD").strip() == head_before,
      f"HEAD={git('rev-parse', '--short', 'HEAD').strip()}")

print("\n[3] 回滚（只动本次产生的）")
if changed:
    subprocess.run(["git", "checkout", "--"] + sorted(changed), cwd=str(REPO), capture_output=True)
print(f"    还原 {len(changed)} 个被修改文件")
deleted = 0
for rel in sorted(created):
    p = REPO / rel
    if p.is_file():
        try:
            p.unlink()
            deleted += 1
        except Exception:
            pass
print(f"    删除 {deleted} 个新增文件")
if TMP_DRAFT.exists():
    TMP_DRAFT.unlink()

fin_tracked, fin_untracked = snapshot()
check("回滚后工作区与测试前一致", fin_tracked == before_tracked and fin_untracked == before_untracked,
      f"多出 {sorted(fin_tracked - before_tracked)[:2]} / {sorted(fin_untracked - before_untracked)[:2]}")

print("\n" + "=" * 62)
if fails:
    print(f"❌ 失败 {len(fails)} 项：" + "、".join(fails))
    sys.exit(1)
print(f"✅ 自检全部通过（流水线 {elapsed:.0f} 秒）")
