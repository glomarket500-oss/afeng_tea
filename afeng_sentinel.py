# -*- coding: utf-8 -*-
"""阿凤姐茶叶站 · 每日哨兵（零 LLM）—— 按"该发的时间"判断，不按死的三篇

三路的应发时间：
  · 普洱点评  20:30   puer_article.py（联网搜当天真新闻，24h 内且事件类）
  · 紫砂点评  04:40   teapot_article.py
  · 故事篇    07:40   afeng_daily_publish.py

关键点：**只对"已经到点"的栏目算缺**。白天查的时候不拿晚上的普洱去算缺，
否则中午就会把普洱提前发掉。

规则：
  · 到点的栏目都齐了 → 闭嘴（stdout 空，不投递）
  · 缺哪篇补哪篇；普洱拒发（rc=3，无真新闻）记为"未发"，不算失败、不重试
  · 同一天最多补 3 次；本地已有当天页面而线上没有 → 交给 30 分钟补推任务

用法：
  python afeng_sentinel.py --check
  python afeng_sentinel.py                 # 按规则执行
  python afeng_sentinel.py --date 20261119 --check
"""
import json
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

REPO = Path(r"C:\afeng_tea")
SITEMAP = "https://feng-tea.com/sitemap.xml"
ARTICLES = REPO / "articles"
LOGDIR = REPO / "cache" / "sentinel"
PY = str(REPO / ".venv" / "Scripts" / "python.exe")
SCRIPTS = Path.home() / "AppData/Local/hermes/scripts"
HDR = {"User-Agent": "Mozilla/5.0 (afeng-sentinel)"}
ECHO = False

KINDS = ("故事篇", "紫砂点评", "普洱点评")
DUE = {"故事篇": (7, 40), "紫砂点评": (4, 40), "普洱点评": (20, 30)}


def log(msg):
    LOGDIR.mkdir(parents=True, exist_ok=True)
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    if ECHO:
        print(line, flush=True)
    with open(LOGDIR / "log.txt", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def say(msg):
    print(msg, flush=True)


def due_kinds(now=None):
    """已经过了应发时间的栏目"""
    now = now or datetime.now()
    return {k for k, (h, m) in DUE.items() if (now.hour, now.minute) >= (h, m)}


def fetch_locs(timeout=40, tries=3):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(SITEMAP, headers=HDR)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                xml = r.read().decode("utf-8", "ignore")
            locs = re.findall(r"<loc>([^<]+)</loc>", xml)
            if locs:
                return locs
            last = RuntimeError("sitemap 里没有 loc")
        except Exception as e:
            last = e
            if i < tries - 1:
                time.sleep(8 * (i + 1))
    raise last if last else RuntimeError("sitemap 取不到")


def _skip_set():
    try:
        return {x.strip() for x in (LOGDIR / "redirects.txt").read_text(encoding="utf-8").splitlines() if x.strip()}
    except Exception:
        return set()


def today_posts(today):
    """返回 dict：故事篇/紫砂点评/普洱点评 → URL 列表（排除已改跳转的废页）"""
    out = {k: [] for k in KINDS}
    skip = _skip_set()
    for u in fetch_locs():
        m = re.search(r"/articles/(\d{8})([^/]*)\.html?$", u)
        if not m or m.group(1) != today:
            continue
        if f"{m.group(1)}{m.group(2)}" in skip:
            continue
        name = m.group(2)
        if "紫砂" in name:
            out["紫砂点评"].append(u)
        elif "普洱" in name:
            out["普洱点评"].append(u)
        else:
            out["故事篇"].append(u)
    return out


def local_drafts(today):
    files = [p.name for p in ARTICLES.glob(f"{today}*.html")]
    return {
        "普洱点评": any("普洱" in n for n in files),
        "紫砂点评": any("紫砂" in n for n in files),
        "故事篇": any(("普洱" not in n and "紫砂" not in n) for n in files),
    }


def load_state(today):
    f = LOGDIR / f"{today}.json"
    if f.exists():
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"attempts": 0, "actions": []}


def save_state(today, s):
    LOGDIR.mkdir(parents=True, exist_ok=True)
    (LOGDIR / f"{today}.json").write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")


def missing_of(posts, due):
    return [k for k in KINDS if k in due and not posts[k]]


def summary(posts, due):
    parts = []
    for k in KINDS:
        n = len(posts[k])
        parts.append(f"{k[:2]} {n}" + ("" if k in due else "(未到点)"))
    return " ｜ ".join(parts)


def wait_and_recount(today, due, tries=5, gap=90):
    posts = {k: [] for k in KINDS}
    for i in range(tries):
        try:
            posts = today_posts(today)
        except Exception as e:
            log(f"  第 {i + 1} 次查询失败（{type(e).__name__}），稍后再试")
            posts = {k: [] for k in KINDS}
        else:
            if not missing_of(posts, due):
                return posts
        if i < tries - 1:
            log(f"  第 {i + 1} 次复查：{summary(posts, due)}，{gap}s 后再看")
            time.sleep(gap)
    return posts


