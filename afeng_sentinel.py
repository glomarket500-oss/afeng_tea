# -*- coding: utf-8 -*-
"""阿凤姐茶叶站 · 每日哨兵（零 LLM）

职责：每天检查 feng-tea.com 今天到底发了几篇，只做一件事——
  · 满 2 篇（1 篇故事 + 1 篇紫砂点评）→ 闭嘴，什么都不做
  · 只有 1 篇 → 判断缺的是「故事篇」还是「点评篇」，把缺的那篇补上
  · 1 篇都没有 → 两篇都补（先补点评、再补故事）

判定依据：线上 sitemap.xml（以真正在线上为准，不看本地文件）
  · /articles/YYYYMMDD…  前缀含「紫砂」→ 点评篇
  · 其它                 → 故事篇（主栏目）

防重复：状态写 cache/sentinel/YYYY-MM-DD.json，同一天最多补 2 次；
        本地已有当天页面但线上没有 → 多半是推送没上去，交给 30 分钟补推任务，不重造。

用法：
  python afeng_sentinel.py --check   只看不发
  python afeng_sentinel.py           照上面的规则执行
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
HDR = {"User-Agent": "Mozilla/5.0 (afeng-sentinel)"}
ECHO = False          # 只有真缺稿、要动手时才往 stdout 说话


def log(msg):
    LOGDIR.mkdir(parents=True, exist_ok=True)
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    if ECHO:
        print(line, flush=True)
    with open(LOGDIR / "log.txt", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def say(msg):
    """要投递出去的话（no_agent 任务里 stdout 就是飞书消息）；为安静时不输出"""
    print(msg, flush=True)


def fetch_locs(timeout=40, tries=3):
    """取 sitemap；网络抖就重试，三次都失败才抛"""
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


def today_posts(today):
    """返回 (故事篇列表, 点评篇列表)，只算今天日期前缀的"""
    story, review = [], []
    for u in fetch_locs():
        m = re.search(r"/articles/(\d{8})([^/]*)\.html?$", u)
        if not m or m.group(1) != today:
            continue
        (review if "紫砂" in m.group(2) else story).append(u)
    return story, review


def local_drafts(today):
    """本地是否已有当天页面（说明发过但可能没推上去）"""
    st = [p for p in ARTICLES.glob(f"{today}*.html") if "紫砂" not in p.name]
    rv = [p for p in ARTICLES.glob(f"{today}*紫砂*.html")]
    return bool(st), bool(rv)


def state_file(today):
    return LOGDIR / f"{today}.json"


def load_state(today):
    f = state_file(today)
    if f.exists():
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"attempts": 0, "actions": []}


def save_state(today, s):
    LOGDIR.mkdir(parents=True, exist_ok=True)
    state_file(today).write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")


def wait_and_recount(today, tries=5, gap=90):
    """给 Vercel 部署留时间，避免把「刚发还在部署」误判成缺稿。
    任何一次网络失败都不许把任务炸掉：当作"这次没查到"，继续下一轮。"""
    story, review = [], []
    for i in range(tries):
        try:
            story, review = today_posts(today)
        except Exception as e:
            log(f"  第 {i + 1} 次查询失败（{type(e).__name__}），稍后再试")
            story, review = [], []
        else:
            if story and review:
                return story, review
        if i < tries - 1:
            log(f"  第 {i + 1} 次复查：故事 {len(story)} 篇 / 点评 {len(review)} 篇，{gap}s 后再看")
            time.sleep(gap)
    return story, review


def run(name, cmd, env_extra=None):
    import os
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    log(f"  → 执行 {name}：{' '.join(cmd[1:])}")
    try:
        p = subprocess.run(cmd, cwd=str(REPO), env=env, timeout=1800,
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        tail = (p.stdout or "").strip().splitlines()[-3:]
        for t in tail:
            log(f"     {t}")
        if p.returncode != 0:
            for t in (p.stderr or "").strip().splitlines()[-3:]:
                log(f"     ! {t}")
        log(f"  → {name} 退出码 {p.returncode}")
        return p.returncode == 0
    except subprocess.TimeoutExpired:
        log(f"  ! {name} 超时（30 分钟）")
        return False


def main():
    dry = "--check" in sys.argv
    today = f"{datetime.now():%Y%m%d}"
    for i, a in enumerate(sys.argv):
        if a == "--date" and i + 1 < len(sys.argv):
            today = sys.argv[i + 1].strip()
    LOGDIR.mkdir(parents=True, exist_ok=True)

    try:
        story, review = today_posts(today)
    except Exception as e:
        log(f"✗ sitemap 取不到：{type(e).__name__}: {str(e)[:80]}")
        return 0

    log(f"今日 {today}：故事篇 {len(story)} ｜ 点评篇 {len(review)}")

    if story and review:
        log("✓ 两篇齐了，哨兵闭嘴，不动作")
        return 0

    if dry:
        missing = []
        if not story:
            missing.append("故事篇")
        if not review:
            missing.append("点评篇")
        say(f"[--check] {today} 缺：{'、'.join(missing)}（不执行补发）")
        return 0

    # 夜里（09:00 前）只查不补：04:40 / 07:40 还没跑，别抢先发文
    if datetime.now().hour < 9 and "--force" not in sys.argv:
        log("还没到 09:00，正常发文流程未跑完，只记录不补（要强补加 --force）")
        return 0

    # 给部署留时间（部署慢时先别急着重造）
    story, review = wait_and_recount(today)
    if story and review:
        log("✓ 复查后两篇齐了，不动作")
        return 0

    global ECHO
    ECHO = True
    msgs = [f"🌙 每日哨兵 · {datetime.now():%Y-%m-%d}",
            f"今天站上只发了 {len(story) + len(review)} 篇"
            f"（故事 {len(story)} / 点评 {len(review)}）"]

    st = load_state(today)
    if st.get("attempts", 0) >= 2:
        log(f"今天已补过 {st['attempts']} 次，不再重复补（避免重复发文）")
        say("\n".join(msgs + [f"⚠ 今天已补过 {st['attempts']} 次仍不齐，请人工看一眼"]))
        return 0

    has_story_local, has_review_local = local_drafts(today)
    did = []

    # 缺点评篇
    if not review:
        if has_review_local:
            log("本地已有当天紫砂点评页，等 30 分钟补推任务处理，不重造")
            msgs.append("点评篇：本地已有页面、线上还没有 → 交给补推任务，不重造")
        else:
            log("缺【点评篇】→ 抓今天真实紫砂新闻，出稿并发布")
            msgs.append("缺【点评篇】→ 正在补：抓今天真实紫砂新闻出稿发布")
            ok = run("紫砂点评", [PY, "teapot_article.py"])
            did.append(("点评篇", ok))

    # 缺故事篇
    if not story:
        if has_story_local:
            log("本地已有当天故事页，等 30 分钟补推任务处理，不重造")
            msgs.append("故事篇：本地已有页面、线上还没有 → 交给补推任务，不重造")
        else:
            log("缺【故事篇】→ 用当天素材（无则积压）出稿并发布")
            msgs.append("缺【故事篇】→ 正在补：用当天素材出稿发布")
            ok = run("故事篇", [PY, str(Path.home() / "AppData/Local/hermes/scripts/afeng_daily_publish.py")])
            did.append(("故事篇", ok))

    st["attempts"] = st.get("attempts", 0) + 1
    st["actions"].append({
        "at": datetime.now().strftime("%H:%M"),
        "did": [{"type": t, "ok": k} for t, k in did],
    })
    save_state(today, st)

    if not did:
        say("\n".join(msgs))
        return 0

    # 补完再核一次线上
    time.sleep(150)
    try:
        s2, r2 = today_posts(today)
        msgs.append(f"补发后线上：故事 {len(s2)} 篇 / 点评 {len(r2)} 篇")
        msgs.append("✅ 补齐了" if (s2 and r2) else "⚠ 还没齐，看门狗和补推任务会接着处理")
        log(f"补发后线上：故事 {len(s2)} / 点评 {len(r2)}")
    except Exception as e:
        log(f"补发后复查失败：{type(e).__name__}")
        msgs.append("⚠ 补发后没能复查线上，稍后看门狗会核对")
    say("\n".join(msgs))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as e:
        # 哨兵不许因为异常把 cron 打成失败（会误报飞书）
        log(f"✗ 哨兵异常已吞掉：{type(e).__name__}: {str(e)[:120]}")
        raise SystemExit(0)
