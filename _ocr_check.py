#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本地 OCR 体检：检测 7 张配图里的文字残留（规范书硬指标：绝不出现任何文字）"""
import sys, subprocess
from pathlib import Path

REPO = Path(r"C:\afeng_tea")
names = ["qiuchu-cover", "qiuchu-s1", "qiuchu-s2", "qiuchu-s3", "qiuchu-s4", "qiuchu-s5", "qiuchu-s6"]

ocr = None
try:
    import pytesseract
    from PIL import Image
    ocr = ("pytesseract", pytesseract)
    print("OCR 引擎: pytesseract")
except Exception as e:
    try:
        import easyocr
        ocr = ("easyocr", easyocr.Reader(["ch_sim", "en"], gpu=False, verbose=False))
        print("OCR 引擎: easyocr")
    except Exception as e2:
        print("无可用 OCR:", e, "|", e2)
        sys.exit(2)

if ocr[0] == "pytesseract":
    import pytesseract
    for n in names:
        p = REPO / "images" / "full" / f"{n}.webp"
        im = Image.open(p).convert("RGB")
        # 中英双查，放大提高识别率
        big = im.resize((im.width * 2, im.height * 2), 1)
        txt = pytesseract.image_to_string(big, lang="chi_sim+eng").strip()
        print(f"{n:14s} OCR='{txt[:80]}' -> {'干净' if not txt else '⚠有文字'}")
else:
    reader = ocr[1]
    for n in names:
        p = REPO / "images" / "full" / f"{n}.webp"
        res = reader.readtext(str(p), detail=0)
        print(f"{n:14s} OCR={res[:10]} -> {'干净' if not res else '⚠有文字'}")
