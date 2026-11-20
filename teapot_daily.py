# -*- coding: utf-8 -*-
"""今日一壶：紫砂壶知识 + 当日真实新闻点评（每天固定栏目）

设计取舍：
  · 知识按队列轮转，讲过的排后面，避免天天重复
  · 新闻只取知识库 `12-新闻素材/` 里当天采集的真实条目；**没有就明说没有**，绝不编造行情
  · 点评只讲使用/工艺常识，不碰"鉴定、升值、投资"——紫砂这行水深，说错要担责
  · 有实拍壶图用实拍，没有才让 AI 生成

产物：一组 (章节标题, [段落])，交给 publish_new 插进正文。
"""
import json
import re
from datetime import datetime
from pathlib import Path

KB = Path(r"C:\Users\Administrator\Desktop\MianAI知识库\MianAI知识库\vault\茶叶知识库")
NEWS_DIR = KB / "12-新闻素材"
STATE = Path(r"C:\afeng_tea\.teapot_state.json")
CACHE_DIR = Path(r"C:\afeng_tea\cache\teapot")
MANUAL = KB / "资料库" / "素材材料" / "茶叶素材" / "今日一壶"

# 知识点队列（讲过的往后排）。每条 = 主题 + 知识点 + 阿凤姐的切入角度
TOPICS = [
    ("西施壶为什么叫西施", "壶身圆润、短嘴短把，整体像一位抱壶的女子，所以叫西施。"
     "它是紫砂里最经典的小容量器型之一，一手能握，出水快。", "为什么老茶客第一把壶常选它"),
    ("石瓢壶的三角骨架", "石瓢上小下大、桥钮直嘴，重心低，看着拙其实稳。"
     "壶身近梯形，出汤利落，泡单丛这种高香茶不容易闷。", "为什么潮州人泡单丛爱用石瓢"),
    ("朱泥为什么多做小壶", "朱泥收缩率大，做大器容易变形开裂，所以多见 100-200ml 的小壶。"
     "密度高、聚香，冲高香型茶很讨巧。", "朱泥壶不是越大越值钱，是越小越难做"),
    ("紫泥、段泥、绿泥的区别", "紫泥最常见、颜色偏紫褐；段泥是紫泥与绿泥的共生矿，颜色偏米黄；"
     "绿泥量少、偏青灰。三种泥性不同，段泥最容易“花”，用完要及时擦干。", "新手先用哪种泥料不吃亏"),
    ("全手工和半手工差在哪", "全手工靠拍打泥片成型，内壁有接缝和手工痕；半手工用模具定形，效率高、规整。"
     "两者都能泡出好茶，差别在工艺与价格，不在“能不能用”。", "别被“全手工”三个字绕晕"),
    ("一壶一茶到底要不要守", "紫砂会吸附香气，混泡容易串味，所以讲究的人一把壶只泡一类茶。"
     "但这是习惯，不是铁律——日常自用，同类茶（比如都是单丛）混着用问题不大。", "我们店里怎么建议客人配壶"),
    ("开壶不用搞仪式感", "清水洗净、温水润透、用准备长期泡的那款茶煮或冲泡几次就够了。"
     "网上那些豆腐、甘蔗、茶叶一起煮的说法，更多是热闹。", "开壶越简单越不容易出事"),
    ("养壶其实是养习惯", "每次用完清水冲净、布擦干、开盖阴干，别用洗洁精，别留茶汤在壶里过夜。"
     "日积月累的润泽，是喝出来的，不是擦出来的。", "见过太多壶是“养”坏的"),
    ("壶嘴出水看三点", "一看嘴根是否通畅、二看内壁网孔是否整齐、三看倒水时是否断水利落。"
     "出水散、滴答漏，多半是做工问题，不是你没学会用。", "挑壶时我一定让客人当场倒一次水"),
    ("紫砂透气但不“净化水质”", "紫砂有双气孔结构，透气不透水，能让茶汤更柔顺，"
     "但说它能“净化水质、去除农残”是夸大。茶好不好，还是看茶本身。", "别把壶当净水器"),
    ("段泥为什么容易花", "段泥颜色浅、显脏，茶汤渗进气孔后容易留下深浅不匀的痕迹。"
     "不是坏了，是正常使用痕迹；想干净就专茶专用、用完立刻擦。", "段泥壶“花”了要不要扔"),
    ("薄胎与厚胎的手感差别", "薄胎轻、传热快，适合高香、快出汤；厚胎保温好、聚热，适合老丛这类耐泡的茶。"
     "同一款茶，换个胎厚，喝起来就不一样。", "为什么同款茶换个壶就变味了"),
    ("壶盖严不严怎么看", "盖口配合要看转动是否顺、是否有明显晃动，倒水时沿口是否渗水。"
     "轻微活动是正常的，紫砂不是玻璃，不必追求严丝合缝。", "盖不严就是做工差吗"),
    ("老壶的“包浆”不是脏", "长期使用后壶表形成的温润光泽叫包浆，是茶汤与手泽长期作用的结果。"
     "但市面上很多“老壶”是人为做旧，买旧壶要看使用痕迹是否自然。", "我们只卖新壶的原因"),
    ("紫砂壶要不要“开盖养”", "长期不用时把盖子拿开、壶内彻底干透，避免闷出异味。"
     "南方回南天尤其注意，紫砂吸潮，闷久了会有霉味。", "惠州回南天，壶怎么过"),
    ("为什么好壶多是“光货”", "光货（不刻不绘）靠线条和比例说话，最见功力；花货、筋纹器更看工艺难度。"
     "日常用，光货耐看也好打理。", "我给客人推荐的多半是光货"),
    ("壶的容量怎么选", "一人独饮 100-150ml 顺手；两三人 200-250ml 合适；"
     "工夫茶讲究“小壶勤泡”，大壶反而容易闷。", "一家人喝茶该买多大"),
    ("倒茶时壶嘴滴水正常吗", "新壶偶尔挂水常见，用久了嘴口被茶汤润过会更利落。"
     "如果一直滴答不止，多半是嘴口做工问题。", "滴水就被说成次品，冤不冤"),
    ("紫砂能放多少年", "紫砂是烧结的陶，正常使用不会“过期”，也不会自己变值钱。"
     "它就是个耐用的器物，用得久、护得好，自然好看。", "别把壶当理财产品"),
    ("冬天为什么先温壶", "紫砂导热慢，骤冷骤热容易惊裂，尤其朱泥。"
     "冬天先温水淋一遍再冲茶，是保护壶，也是保护茶。", "一把裂了的壶，都是这么来的"),
]

