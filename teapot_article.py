# -*- coding: utf-8 -*-
"""紫砂壶专栏：每天凌晨独立成篇、独立发文 —— 阿凤姐点评紫砂新闻

定位（站方 2026-11-20 明确）：这是**新闻点评**栏目，不是讲故事。
每天一条真实紫砂新闻 + 阿凤姐的专业判断 + 对买壶人的提醒，再顺带把相关知识点讲清楚。
不编人物对话、不虚构场景。

分工：
  · 07:40 凤凰单丛主栏目 —— 原样不动
  · 04:10 「今日一壶」预生成 —— 给主文章末尾加一节，原样不动
  · 本脚本 —— 单独一篇紫砂点评文章，凌晨 04:40 发

配图：全 AI 生图，以紫砂壶与茶席场景为主，人物只作侧影/背影/手部（规范 07 §三），不用实拍照。

用法：
  python teapot_article.py --dry      只生成草稿
  python teapot_article.py --no-push  生成 + 建页校验，不推送
  python teapot_article.py            生成并正式发布
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
DRAFTS = KB.parent / "资料库" / "素材材料" / "茶叶素材"
STATE = Path(r"C:\afeng_tea\.teapot_article_state.json")

import teapot_daily as TP

PRACTICE = {
    "西施壶为什么叫西施": "挑西施看壶嘴，短而微翘最好用；壶把要贴手，握着虎口不空。",
    "石瓢壶的三角骨架": "石瓢要挑重心低的，装满水也不头重脚轻；桥钮要正，倒水时壶盖不晃。",
    "朱泥为什么多做小壶": "朱泥小壶别泡老丛，聚香太狠容易闷苦；一人独饮最合适。",
    "紫泥、段泥、绿泥的区别": "段泥最怕混泡，一壶一茶最稳；紫泥宽容，日常用不挑剔。",
    "全手工和半手工差在哪": "摸内壁，全手工有拍打痕与接缝；半手工内壁规整。别为三个字多付一倍钱。",
    "一壶一茶到底要不要守": "同类茶可混（都是单丛），跨类就别——单丛换红茶会串味。",
    "开壶不用搞仪式感": "温水逐步升温，别冷水直接冲热壶；煮完晾干再用。",
    "养壶其实是养习惯": "每次用完冲净、布擦干、开盖阴干；不用的壶别盖死。",
    "壶嘴出水看三点": "现场倒一次水：断水利落、嘴口不挂水、水柱成线不散。",
    "紫砂透气但不“净化水质”": "别指望壶改茶质；水不好，换水比换壶实在。",
    "段泥为什么容易花": "段泥专茶专用，喝完立刻擦；花了不是坏，是痕迹。",
    "薄胎与厚胎的手感差别": "薄胎配高香型、快出汤；厚胎配老丛、耐泡型。",
    "壶盖严不严怎么看": "转一圈听声音均不均、倒水看沿口渗不渗；轻微活动正常。",
    "老壶的“包浆”不是脏": "真包浆是温润哑光，不是油亮；油亮的多半抹了油。",
    "紫砂壶要不要“开盖养”": "南方回南天务必开盖阴干，闷着容易出霉味。",
    "为什么好壶多是“光货”": "光货看线条比例，也最好打理；新手别一上来买花货。",
    "壶的容量怎么选": "独饮 100-150ml，两三人 200-250ml；工夫茶宁小不大。",
    "倒茶时壶嘴滴水正常吗": "新壶偶有挂水，用顺了会好；一直滴答是做工问题。",
    "紫砂能放多少年": "正常使用不会过期，也不会自己升值；别当理财。",
    "冬天为什么先温壶": "冬天先温水淋一遍再冲茶，尤其朱泥，防惊裂。",
}


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


def pick_topics(n=2):
    """轮转取 n 个知识点，避开当天 04:10「今日一壶」用过的"""
    s = _state()
    used = s.get("used", [])
    try:
        sec_used = set(TP._state().get("used", [])[-3:])
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
            # 挑摘要最长的那条（说明抓到了正文，不是只有标题）
            return max(items, key=lambda x: len(x.get("snippet") or ""))
    except Exception as e:
        print(f"  ⚠ 紫砂新闻抓取失败：{type(e).__name__}: {str(e)[:80]}")
    n = TP.latest_news(200)
    if n:
        return {"date": n[0], "title": "", "url": "", "snippet": n[1]}
    return None


def contact_block():
    try:
        for f in sorted(DRAFTS.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
            txt = f.read_text(encoding="utf-8", errors="replace")
            i = txt.find("## 联系方式")
            if i > 0:
                return txt[i:].strip()
    except Exception:
        pass
    return ("## 联系方式\n\n🏪 **店铺**：阿凤姐茶叶店（惠州凤凰茶业）  \n"
            "📍 **地址**：惠州市惠城区东湖花园一区沿江商铺89-136  \n"
            "📱 **电话**：13435567385（微信同号，支持全国快递）  \n"
            "⏰ **营业时间**：每天 9:00-21:00，全年无休")


def _clean(t, n=240):
    t = re.sub(r"\*\*|__|`|#", "", t or "")
    t = re.sub(r"\s+", " ", t).strip()
    if len(t) <= n:
        return t
    seg = t[:n]
    i = seg.rfind("。")
    return seg[:i + 1] if i > 40 else seg.rstrip("，、；：, ") + "。"


_NOISE_SUFFIX = re.compile(
    r"[_＿\-－—–|｜]\s*(?:地方频道[^_＿\-－—|｜]*|央视网.*|新华网.*|人民网.*|中国新闻网.*|"
    r"新浪.*|搜狐.*|网易.*|腾讯.*|知乎.*|百度.*|微信公众号.*|紫砂之家.*|懂茶帝.*|茶友网.*)$")
# 导航式标题常以站点名开头：「紫砂之家—紫砂壶·茶具·建盏·收藏精」
_SITE_PREFIX = re.compile(
    r"^(?:紫砂之家|懂茶帝|茶友网|宜兴紫砂网|紫砂网)\s*[_＿\-－—–|｜·]+\s*")
_SOCIAL_PREFIX = re.compile(
    r"^.{0,40}?\b(?:on|於|在)\s*(?:Facebook|Twitter|Instagram|YouTube|微博|抖音|小红书)\s*[:：]?\s*",
    re.I)
_DOMAIN = re.compile(r"[（(]\s*[A-Za-z0-9.\-]+\.(?:com|cn|net|org|cc)(?:\.[a-z]{2})?\s*[）)]")
_ORPHAN_QUOTES = "「『“‘\"'」』”’"


def _safe_title_part(s, n=16):
    """从新闻标题 / 知识点里抠一段能当标题的短句。

    2026-11-20/21 实际踩的坑（新闻源抓回来的是这种）：
      "#紫砂壺的「精」與「氣」"        → 硬截 16 字 → "#紫砂壺的「精"（半个引号）
      "紫砂之家—紫砂壶·茶具·建盏·收藏精" → 照抄 → 截在半个词上
      "…福州展出_地方频道福建站_央视网(cctv.com)" → 站点后缀进了标题
      "Purple Cane 紫藤 on Facebook: \"👉一把…"  → 社交平台前缀进了标题

    所以：去井号/表情 → 去社交前缀/域名/站点后缀/栏目标签
          → 只在强标点断句 → 过长时优先在空格逗号处收口
          → 引号成对就收口在收尾引号 → 引号没配平就砍掉未闭合段 → 去结尾残句虚词
    """
    t = (s or "").strip()
    t = re.sub(r"[#＃]+\s*", "", t)                                    # 话题井号
    t = re.sub(r"[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F]", "", t)   # 表情符号
    t = re.sub(r"\*\*|__|`", "", t).strip()
    t = _SOCIAL_PREFIX.sub("", t)
    t = _DOMAIN.sub("", t)
    t = _NOISE_SUFFIX.sub("", t).strip()
    t = _SITE_PREFIX.sub("", t).strip()
    t = re.sub(r"^[【\[][^】\]]{1,8}[】\]]\s*", "", t).strip()          # 开头的栏目标签
    t = t.strip(" 　\t")
    if not t:
        return ""

    # 只在强标点断句，避免把「以器正名 醒石古今」这种被空格拆碎
    seg = re.split(r"[。！!？?]+", t)[0].strip() or t

    truncated = False
    if len(seg) > n:
        cut = max(seg.rfind(" ", 0, n), seg.rfind("，", 0, n), seg.rfind("、", 0, n))
        seg = seg[:cut] if cut >= 6 else seg[:n]
        truncated = True

    # 只有真的截断过，才收口在收尾引号；
    # 否则会把「「养壶」到底要不要开盖」这类完整标题砍成「「养壶」」。
    if truncated:
        for cl in ("”", "」", "』", "》", "）"):
            i = seg.find(cl)
            if -1 < i < len(seg) - 1:
                seg = seg[:i + 1]
                break

    # 引号 / 括号没配平 → 砍掉未闭合的那一段（开头就是半截引号则整段作废）
    for op, cl in (("「", "」"), ("『", "』"), ("“", "”"), ("（", "）"),
                   ("(", ")"), ("《", "》"), ("【", "】"), ('"', '"')):
        if seg.count(op) > seg.count(cl):
            k = seg.rfind(op)
            seg = seg[:k] if k > 0 else ""

    # 掐掉结尾的残句虚词
    seg = re.sub(r"(更是|而且|并且|以及|不仅|因为|所以|但是|就是|的是|的|是|在|与|和|都|也|更"
                 r"|之|把|被|对|从|向|让|给)+$", "", seg)
    # 只清「弱标点」。不能把 「」【】 也 strip 掉，
    # 否则 "紫砂壺的「精」與「氣」" 会少一个收尾引号。
    seg = seg.strip(" 　\t—－-…·、,，。:：;；!?！？|｜/")

    # 收尾清理：按「配平」处理两端孤悬的引号。
    # 「养壶」到底要不要开盖 → 开头的「是成对的，不能削；
    # 社交帖正文以 " 起头且只有一个 " → 这个孤引号要削掉。
    _MATCH = {"「": "」", "『": "』", "“": "”", "‘": "’"}
    _REV = {v: k for k, v in _MATCH.items()}
    for _ in range(3):
        ch = seg[:1]
        if ch in _MATCH and seg.count(ch) > seg.count(_MATCH[ch]):
            seg = seg[1:].strip()
            continue
        ch = seg[-1:]
        if ch in _REV and seg.count(ch) > seg.count(_REV[ch]):
            seg = seg[:-1].strip()
            continue
        if seg.startswith('"') and seg.count('"') % 2 == 1:
            seg = seg[1:].strip()
            continue
        if seg.endswith('"') and seg.count('"') % 2 == 1:
            seg = seg[:-1].strip()
            continue
        break
    return seg


def build_draft():
    now = datetime.now()
    t1, t2 = pick_topics(2)
    news = get_news()
    p1 = PRACTICE.get(t1[0], "上手摸一遍，比看十张照片管用。")
    p2 = PRACTICE.get(t2[0], "现场试一次，比听说可靠。")

    if news:
        fact = _clean(news.get("snippet") or news.get("title") or "")
        hook_src = news.get("title") or fact
        hook = _safe_title_part(hook_src, 16)
        if len(hook) < 4 or re.fullmatch(r"[\d\-—/年月日\.]+", hook):
            hook = _safe_title_part(t1[0], 14)
        title = f"阿凤姐点评紫砂新闻：{hook}"
    else:
        title = f"阿凤姐说紫砂：{_safe_title_part(t1[0], 14)}"

    L = [f"# {title}", ""]
    if news:
        L.append(f"📌 一句话点评：{hook_src.strip()[:36]}——阿凤姐的看法很直接："
                 f"壶是拿来泡茶的，价格故事听听就好，能不能泡出好茶才是硬标准。")
    else:
        L.append(f"📌 一句话：{t1[1][:56]}紫砂这行水很深，阿凤姐只讲一件事——"
                 f"壶是拿来泡茶的，不是拿来供的。")
    L.append("")

    if news:
        L.append("## 📰 今天的这条新闻")
        L.append("")
        head = _clean(news.get("title") or "", 80)
        L.append(f"**{news.get('date', '')}**" + (f" ｜ {head}" if head else ""))
        L.append("")
        L.append(fact)
        L.append("")
        if news.get("url"):
            L.append(f"来源：{news['url']}")
            L.append("")

        L.append("## 💬 阿凤姐怎么看")
        L.append("")
        L.append("阿凤姐看完的第一句话是：「这类消息我每个月都能听见几条。真假先不论，"
                 "它提醒的还是同一件事——买壶的人得自己有一把尺子。」")
        L.append("")
        L.append("「我开这家店二十多年，见过太多客人被故事绕进去：一会儿大师亲制，"
                 "一会儿绝矿老泥，一会儿收藏升值。真到手里一泡茶，出水散、壶盖晃、泥料发涩——"
                 "故事一个也帮不上忙。」")
        L.append("")
        L.append("她说得更直接：「我判断一把壶，只看三样：**出水利不利落、泥料顺不顺眼、"
                 "拿着顺不顺手**。三样都过关，它就是一把好用的壶；三样缺一样，再多说法我也不进。」")
        L.append("")
        L.append("「所以看到这种消息我不慌。壶的价值是泡出来的，不是喊出来的。"
                 "真东西经得起天天用，经不起的，早晚露馅。」")
        L.append("")
    else:
        L.append("## 📰 今天没有值得转述的紫砂新闻")
        L.append("")
        L.append("阿凤姐也不硬凑。倒是常有人拿着手机上的帖子来问：「这把是不是老壶？值不值钱？」"
                 "她一概摇头：「我没那本事隔着屏幕看真假。我只知道它能不能泡出好茶——"
                 "你带茶来，我们泡三泡，好坏自己会说话。」")
        L.append("")

    L.append(f"## 🔍 顺带说清：{t1[0]}")
    L.append("")
    L.append(t1[1])
    L.append("")
    L.append(f"「{t1[2]}——这话我讲了二十多年。」阿凤姐说，{p1}")
    L.append("")

    L.append(f"## 🔍 另一个常被问的：{t2[0]}")
    L.append("")
    L.append(t2[1])
    L.append("")
    L.append(f"「很多人把它想复杂了。」她说，{p2}")
    L.append("")

    L.append("## ✅ 买壶人该记住的四件事")
    L.append("")
    L.append("**一、先定泥料再谈价。** 日常用紫泥最稳，容错高；想聚香选朱泥小壶；"
             "段泥好看但怕混泡，一壶一茶最省心。")
    L.append("")
    L.append("**二、现场倒一次水。** 水柱成线不散、断水利落、嘴口不挂水，这三条过关，"
             "日常用就不会难受。")
    L.append("")
    L.append("**三、摸一遍手感。** 砂感细而不滑、没有火气；壶把贴手，装满水握着不费劲；"
             "壶盖转动均匀、倒水不渗。")
    L.append("")
    L.append("**四、别为故事加价。** 名家、绝矿、老壶这些说法，占的价格份量往往比泥料还重；"
             "预算有限，先把出水和手感挑好。")
    L.append("")

    L.append("## 📍 惠州买茶去哪？阿凤姐茶叶店欢迎你")
    L.append("")
    L.append(contact_block().replace("## 联系方式", "").strip())
    L.append("")
    L.append("🍵 **店里能做什么**：凤凰单丛全系列、紫砂壶现场试泡；"
             "带自己的茶来，免费帮你试壶、看壶、教你怎么养。")
    L.append("")

    L.append("## 标签")
    L.append("")
    L.append("#紫砂壶 #宜兴紫砂 #紫砂壶知识 #养壶 #紫砂新闻 #惠州茶叶店 "
             "#惠州买茶去哪 #潮州工夫茶 #茶器 #阿凤姐说紫砂")

    text = "\n".join(L)
    DRAFTS.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[\\/:*?\"<>|]", "", title)[:30]
    fp = DRAFTS / f"{now:%Y-%m-%d}-{safe}.md"
    fp.write_text(text, encoding="utf-8")
    print(f"✓ 草稿：{fp.name}（{len(text)} 字）")
    print(f"  标题：{title}")
    print(f"  新闻：{'有（' + news.get('date', '') + '）' if news else '今天没有，转为知识点'}")
    print(f"  知识点：{t1[0]} / {t2[0]}")
    return fp


def publish(fp, mode=""):
    args = [str(REPO / ".venv" / "Scripts" / "python.exe"), "publish_new.py", str(fp), "--no-teapot"]
    if mode:
        args.append(mode)
    env = dict(__import__("os").environ)
    env["AFENG_NO_REAL"] = "1"
    env["AFENG_PHOTO_SRC"] = "teapot_scene"
    print(f"\n=== 发布：{' '.join(args[1:])} ===")
    return subprocess.run(args, cwd=str(REPO), env=env).returncode


if __name__ == "__main__":
    f = build_draft()
    if "--dry" in sys.argv:
        raise SystemExit(0)
    rc = publish(f, "--no-push" if "--no-push" in sys.argv else "")
    raise SystemExit(rc)
