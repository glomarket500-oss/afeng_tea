# -*- coding: utf-8 -*-
"""普洱茶专栏：每天凌晨 03:00 独立成篇 —— 阿凤姐点评普洱茶新闻

定位与紫砂专栏一致：**新闻点评**，不是讲故事。
每天一条真实普洱新闻（云南产区/行情/打假/仓储/拍卖/标准）+ 阿凤姐的专业判断
+ 对买茶人的提醒，再顺带把相关普洱知识点讲清楚。不编人物对话、不虚构场景。

分工：
  · 04:40 紫砂壶点评（teapot_article.py）
  · 04:10 「今日一壶」预生成（给 07:40 主文加一节）
  · 07:40 凤凰单丛主栏目（afeng_daily_publish.py）
  · 本脚本 —— 普洱茶点评，凌晨 03:00 发

配图：全 AI 生图（AFENG_NO_REAL=1 + AFENG_PHOTO_SRC=puer_scene），
      主体是茶饼/茶汤/器物，人物只作侧影/背影/手部，不露正脸、画面无文字。

用法：
  python puer_article.py --dry      只生成草稿
  python puer_article.py --no-push  生成 + 建页校验，不推送
  python puer_article.py            生成并正式发布
"""
import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

REPO = Path(r"C:\afeng_tea")
sys.path.insert(0, str(REPO))
KB = Path(r"C:\Users\Administrator\Desktop\MianAI知识库\MianAI知识库\vault\茶叶知识库")
DRAFTS = KB.parent / "资料库" / "素材材料" / "茶叶素材"
STATE = Path(r"C:\afeng_tea\.puer_article_state.json")

# (标题, 知识点, 阿凤姐的口头禅/落点)
TOPICS = [
    ("生茶和熟茶到底差在哪",
     "熟茶比生茶多一道渥堆发酵：茶叶在温湿环境下堆起来发酵几十天，出来的汤色红浓、入口醇厚，几乎不苦不涩；生茶是杀青压饼自然陈化，新茶清冽带青味，越放越转。",
     "别拿生茶的标准去嫌弃熟茶没香气，也别拿熟茶的顺口去判断生茶的潜力"),
    ("普洱为什么压成饼",
     "压成饼主要是为了运输和陈化：散茶占地、易碎、走味快，紧压之后茶与空气接触慢，转化更稳。同样一批料，压饼和散放几年后是两个味道。",
     "存茶不是堆着不管，压饼只是把节奏放慢"),
    ("「越陈越香」有前提",
     "越陈越香不是所有普洱都成立：原料要够、工艺要正、仓储要干净，三样缺一样，放十年也只是变旧。存坏了的老茶，比新茶更难喝。",
     "我从不跟客人说买了就升值，只说存得好会更好喝"),
    ("干仓和湿仓的区别",
     "干仓是常温、湿度可控、通风干净的环境，转化慢但干净；湿仓靠高湿催熟，转得快，容易带仓味、霉味。老茶有仓味不一定是坏，但仓味重到盖住茶味，就不值得喝。",
     "闻到闷味、霉味、纸箱味压过茶香的，先别急着买"),
    ("古树茶和台地茶",
     "古树指树龄大的乔木型茶树，台地是密植修剪的茶园茶。古树未必人人喝得惯，台地也未必差——好不好喝看工艺和仓储，树龄只是一个变量，不是价签。",
     "别一听古树就掏钱，先喝三泡再说话"),
    ("年份不能只看包装",
     "棉纸、内飞、印章都可以后做，包装上的年份只能当参考。真正看年份要看茶汤的厚度、叶底的活性、仓储的干净程度，这些骗不了人。",
     "我店里从不替人隔着包装认年份"),
    ("拼配不是坏事",
     "拼配是把不同产区、不同年份、不同等级的料按比例调，目的是稳定口感和成本。大厂靠拼配做标准味，纯料靠个性。没有谁高谁低，只看合不合你的口。",
     "拼配做得好，是手艺，不是掺假"),
    ("撬茶别撬成碎末",
     "顺着茶饼压制的纹路，从边缘插茶刀、轻轻往上抬，能撬出成块的茶；硬掰会碎一地，碎末出汤快、容易苦。",
     "撬茶这动作看着小，直接影响这一泡好不好喝"),
    ("熟茶怎么泡才不闷",
     "熟茶要用沸水、快出汤：洗茶一道，前几泡三到五秒就出，出慢了就闷出堆味。壶小、水滚、手快，是熟茶的三字诀。",
     "很多人说熟茶不好喝，其实是泡闷了"),
    ("新生茶别急着喝",
     "刚压好的生茶青味重、刺激性大，胃不好的喝多了不舒服。放一年半载退退火气再喝，或者少放一点、快出汤。",
     "新茶不是不能喝，是别当口粮猛灌"),
    ("普洱存放要避开什么",
     "避光、避潮、避异味、避高温：厨房、阳台、樟木箱都不合适。纸箱加干净的房间，离地离墙，比什么紫砂罐都实在。",
     "存茶最贵的是环境，不是容器"),
    ("茶饼上的白霜是什么",
     "白霜有两种：一种是茶叶里的咖啡碱等物质析出的结晶，无害；一种是受潮长霉，带霉味、呈绒毛状。分不清就看味道——有霉味就整饼放弃。",
     "长毛的茶不要舍不得，喝坏肚子更贵"),
    ("「宫廷普洱」是什么",
     "宫廷是等级说法，指细嫩的芽头级熟茶，不是贡品也不是配方名。口感细、耐泡度一般，别被名字带跑。",
     "名字越贵气，越要看汤色和叶底"),
    ("老茶头是怎么来的",
     "老茶头是渥堆发酵时结成的茶块，出汤慢、耐泡、甜度高，价格通常不贵。喜欢醇厚顺滑的可以试试，但别当成什么稀罕物。",
     "老茶头就是茶疙瘩，好喝不贵，实在"),
    ("普洱的「茶气」怎么理解",
     "茶气是喝下去的身体感受——发热、出汗、打嗝、通透，因人而异，也受浓度影响。它是体验，不是可以标价的东西。",
     "别人说有茶气，你喝着没感觉，也正常"),
]

