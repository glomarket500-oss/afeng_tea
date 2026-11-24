# -*- coding: utf-8 -*-
"""每天抓「普洱茶」真实新闻（Tavily）→ 存知识库，供 03:00 普洱茶点评用

为什么单开一路：知识库 12-新闻素材/ 综合新闻里普洱条目稀少，且常被泛茶市新闻挤掉。
阿凤姐要点评的是**普洱茶本身**的新闻（云南产区、行情、打假查处、仓储、拍卖、非遗、标准）。

产物：vault\\茶叶知识库\\12-新闻素材\\普洱茶\\YYYY-MM-DD.md
去重：.puer_news_seen.json 记 URL，同一件事不重复点评
"""
import json
import re
import urllib.request
from datetime import datetime
from pathlib import Path

KB = Path(r"C:\Users\Administrator\Desktop\MianAI知识库\MianAI知识库\vault\茶叶知识库")
OUT_DIR = KB / "12-新闻素材" / "普洱茶"
SEEN = Path(r"C:\afeng_tea\.puer_news_seen.json")
ENV = Path(r"C:\Users\Administrator\AppData\Local\hermes\.env")

QUERIES = [
    "普洱茶 最新消息",
    "普洱茶 市场 行情 云南",
    "普洱茶 打假 查处 假冒",
    "普洱茶 收藏 拍卖 老茶",
]

# 标题里必须出现的普洱相关词（宁可漏，不要抓成别的茶）
HIT = ("普洱", "云南", "勐海", "易武", "冰岛", "班章", "布朗山", "熟茶", "生茶", "茶饼", "古树")

BAN_URL = r"(taobao|tmall|jd\.com|1688|pinduoduo|suning|zhe800|smzdm|xiaohongshu)"
BAN_TITLE = r"(排行榜|京东|淘宝|天猫|1688|拼多多|旗舰店|优惠|券后|秒杀|包邮|卖家|促销|已售)"
BAN_BODY = r"(卖家|￥|促销|包邮|已售|销量|优惠券|下单)"


def _keys():
    out = []
    try:
        for line in ENV.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line.startswith("TAVILY_API_KEY") and "=" in line:
                v = line.split("=", 1)[1].strip().strip('"').strip("'")
                if v and v not in out:
                    out.append(v)
    except Exception:
        pass
    return out


def _norm_date(s):
    """Tavily 的 published_date 有时是 'Wed, 18 Nov 2026 …' 这种 RFC 格式"""
    s = (s or "").strip()
    if not s:
        return ""
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return m.group(0)
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(s).strftime("%Y-%m-%d")
    except Exception:
        return ""


def _search(key, query, days=7):
    body = json.dumps({
        "api_key": key, "query": query, "topic": "news",
        "days": days, "max_results": 10,
        "search_depth": "basic", "include_answer": False,
    }).encode()
    req = urllib.request.Request("https://api.tavily.com/search", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=50) as r:
        return json.loads(r.read().decode("utf-8")).get("results", [])


def _seen():
    if SEEN.exists():
        try:
            return json.loads(SEEN.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def fetch(save=True, days=7):
    """返回本次抓到的新条目列表 [{title, url, date, snippet}]"""
    keys = _keys()
    if not keys:
        print("⚠ 没找到 TAVILY key（hermes\\.env）")
        return []

    seen = set(_seen())
    items, tried = [], 0
    for q in QUERIES:
        res = None
        alt = list(keys[tried % len(keys):] + keys[:tried % len(keys)])
        for key in alt[:2]:                      # 401/超时就换下一个 key
            try:
                res = _search(key, q, days=days)
                break
            except Exception as e:
                print(f"  ⚠ 搜索「{q}」失败（{type(e).__name__}），换 key 重试：{str(e)[:60]}")
        tried += 1
        if res is None:
            continue
        for r in res:
            url = (r.get("url") or "").strip()
            title = re.sub(r"\s+", " ", (r.get("title") or "")).strip()
            if not url or url in seen:
                continue
            if len(title) < 8:
                continue
            if not any(k in title for k in HIT):
                continue
            if re.search(BAN_TITLE, title) or re.search(BAN_URL, url):
                continue
            # 拍卖广告 / SEO 科普稿，不算新闻
            if re.search(r"(微拍|第\d+期|拍品|开拍|征集|全解析|一篇看懂|攻略|指南|盘点|排行榜|怎么选|是什么|值多少钱)", title):
                continue
            body_txt = re.sub(r"\s+", " ", (r.get("content") or ""))
            if re.search(BAN_BODY, body_txt[:200]):
                continue
            # 掐掉站点名尾巴（"—普洱茶之家" "·茶友网" 这类导航标题）
            if re.search(r"[—\-－_|｜].*(网|之家|商城|官网|首页|频道)$", title) or title.count("·") >= 2:
                continue
            pd = _norm_date(r.get("published_date"))
            if not pd:
                continue
            try:
                age = (datetime.now() - datetime.strptime(pd, "%Y-%m-%d")).days
                if age < 0 or age > days:
                    continue
            except Exception:
                continue
            seen.add(url)
            # 「像不像真新闻」打分：有事件动词的优先，纯介绍性的排后面
            NEWS_WORDS = ("通报", "查处", "抽查", "不合格", "标准", "签约", "开幕", "启动",
                          "调查", "涨价", "上涨", "下跌", "收购", "产量", "出口", "进口",
                          "非遗", "博物馆", "论坛", "大会", "监管", "案件", "判决", "罚款",
                          "发布", "开幕", "投产", "减产", "干旱", "暴雨", "协会")
            score = 3 if any(w in title for w in NEWS_WORDS) else 1
            items.append({
                "title": title[:120],
                "url": url,
                "date": pd,
                "score": score,
                "snippet": re.sub(r"\s+", " ", body_txt)[:400],
            })

    if not items:
        print("  今天没有新的普洱茶新闻（全部去重后为空）")
        return []

    items.sort(key=lambda x: x["date"], reverse=True)
    print(f"  ✓ 抓到 {len(items)} 条新普洱茶新闻")
    for it in items[:5]:
        print(f"    · {it['date']} {it['title'][:52]}")

    if save:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        day = datetime.now().strftime("%Y-%m-%d")
        fp = OUT_DIR / f"{day}-普洱茶新闻.md"
        lines = [f"# {day} 普洱茶新闻（{len(items)} 条，Tavily 采集）", ""]
        for it in items:
            lines += [f"## {it['title']}", f"- 日期：{it['date']}", f"- 链接：{it['url']}",
                      f"- 摘要：{it['snippet']}", ""]
        fp.write_text("\n".join(lines), encoding="utf-8")
        SEEN.write_text(json.dumps(sorted(seen)[-600:], ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  已写入 {fp}")
    return items


if __name__ == "__main__":
    fetch()
