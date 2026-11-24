# -*- coding: utf-8 -*-
"""每日发文日报（零 LLM）—— 哨兵负责"补"，这个负责"报"

每天固定时间把三篇的核查结果发出来，不论齐不齐，让人一眼看到：
  · 今天应有 3 篇：故事 / 紫砂点评 / 普洱点评
  · 每篇的真实地址、HTTP 状态、页面体积、标题
  · 缺的就标缺，重复页（已改跳转的）不计入

产物：cache/sentinel/report-YYYYMMDD.md；stdout 就是投递出去的正文。
"""
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

REPO = Path(r"C:\afeng_tea")
LOGDIR = REPO / "cache" / "sentinel"
SKIP_FILE = LOGDIR / "redirects.txt"      # 已改成跳转的废页，不计入发文数
SITEMAP = "https://feng-tea.com/sitemap.xml"
HDR = {"User-Agent": "Mozilla/5.0 (afeng-report)"}

COLS = [("故事篇", "07:40"), ("紫砂点评", "04:40"), ("普洱点评", "03:00")]


def get(u, timeout=40):
    req = urllib.request.Request(urllib.parse.quote(u, safe=":/?&=%#"), headers=HDR)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


def skip_set():
    try:
        return {x.strip() for x in SKIP_FILE.read_text(encoding="utf-8").splitlines() if x.strip()}
    except Exception:
        return set()


def main():
    today = f"{datetime.now():%Y%m%d}"
    for i, a in enumerate(sys.argv):
        if a == "--date" and i + 1 < len(sys.argv):
            today = sys.argv[i + 1].strip()

    _, xml = get(SITEMAP)
    locs = re.findall(r"<loc>([^<]+)</loc>", xml.decode("utf-8", "ignore"))
    skip = skip_set()

    found = {"故事篇": [], "紫砂点评": [], "普洱点评": []}
    for u in locs:
        m = re.search(rf"/articles/{today}([^/]*)\.html?$", u)
        if not m:
            continue
        slug = f"{today}{m.group(1)}"
        if slug in skip:
            continue
        name = m.group(1)
        if "紫砂" in name:
            found["紫砂点评"].append(u)
        elif "普洱" in name:
            found["普洱点评"].append(u)
        else:
            found["故事篇"].append(u)

    lines = [f"📊 阿凤姐茶叶站 · {datetime.now():%Y-%m-%d} 发文核查", ""]
    n_ok = 0
    for col, t in COLS:
        urls = found[col]
        if not urls:
            lines.append(f"❌ **{col}**（{t}）：今天线上没有")
            continue
        for u in urls:
            try:
                st, body = get(u)
                h = body.decode("utf-8", "ignore")
                m = re.search(r"<title>(.*?)</title>", h, re.S)
                title = re.sub(r"\s+", " ", m.group(1)).strip()[:46] if m else "—"
                ok = st == 200 and len(body) > 3000
                n_ok += 1 if ok else 0
                lines.append(f"{'✅' if ok else '⚠️'} **{col}**（{t}）：HTTP {st}｜{len(body):,} 字节")
                lines.append(f"　　《{title}》")
                lines.append(f"　　{u}")
            except Exception as e:
                lines.append(f"❌ **{col}**（{t}）：取不到（{type(e).__name__}）")
                lines.append(f"　　{u}")

    lines.append("")
    total = sum(len(v) for v in found.values())
    if total >= 3 and n_ok >= 3:
        lines.append("结论：**三篇齐全，全部正常** ✅")
    elif total >= 3:
        lines.append(f"结论：三篇都在线，其中 {total - n_ok} 篇访问异常，看门狗会跟进")
    else:
        miss = [c for c, _ in COLS if not found[c]]
        lines.append(f"结论：缺 {'、'.join(miss)}；哨兵会在 12:00–14:00 窗口补")

    if skip:
        lines.append(f"（另有 {len(skip)} 个已改跳转的废页不计入）")

    text = "\n".join(lines)
    LOGDIR.mkdir(parents=True, exist_ok=True)
    (LOGDIR / f"report-{today}.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