PERSONA = "阿凤姐"


def _state():
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"used": [], "last": ""}


def _save_state(s):
    try:
        STATE.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def pick_topic():
    """按轮转取一个知识点：讲过的排到最后"""
    s = _state()
    used = s.get("used", [])
    idx = 0
    for i, (name, _, _) in enumerate(TOPICS):
        if name not in used:
            idx = i
            break
    else:
        s["used"] = []          # 全讲完一轮，重置
        idx = 0
    name, know, angle = TOPICS[idx]
    used.append(name)
    s["used"] = used[-len(TOPICS):]
    s["last"] = name
    _save_state(s)
    return name, know, angle


def _clean_news_line(line, max_len=150):
    """去掉 markdown 记号/小标题，按句号截断，避免半句话"""
    line = re.sub(r"\*\*|__|`", "", line)
    line = re.sub(r"^(要点|来源|标题|摘要|正文)[:：]\s*", "", line)
    line = re.sub(r"^\d+[.、)]\s*", "", line).strip()
    if len(line) <= max_len:
        return line
    seg = line[:max_len]
    i = seg.rfind("。")
    if i > 40:
        return seg[:i + 1]
    return seg.rstrip("，、；：, ") + "。"


def latest_news(max_len=150):
    """取当天采集的真实新闻里与紫砂/茶器相关的一条；没有返回 None（绝不编造）
    相关性排序：紫砂/宜兴/壶 > 茶器/建盏 > 其他茶市消息"""
    today = datetime.now()
    cands = []
    if NEWS_DIR.exists():
        files = sorted(NEWS_DIR.rglob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)[:5]
        for p in files:
            m = re.search(r"(\d{4})-(\d{2})-(\d{2})", p.stem)
            if m:
                try:
                    dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                    if (today - dt).days > 2:      # 只要最近三天的
                        continue
                except Exception:
                    pass
            try:
                txt = p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                txt = ""
            for line in txt.splitlines():
                line = line.strip(" -*>|#\t")
                if len(line) < 20:
                    continue
                # 跳过文件头/元数据行（"2026-11-20 紫砂壶新闻（2 条，Tavily 采集）"、"日期：…"）
                if re.search(r"(Tavily 采集|新闻（\d+ 条|^日期：|^链接：|^摘要：)", line):
                    continue
                if "紫砂" in line or "宜兴" in line or "壶" in line:
                    score = 3
                elif "茶器" in line or "建盏" in line:
                    score = 2
                elif any(k in line for k in ("茶市", "茶叶", "茶产业", "茶博会", "茶馆")):
                    score = 1
                else:
                    continue
                cands.append((score, m.group(0) if m else p.stem[:10], _clean_news_line(line, max_len)))
    if not cands:
        return None
    cands.sort(key=lambda x: -x[0])
    score, date_str, text = cands[0]
    return date_str, text, score


