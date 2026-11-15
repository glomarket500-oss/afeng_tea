#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
选稿器：找出下一篇待发布的素材草稿
=====================================================
用法:
    python next_draft.py              # 输出下一篇草稿路径（JSON）
    python next_draft.py --list       # 列出全部待发
    python next_draft.py --mark <path># 标记已发布
    python next_draft.py --today-only # 只选今天生成的

规则: 优先当天素材 → 其次积压素材（按日期倒序）; 已标记的跳过
"""
import os
import re
import sys
import json
from pathlib import Path
from datetime import datetime

DRAFTS = Path(r"C:\Users\a\Desktop\MianAI知识库\MianAI知识库\vault\资料库\素材材料\茶叶素材")
REPO = Path(r"C:\afeng_tea")
STATE = REPO / ".published_drafts.json"


def load_state():
    if STATE.exists():
        try:
            d = json.loads(STATE.read_text(encoding="utf-8"))
            return d if isinstance(d, dict) else {}
        except Exception:
            return {}
    return {}


def save_state(st):
    STATE.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")


def draft_date(p):
    m = re.match(r"(\d{4}-\d{2}-\d{2})", p.name)
    return m.group(1) if m else "0000-00-00"


def draft_title(p):
    try:
        for line in p.read_text(encoding="utf-8", errors="replace").split("\n"):
            s = line.strip()
            if not s or s in ("---",) or s.startswith(">"):
                continue
            t = s.lstrip("#").strip()
            t = re.sub(r"^[^\w\u4e00-\u9fa5]+", "", t).strip()
            if len(t) > 3:
                return t
    except Exception:
        pass
    return p.stem


def is_published(p, st):
    if p.name in st:
        return True
    # 兜底：仓库里已有标题高度相似的页面
    title = re.sub(r"[^\u4e00-\u9fa5A-Za-z0-9]", "", draft_title(p))[:12]
    if not title:
        return False
    for f in REPO.glob("articles/*.html"):
        stem = re.sub(r"[^\u4e00-\u9fa5A-Za-z0-9]", "", f.stem)
        if title and title in stem:
            return True
    return False


def candidates(today_only=False):
    st = load_state()
    today = datetime.now().strftime("%Y-%m-%d")
    out = []
    for p in sorted(DRAFTS.glob("*.md")):
        d = draft_date(p)
        if today_only and d != today:
            continue
        if is_published(p, st):
            continue
        # 结构门槛
        raw = p.read_text(encoding="utf-8", errors="replace")
        if len(raw) < 600:
            continue
        out.append({
            "path": str(p),
            "name": p.name,
            "date": d,
            "size": len(raw),
            "title": draft_title(p),
        })
    # 当天优先，其次日期倒序
    out.sort(key=lambda x: (x["date"] != today, x["date"]), reverse=False)
    out.sort(key=lambda x: (0 if x["date"] == today else 1, x["date"]), reverse=False)
    return out


def main():
    args = sys.argv[1:]
    if not DRAFTS.exists():
        print(json.dumps({"error": f"素材目录不存在: {DRAFTS}"}, ensure_ascii=False))
        sys.exit(1)

    if "--mark" in args:
        i = args.index("--mark")
        path = Path(args[i + 1])
        st = load_state()
        st[path.name] = {
            "marked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "title": draft_title(path),
        }
        save_state(st)
        print(json.dumps({"marked": path.name, "total": len(st)}, ensure_ascii=False))
        return

    lst = candidates(today_only="--today-only" in args)

    if "--list" in args:
        print(json.dumps(lst, ensure_ascii=False, indent=2))
        return

    if not lst:
        print(json.dumps({"done": True, "message": "没有待发布的新素材"}, ensure_ascii=False))
        return

    print(json.dumps(lst[0], ensure_ascii=False))


if __name__ == "__main__":
    main()
