# -*- coding: utf-8 -*-
"""真实照片优先取材（阿凤姐店里的实拍图）

规则（2026-11-19 站方要求）：
  1. 先用真实照片：C:\\茶叶素材\\图片文件夹 里的实拍图
  2. 需要人物时优先用阿凤姐的实拍照片（可裁剪、可换背景，但优先原图）
  3. 真实图不够用，才用免费 AI 生图（Kolors）兜底

配套：
  · images/real_photos.json   —— 每张实拍图的标签（由 _classify_photos.py 生成）
  · .real_photo_usage.json     —— 每张图最近被哪篇文章用过（避免连续重复）
"""
import json
from pathlib import Path

from PIL import Image, ImageOps

try:                                        # Pillow 10+ 把重采样常量移到了 Resampling
    LANCZOS = Image.Resampling.LANCZOS
except AttributeError:                      # 老版本兜底
    LANCZOS = Image.LANCZOS

SRC = Path(r"C:\茶叶素材\图片文件夹")
TEAPOT_SRC = Path(r"C:\茶叶素材\紫砂壶图片")     # 紫砂壶实拍（晚点放图，空目录自动退回 AI）
REPO = Path(r"C:\afeng_tea")
MANIFEST = REPO / "images" / "real_photos.json"
USAGE = REPO / ".real_photo_usage.json"

# 主题 → 想要的标签（命中越多越优先）
THEME_TAGS = {
    "person": ["人物", "泡茶", "店内"],
    "tea": ["干茶", "茶具", "泡茶"],
    "shop": ["店内", "茶架", "礼盒"],
    "garden": ["茶园", "山景"],
}


def _remap_missing(items):
    """文件名被整理/重命名后，按「文件大小最接近」把清单里的旧名纠正成现名。
    返回是否有改动（有则回写清单）。"""
    missing = [i for i in items if not (SRC / i["file"]).exists()]
    if not missing:
        return False
    actual = [p for p in SRC.iterdir() if p.is_file() and p.suffix.lower() in
              (".jpg", ".jpeg", ".png", ".webp")]
    used = {i["file"] for i in items if (SRC / i["file"]).exists()}
    changed = False
    for it in missing:
        want = int(it.get("size_kb") or 0) * 1024
        best, best_diff = None, None
        for p in actual:
            if p.name in used:
                continue
            diff = abs(p.stat().st_size - want)
            if best_diff is None or diff < best_diff:
                best, best_diff = p, diff
        if best is not None and best_diff is not None and best_diff < max(4096, want * 0.05):
            it["file"] = best.name
            used.add(best.name)
            changed = True
    return changed


def load_manifest():
    if not MANIFEST.exists():
        return []
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        items = data.get("items", [])
        if _remap_missing(items):
            data["items"] = items
            MANIFEST.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return items
    except Exception:
        return []