PRACTICE = {
    "生茶和熟茶到底差在哪": "新手先各买一小块对照着喝，一次就分清了。",
    "普洱为什么压成饼": "买饼回来别急着全撬开，喝多少撬多少，剩下的原样放着。",
    "「越陈越香」有前提": "存茶先解决环境：干净、避光、不靠墙不靠地。",
    "干仓和湿仓的区别": "买老茶一定要现场泡，闻盖香、看叶底，别只听年份。",
    "古树茶和台地茶": "同价位里挑汤感厚、回甘久的，比认树龄实际。",
    "年份不能只看包装": "让店家现场撬给你泡，汤色和叶底不会撒谎。",
    "拼配不是坏事": "喜欢稳定口感的选拼配，喜欢个性的选纯料，别互相看不起。",
    "撬茶别撬成碎末": "茶刀从饼边斜插，往上抬，别往下压。",
    "熟茶怎么泡才不闷": "沸水、快出、小壶，出汤时间按秒数。",
    "新生茶别急着喝": "新茶少放茶、快出汤，胃不好的别空腹喝。",
    "普洱存放要避开什么": "纸箱装、离地离墙、避开厨房和阳台。",
    "茶饼上的白霜是什么": "有霉味就整饼放弃，别刮掉接着喝。",
    "「宫廷普洱」是什么": "看汤色透不透、叶底活不活，别只看名字。",
    "老茶头是怎么来的": "喜欢醇厚的可以买小份试，别当投资品。",
    "普洱的「茶气」怎么理解": "浓度别太高，空腹别猛喝，体感自己体会。",
}


def _state():
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"used": []}


def _save(s):
    try:
        STATE.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def pick_topics(n=2):
    s = _state()
    used = s.get("used", [])
    pool = [t for t in TOPICS if t[0] not in used] or TOPICS
    picked = pool[:n]
    used += [t[0] for t in picked]
    s["used"] = used[-len(TOPICS):]
    _save(s)
    return picked


OVERRIDE = Path(r"C:\afeng_tea\cache\puer_news_override.json")


def _override_news():
    """03:00 那个任务用联网搜索找到的真新闻会写在这里（当天有效）。
    只认：有链接、有日期、有正文摘要。"""
    try:
        if not OVERRIDE.exists():
            return None
        if OVERRIDE.stat().st_mtime < time.time() - 86400:
            return None
        data = json.loads(OVERRIDE.read_text(encoding="utf-8"))
        it = data[0] if isinstance(data, list) and data else data
        if not isinstance(it, dict):
            return None
        if not (it.get("url") and it.get("date") and len(it.get("snippet") or "") >= 40):
            return None
        # 必须是今天发布的新闻（站方要求用当天真实新闻）
        try:
            age = (datetime.now() - datetime.strptime(it["date"], "%Y-%m-%d")).days
            if age < 0 or age > 0:
                print(f"  ⚠ 搜索到的新闻是 {it['date']} 的，不是今天，弃用")
                return None
        except Exception:
            return None
        it.setdefault("score", 3)
        return it
    except Exception:
        return None


