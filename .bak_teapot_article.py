# -*- coding: utf-8 -*-
"""紫砂壶专栏：每天凌晨独立成篇、独立发文（阿凤姐讲紫砂 + 点评真实新闻）

与其他两路的分工：
  · 07:40 凤凰单丛主栏目 —— 原样不动
  · 04:10 「今日一壶」预生成 —— 给主文章末尾加一节，原样不动
  · 本脚本 —— **单独一篇文章**，只讲紫砂壶，凌晨 04:40 发

流程：抓新闻 → 选 3 个知识点（轮转）→ 按现有稿子格式写成 draft → 交给 publish_new 发文（走同一套
      生图/建页/首页/sitemap/推送/线上校验，不另起炉灶）

用法：
  python teapot_article.py            # 生成草稿并发布
  python teapot_article.py --dry      # 只生成草稿，不发文
  python teapot_article.py --no-push  # 生成草稿 + 建页校验，不推送
"""
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(r"C:\afeng_tea")
sys.path.insert(0, str(REPO))
KB = Path(r"C:\Users\Administrator\Desktop\MianAI知识库\MianAI知识库\vault\茶叶知识库")
DRAFTS = KB / "资料库" / "素材材料" / "茶叶素材"
STATE = Path(r"C:\afeng_tea\.teapot_article_state.json")

import teapot_daily as TP

WEEK = "一二三四五六日"


def _state():
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"used": [], "last": ""}


def _save(s):
    try:
        STATE.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def pick_topics(n=3):
    """轮转取 n 个知识点，尽量不重复；也避开当天 04:10「今日一壶」已用过的那几个"""
    s = _state()
    used = s.get("used", [])
    try:
        sec_used = set(TP._state().get("used", [])[-3:])     # 主文章里已经讲过的
    except Exception:
        sec_used = set()
    pool = [t for t in TP.TOPICS if t[0] not in used and t[0] not in sec_used]
    if not pool:
        pool = [t for t in TP.TOPICS if t[0] not in used] or TP.TOPICS
    picked = pool[:n]
    used += [t[0] for t in picked]
    s["used"] = used[-len(TP.TOPICS):]
    _save(s)
    while len(picked) < n:
        picked.append(TP.TOPICS[len(picked)])
    return picked


def get_news():
    """先试当天抓取，再退回知识库综合新闻；都没有返回 None（绝不编）"""
    try:
        import teapot_news
        items = teapot_news.fetch(save=True)
        if items:
            return {"date": items[0]["date"], "title": items[0]["title"],
                    "url": items[0]["url"], "snippet": items[0]["snippet"]}
    except Exception as e:
        print(f"  ⚠ 紫砂新闻抓取失败：{type(e).__name__}: {str(e)[:80]}")
    n = TP.latest_news(150)
    if n:
        return {"date": n[0], "title": "", "url": "", "snippet": n[1]}
    return None


