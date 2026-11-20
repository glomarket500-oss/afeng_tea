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
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import next_draft as ND
import vercel_nudge as VN

REPO = ND.REPO
PY = sys.executable

# 单次发布硬上限：绝不允许挂死
# （2026-11-17 因 git push 无超时，进程整整挂了 25 小时，把后面几天全堵死）
PUBLISH_TIMEOUT = 900
# 线上补救总等待上限（秒）
NUDGE_WAIT = 240


def pick():
    for today_only, scope in ((True, "当天新素材"), (False, "积压素材")):
        lst = ND.candidates(today_only=today_only)
        if lst:
            return lst[0], scope, len(lst)
    return None, "", 0


def run_publish(draft_path):
    """跑 publish_new.py，带硬超时。返回 (out, rc)。"""
    try:
        r = subprocess.run(
            [PY, str(REPO / "publish_new.py"), str(draft_path)],
            cwd=str(REPO), capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            timeout=PUBLISH_TIMEOUT,
        )
        return (r.stdout or "") + (r.stderr or ""), r.returncode
    except subprocess.TimeoutExpired as e:
        so, se = e.stdout or "", e.stderr or ""
        if isinstance(so, bytes):
            so = so.decode("utf-8", "replace")
        if isinstance(se, bytes):
            se = se.decode("utf-8", "replace")
        return (so + se
                + "\n⏱ 超时 %d 秒，已强制中止（多半卡在 git push / 图片接口）"
                % PUBLISH_TIMEOUT), 124


def find_article_url(out):
    """从输出里抓文章页 URL。"""
    m = re.search(r"✅ 完成: (https?://\S+)", out)
    if m:
        return m.group(1).strip()
    m = re.search(r"(https?://feng-tea\.com/articles/\S+\.html)", out)
    return m.group(1).strip() if m else None


def main():
    d, scope, remain = pick()
    if not d:
        print("今日无新素材待发（积压也已清空）")
        return 0

    print(f"【选稿】{scope}｜{d['date']}｜{d['title']}")
    print(f"       剩余待发 {remain} 篇")
    print(f"【草稿】{d['name']}")
    print("=" * 60)

    out, rc = run_publish(d["path"])
    print(out)

    ok = rc == 0 and "线上验证通过" in out

    # ---- Vercel 补救：内容已推上去，但线上没接住（大提交偶发不被 Vercel 触发） ----
    if not ok:
        url = find_article_url(out)
        pushed = ("API 推送成功" in out) or ("推送成功" in out)
        if url and pushed:
            print("=" * 60)
            print("⚠ 内容已推送到仓库，但线上未生效 —— 启动 Vercel 补救")
            try:
                VN.nudge(log=print)
                live, cost = VN.wait_online(url, max_wait=NUDGE_WAIT, log=print)
                if live:
                    print("✅ 补救成功：文章已上线（用时 %ss）" % cost)
                    ok = True
                else:
                    print("❌ 补救后仍未上线，请到 Vercel 后台看构建日志")
            except Exception as e:
                print("❌ 补救过程出错：%s: %s" % (type(e).__name__, e))

    print("=" * 60)
    if ok:
        print(f"✅ 发布成功并线上验证通过：{d['title']}")
        url = find_article_url(out)
        if url:
            print(f"   文章地址：{url}")
        return 0
    print(f"❌ 发布失败（退出码 {rc}）：{d['title']}")
    if "配图缺失" in out:
        print("   原因：配图未生成，已按硬闸中止，仓库与线上均未改动")
    elif "超时" in out:
        print("   原因：发布流程超时被强制中止；本地提交已保留，下次运行可续推")
    elif "push" in out.lower() and "失败" in out:
        print("   原因：git push 未成功；本地提交已保留，下次运行可续推")
    print("   请查看上面的日志定位。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