def get_news():
    """素材优先级：① 联网搜索写入的当日真新闻 → ② Tavily 抓取。
    两样都没有就返回 None（宁可这条不发，也不编新闻）。"""
    ov = _override_news()
    if ov:
        print(f"  ✓ 采用联网搜索到的普洱新闻：{ov.get('date')} {ov.get('title', '')[:40]}")
        return ov
    try:
        import puer_news as PN
        # 只要今天发布的（站方要求用当天真实新闻）；没有就不发，绝不拿旧新闻冒充
        items = PN.fetch(save=True, days=1, max_age=0)
        real = [x for x in items if x.get("url") and len(x.get("snippet") or "") >= 60]
        if real:
            # 先按「像不像真新闻」，再按正文长度
            return max(real, key=lambda x: (x.get("score", 1), len(x.get("snippet") or "")))
        print("  今天没有『带正文的真实普洱新闻』")
    except Exception as e:
        print(f"  ⚠ 普洱新闻抓取失败：{type(e).__name__}: {str(e)[:80]}")
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


def _first_sentence(s, n=90):
    """取新闻正文第一句原文，用来在点评里"指着原话说" """
    t = _clean(s or "", 400)
    parts = re.split(r"(?<=[。！？])", t)
    return (parts[0] if parts and parts[0] else t)[:n]


def _commentary(news):
    """按新闻类型分别点评：先引用原文一句，再落到买茶人身上"""
    text = (news.get("title") or "") + " " + (news.get("snippet") or "")
    lead = _first_sentence(news.get("snippet") or "")
    out = []
    if lead:
        out.append(f"阿凤姐把这条消息读了两遍，指着其中一句说：「{lead}」——这句是实在话。")

    if re.search(r"(查处|通报|假冒|不合格|抽检|整治|违法|案件|销毁)", text):
        out += [
            "「这类消息我最愿意看到。茶这行最怕的不是贵，是假——假货一多，老老实实做茶的人先被拖垮。」",
            "「所以客人问我怎么防，我只给一句：别信故事，信汤色和叶底。能泡出一杯干净茶汤的，才叫茶。」",
        ]
    elif re.search(r"(标准|规范|标识|地标|技术规程|溯源)", text):
        out += [
            "「标准落地比标准发布难。文件上写得再清楚，到了市场还得有人一句句讲给买茶的人听。」",
            "「我店里做的是最土的一件事：每一罐写清产地、品种、季别。溯源不是高科技，是敢写，敢让人打电话来问。」",
        ]
    elif re.search(r"(博览会|茶博会|展会|开幕|论坛|大会|推介会)", text):
        out += [
            "「展会我这些年去过不少。台上讲产值、讲品牌，热闹是热闹；我真正想看的，是产区那些年轻人"
            "怎么把普洱做成能天天喝的东西，而不是只供在柜子里等人来问价。」",
            "「同一片叶子，做成天天能喝的茶，才是产业的底气。价格炒得再高，喝的人少了，最后伤的还是茶农。」",
        ]
    elif re.search(r"(产量|减产|干旱|暴雨|行情|价格|收购|涨价|下跌)", text):
        out += [
            "「行情涨跌，跟坐下来喝茶的人关系没那么大。涨了就少买点，跌了正好试试以前舍不得的那几饼。」",
            "「我这些年看到的是：真按工艺做、仓储干净的茶，价格有波动，喝起来没变；"
            "靠故事撑起来的，风一过就现形。」",
        ]
    else:
        out += ["「这类消息我当参考，不当依据。行情是别人的，杯子是你自己的。」"]

    out.append("她说自己的标准很土：「**汤色透不透、入口顺不顺、回甘久不久、叶底活不活**。"
               "四样过关，价钱合理，就是好茶。四样不过关，哪怕年份再老、名字再响，我也不进。」")
    return out