def run_code(name, cmd):
    import os
    log(f"  → 执行 {name}：{' '.join(cmd[1:])}")
    try:
        p = subprocess.run(cmd, cwd=str(REPO), env=dict(os.environ), timeout=1800,
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        for t in (p.stdout or "").strip().splitlines()[-3:]:
            log(f"     {t}")
        if p.returncode != 0:
            for t in (p.stderr or "").strip().splitlines()[-3:]:
                log(f"     ! {t}")
        log(f"  → {name} 退出码 {p.returncode}")
        return p.returncode
    except subprocess.TimeoutExpired:
        log(f"  ! {name} 超时（30 分钟）")
        return -1


CMD = {
    "普洱点评": lambda: [PY, "puer_article.py"],
    "紫砂点评": lambda: [PY, "teapot_article.py"],
    "故事篇": lambda: [PY, str(SCRIPTS / "afeng_daily_publish.py")],
}


def main():
    dry = "--check" in sys.argv
    today = f"{datetime.now():%Y%m%d}"
    for i, a in enumerate(sys.argv):
        if a == "--date" and i + 1 < len(sys.argv):
            today = sys.argv[i + 1].strip()
    LOGDIR.mkdir(parents=True, exist_ok=True)

    due = due_kinds()
    try:
        posts = today_posts(today)
    except Exception as e:
        log(f"✗ sitemap 取不到：{type(e).__name__}: {str(e)[:80]}")
        return 0

    log(f"今日 {today}：{summary(posts, due)}")

    miss = missing_of(posts, due)
    if not miss:
        log(f"✓ 到点的栏目都齐了（{'、'.join(sorted(due))}），哨兵闭嘴，不动作")
        return 0

    if dry:
        say(f"[--check] {today} 到点的栏目缺：{'、'.join(miss)}（不执行补发）")
        return 0

    # 夜里（09:00 前）只查不补：04:40/07:40 还没跑，别抢先发文
    if datetime.now().hour < 9 and "--force" not in sys.argv:
        log("还没到 09:00，正常发文流程未跑完，只记录不补（要强补加 --force）")
        return 0

    posts = wait_and_recount(today, due)
    miss = missing_of(posts, due)
    if not miss:
        log("✓ 复查后都齐了，不动作")
        return 0

    global ECHO
    ECHO = True
    msgs = [f"🌙 每日哨兵 · {datetime.now():%Y-%m-%d}",
            f"到点栏目缺 {len(miss)} 篇（{summary(posts, due)}）"]

    st = load_state(today)
    if st.get("attempts", 0) >= 3:
        log(f"今天已补过 {st['attempts']} 次，不再重复补")
        say("\n".join(msgs + [f"⚠ 已补 {st['attempts']} 次仍不齐，请人工看一眼"]))
        return 0

    has = local_drafts(today)
    did, skipped = [], []

    for k in miss:
        if has[k]:
            log(f"{k}：本地有页面、线上没有 → 交给补推，不重造")
            msgs.append(f"{k}：本地有页面、线上没有 → 交给补推任务")
            continue
        log(f"缺【{k}】→ 出稿发布")
        msgs.append(f"缺【{k}】→ 正在补")
        rc = run_code(k, CMD[k]())
        if k == "普洱点评" and rc == 3:
            msgs.append("普洱点评：24 小时内没有合格真新闻，按规矩未发（不编）")
            skipped.append(k)
        else:
            did.append((k, rc == 0))

    st["attempts"] = st.get("attempts", 0) + 1
    st["actions"].append({"at": datetime.now().strftime("%H:%M"),
                          "did": [{"type": t, "ok": o} for t, o in did], "skipped": skipped})
    save_state(today, st)

    if not did:
        say("\n".join(msgs))
        return 0

    time.sleep(150)
    try:
        p2 = today_posts(today)
        msgs.append(f"补发后：{summary(p2, due)}")
        miss2 = missing_of(p2, due)
        if not miss2:
            msgs.append("✅ 补齐了")
        elif skipped:
            msgs.append("⚠ 除普洱（今天无真新闻）外都齐了")
        else:
            msgs.append("⚠ 还没齐，看门狗和补推任务会接着处理")
        log(f"补发后：{summary(p2, due)}")
    except Exception as e:
        log(f"补发后复查失败：{type(e).__name__}")
        msgs.append("⚠ 补发后没能复查线上")
    say("\n".join(msgs))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as e:
        log(f"✗ 哨兵异常已吞掉：{type(e).__name__}: {str(e)[:120]}")
        raise SystemExit(0)
