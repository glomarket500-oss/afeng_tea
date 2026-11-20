# -*- coding: utf-8 -*-
"""紫砂壶实拍 → 4 种排版方案样张（解决"场景太近"）

方案思路：
  A 模糊延展   ：整张照片完整保留（不裁），四周用自身模糊填充成 16:9 —— 场景感最强，壶不会顶到边
  B 留白式     ：左 60% 放照片（等比缩放不裁切），右 40% 淡色留白给标题/文字
  C 画框式     ：照片缩到中间当"画中画"，外圈米色纸上加细边线，像装裱
  D 低裁切     ：只裁掉最边缘 8%，保留原构图（对比"以前裁到只剩壶身"）
"""
import hashlib
from pathlib import Path

from PIL import Image, ImageFilter, ImageDraw

SRC = Path(r"C:\茶叶素材\紫砂壶图片")
OUT = Path(r"C:\Users\Administrator\AppData\Local\hermes\cache\scratch\teapot_demo")
W, H = 869, 489


def uniq_photos(n=4):
    """按面积挑 n 张内容不同的图"""
    seen, out = set(), []
    for p in sorted(SRC.glob("*.jpg"), key=lambda x: ("(1)" in x.stem, x.name)):
        try:
            d = hashlib.md5(p.read_bytes()).hexdigest()
            with Image.open(p) as im:
                w, h = im.size
        except Exception:
            continue
        if d in seen or w < 600 or h < 400:
            continue
        seen.add(d)
        out.append((w * h, p))
    out.sort(reverse=True)
    return [p for _, p in out[:n]]


def A_blur_pad(im):
    """整图保留 + 自身模糊填边"""
    bg = im.copy()
    s = max(W / bg.width, H / bg.height)
    bg = bg.resize((max(W, int(bg.width * s)), max(H, int(bg.height * s))), Image.LANCZOS)
    bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2,
                  (bg.width - W) // 2 + W, (bg.height - H) // 2 + H)).filter(ImageFilter.GaussianBlur(28))
    fg = im.copy()
    fg.thumbnail((W, H), Image.LANCZOS)
    bg.paste(fg, ((W - fg.width) // 2, (H - fg.height) // 2))
    return bg


def B_side_pad(im):
    """左 60% 放照片，右侧留白"""
    canvas = Image.new("RGB", (W, H), (246, 242, 234))
    fg = im.copy()
    fg.thumbnail((int(W * 0.60), H - 24), Image.LANCZOS)
    canvas.paste(fg, (24, (H - fg.height) // 2))
    return canvas


def C_frame(im):
    """画框式：米色纸底 + 细边"""
    canvas = Image.new("RGB", (W, H), (238, 232, 220))
    fg = im.copy()
    fg.thumbnail((int(W * 0.66), int(H * 0.78)), Image.LANCZOS)
    x, y = (W - fg.width) // 2, (H - fg.height) // 2
    canvas.paste(fg, (x, y))
    d = ImageDraw.Draw(canvas)
    d.rectangle([x - 6, y - 6, x + fg.width + 5, y + fg.height + 5], outline=(180, 165, 140), width=2)
    return canvas


def D_light_crop(im):
    """只裁掉边缘 8%，尽量保留原场景"""
    sw, sh = im.size
    target = W / H
    if sw / sh > target:                       # 太宽 → 轻微裁两侧
        nw = int(sh * target * 1.08)
        nw = min(nw, sw)
        box = ((sw - nw) // 2, 0, (sw - nw) // 2 + nw, sh)
    else:                                      # 太高 → 轻微裁上下
        nh = int(sw / target * 1.08)
        nh = min(nh, sh)
        box = (0, (sh - nh) // 2, sw, (sh - nh) // 2 + nh)
    return im.crop(box).resize((W, H), Image.LANCZOS)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    photos = uniq_photos(3)
    print(f"取到 {len(photos)} 张样图")
    for i, p in enumerate(photos, 1):
        with Image.open(p) as im:
            im = im.convert("RGB")
            for name, fn in (("A模糊延展", A_blur_pad), ("B留白式", B_side_pad),
                             ("C画框式", C_frame), ("D低裁切", D_light_crop)):
                out = OUT / f"{i}_{name}.webp"
                fn(im).save(out, "WEBP", quality=86)
                print(f"  {out.name}  {out.stat().st_size // 1024}KB")
        print(f"  源图: {p.name}（{im.width}×{im.height}）")
