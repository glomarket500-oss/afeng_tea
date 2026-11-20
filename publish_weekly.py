# -*- coding: utf-8 -*-
"""周评全自动发布入口（供 cron no_agent 脚本模式调用）
流程：取 weekly_drafts 里最新未发布草稿 → 调 publish_new.py 九步全流程 → 打印结果报告
设计要点：
 - 无 LLM 参与，由调度器直接执行脚本，避免长任务被 cron 打断
 - 发布前核对 git：本地若有「非本流水线」的未推送提交 → 拒绝发布并报告（防止把别人未验收的稿推上线）
 - 成功后把草稿名记入 .published.json，避免重复发布
 - stdout 即投递给用户的飞书消息
"""
import os
import re
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

REPO = Path(r"C:\afeng_tea")
DRAFTS = REPO / "weekly_drafts"
STATE = DRAFTS / ".published.json"
SITE = "https://feng-tea.com"


def sh(cmd, cwd=REPO, timeout=900):
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)


def load_state():
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"published": []}


def save_state(st):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")


def pick_draft(st):
    if not DRAFTS.exists():
        return None
    done = set(st.get("published", []))
    cands = [p for p in DRAFTS.glob("*.md") if p.name not in done]
    if not cands:
        return None
    return max(cands, key=lambda p: p.stat().st_mtime)


def git_guard():
    """守则铁律3/6：以 origin/main 最新版为基准发布。
    - 本地落后（别人刚推过）→ 先 pull --ff-only 跟上，再发
    - 本地有未推送提交/已分叉 → 中止（一次 push 会把它们一起推上线）
    """
    sh(["git", "fetch", "origin"], timeout=120)          # 网络抖动不致命，失败退化为用旧 ref
    head = sh(["git", "rev-parse", "HEAD"]).stdout.strip()
    origin = sh(["git", "rev-parse", "origin/main"]).stdout.strip()
    if not head or not origin:
        return False, "无法读取 git 状态"
    if head == origin:
        return True, ""

    ahead = sh(["git", "rev-list", "--count", "origin/main..HEAD"]).stdout.strip() or "0"
    behind = sh(["git", "rev-list", "--count", "HEAD..origin/main"]).stdout.strip() or "0"

    # 纯落后：拉最新再发（铁律3）
    if ahead == "0" and behind != "0":
        p = sh(["git", "pull", "--ff-only", "origin", "main"], timeout=300)
        if p.returncode == 0:
            return True, f"已先行同步远程最新版（落后 {behind} 个提交）"
        return False, f"落后远程 {behind} 个提交，且 pull --ff-only 失败：{(p.stdout + p.stderr)[:200]}"

    log = sh(["git", "log", "--oneline", "origin/main..HEAD"]).stdout.strip()
    return False, (f"本地领先 origin/main {ahead} 个提交，其中可能含其它会话尚未验收的稿子：\n{log}\n"
                   f"为避免把它们一起推上线，本次已中止。请先确认这些提交如何处理（push 或 revert）。")


def main():
    dry = "--dry" in sys.argv
    st = load_state()
    draft = pick_draft(st)
    if not draft:
        print("📭 周评：weekly_drafts 里没有待发布的新草稿（本期未产出，请检查写稿任务是否正常）")
        return 0

    ok, why = git_guard()
    if not ok:
        print(f"⛔ 周评发布中止：{why}")
        return 2
    if why:
        print(f"ℹ {why}")

    print(f"📰 周评自动发布开始 {datetime.now():%Y-%m-%d %H:%M}")
    print(f"草稿：{draft.name}")
    cmd = [sys.executable, "publish_new.py", str(draft)]
    if dry:
        cmd.append("--dry-run")
    r = sh(cmd)
    out = (r.stdout or "") + (r.stderr or "")

    m = re.search(r"✅ 完成: (\S+)", out)
    tags = re.search(r"✅ 标签（三处一致）(\d+) 个: (.+)", out)
    img = re.search(r"⚠ 图片合规: (.+)", out)
    url = m.group(1) if m else ""
    failed = r.returncode != 0 or not m

    if dry:
        print("\n—— DRY-RUN 输出（末 15 行）——")
        print("\n".join(out.strip().split("\n")[-15:]))
        return 0 if not failed else 1

    if failed:
        print(f"❌ 周评发布失败（publish_new.py 退出码 {r.returncode}）")
        print("\n".join(out.strip().split("\n")[-25:]))
        return 1

    # 线上复核（部署 10-40 秒，重试到 3 分钟）
    import time
    import urllib.request
    import urllib.parse
    check = "未复核"
    for att in range(9):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                html = resp.read().decode("utf-8", "ignore")
            good = ('class="lead"' in html and "Q1：" in html and "惠州买茶去哪" in html
                    and html.count("scene-fig") >= 4 and "林玉凤" not in html
                    and "1079790744" not in html and "homepage-hero" not in html)
            check = "✅ 线上复核通过" if good else "⚠ 线上可访问但内容项未全绿"
            if good:
                break
        except Exception:
            pass
        time.sleep(20)

    st.setdefault("published", []).append(draft.name)
    save_state(st)

    print(f"\n✅ 本周周评已上线")
    print(f"🔗 {url}")
    if tags:
        print(f"🏷 标签（三处一致）{tags.group(1)} 个：{tags.group(2)}")
    if img:
        print(f"🖼 配图：像素检测 {img.group(1)}")
    pref_m = re.search(r"prefix = (a\w+)", out)
    if pref_m:
        pref = pref_m.group(1)
        print("🖼 配图地址（**请目视抽查有无汉字/水印**——像素检测会漏判伪汉字）:")
        for k in ("cover", "s1", "s2", "s3", "s4", "s5", "s6"):
            print(f"   {SITE}/images/full/{pref}-{k}.webp")
    print(f"🔍 {check}")
    print(f"\n（自检：标题/开篇三问/场景图/标签/分享图/隐私红线 已由脚本逐项校验；"
          f"版本可回滚：git revert 即可下架）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
