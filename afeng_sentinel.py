# -*- coding: utf-8 -*-
"""阿凤姐茶叶站 · 每日哨兵（零 LLM）

每天检查 feng-tea.com 今天发了几篇，站上现在有两路点评 + 一路故事，共 **3 篇**：
  · 故事篇      —— 07:40  afeng_daily_publish.py（凤凰单丛主栏目）
  · 紫砂点评    —— 04:40  teapot_article.py（阿凤姐点评紫砂新闻）
  · 普洱点评    —— 03:00  联网搜索找真新闻 → puer_article.py

规则：
  · 3 篇齐 → 闭嘴，什么都不做（stdout 为空，cron 不投递）
  · 缺哪篇补哪篇；一篇都没有就按「普洱 → 紫砂 → 故事」补齐
  · 普洱点评如果《今天没有合格真新闻》，脚本会以退出码 3 拒绝发文
    —— 这是对的，不许拿编的新闻凑数；哨兵遇到 3 就记一笔、不当失败

判定依据：线上 sitemap.xml（以真正在线上为准，不看本地文件）
  · 标题含「紫砂」→ 紫砂点评
  · 标题含「普洱」→ 普洱点评
  · 其它          → 故事篇

防重复：状态写 cache/sentinel/YYYY-MM-DD.json，同一天最多补 3 次；
        本地已有当天页面但线上没有 → 多半是推送没上去，交给 30 分钟补推任务，不重造。

用法：
  python afeng_sentinel.py --check   只看不发
  python afeng_sentinel.py           按规则执行
  python afeng_sentinel.py --date 20261119 --check   查历史某天
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
ECHO = False          # 只在真缺稿、要动手时才往 stdout 说话

KINDS = ("故事篇", "紫砂点评", "普洱点评")


def log(msg):
    LOGDIR.mkdir(parents=True, exist_ok=True)
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    if ECHO:
        print(line, flush=True)
    with open(LOGDIR / "log.txt", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def say(msg):
    """要投递出去的话（no_agent 任务里 stdout 就是飞书消息）"""
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
    """返回 (故事篇, 紫砂点评, 普洱点评) 三个列表
    已改成跳转的废页（cache/sentinel/redirects.txt）不算发文。"""
    skip = set()
    try:
        skip = {x.strip() for x in (LOGDIR / "redirects.txt").read_text(encoding="utf-8").splitlines() if x.strip()}
    except Exception:
        pass
    story, zisha, puer = [], [], []
    for u in fetch_locs():
        m = re.search(r"/articles/(\d{8})([^/]*)\.html?$", u)
        if not m or m.group(1) != today:
            continue
        if f"{m.group(1)}{m.group(2)}" in skip:
            continue
        name = m.group(2)
        if "紫砂" in name:
            zisha.append(u)
        elif "普洱" in name:
            puer.append(u)
        else:
            story.append(u)
    return story, zisha, puer


def local_drafts(today):
    """本地是否已有当天页面（发过但可能没推上去）→ (故事, 紫砂, 普洱)"""
    files = [p.name for p in ARTICLES.glob(f"{today}*.html")]
    has_puer = any("普洱" in n for n in files)
    has_zisha = any("紫砂" in n for n in files)
    has_story = any(("普洱" not in n and "紫砂" not in n) for n in files)
    return has_story, has_zisha, has_puer


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


def all_present(story, zisha, puer):
    return bool(story) and bool(zisha) and bool(puer)


def wait_and_recount(today, tries=5, gap=90):
    """给部署留时间。任何一次网络失败都不许把任务炸掉。"""
    story, zisha, puer = [], [], []
    for i in range(tries):
        try:
            story, zisha, puer = today_posts(today)
        except Exception as e:
            log(f"  第 {i + 1} 次查询失败（{type(e).__name__}），稍后再试")
            story, zisha, puer = [], [], []
        else:
            if all_present(story, zisha, puer):
                return story, zisha, puer
        if i < tries - 1:
            log(f"  第 {i + 1} 次复查：故事 {len(story)} / 紫砂 {len(zisha)} / 普洱 {len(puer)}，{gap}s 后再看")
            time.sleep(gap)
    return story, zisha, puer


def run_code(name, cmd):
    """跑子进程，返回退出码（-1 表示超时）"""
    import os
    env = dict(os.environ)
    log(f"  → 执行 {name}：{' '.join(cmd[1:])}")
    try:
        p = subprocess.run(cmd, cwd=str(REPO), env=env, timeout=1800,
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


def main():
    dry = "--check" in sys.argv
    today = f"{datetime.now():%Y%m%d}"
    for i, a in enumerate(sys.argv):
        if a == "--date" and i + 1 < len(sys.argv):
            today = sys.argv[i + 1].strip()
    LOGDIR.mkdir(parents=True, exist_ok=True)

    try:
        story, zisha, puer = today_posts(today)
    except Exception as e:
        log(f"✗ sitemap 取不到：{type(e).__name__}: {str(e)[:80]}")
        return 0

    log(f"今日 {today}：故事 {len(story)} ｜ 紫砂 {len(zisha)} ｜ 普洱 {len(puer)}")

    if all_present(story, zisha, puer):
        log("✓ 三篇齐了，哨兵闭嘴，不动作")
        return 0

    if dry:
        miss = [k for k, v in zip(KINDS, (story, zisha, puer)) if not v]
        say(f"[--check] {today} 缺：{'、'.join(miss)}（不执行补发）")
        return 0

    # 夜里（09:00 前）只查不补：03:00 / 04:40 / 07:40 还没跑，别抢先发文
    if datetime.now().hour < 9 and "--force" not in sys.argv:
        log("还没到 09:00，正常发文流程未跑完，只记录不补（要强补加 --force）")
        return 0

    story, zisha, puer = wait_and_recount(today)
    if all_present(story, zisha, puer):
        log("✓ 复查后三篇齐了，不动作")
        return 0

    global ECHO
    ECHO = True
    total = len(story) + len(zisha) + len(puer)
    msgs = [f"🌙 每日哨兵 · {datetime.now():%Y-%m-%d}",
            f"今天站上只发了 {total} 篇（故事 {len(story)} / 紫砂 {len(zisha)} / 普洱 {len(puer)}）"]

    st = load_state(today)
    if st.get("attempts", 0) >= 3:
        log(f"今天已补过 {st['attempts']} 次，不再重复补（避免重复发文）")
        say("\n".join(msgs + [f"⚠ 今天已补 {st['attempts']} 次仍不齐，请人工看一眼"]))
        return 0

    has_story, has_zisha, has_puer = local_drafts(today)
    did, skipped = [], []

    # 1) 普洱点评
    if not puer:
        if has_puer:
            log("本地已有当天普洱页面，等 30 分钟补推任务处理，不重造")
            msgs.append("普洱点评：本地有页面、线上没有 → 交给补推，不重造")
        else:
            log("缺【普洱点评】→ 联网找真新闻出稿发布")
            msgs.append("缺【普洱点评】→ 正在补（须真实新闻）")
            rc = run_code("普洱点评", [PY, "puer_article.py"])
            if rc == 3:
                msgs.append("普洱点评：今天没有合格的真实新闻，按规矩未发（不编）")
                skipped.append("普洱点评")
            else:
                did.append(("普洱点评", rc == 0))

    # 2) 紫砂点评
    if not zisha:
        if has_zisha:
            log("本地已有当天紫砂页面，等补推，不重造")
            msgs.append("紫砂点评：本地有页面、线上没有 → 交给补推，不重造")
        else:
            log("缺【紫砂点评】→ 抓今天真实紫砂新闻出稿发布")
            msgs.append("缺【紫砂点评】→ 正在补")
            did.append(("紫砂点评", run_code("紫砂点评", [PY, "teapot_article.py"]) == 0))

    # 3) 故事篇
    if not story:
        if has_story:
            log("本地已有当天故事页，等补推，不重造")
            msgs.append("故事篇：本地有页面、线上没有 → 交给补推，不重造")
        else:
            log("缺【故事篇】→ 用当天素材（无则积压）出稿发布")
            msgs.append("缺【故事篇】→ 正在补")
            did.append(("故事篇", run_code("故事篇", [PY, str(SCRIPTS / "afeng_daily_publish.py")]) == 0))

    st["attempts"] = st.get("attempts", 0) + 1
    st["actions"].append({
        "at": datetime.now().strftime("%H:%M"),
        "did": [{"type": t, "ok": k} for t, k in did],
        "skipped": skipped,
    })
    save_state(today, st)

    if not did:
        say("\n".join(msgs))
        return 0

    # 补完再核一次线上
    time.sleep(150)
    try:
        s2, z2, p2 = today_posts(today)
        msgs.append(f"补发后线上：故事 {len(s2)} / 紫砂 {len(z2)} / 普洱 {len(p2)}")
        if all_present(s2, z2, p2):
            msgs.append("✅ 补齐了")
        elif skipped and not p2:
            msgs.append("⚠ 除了普洱（今天没真新闻），其余还在补/等部署")
        else:
            msgs.append("⚠ 还没齐，看门狗和补推任务会接着处理")
        log(f"补发后：故事 {len(s2)} / 紫砂 {len(z2)} / 普洱 {len(p2)}")
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
        log(f"✗ 哨兵异常已吞掉：{type(e).__name__}: {str(e)[:120]}")
        raise SystemExit(0)
