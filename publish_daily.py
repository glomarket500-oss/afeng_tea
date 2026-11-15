#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""每日自动发文（供 cron 直跑，不经模型）
=====================================================
1. 选稿：当天素材优先，当天没有则取积压最新一篇
2. 发布：调 publish_new.py 走完九步
   （内部已含：隐私清洗 / 去水印裁底 / 429退避重试 / 缺图硬闸 /
     首页首卡 / sitemap / 页脚同步 / 原子提交 / push重试8次 / 线上验证）
3. 输出纯文本报告，由调度器直接投递

退出码：0 = 发了且线上验证通过；1 = 失败（报告里写明卡在哪一步）
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import next_draft as ND

REPO = ND.REPO
PY = sys.executable


def pick():
    for today_only, scope in ((True, "当天新素材"), (False, "积压素材")):
        lst = ND.candidates(today_only=today_only)
        if lst:
            return lst[0], scope, len(lst)
    return None, "", 0


def main():
    d, scope, remain = pick()
    if not d:
        print("今日无新素材待发（积压也已清空）")
        return 0

    print(f"【选稿】{scope}｜{d['date']}｜{d['title']}")
    print(f"       剩余待发 {remain} 篇")
    print(f"【草稿】{d['name']}")
    print("=" * 60)

    r = subprocess.run(
        [PY, str(REPO / "publish_new.py"), d["path"]],
        cwd=str(REPO), capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    out = (r.stdout or "") + (r.stderr or "")
    print(out)

    ok = r.returncode == 0 and "线上验证通过" in out
    print("=" * 60)
    if ok:
        print(f"✅ 发布成功并线上验证通过：{d['title']}")
        return 0
    print(f"❌ 发布失败（退出码 {r.returncode}）：{d['title']}")
    if "配图缺失" in out:
        print("   原因：配图未生成，已按硬闸中止，仓库与线上均未改动")
    elif "push" in out.lower() and "失败" in out:
        print("   原因：git push 未成功；本地提交已保留，下次运行可续推")
    print("   请查看上面的日志定位。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