def contact_block():
    """从最新一篇现成稿子里复制「联系方式」段，避免在这里硬编码店铺信息"""
    try:
        files = sorted(DRAFTS.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
        for f in files:
            txt = f.read_text(encoding="utf-8", errors="replace")
            i = txt.find("## 联系方式")
            if i > 0:
                return txt[i:].strip()
    except Exception:
        pass
    return "## 联系方式\n\n店在惠州市惠城区东湖花园一区沿江商铺 89-136（凤凰茶业），上午九点到晚上九点。"


def build_draft(dry=False):
    now = datetime.now()
    day_cn = f"{now.month}月{now.day}日"
    topics = pick_topics(3)
    t1, t2, t3 = topics
    news = get_news()

    if news:
        raw = news["title"] or news["snippet"]
        # 只取第一句做钩子，避免"…一篇讲清原产地、泥料产"这种断句
        hook = re.split(r"[？?！!。，,：:；;、\s]", raw.strip())[0][:18]
        # 钩子不合格（空/太短/纯日期）就退回知识点，别出现"阿凤姐说紫砂：2026-11-20"
        if len(hook) < 4 or re.fullmatch(r"[\d\-—/年月日\.]+", hook):
            hook = t1[0]
        title = f"阿凤姐说紫砂：{hook}"
    else:
        title = f"阿凤姐说紫砂：{t1[0]}"

    lead = (f"紫砂壶这事，说到底就两句：泥要好，人要常用。{t1[1][:38]}"
            f"这两天紫砂圈有动静，她泡着茶说：听见了也得自己上手才作数。") if news else \
           (f"紫砂壶这事，说到底就两句：泥要好，人要常用。{t1[1][:44]}")

    p_news = ""
    if news:
        src = f"（{news['date']} 的报道）"
        p_news = (f"这两天有条消息：{news['snippet']}{src}。"
                  f"阿凤姐听完没急着评价，先给自己倒了半杯：\"真真假假，泡一壶就知道了。"
                  f"壶不骗人，泥料对不对，热水一冲,气味先出来。\"她把壶盖揭开看了看，"
                  f"\"我们店里不碰那些说不清的来路，卖的都是能泡、能养、能天天用的。\"")
    else:
        p_news = ("这两天没有值得转述的紫砂新闻，也不硬凑。倒是常有人拿手机上的帖子来问："
                  "\"这把是不是老壶、值不值钱。\"阿凤姐一概摇头：\"我没那本事看真假，"
                  "我只知道它能不能泡出好茶。\"")

    faq = [
        ("新手第一把壶买什么样的？", f"{t3[1][:40]} 先别追名家，挑个出水利落、拿着顺手的。"),
        ("紫砂壶一定要一把配一种茶吗？", "讲究的人一把一茶，日常自用同类茶混着问题不大，别今天单丛明天红茶就行。"),
        ("壶用久了发花、颜色不匀要紧吗？", "多半是正常使用痕迹，段泥尤其明显；嫌难看就专茶专用、用完立刻擦干。"),
        ("店里能先看看真壶再决定吗？", "能。上午九点开门，坐下泡一泡，壶和茶配不配，手上就有答案。"),
    ]

    tags = "#紫砂壶 #宜兴紫砂 #紫砂壶知识 #养壶 #惠州茶叶店 #惠州买茶去哪 #潮州工夫茶 #茶器 #凤凰茶业 #阿凤姐说紫砂"

    body = []
    body.append(f"# {title}")
    body.append("")
    body.append(f"📌 开篇回答：{lead}")
    body.append("")
    body.append("## 【场景开头】")
    body.append("")
    body.append(f"{day_cn}，东湖花园沿江商铺的卷闸门推开，江面还浮着白雾。阿凤姐把一把"
                f"{t1[0].replace('为什么', '').replace('的', '的')}壶摆在茶盘上，先淋了一遍热水。"
                f"早来的客人探头：\"这么早就在弄壶？\"\"壶也得醒。\"她说，\"人醒了，壶没醒，第一泡就白瞎了。\"")
    body.append("")
    body.append(f"## 【第一幕：{t1[0]}】")
    body.append("")
    body.append(t1[1])
    body.append("")
    body.append(f"她说到这儿停一下：\"{t1[2]}——这话我讲了二十多年，还是有人不信。\"")
    body.append("")
    body.append(f"## 【第二幕：{t2[0]}】")
    body.append("")
    body.append(t2[1])
    body.append("")
    body.append(f"客人把壶翻过来看底款，阿凤姐摆手：\"底款能印，手感不能印。"
                f"你摸摸这壶身，砂感细不细、有没有火气，比看字可靠。\"")
    body.append("")
    body.append("## 【第三幕：新闻里这件事，她怎么看】")
    body.append("")
    body.append(p_news)
    body.append("")
    body.append(f"## 【第四幕：{t3[0]}】")
    body.append("")
    body.append(t3[1])
    body.append("")
    body.append("## 【尾声】")
    body.append("")
    body.append("太阳把雾揭掉一层，茶盘上的水痕一圈圈干了。阿凤姐把壶擦净、开盖阴干，"
                "顺手摆回架上：\"壶是用的东西，用顺了它自己会好看。\"")
    body.append("")
    body.append("## FAQ")
    body.append("")
    for q, a in faq:
        body.append(f"**Q：{q}**")
        body.append(f"A：{a}")
        body.append("")
    body.append("## 标签")
    body.append("")
    body.append(tags)
    body.append("")
    body.append(contact_block())
    body.append("")

    text = "\n".join(body)
    DRAFTS.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[\\/:*?\"<>|]", "", title)[:30]
    fp = DRAFTS / f"{now:%Y-%m-%d}-{safe}.md"
    fp.write_text(text, encoding="utf-8")
    print(f"✓ 草稿已生成：{fp.name}（{len(text)} 字）")
    print(f"  标题：{title}")
    print(f"  知识点：{t1[0]} / {t2[0]} / {t3[0]}")
    print(f"  新闻：{'有（' + news['date'] + '）' if news else '今天没有，按知识点讲'}")
    return fp


def publish(fp, mode=""):
    args = [str(REPO / ".venv" / "Scripts" / "python.exe"), "publish_new.py", str(fp), "--no-teapot"]
    if mode:
        args.append(mode)
    env = dict(**__import__("os").environ, AFENG_NO_REAL="1",
               AFENG_PHOTO_SRC="teapot_scene")   # 紫砂专栏：全场景、无人物、无文字、全 AI 生图
    print(f"\n=== 发布：{' '.join(args[1:])} ===")
    p = subprocess.run(args, cwd=str(REPO), env=env)
    return p.returncode


if __name__ == "__main__":
    dry = "--dry" in sys.argv
    no_push = "--no-push" in sys.argv
    f = build_draft(dry)
    if dry:
        raise SystemExit(0)
    rc = publish(f, "--no-push" if no_push else "")
    raise SystemExit(rc)