def build_draft():
    now = datetime.now()
    t1, t2 = pick_topics(2)
    news = get_news()
    p1 = PRACTICE.get(t1[0], "上手试一次，比听人说可靠。")
    p2 = PRACTICE.get(t2[0], "自己泡过才算数。")

    if news:
        fact = _clean(news.get("snippet") or "")
        hook_src = news.get("title") or fact
        cand = re.sub(r"\s+", " ", hook_src.strip())
        hook = cand if len(cand) <= 22 else cand[:22]
        hook = re.sub(r"(更是|而且|并且|以及|不仅|因为|所以|但是|就是|的是|的|是|在|与|和|都|也|更|于)+$", "", hook)
        if len(hook) < 4 or re.fullmatch(r"[\d\-—/年月日\.]+", hook):
            hook = t1[0]
        title = f"阿凤姐点评普洱茶新闻：{hook}"
    else:
        title = f"阿凤姐说普洱：{t1[0]}"

    L = [f"# {title}", ""]
    if news:
        L.append(f"📌 一句话点评：{hook_src.strip()[:36]}——阿凤姐的看法照旧："
                 f"茶是拿来喝的，年份和故事都排在汤感后面。")
    else:
        L.append(f"📌 一句话：{t1[1][:56]}普洱这行水不比别的茶浅，阿凤姐只认一件事——"
                 f"喝得舒服、存得干净，才叫好茶。")
    L.append("")

    if news:
        L.append(f"## 📰 这条新闻（{news.get('date', '')} 发布）")
        L.append("")
        L.append(f"**{news.get('date', '')}**" + (f" ｜ {_clean(news.get('title') or '', 80)}" if news.get("title") else ""))
        L.append("")
        if fact:
            L.append(fact)
            L.append("")
        if news.get("url"):
            L.append(f"来源：{news['url']}")
            L.append("")

        L.append("## 💬 阿凤姐怎么看")
        L.append("")
        for para in _commentary(news):
            L.append(para)
            L.append("")
    else:
        L.append("## 📰 今天没有值得转述的普洱新闻")
        L.append("")
        L.append("阿凤姐也不硬凑。倒是常有人拿着手机上的帖子来问：「这饼是不是老的？值不值钱？」"
                 "她一概摇头：「隔着屏幕认年份，我没那本事。你带茶来，我们撬开泡三泡，"
                 "汤色、叶底、回甘，好坏自己会说话。」")
        L.append("")

    L.append(f"## 🔍 顺带说清：{t1[0]}")
    L.append("")
    L.append(t1[1])
    L.append("")
    L.append(f"「{t1[2]}——这话我讲过很多遍。」阿凤姐说，{p1}")
    L.append("")

    L.append(f"## 🔍 另一个常被问的：{t2[0]}")
    L.append("")
    L.append(t2[1])
    L.append("")
    L.append(f"「很多人把它想复杂了。」她说，{p2}")
    L.append("")

    L.append("## ✅ 买普洱该记住的四件事")
    L.append("")
    L.append("**一、先分生熟再谈别的。** 生茶清冽有陈化空间，熟茶醇厚顺口；"
             "胃不好的先从熟茶、老生茶入手。")
    L.append("")
    L.append("**二、现场撬开泡三泡。** 汤色透不透、入口顺不顺、回甘久不久、叶底活不活，"
             "四样自己看，别只听介绍。")
    L.append("")
    L.append("**三、年份当参考，不当价签。** 棉纸和内飞都能后做；仓储干净、汤感厚实才是硬证据。")
    L.append("")
    L.append("**四、存茶先解决环境。** 避光、避潮、避异味，纸箱离地离墙，比买贵的存茶罐有用。")
    L.append("")

    L.append("## 📍 惠州买茶去哪？阿凤姐茶叶店欢迎你")
    L.append("")
    L.append(contact_block().replace("## 联系方式", "").strip())
    L.append("")
    L.append("🍵 **店里能做什么**：凤凰单丛全系列、普洱生熟茶现场撬饼试泡；"
             "带自己的茶来，免费帮你试、帮你看仓储。")
    L.append("")

    L.append("## 标签")
    L.append("")
    L.append("#普洱茶 #普洱生茶 #普洱熟茶 #普洱茶知识 #撬茶 #惠州茶叶店 "
             "#惠州买茶去哪 #潮州工夫茶 #茶饼 #阿凤姐说普洱")

    text = "\n".join(L)
    DRAFTS.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[\\/:*?\"<>|]", "", title)[:30]
    fp = DRAFTS / f"{now:%Y-%m-%d}-{safe}.md"
    fp.write_text(text, encoding="utf-8")
    print(f"✓ 草稿：{fp.name}（{len(text)} 字）")
    print(f"  标题：{title}")
    print(f"  新闻：{'有（' + news.get('date', '') + '）' if news else '今天没有，转为知识点'}")
    print(f"  知识点：{t1[0]} / {t2[0]}")
    return fp, bool(news)


def publish(fp, mode=""):
    args = [str(REPO / ".venv" / "Scripts" / "python.exe"), "publish_new.py", str(fp), "--no-teapot"]
    if mode:
        args.append(mode)
    env = dict(__import__("os").environ)
    env["AFENG_NO_REAL"] = "1"
    env["AFENG_PHOTO_SRC"] = "puer_scene"
    print(f"\n=== 发布：{' '.join(args[1:])} ===")
    return subprocess.run(args, cwd=str(REPO), env=env).returncode


if __name__ == "__main__":
    f, has_news = build_draft()
    if "--dry" in sys.argv:
        raise SystemExit(0)
    if not has_news:
        # 站方要求：必须是真实新闻。抓不到就不发，绝不编一条来凑。
        print("⚠ 今天没有可靠的普洱真实新闻（带链接+有正文），按规矩不发这一篇。")
        raise SystemExit(3)
    rc = publish(f, "--no-push" if "--no-push" in sys.argv else "")
    raise SystemExit(rc)
