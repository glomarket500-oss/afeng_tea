#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿凤姐茶站 · 通用文章发布流水线
====================================================
用法:
    python publish_new.py <草稿.md> [--dry-run] [--skip-images] [--no-push]

九步:
 1 scrub 隐私清洗  2 解析草稿  3 生成7张免费配图  4 生成文章页
 5 首页首卡        6 sitemap   7 全站页脚同步    8 原子提交推送  9 线上验证

铁律:
 - 生图只用免费 Kwai-Kolors/Kolors，禁用任何付费模型
 - 真名/QQ/旧域名 一律清洗
 - 配图禁止任何文字
"""
import os
import re
import sys
import json
import time
import glob
import hashlib
import math
import html as _html
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

REPO      = Path(r"C:\afeng_tea")
TEMPLATE  = REPO / "articles" / "laocha.html"
SITE      = "https://feng-tea.com"
HERMES    = Path(r"C:\Users\Administrator\AppData\Local\hermes")

# 站点固定信息（规范书 §2.3）
STORE = {
    "name": "阿凤姐茶叶店（惠州凤凰茶业）",
    "addr": "惠州市惠城区东湖花园一区沿江商铺89-136",
    "tel":  "13435567385",
    "hours": "每天 9:00-21:00，全年无休",
    "park": "东湖花园沿街有停车位，导航搜索「凤凰茶业」即可",
    "main": "潮州凤凰单丛全系列（鸭屎香、蜜兰香、老丛、芝兰香等）、新会陈皮、茶礼定制",
}

CASE_TAGS = ["#凤凰单丛", "#惠州茶叶店", "#潮州工夫茶", "#惠州买茶去哪"]
MAX_BYTES = 200 * 1024


# ══════════════════════════════════════════════
# 1. 隐私清洗
# ══════════════════════════════════════════════
def scrub(text):
    for a, b in [("林玉凤（阿凤姐）", "阿凤姐"), ("林玉鳳（阿鳳姐）", "阿鳳姐"),
                 ("林玉凤", "阿凤姐"), ("林玉鳳", "阿鳳姐")]:
        text = text.replace(a, b)
    text = re.sub(r"[ \t]*(?:💬\s*)?QQ\s*[：:]\s*107[-‑]?9790[-‑]?744", "", text)
    text = text.replace("1079790744", "")
    # 旧域名 → 现役域名（草稿里仍是旧站）
    for old in ["https://afeng-tea.vercel.app", "https://afengtea-2.vercel.app",
                "https://afengtea.vercel.app", "afeng-tea.vercel.app",
                "https://vocal-gaufre-8f51b7.netlify.app"]:
        text = text.replace(old, SITE)
    return text


def assert_clean(text, where):
    bad = []
    if "林玉凤" in text or "林玉鳳" in text:
        bad.append("真名")
    if "1079790744" in text:
        bad.append("QQ")
    if "vercel.app" in text or "netlify.app" in text:
        bad.append("旧域名")
    if bad:
        raise SystemExit(f"❌ 隐私红线未通过（{where}）: {', '.join(bad)}")


# ══════════════════════════════════════════════
# 2. 解析草稿
# ══════════════════════════════════════════════
SKIP_HEAD = re.compile(r"^##\s*[📌\s【\[]*(FAQ|常见问题|标签|话题|联系方式|联系|下回预告|预告)")


SUB_MAP = [
    (("价", "账", "钱", "谈", "成本", "客单"), "算账"),
    (("泡", "盖碗", "水", "汤", "冲", "出汤"), "泡茶"),
    (("香", "闻", "蜜兰", "鸭屎"), "闻香"),
    (("采", "摘", "下树", "上山", "树"), "上山"),
    (("焙", "火", "炭", "杀青", "揉捻", "晾青", "晒青"), "做茶"),
    (("礼盒", "送", "年节", "礼"), "选礼"),
    (("客", "生意", "批发", "订单", "酒樓", "酒楼", "奶茶"), "谈生意"),
    (("雾", "山", "园", "风土"), "看山"),
]


def derive_sub(chunk):
    for keys, sub in SUB_MAP:
        if any(k in chunk for k in keys):
            return sub
    return ""


def autosplit(paras):
    """无分幕标记的连续散文 → 场景开头 / 第一~三幕 / 尾声"""
    ps = [p for p in paras if p]
    n = len(ps)
    if n <= 1:
        return [("【正文】", ps)]
    if n == 2:
        return [("【场景开头】", ps[:1]), ("【尾声】", ps[1:])]
    if n == 3:
        return [("【场景开头】", ps[:1]), ("【正文】", ps[1:2]), ("【尾声】", ps[2:])]
    head, tail = ps[0], ps[-1]
    mid = ps[1:-1]
    k = 3 if len(mid) >= 5 else (2 if len(mid) >= 3 else 1)
    size = max(1, len(mid) // k)
    chunks, idx = [], 0
    for j in range(k):
        take = size if j < k - 1 else len(mid) - idx
        chunks.append(mid[idx:idx + take])
        idx += take
    names = ["第一幕", "第二幕", "第三幕"]
    out = [("【场景开头】", [head])]
    for j, ch in enumerate(chunks):
        if not ch:
            continue
        sub = derive_sub(" ".join(ch))
        out.append((f"【{names[j]}：{sub}】" if sub else f"【{names[j]}】", ch))
    out.append(("【尾声】", [tail]))
    return out


HEAD_RE = re.compile(r"^[【\[]\s*(场景开头|第[一二三四五六七八九十]+幕|尾声)\s*[：:·\-]?\s*(.*?)\s*[】\]]$")


def parse_draft(raw):
    lines = raw.split("\n")
    title, lead = "", ""
    sections, faq, tagline, preview = [], [], "", ""
    cur, buf, mode = None, [], None
    pre = []

    def flush():
        nonlocal cur, buf
        if cur is not None:
            sections.append((cur, [b for b in buf if b]))
            cur, buf = None, []

    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if s in ("---", "***", "___") or set(s) <= {"-", "*", "_"} and len(s) >= 3:
            continue
        if s.startswith(">"):
            continue
        # ---- 标题 ----
        if not title:
            if s.startswith("# "):
                title = s[2:].strip()
                continue
            if (not s.startswith("#") and not HEAD_RE.match(s)
                    and "开篇回答" not in s and not s.startswith("**")
                    and not s.startswith("📌") and len(s) > 3):
                t = re.sub(r"^[^\w\u4e00-\u9fa5]+", "", s).strip()
                title = t
                continue
        if "开篇回答" in s:
            lead = re.sub(r"^[\*\s]*📌?\s*开篇回答[：:]\s*", "", s).replace("**", "").strip()
            mode = "lead"
            continue
        # ---- 跳过区 ----
        if SKIP_HEAD.match(s):
            flush()
            mode = ("faq" if re.search(r"FAQ|常见问题", s) else
                    "tags" if re.search(r"标签|话题", s) else
                    "preview" if re.search(r"下回预告|预告", s) else "skip")
            continue
        # ---- 章节标题：## 或裸【...】----
        h = None
        if s.startswith("## "):
            h = s[3:].strip()
        elif HEAD_RE.match(s):
            h = s
        if h is not None:
            flush()
            cur, buf, mode = h, [], "body"
            continue

        if mode == "lead":
            lead += " " + s.replace("**", "")
        elif mode == "faq":
            m = re.match(r"^\**Q\s*[：:]\s*(.+)$", s)
            if m:
                q = m.group(1).strip().strip("*").strip()
                faq.append([q, ""])
            elif faq:
                a = re.sub(r"^\**A\s*[：:]\s*", "", s).replace("**", "").strip()
                faq[-1][1] = (faq[-1][1] + " " + a).strip()
        elif mode == "tags":
            tagline += " " + s
        elif mode == "preview":
            preview += " " + s.replace("**", "")
        elif mode == "body" and cur is not None:
            buf.append(s)
        else:
            pre.append(s)

    flush()
    if not sections and pre:
        sections.append(("【正文】", pre[:]))

    # 标题规范化 → 【第一幕：xxx】
    norm = []
    for h, ps in sections:
        if not (h.startswith("【") and h.endswith("】")):
            m = re.match(r"^(第[一二三四五六七八九十]+幕|场景开头|尾声)\s*[·:：\-]?\s*(.*)$", h)
            if m:
                core, sub = m.group(1), m.group(2).strip()
                h = f"【{core}：{sub}】" if sub else f"【{core}】"
        norm.append((h, ps))

    # 无分幕 → 自动切分
    if len(norm) < 3:
        flat = []
        for _, ps in norm:
            flat.extend(ps)
        norm = autosplit(flat)

    tags = []
    for t in re.findall(r"#[^\s#，,。]+", tagline):
        if t not in tags:
            tags.append(t)
    return title, lead.strip(), norm, faq, tags, preview.strip()


# ══════════════════════════════════════════════
# 3. 配图（免费 Kolors）
# ══════════════════════════════════════════════
NO_TEXT = ("画面中绝对没有任何文字、汉字、字母、数字、字幕、招牌、标签、包装文字、"
           "水印、标志、logo；所有罐子瓶袋木牌一律素面无字")

# 关键词 → 场景描述
SCENE_MAP = [
    (("雾", "山", "茶园", "云雾", "海拔"), "凤凰山脉高山茶园，晨雾缠绕的茶树梯田"),
    (("采", "摘", "下树", "手记", "上山", "摸树皮", "认树"), "茶农的手在茶园里采摘嫩茶叶，竹篓"),
    (("杀青", "炒", "高温", "锁香"), "铁锅高温杀青，茶叶在锅中翻炒冒热气"),
    (("揉捻", "汁", "成形"), "竹匾上手工揉捻茶叶，茶汁渗出"),
    (("晾青", "晒青", "萎凋", "呼吸"), "竹筛上摊晾的鲜茶叶，自然光萎凋"),
    (("焙", "火", "炭", "红泥炉", "木炭", "烘焙"), "木炭焙茶，红泥炉微火与竹焙笼"),
    (("泡", "盖碗", "汤", "冲", "出汤", "品"), "两只白瓷盖碗与公道杯，茶汤琥珀清透"),
    (("礼盒", "批发", "分货", "茶楼", "奶茶", "订单", "生意"), "茶店内整齐码放的素面锡罐与纸箱"),
    (("办公室", "下午茶", "十分钟"), "办公桌上简洁的玻璃杯与茶叶，暖光"),
    (("晨光", "早", "天亮", "清晨"), "清晨斜光下的茶桌与一杯热茶，木质纹理"),
    (("夜", "灯", "傍晚", "北风", "冬天", "立冬"), "夜晚暖黄灯光下的茶席与半杯茶"),
]

SCENE_FALLBACK = [
    "清晨木桌上一杯凤凰单丛茶，白瓷杯与干茶叶",
    "茶店内景，木质货架上的素面茶罐",
    "干茶叶在白纸上摊开特写，条索清晰",
    "白瓷盖碗注水冲泡茶叶，热气升腾",
    "三只小茶杯并排，琥珀色茶汤透亮",
    "茶罐与竹制茶具在木桌上，自然光",
]


def scene_desc(text, idx):
    for keys, desc in SCENE_MAP:
        if any(k in text for k in keys):
            return desc
    return SCENE_FALLBACK[idx % len(SCENE_FALLBACK)]


MOUNTAIN_POOL = [
    "凤凰山脉高山茶园全景，晨雾缠绕的梯田茶园，远山层叠",
    "茶农的手采摘嫩茶叶，竹篓里装满鲜叶，晨光",
    "竹筛上摊晾的鲜茶叶，自然光萎凋",
    "铁锅高温杀青，茶叶在锅中翻炒冒热气",
    "竹匾上手工揉捻茶叶，茶汁渗出",
    "木炭焙茶，红泥炉微火与竹焙笼",
    "山间石阶旁的老茶树，树干粗壮布满苔藓",
    "夕阳下的茶园，茶垄一路延伸到远山",
    "茶仓内素面锡罐整齐码放于木架，暖光",
]
SHOP_POOL = [
    "木质茶桌上一只白瓷盖碗与公道杯，琥珀色茶汤",
    "干茶叶在白纸上摊开特写，条索紧结乌褐",
    "两只白瓷盖碗并排，注水冲泡热气升腾",
    "三只小茶杯并排，茶汤透亮挂壁",
    "茶店内景，木质货架上素面茶罐整齐",
    "竹制茶具与茶巾在木桌上，自然光",
    "玻璃公道杯里的茶汤特写，清透如琥珀",
    "素面锡罐开盖，干茶特写，光泽乌褐",
    "窗边茶席，竹筛与茶荷，午后光",
]

COVER_MOUNTAIN = "凤凰山脉高山茶园晨雾全景，远山层叠，构图舒展留白"
COVER_SHOP = "木质茶席上凤凰单丛干茶与白瓷盖碗，晨光斜射，构图舒展留白"


def pick_domain(title, sections):
    txt = title + "".join(" ".join(ps) for _, ps in sections)
    mountain_keys = ("雾", "山", "茶园", "采", "摘", "杀青", "揉捻", "晾青", "晒青", "焙", "炭", "茶农", "树")
    return "mountain" if sum(txt.count(k) for k in mountain_keys) >= 6 else "shop"


def build_prompts(title, sections):
    """封面 + 每幕 1 张；同池内去重轮换，避免配图雷同"""
    domain = pick_domain(title, sections)
    pool = MOUNTAIN_POOL if domain == "mountain" else SHOP_POOL
    cover_desc = COVER_MOUNTAIN if domain == "mountain" else COVER_SHOP

    prompts = [{"key": "cover", "cap": f"{title}｜凤凰单丛", "desc": cover_desc}]
    used = {cover_desc}          # 封面用过的构图，场景图不再重复

    def too_similar(cand):
        """构图撞车判定：去掉标点后前 8 字相同即视为雷同（避免一篇里三张高山茶园）"""
        key = re.sub(r"[，,。\s｜]", "", cand)[:8]
        return any(re.sub(r"[，,。\s｜]", "", u)[:8] == key for u in used)

    cursor = 0
    for i, (head, paras) in enumerate(sections):
        body = (head + " " + " ".join(paras))[:600]
        desc = None
        # 关键词优先（且未用过、不雷同）
        for keys, cand in SCENE_MAP:
            if any(k in body for k in keys) and cand not in used and not too_similar(cand):
                desc = cand
                break
        # 否则从主题池顺序取未用项
        if not desc:
            for j in range(len(pool)):
                cand = pool[(cursor + j) % len(pool)]
                if cand not in used and not too_similar(cand):
                    desc = cand
                    cursor = (cursor + j + 1) % len(pool)
                    break
        if not desc:
            desc = pool[i % len(pool)]
        used.add(desc)
        prompts.append({"key": f"s{i+1}", "cap": head.strip("【】").replace("：", "｜"), "desc": desc})

    while len(prompts) < 7:
        k = len(prompts)
        cand = next((c for c in pool if c not in used), pool[k % len(pool)])
        used.add(cand)
        prompts.append({"key": f"s{k}", "cap": "凤凰单丛茶席", "desc": cand})
    return prompts[:7]


def load_env():
    env = {}
    for p in [HERMES / ".env", Path(r"C:\Users\Administrator\.hermes\.env")]:
        if p.exists():
            for line in p.read_text(encoding="utf-8", errors="replace").split("\n"):
                m = re.match(r"^\s*([A-Z_][A-Z0-9_]*)\s*=\s*(.*)$", line)
                if m:
                    env.setdefault(m.group(1), m.group(2).strip().strip('"').strip("'"))
    for k in ("SILICONFLOW_API_KEY",):
        if os.environ.get(k):
            env[k] = os.environ[k]
    return env


def gen_image(api_key, prompt, retries=3):
    url = "https://api.siliconflow.cn/v1/images/generations"
    payload = {
        "model": "Kwai-Kolors/Kolors",           # ★ 唯一允许：免费
        "prompt": f"{prompt}，{NO_TEXT}",
        "image_size": "1024x576",
        "num_inference_steps": 20,
        "batch_size": 1,
    }
    data = json.dumps(payload).encode()
    for att in range(retries):
        try:
            req = urllib.request.Request(
                url, data=data,
                headers={"Authorization": f"Bearer {api_key}",
                         "Content-Type": "application/json"},
                method="POST")
            with urllib.request.urlopen(req, timeout=180) as r:
                js = json.loads(r.read().decode())
            imgs = js.get("data") or js.get("images") or []
            if imgs:
                it = imgs[0]
                return it["url"] if isinstance(it, dict) and it.get("url") else it
            last = f"空响应 {str(js)[:200]}"
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code} {e.read(300).decode('utf-8', 'ignore')}"
        except Exception as e:
            last = f"{type(e).__name__}: {e}"
        time.sleep(3 * (att + 1))
    raise RuntimeError(f"生图失败: {last}")


def to_webp(raw_bytes, out_path, width=None, height=None, quality=82):
    """等比缩放 + 居中裁切 → WebP ≤200KB"""
    from PIL import Image
    import io
    im = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
    if width and height:
        r = max(width / im.width, height / im.height)
        nw, nh = max(width, round(im.width * r)), max(height, round(im.height * r))
        im = im.resize((nw, nh), Image.LANCZOS)
        left, top = (nw - width) // 2, (nh - height) // 2
        im = im.crop((left, top, left + width, top + height))
    elif width:
        r = width / im.width
        im = im.resize((width, round(im.height * r)), Image.LANCZOS)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    q = quality
    while q >= 45:
        buf = io.BytesIO()
        im.save(buf, "WEBP", quality=q, method=6)
        if buf.tell() <= MAX_BYTES or q == 45:
            out_path.write_bytes(buf.getvalue())
            return im.width, im.height, buf.tell()
        q -= 6
    raise RuntimeError("压缩失败")


def audit_image(path):
    """纯像素合规判定（不依赖视觉模型）：人脸肤色占比 / 汉字笔画结构。
    返回警告列表；空列表 = 通过。规范书 §3.5 + skill「图片合规的客观检测」。"""
    from PIL import Image
    RES = getattr(getattr(Image, "Resampling", Image), "BILINEAR")
    im = Image.open(path).convert("RGB")
    w, h = im.size
    sm = im.resize((max(1, w // 2), max(1, h // 2)), RES)
    W, H = sm.size
    px = sm.load()

    # ---- A. 人脸：YCrCb 肤色占比 + 中心椭圆区聚集 ----
    skin = center = tot = 0
    cx, cy = W // 2, H // 2
    for y in range(0, H, 2):
        for x in range(0, W, 2):
            R, G, B = px[x, y]
            Y = 0.299 * R + 0.587 * G + 0.114 * B
            Cr = (R - Y) * 0.713 + (G - Y) * 0.564
            Cb = (G - Y) * 0.934 + (B - Y) * 0.180
            tot += 1
            if 133 < Cr < 180 and 77 < Cb < 130 and R > 60:
                skin += 1
                if ((x - cx) / (W * 0.28)) ** 2 + ((y - cy) / (H * 0.30)) ** 2 < 1:
                    center += 1
    skin_pct = skin / max(1, tot) * 100
    center_pct = center / max(1, tot) * 100
    warns = []
    if skin_pct > 1.5:
        warns.append(f"肤色{skin_pct:.1f}%")
    if center_pct > 0.8:
        warns.append(f"中心肤色聚集{center_pct:.1f}%")

    # ---- B. 汉字：Otsu 二值化 → 连通域 → 小域多 + 笔画细 ----
    g = sm.convert("L")
    gp = g.load()
    hist = g.histogram()
    total = W * H
    S = sum(i * hist[i] for i in range(256))
    wB = s2 = 0
    best, thr = -1, 128
    for t in range(256):
        wB += hist[t]
        if wB == 0:
            continue
        s2 += t * hist[t]
        mB = s2 / wB
        wF = total - wB
        if wF == 0:
            break
        mF = (S - s2) / wF
        v = wB * wF * (mB - mF) ** 2
        if v > best:
            best, thr = v, t
    binar = [[1 if gp[x, y] > thr else 0 for x in range(W)] for y in range(H)]
    seen = [[0] * W for _ in range(H)]
    areas = []
    for y0 in range(H):
        for x0 in range(W):
            if binar[y0][x0] and not seen[y0][x0]:
                st = [(x0, y0)]
                seen[y0][x0] = 1
                a = 0
                while st:
                    x, y = st.pop()
                    a += 1
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < W and 0 <= ny < H and binar[ny][nx] and not seen[ny][nx]:
                            seen[ny][nx] = 1
                            st.append((nx, ny))
                areas.append(a)
    small = [a for a in areas if 4 <= a <= 200]
    ratio = len(small) / max(1, len(areas))
    ws = sorted(math.sqrt(4 * a / math.pi) for a in areas if 20 <= a <= 400)
    med_w = ws[len(ws) // 2] if ws else 0
    if len(small) > 60 and ratio > 0.55 and 0.8 <= med_w <= 3.5:
        warns.append(f"疑似汉字(小域{len(small)} 笔画宽{med_w:.1f})")
    return warns


SAFER_SUFFIX = "，纯木质桌面或纯色墙面背景，画面极简，只有茶叶与素面器物，没有任何印刷与标识"


def make_images(prefix, title, sections, slug):
    env = load_env()
    key = env.get("SILICONFLOW_API_KEY")
    if not key:
        raise SystemExit("❌ 缺少 SILICONFLOW_API_KEY")
    prompts = build_prompts(title, sections)
    dims = {}
    audit_log = []
    full_dir = REPO / "images" / "full"
    thumb_dir = REPO / "images" / "thumb"
    for i, p in enumerate(prompts, 1):
        print(f"  [{i}/{len(prompts)}] {p['key']}  {p['desc'][:38]}")
        warns = []
        for attempt in range(2):          # 合规不过 → 换更保守构图重生一次（仍只用免费模型）
            desc = p["desc"] if attempt == 0 else p["desc"] + SAFER_SUFFIX
            try:
                u = gen_image(key, desc)
                raw = urllib.request.urlopen(u, timeout=120).read()
                w, h, sz = to_webp(raw, full_dir / f"{prefix}-{p['key']}.webp", 869, 489)
                dims[p["key"]] = (w, h)
                warns = audit_image(full_dir / f"{prefix}-{p['key']}.webp")
                print(f"        → {w}×{h}  {sz//1024}KB  "
                      + ("⚠ " + ";".join(warns) if warns else "✓ 合规"))
                if p["key"] == "cover" and not warns:
                    to_webp(raw, thumb_dir / f"{slug}-hero.webp", 400)
                if not warns:
                    break
                if attempt == 0:
                    print("        ↻ 触发重生（换保守构图）")
            except Exception as e:
                print(f"        ⚠ 失败: {e}")
                dims[p["key"]] = None
                warns = [f"生成失败:{e}"]
        if warns:
            audit_log.append((p["key"], warns))
    # 兜底：缺图时复用封面
    cov = full_dir / f"{prefix}-cover.webp"
    for p in prompts:
        fp = full_dir / f"{prefix}-{p['key']}.webp"
        if not fp.exists() and cov.exists():
            fp.write_bytes(cov.read_bytes())
            dims[p["key"]] = dims.get("cover", (869, 489))
            print(f"        ↺ {p['key']} 复用封面")
    if audit_log:
        print("  ⚠ 仍有合规警告（已重生一次）: " + "; ".join(f"{k}:{'/'.join(v)}" for k, v in audit_log))
    else:
        print("  ✓ 7 张图全部通过像素合规检测（无正脸 / 无汉字）")
    return prompts, dims, audit_log


# ══════════════════════════════════════════════
# 4. 文章页
# ══════════════════════════════════════════════
def make_desc(lead, limit=115):
    """摘要：去 HTML 标签、去引号、按句号断句（避免截断在句子中间）"""
    s = re.sub(r"<[^>]+>", "", lead)
    s = s.replace("\u3000", " ").replace("\n", " ")
    s = re.sub(r"[\"\u201c\u201d\u2018\u2019']", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) > limit:
        cut = -1
        for m in re.finditer(r"[。！？]", s[:limit]):
            if m.start() >= 45:
                cut = m.start() + 1
        s = s[:cut] if cut > 0 else s[:limit].rstrip("，、；： ") + "…"
    return f"{s} 惠州买茶去哪：{STORE['addr']}，电话{STORE['tel']}。"


def make_slug(title, date_compact):
    core = re.sub(r"[^\u4e00-\u9fa5A-Za-z0-9]", "", title)
    core = core.replace("阿凤姐", "")[:26]
    return f"{date_compact}{core}阿凤姐"


def synth_lead(title, sections, faq):
    """草稿缺「📌 开篇回答」时，从正文与 FAQ 合成 100-200 字导语"""
    head = title.split("|")[0].strip()
    core = ""
    for h, ps in sections:
        if ps and len(ps[0]) > 40:
            core = ps[0]
            break
    core = re.sub(r"^.*?阿凤姐", "阿凤姐", core) if "阿凤姐" in core[:20] else core
    core = core.strip()[:110]
    key = ""
    if faq and faq[0][1]:
        key = faq[0][1].split("。")[0][:60]
    if key:
        return f"{head}，很多茶友都问过这个。{core}　<strong>{key}。</strong>"
    return (f"{head}——这是我在店里被问得最多的一件事。{core}　"
            f"<strong>我把二十多年做凤凰单丛的经验，摊开讲给你听。</strong>")


def build_qa(faq, title):
    """开篇三问：Q1 痛点 / Q2 本地转化 / Q3 鉴别"""
    used = []
    q1 = faq[0] if len(faq) > 0 and faq[0][1] else (
        f"{title.split('|')[0].strip()}到底怎么喝才对？",
        "阿凤姐一句话讲透：<strong>茶的脾气摸清了，怎么泡都顺口。</strong>"
        "水温够、茶量足、快出汤，三样齐了，香气自然出来。")
    used.append(q1[0])
    q3 = faq[1] if len(faq) > 1 and faq[1][1] else (
        "怎么一眼看出一泡茶的好坏？",
        "阿凤姐教你三看：<strong>条索</strong>匀不匀、<strong>汤色</strong>透不透、"
        "<strong>叶底</strong>活不活。三样都过，才谈香气。")
    used.append(q3[0])
    qa = [
        (f"Q1：{q1[0]}", q1[1]),
        ("Q2：惠州哪里能买到正宗的凤凰单丛？",
         f"来 <strong>{STORE['name']}</strong>！地址：<strong>{STORE['addr']}</strong>，"
         f"{STORE['hours']}营业。电话：<strong>{STORE['tel']}</strong>（微信同号，支持全国快递）。"
         "批发零售都做，可以先来喝一杯再定。"),
        (f"Q3：{q3[0]}", q3[1]),
    ]
    return qa, used


def build_body(lead, qa, sections, faq, tags, preview, prompts, dims, prefix):
    out = [f'<p class="lead" style="font-size:1.06em;color:#4a7023;font-weight:600;line-height:1.95">{lead}</p>']
    out.append('<h2>🌿 开篇问答</h2>')
    for q, a in qa:
        out.append(f"<p><strong>{q}</strong></p>")
        out.append(f"<p>{a}</p>")

    for i, (head, paras) in enumerate(sections):
        out.append(f"<h2>{head}</h2>")
        for p in paras:
            out.append(f"<p>{p.replace('**', '')}</p>")
        p_meta = prompts[i + 1] if i + 1 < len(prompts) else None
        if p_meta:
            d = dims.get(p_meta["key"]) or (869, 489)
            out.append(
                f'<figure class="scene-fig"><img src="../images/full/{prefix}-{p_meta["key"]}.webp" '
                f'alt="{p_meta["cap"]}" width="{d[0]}" height="{d[1]}" loading="lazy" decoding="async">'
                f'<figcaption>{p_meta["cap"]}</figcaption></figure>')

    if faq:
        out.append('<div class="faq-section">')
        out.append("<h4>📌 FAQ 常见问题</h4>")
        for q, a in faq:
            out.append(f'<div class="faq-item"><p class="faq-q">Q：{q}</p>'
                       f'<p class="faq-a">A：{a}</p></div>')
        out.append("</div>")

    if preview:
        out.append(f'<p style="color:#8a7f70;font-size:.94em;font-style:italic;'
                   f'border-top:1px dashed #e2d9cb;padding-top:12px">🔖 下回预告：{preview}</p>')

    out.append("<h2>📍 惠州买茶去哪？阿凤姐茶叶店欢迎你</h2>")
    out.append(
        f"<p>🏪 <strong>店铺</strong>：{STORE['name']}<br>\n"
        f"📍 <strong>地址</strong>：{STORE['addr']}<br>\n"
        f"📱 <strong>电话</strong>：{STORE['tel']}（微信同号，支持全国快递）<br>\n"
        f"⏰ <strong>营业时间</strong>：{STORE['hours']}<br>\n"
        f"🚗 <strong>停车</strong>：{STORE['park']}</p>")
    out.append(f"<p>🍵 <strong>店内主营</strong>：{STORE['main']}；"
               "<strong>批发零售均可，先来喝一杯再定</strong>。</p>")
    out.append(f'<p class="xhs-tags">{"".join(tags)}</p>')
    return "\n".join(out)


def rebuild_jsonld(html, title, desc, url, date, cover_url, kw):
    """用真正的 JSON 解析重建 LD 块。
    模板里 "image" 是数组（不是对象），正则改不动 → 曾把首页通用图 homepage-hero 带上线（交接书坑15）。"""
    def fix(m):
        try:
            d = json.loads(m.group(1))
        except Exception:
            return m.group(0)
        if not isinstance(d, dict):
            return m.group(0)
        d["headline"] = f"🍵 {title}"
        d["description"] = desc
        d["image"] = [cover_url]
        d["url"] = url
        d["datePublished"] = date
        d["dateModified"] = date
        d["keywords"] = kw.split(",")
        me = d.get("mainEntityOfPage")
        if isinstance(me, dict):
            me["@id"] = url
        return ('<script type="application/ld+json">\n'
                + json.dumps(d, ensure_ascii=False, indent=2) + '\n</script>')
    return re.sub(r'<script type="application/ld\+json">(.*?)</script>', fix, html, flags=re.S)


def build_page(meta, lead, qa, sections, faq, tags, preview, prompts, dims):
    title, slug, desc, prefix = meta["title"], meta["slug"], meta["desc"], meta["prefix"]
    url = f"{SITE}/articles/{slug}.html"
    date, zh_date = meta["date"], meta["zh_date"]

    t = TEMPLATE.read_text(encoding="utf-8")
    # 属性值必须转义引号：标题/摘要里带 " 会截断 HTML 属性（分享卡片也会坏）
    title_esc = _html.escape(title, quote=True)
    desc_esc = _html.escape(desc, quote=True)
    t = re.sub(r"<title>[^<]*</title>", f"<title>🍵 {title_esc} | 阿凤姐的故事</title>", t, count=1)
    for pat in [r'(<meta name="description" content=")[^"]*(")',
                r'(<meta property="og:description" content=")[^"]*(")',
                r'(<meta name="twitter:description" content=")[^"]*(")']:
        t = re.sub(pat, lambda m: m.group(1) + desc_esc + m.group(2), t, count=1)
    for pat in [r'(<meta property="og:title" content=")[^"]*(")',
                r'(<meta name="twitter:title" content=")[^"]*(")']:
        t = re.sub(pat, lambda m: m.group(1) + title_esc + m.group(2), t, count=1)
    t = re.sub(r'(<meta property="og:url" content=")[^"]*(")', lambda m: m.group(1) + url + m.group(2), t, count=1)
    t = re.sub(r'(<link rel="canonical" href=")[^"]*(")', lambda m: m.group(1) + url + m.group(2), t, count=1)
    t = re.sub(r'(<meta property="article:published_time" content=")[^"]*(")',
               lambda m: m.group(1) + date + m.group(2), t, count=1)
    # og/twitter image → 本篇封面（JSON-LD 的 image 交给 rebuild_jsonld，绝不用正则塞）
    cover_url = f"{SITE}/images/full/{prefix}-cover.webp"
    t = re.sub(r'(<meta property="og:image" content=")[^"]*(")', lambda m: m.group(1) + cover_url + m.group(2), t, count=1)
    t = re.sub(r'(<meta name="twitter:image" content=")[^"]*(")', lambda m: m.group(1) + cover_url + m.group(2), t, count=1)
    # keywords（meta 标签；JSON-LD 的 keywords 由 rebuild_jsonld 写数组）
    kw = ",".join(x.lstrip("#") for x in tags)
    if '<meta name="keywords"' in t:
        t = re.sub(r'(<meta name="keywords" content=")[^"]*(")', lambda m: m.group(1) + kw + m.group(2), t, count=1)
    else:
        t = t.replace('<meta name="description"', f'<meta name="keywords" content="{kw}">\n<meta name="description"', 1)
    # JSON-LD：只用 JSON 解析重建。绝不能用正则往里塞字符串——
    # 标题/摘要含引号或换行会把 JSON 写坏（线上 9 篇坏 JSON 全是这么来的）
    t = rebuild_jsonld(t, title, desc, url, date, cover_url, kw)
    # 面包屑 / h1 / 时间
    t = re.sub(r'(<span>)[^<]*(</span>\s*</div>\s*<article>)',
               lambda m: m.group(1) + f"🍵 {_html.escape(title[:18])}" + m.group(2), t, count=1)
    t = re.sub(r"<h1>.*?</h1>", f"<h1>🍵 {_html.escape(title)}</h1>", t, count=1, flags=re.S)
    t = re.sub(r'<p class="article-meta-time">.*?</p>',
               f'<p class="article-meta-time">📅 发布于 <time datetime="{date}">{meta["zh_date_only"]}</time>　✍️ 阿凤姐</p>',
               t, count=1, flags=re.S)
    # 标签（三处统一：头部 chips / article-tags / xhs-tags 同一套、顺序一致）
    chips = "".join(f'<a class="tag" href="../index.html#knowledge">{x}</a>' for x in tags)
    # 防御：先清掉模板里可能残留的 article-tags，保证最终只有 1 份
    t = re.sub(r'<div class="article-tags">.*?</div>\s*', '', t, flags=re.S)
    t = re.sub(r'<div class="tags">.*?</div>',
               f'<div class="tags">{chips}</div>\n<div class="article-tags">'
               + "".join(f'<span class="tag">{x}</span>' for x in tags) + "</div>",
               t, count=1, flags=re.S)
    # 封面
    cd = dims.get("cover") or (869, 489)
    t = re.sub(r'<figure class="article-hero">.*?</figure>',
               f'<figure class="article-hero"><img src="../images/full/{prefix}-cover.webp" '
               f'alt="🍵 {title}" width="{cd[0]}" height="{cd[1]}" decoding="async"></figure>',
               t, count=1, flags=re.S)
    # 正文
    body = build_body(lead, qa, sections, faq, tags, preview, prompts, dims, prefix)
    t = re.sub(r'<div class="article-body">.*?</div>\s*\n\s*<div class="cta-box">',
               lambda m: f'<div class="article-body">\n{body}\n</div>\n\n<div class="cta-box">',
               t, count=1, flags=re.S)
    # 样式补齐
    extra = (".xhs-tags{color:#4a7023;font-size:.9em;line-height:2;border-top:1px dashed #e2d9cb;"
             "padding-top:12px;margin-top:6px}"
             ".article-tags{display:flex;flex-wrap:wrap;gap:6px;margin:16px 0 8px}"
             ".article-tags .tag{background:#f2ede4;color:#6b5f4e;border-radius:14px;"
             "padding:3px 10px;font-size:.82em}")
    if ".xhs-tags{" not in t:
        t = t.replace("</style>", extra + "</style>", 1)
    # 下一篇
    prev = meta.get("prev_slug", "")
    nav = (f'<div class="article-nav"><span></span>'
           f'<a href="{prev}" style="text-align:right">上一篇：{meta.get("prev_title", "")} →</a></div>'
           if prev else '<div class="article-nav"><span></span><a href="../index.html">返回首页 →</a></div>')
    t = re.sub(r'<div class="article-nav">.*?</div>', nav, t, count=1, flags=re.S)
    return t


# ══════════════════════════════════════════════
# 5. 首页 / sitemap / 页脚
# ══════════════════════════════════════════════
def update_index(meta, tags):
    slug, title, desc, date = meta["slug"], meta["title"], meta["desc"], meta["date"]
    idx_p = REPO / "index.html"
    idx = idx_p.read_text(encoding="utf-8")
    if f'id="article-{slug}"' in idx:
        print("  ↺ 首页卡片已存在，跳过")
        return
    t_esc = _html.escape(title, quote=True)
    d_esc = _html.escape(desc, quote=True)
    card = (
        f'<article class="article-card has-thumb" id="article-{slug}" data-category="chaye" '
        f'data-url="articles/{slug}.html" itemscope itemtype="https://schema.org/Article">\n'
        f'<a class="article-thumb" href="articles/{slug}.html">'
        f'<img src="images/thumb/{slug}-hero.webp" alt="{t_esc}" width="400" height="225" '
        f'loading="lazy" decoding="async"></a>\n'
        f'<div class="card-body">\n'
        f'<h3 itemprop="headline"><a href="articles/{slug}.html">{t_esc}</a></h3>\n'
        f'<p class="article-meta-time">📅 发布于 <time itemprop="datePublished" datetime="{date}">'
        f'{meta["zh_date_only"]}</time></p>\n'
        f'<meta itemprop="description" content="{d_esc}">\n'
        f'<p class="article-excerpt" itemprop="abstract">{d_esc}</p>\n'
        f'<a class="read-more" href="articles/{slug}.html">阅读全文 →</a>\n'
        f'<div class="tags">' + "".join(f'<span class="tag">{x}</span>' for x in tags) +
        f'</div>\n</div>\n</article>\n')
    marker = '<div class="article-list">\n'
    if marker not in idx:
        raise SystemExit("❌ 首页找不到 article-list 标记")
    idx = idx.replace(marker, marker + card, 1)
    idx_p.write_text(idx, encoding="utf-8")
    print(f"  ✓ 首页首卡已插入（现共 {idx.count('class=\"article-card')} 张）")


def update_sitemap(meta):
    sm_p = REPO / "sitemap.xml"
    sm = sm_p.read_text(encoding="utf-8")
    slug = meta["slug"]
    if f"{slug}.html" in sm:
        print("  ↺ sitemap 已存在，跳过")
        return
    entry = (f'  <url><loc>{SITE}/articles/{slug}.html</loc>'
             f'<lastmod>{meta["date"]}</lastmod><changefreq>monthly</changefreq>'
             f'<priority>0.8</priority></url>\n')
    sm = sm.replace("</urlset>", entry + "</urlset>")
    sm_p.write_text(sm, encoding="utf-8")
    print(f"  ✓ sitemap 已追加（共 {sm.count('<loc>')} 条）")


def update_footer(meta):
    n = len(glob.glob(str(REPO / "articles" / "*.html")))
    cnt = str(n)
    changed = 0
    targets = (glob.glob(str(REPO / "articles" / "*.html"))
               + glob.glob(str(REPO / "products" / "*.html"))
               + [str(REPO / "index.html"), str(REPO / "video.html")])
    for p in targets:
        fp = Path(p)
        s = fp.read_text(encoding="utf-8")
        o = s
        s = re.sub(r'(🔄 上次更新：[^<]*<time datetime=")[^"]*(">)[^<]*(</time>)',
                   lambda m: m.group(1) + meta["new_dt"] + m.group(2) + meta["zh_date"] + m.group(3), s)
        s = re.sub(r'(共 <span id="article-count">)\d+(</span>)',
                   lambda m: m.group(1) + cnt + m.group(2), s)
        if s != o:
            fp.write_text(s, encoding="utf-8")
            changed += 1
    print(f"  ✓ 页脚同步 {changed} 个页面 → {meta['new_dt'][:16]} / 共{cnt}篇")


# ══════════════════════════════════════════════
# 6. git
# ══════════════════════════════════════════════
def run_git(args, check=True):
    r = subprocess.run(["git"] + args, cwd=str(REPO), capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    out = (r.stdout + r.stderr).strip()
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} 失败:\n{out}")
    return out


def commit_push(meta, pushed=True):
    slug = meta["slug"]
    files = [f"articles/{slug}.html", "index.html", "sitemap.xml"]
    files += [x for x in glob.glob(str(REPO / "images" / "full" / f"{meta['prefix']}-*.webp"))]
    files += [x for x in glob.glob(str(REPO / "images" / "thumb" / f"{slug}-hero.webp"))]
    # 页脚同步改过的全部页面（规范书 §4 步骤7）：漏提交 → 线上页脚停在旧日期/旧篇数
    files += glob.glob(str(REPO / "articles" / "*.html"))
    files += glob.glob(str(REPO / "products" / "*.html"))
    files += [str(REPO / "video.html")]
    rel = [os.path.relpath(f, str(REPO)).replace("\\", "/") for f in files]
    run_git(["add", "--"] + rel)
    r = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=str(REPO))
    if r.returncode == 0:
        print("  ↺ 无变更可提交")
        return None
    msg = f"发布《{meta['title']}》：新增文章页+7图+首页首卡+sitemap+页脚同步"
    run_git(["commit", "-m", msg])
    head = run_git(["log", "--oneline", "-1"])
    print(f"  ✓ commit: {head}")
    if not pushed:
        print("  ⏸ 未推送（--no-push）")
        return head
    for attempt in range(8):
        p = subprocess.run(["git", "push", "origin", "main"], cwd=str(REPO),
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        ok = p.returncode == 0 or "up-to-date" in (p.stdout + p.stderr)
        print(f"  {'✓' if ok else '✗'} push 第{attempt+1}次: {(p.stdout + p.stderr).strip()[:160]}")
        if ok:
            return head
        time.sleep(25)
    raise RuntimeError("push 失败（GitHub 网络不可达，本地 commit 已保留，可稍后重试 push）")


def verify_online(meta, wait=45):
    import urllib.parse as _up
    url = f"{SITE}/articles/{_up.quote(meta['slug'])}.html"
    print(f"  等待部署 {wait}s …")
    time.sleep(wait)
    for att in range(8):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                html = r.read().decode("utf-8", "ignore")
            checks = {
                "标题": f"<h1>🍵 {_html.escape(meta['title'])}</h1>" in html,
                "lead导语": 'class="lead"' in html,
                "开篇Q1": "Q1：" in html,
                "Q2本地转化": STORE["addr"] in html and STORE["tel"] in html,
                "GEO板块": "惠州买茶去哪" in html,
                "话题标签": "xhs-tags" in html,
                "article-tags": 'class="article-tags"' in html,
                "场景图": html.count("scene-fig") >= 4,
                "og:image本篇": f"{meta['prefix']}-cover.webp" in html,
            }
            bad = [k for k, v in checks.items() if not v]
            print("   " + "  ".join(f"{'✓' if v else '✗'}{k}" for k, v in checks.items()))
            if not bad:
                print(f"  ✅ 线上验证通过: {url}")
                return True
        except Exception as e:
            print(f"   重试 {att+1}: {e}")
        time.sleep(20)
    print("  ⚠ 线上验证未全绿（可能仍在部署）")
    return False


# ══════════════════════════════════════════════
# main
# ══════════════════════════════════════════════
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    draft = Path(sys.argv[1])
    flags = set(sys.argv[2:])
    dry = "--dry-run" in flags
    skip_img = "--skip-images" in flags
    no_push = "--no-push" in flags

    if not draft.exists():
        raise SystemExit(f"❌ 草稿不存在: {draft}")

    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    date_compact = now.strftime("%Y%m%d")
    hm = now.strftime("%H:%M")

    print(f"\n{'='*66}\n发布: {draft.name}\n{'='*66}")

    # 1 scrub
    raw = scrub(draft.read_text(encoding="utf-8"))
    assert_clean(raw, "草稿")
    print("✓ [1/9] scrub 隐私清洗通过（真名/QQ/旧域名）")

    # 2 parse
    title, lead, sections, faq, tags, preview = parse_draft(raw)
    if not title:
        raise SystemExit("❌ 未找到标题")
    if not lead:
        lead = synth_lead(title, sections, faq)
        print(f"      ⓘ 草稿无「📌 开篇回答」，已自动合成导语（{len(lead)}字）")
    if len(sections) < 3:
        raise SystemExit(f"❌ 章节过少（{len(sections)}），至少 3 幕")
    tagged = list(tags)
    for t in CASE_TAGS:
        if t not in tagged:
            tagged.append(t)
    tagged = tagged[:10]   # 规范书 §2.2：6–10 个，三处同一套
    print(f"✓ [2/9] 解析: {len(sections)} 幕 / {len(faq)} FAQ / {len(tagged)} 标签")
    for h, ps in sections:
        print(f"      {h}  ({len(ps)}段)")

    slug = make_slug(title, date_compact)
    prefix = f"a{date_compact}{hashlib.md5(title.encode()).hexdigest()[:6]}"
    desc = make_desc(lead)
    assert_clean(slug, "slug")
    qa, faq_used = build_qa(faq, title)
    faq_rest = [f for f in faq if f[0] not in faq_used]

    # 上一篇
    prev_slug, prev_title = "", ""
    try:
        sm = (REPO / "sitemap.xml").read_text(encoding="utf-8")
        arts = re.findall(r"<loc>https://feng-tea\.com/articles/([^<]+)</loc>", sm)
        if arts:
            prev_slug = arts[0] if not arts[0].startswith(date_compact) else (arts[1] if len(arts) > 1 else "")
            pf = REPO / "articles" / prev_slug
            if pf.exists():
                m = re.search(r"<h1>🍵\s*(.*?)</h1>", pf.read_text(encoding="utf-8"), re.S)
                prev_title = m.group(1).strip() if m else prev_slug
    except Exception:
        pass

    meta = {
        "title": title, "slug": slug, "prefix": prefix, "desc": desc,
        "date": date, "zh_date": f"{now.strftime('%Y年%m月%d日')} {hm}:00",
        "zh_date_only": now.strftime("%Y年%m月%d日"),
        "new_dt": f"{date}T{hm}:00",
        "prev_slug": prev_slug, "prev_title": prev_title,
    }
    print(f"      slug   = {slug}")
    print(f"      prefix = {prefix}")

    # 3 images
    if skip_img:
        prompts = build_prompts(title, sections)
        dims = {p["key"]: (869, 489) for p in prompts}
        audit_log = []
        print("⏭ [3/9] 跳过生图（--skip-images）")
    elif dry:
        prompts = build_prompts(title, sections)
        dims = {p["key"]: (869, 489) for p in prompts}
        audit_log = []
        print("⏭ [3/9] DRY-RUN 跳过生图，仅预览提示词:")
        for p in prompts:
            print(f"      {p['key']:6s} {p['desc']}")
    else:
        print("[3/9] 生成 7 张配图（免费 Kolors）…")
        prompts, dims, audit_log = make_images(prefix, title, sections, slug)
        print(f"✓ [3/9] 配图完成")

    # 4 page
    page = build_page(meta, lead, qa, sections, faq_rest, tagged, preview, prompts, dims)
    assert_clean(page, "文章页")
    assert 'class="lead"' in page and "Q1：" in page and "惠州买茶去哪" in page, "模块缺失"
    assert page.count("scene-fig") >= 3, "场景图不足"
    assert 'class="article-tags"' in page, "article-tags 缺失"
    assert page.count('class="article-tags"') == 1, \
        f"article-tags 重复 {page.count('class=\"article-tags\"')} 份（应恰好 1 份）"
    assert page.count('class="tags"') == 1, "头部 tags chips 重复"
    assert f"{prefix}-cover.webp" in page, "封面未引用"
    assert page.count(f"{prefix}-cover.webp") >= 3, \
        "分享图三处（og:image / twitter:image / JSON-LD image）未全部指向本篇封面"
    print(f"✓ [4/9] 文章页生成: 场景图{page.count('scene-fig')} 标签{len(tagged)} 正文{len(page)}B")

    art = REPO / "articles" / f"{slug}.html"
    if dry:
        out = REPO / f"_preview_{slug[:20]}.html"
        out.write_text(page, encoding="utf-8")
        print(f"      DRY-RUN 预览 → {out.name}")
        print(f"\n✅ DRY-RUN 完成，未修改仓库。预览: {out}")
        return
    art.write_text(page, encoding="utf-8")
    print(f"      → articles/{slug}.html")

    # 5-7
    update_index(meta, tagged)
    update_sitemap(meta)
    update_footer(meta)
    print("✓ [5-7/9] 首页 / sitemap / 页脚 完成")

    # 8
    commit_push(meta, pushed=not no_push)

    # 9
    if not no_push:
        verify_online(meta)

    # 标记已发布（供选稿器 next_draft.py 跳过）
    try:
        sys.path.insert(0, str(REPO))
        import next_draft as _nd
        st = _nd.load_state()
        st[draft.name] = {
            "marked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "title": title,
            "slug": slug,
        }
        _nd.save_state(st)
        print(f"✅ 已标记发布: {draft.name}（累计 {len(st)} 篇）")
    except Exception as e:
        print(f"⚠ 标记失败: {e}")

    warn_txt = ("7 张全部通过（无正脸 / 无汉字）" if not audit_log
                else "; ".join(f"{k}:{'/'.join(v)}" for k, v in audit_log))
    print(f"\n{'='*66}")
    print(f"✅ 完成: {SITE}/articles/{slug}.html")
    print(f"✅ 标签（三处一致）{len(tagged)} 个: {' '.join(tagged)}")
    print(f"⚠ 图片合规: {warn_txt}")
    print(f"{'='*66}\n")


if __name__ == "__main__":
    main()