def _usage():
    if USAGE.exists():
        try:
            return json.loads(USAGE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_usage(u):
    try:
        USAGE.write_text(json.dumps(u, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def _score(meta, text, want_person, recent):
    """打分：越相关越高；最近用过的扣分（避免每篇都同一张）"""
    s = 0.0
    tags = set(meta.get("useful_tags") or [])
    if want_person:
        if meta.get("has_person"):
            s += 5
        if "正面" in str(meta.get("person") or "") or "侧脸" in str(meta.get("person") or ""):
            s += 1
    if "店内" in tags:
        s += 1.5
    if "茶架" in tags:
        s += 1
    if "泡茶" in tags or "茶具" in tags:
        s += 1.5
    if "干茶" in tags:
        s += 1
    if "礼盒" in tags:
        s += 0.8
    # 与文章文字重合的标签再加分
    for t in tags:
        if t and t in text:
            s += 0.6
    q = str(meta.get("quality") or "")
    s += {"good": 1.0, "ok": 0.3}.get(q, -1.0)
    # 场景相关性：茶店/茶架优先，餐厅、阳台、海边、商场这类生活照降权
    scene = str(meta.get("scene") or "")
    if "茶店" in scene or "茶叶店" in scene or "茶架" in scene:
        s += 2.5
    for off in ("餐厅", "阳台", "海边", "圣诞", "商场", "广场", "街"):
        if off in scene:
            s -= 2.0
            break
    if int(meta.get("w") or 0) < 800:
        s -= 1            # 分辨率偏低（576 宽），轻微降权但仍可用
    s -= 1.2 * recent.get(meta["file"], 0)   # 最近用过 → 降权
    return s


def pick(title, sections_text, need, want_person=True, min_count=0):
    """挑 need 张真实照片（可能少于 need，剩下的交回 AI 生图）。
    规则是"真实照片优先"，所以只要不是低清/劣质/不存在，就优先用实拍；
    分数只决定**顺序**，不决定要不要用。"""
    items = [i for i in load_manifest()
             if i.get("suitable_for_article") and i.get("quality") != "poor"
             and int(i.get("w") or 0) >= 560 and (SRC / i["file"]).exists()]
    if not items:
        return []
    recent = _usage()
    text = (title or "") + " " + (sections_text or "")
    ranked = sorted(items, key=lambda m: _score(m, text, want_person, recent), reverse=True)
    return ranked[:need]


def pick_teapot(need=1):
    """紫砂壶实拍：直接扫目录（不依赖标签清单），按像素面积 + 使用次数挑。
    目录为空 → 返回 []，调用方自动退回 AI 生图。
    去重：按内容哈希，且优先用不带 "(1)" 的原图（目录里常有大量副本）。"""
    if not TEAPOT_SRC.exists():
        return []
    import hashlib

    out, seen = [], set()
    for p in sorted(TEAPOT_SRC.iterdir(), key=lambda x: ("(1)" in x.stem, x.name)):
        if p.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
            continue
        try:
            with Image.open(p) as im:
                w, h = im.size
        except Exception:
            continue
        if w < 480 or h < 320:
            continue
        try:
            digest = hashlib.md5(p.read_bytes()).hexdigest()
        except Exception:
            continue
        if digest in seen:          # 同一张图的副本，跳过
            continue
        seen.add(digest)
        out.append({"file": p.name, "w": w, "h": h, "scene": "紫砂壶",
                    "quality": "good", "useful_tags": ["茶具", "紫砂"], "_dir": str(TEAPOT_SRC)})
    out.sort(key=lambda m: m["w"] * m["h"], reverse=True)
    recent = _usage()
    out.sort(key=lambda m: recent.get(m["file"], 0))     # 没怎么用过的优先
    return out[:need]


def prepare(meta, dst, w=869, h=489, quality=82):
    """把实拍图规整成文章用图：按 EXIF 转正 → 居中裁 16:9 → 缩放 → 存 webp"""
    src = Path(meta.get("_dir") or SRC) / meta["file"]
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        sw, sh = im.size
        target = w / h
        if sw / sh > target:                     # 太宽 → 裁两边
            nw = int(sh * target)
            left = (sw - nw) // 2
            im = im.crop((left, 0, left + nw, sh))
        else:                                     # 太高 → 裁上下
            nh = int(sw / target)
            # 竖版（多为怼脸自拍）：直接从顶部取，保住整个头顶和脸，宁可不露身体
            top = 0 if sh / max(sw, 1) >= 1.4 else max(0, int((sh - nh) * 0.22))
            im = im.crop((0, top, sw, top + nh))
        im = im.resize((w, h), LANCZOS)
        dst.parent.mkdir(parents=True, exist_ok=True)
        im.save(dst, "WEBP", quality=quality, method=6)
    return w, h, dst.stat().st_size


def prepare_thumb(meta, dst, w=400, quality=82):
    src = Path(meta.get("_dir") or SRC) / meta["file"]
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        sw, sh = im.size
        nh = int(sw * 9 / 16)
        top = 0 if sh / max(sw, 1) >= 1.4 else max(0, int((sh - nh) * 0.22))
        im = im.crop((0, top, sw, min(sh, top + nh))).resize((w, int(w * 9 / 16)), LANCZOS)
        dst.parent.mkdir(parents=True, exist_ok=True)
        im.save(dst, "WEBP", quality=quality, method=6)
    return dst.stat().st_size


def mark_used(metas, slug):
    u = _usage()
    for m in metas:
        u[m["file"]] = u.get(m["file"], 0) + 1
    u["_last_slug"] = slug
    _save_usage(u)


def describe(meta):
    return f"{meta['file'][:14]}（{meta.get('person', '')}/{meta.get('scene', '')[:14]}）"
