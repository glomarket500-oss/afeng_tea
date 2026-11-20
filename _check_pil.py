# -*- coding: utf-8 -*-
"""确认当前解释器能不能跑流水线所需的依赖"""
import sys
print("exe:", sys.executable)
print("ver:", sys.version.split()[0])
for mod in ("PIL", "urllib.request", "json", "subprocess"):
    try:
        __import__(mod)
        print(f"  OK  {mod}")
    except Exception as e:
        print(f"  FAIL {mod}: {e}")
try:
    from PIL import Image
    print("  Pillow:", Image.__name__, "WebP保存支持:",
          "WEBP" in " ".join(Image.registered_extensions().values()) or "webp" in str(Image.OPEN))
except Exception as e:
    print("  Pillow detail fail:", e)