def build_section(slug="", with_news=True):
    """生成「今日一壶」章节：返回 (标题, [段落1, 段落2, 段落3])"""
    name, know, angle = pick_topic()
    news = latest_news() if with_news else None

    p1 = f"<strong>{name}。</strong>{know}"

    if news:
        date_str, line, score = news
        lead = "紫砂这行" if score >= 3 else ("茶器这一块" if score == 2 else "茶市")
        p2 = (f"{lead}，值得留意的一条：{line}"
              f"（{date_str} 采集）说到底是一件事——<strong>器物是拿来用的，不是拿来供的</strong>。")
    else:
        p2 = ("今天没有值得转述的紫砂新消息，就不硬凑。"
              "行情、价格这些事，听见了也得自己回去泡一壶才知道真假。")

    p3 = (f"{angle}——这是店里被问得最多的一类问题。我开这家店二十多年，"
          f"见过太多客人被“老壶”“大师壶”绕进去，其实先把手边这把用顺了，比什么都实在。"
          f"到店里坐坐，我给你冲一泡，壶和茶配不配，喝一口就知道。")

    return f"今日一壶：{name}", [p1, p2, p3]


def get_section():
    """优先用凌晨 04:10 预生成的当天栏目（缓存），没有再现场生成并写入缓存。
    预生成的意义：把取材/新闻核对放在闲时窗凌晨，07:40 发文只做拼装，快且稳。"""
    c = load_today()
    if c:
        return c["head"], c["paras"]
    head, paras = build_section()
    save_today(head, paras)
    return head, paras


def cache_path(day=None):
    day = day or datetime.now().strftime("%Y-%m-%d")
    return CACHE_DIR / f"{day}.json"


def save_today(head, paras, extra=None):
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        data = {"head": head, "paras": paras,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "created_at": datetime.now().isoformat(timespec="seconds")}
        if extra:
            data.update(extra)
        cache_path().write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False


def load_today():
    p = cache_path()
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        if d.get("head") and d.get("paras") and d.get("date") == datetime.now().strftime("%Y-%m-%d"):
            return d
    except Exception:
        pass
    return None


# 紫砂专栏配图场景池（站方 2026-11-20：要场景、不要人物；画面不许出现汉字）
SCENES = [
    "茶店木质长桌前，一位穿素色上衣的中年女店主侧身低头斟茶，手边是一把紫红色紫砂壶与两只白瓷小杯，晨光从百叶窗斜照进来",
    "紫砂壶放在深色茶盘上，一只手的指尖正扶着壶盖，壶口升起一缕水汽，暖调侧光，人物只露出手部",
    "茶店里一位顾客的背影坐在茶席前，对面茶盘上并排三把不同泥色的紫砂壶（紫泥、段泥、朱泥），浅景深",
    "竹帘窗边的小茶桌，一人端着公道杯往小杯里倒琥珀色茶汤，桌上一把石瓢壶，午后柔光，人物为侧影",
    "老木桌上铺着粗麻布，一双正在擦壶的手与紫砂壶同框，旁边茶则、茶针、茶巾围成一圈，俯拍",
    "茶洗前，一双手把紫砂壶浸入清水，水面映出壶与手的倒影，泥料颗粒质感清晰，微距",
    "店铺木质货架前，一位顾客伸手从架上取下一把紫砂壶，背景是成排壶与暖黄灯光，人物为侧后方",
    "冬日午后茶席，一人捧着小杯坐在桌边，桌上紫砂壶与另一只空杯，光斑落在桌面，背景纸窗与竹影",
]


def scene_pool(n=7):
    """取 n 个场景提示词：茶席场景 + 自然出现的人物（侧影/背影/手部，不要正脸特写）+ 无文字"""
    out = []
    for i in range(n):
        out.append(SCENES[i % len(SCENES)]
                   + "，画面里以紫砂壶和茶席场景为主，人物只作陪衬（侧影、背影或手部，不出现正面特写），"
                     "不出现任何文字、汉字、书法、印章、标识或水印")
    return out


def image_prompt():
    """没有实拍壶图时的 AI 生图提示（只拍壶与茶席，不出现人）"""
    return ("宜兴紫砂壶放在原木茶席上，壶身温润，旁边一只白瓷小杯与少量凤凰单丛干茶，"
            "侧逆光，背景虚化的木质墙面，构图简洁留白，没有任何文字与标识")
