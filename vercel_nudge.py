#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vercel 部署补救：当一个「大提交」没被 Vercel 接住时，补推一个极小的
改动重新触发构建。

背景
----
每天发文一次要推 110-120 个文件（正文页 + 7 图 + 首页 + sitemap + 页脚同步）。
这种大提交偶尔不会被 Vercel 的 GitHub 集成接住 —— 仓库里有文件、线上却 404
（2026-11-20 实测：118 文件的提交 7a00e784 完全没生成部署记录，而紧接着推
一个 1 文件的提交，Vercel 立刻建了两个 Production 部署）。

用法
----
    python vercel_nudge.py            # 推一个探针提交
    python vercel_nudge.py --wait 180 # 推完并等线上 URL 出现（需给 URL）

也可作为模块：
    from vercel_nudge import nudge, wait_online
"""
import re
import sys
import time
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))

PING_NAME = "deploy_ping.txt"


def nudge(repo=REPO, log=print):
    """写一个带时间戳的极小文件并推送，重新触发 Vercel 构建。返回新 commit sha。"""
    import git_push_api as GP

    repo = Path(repo)
    ping = repo / PING_NAME
    ping.write_text(
        "deploy nudge %s\n" % time.strftime("%Y-%m-%d %H:%M:%S"), encoding="utf-8"
    )
    subprocess.run(["git", "add", PING_NAME], cwd=str(repo), check=True,
                   capture_output=True)
    r = subprocess.run(
        ["git", "commit", "-m", "部署补救：补推探针以重新触发 Vercel 构建"],
        cwd=str(repo), capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    if r.returncode != 0:
        log("  [探针] 无新改动可提交，直接重推")
    sha = GP.push_via_api(str(repo), log=log)
    log("  [探针] 已推送: %s" % sha)
    return sha


def http_code(url, timeout=30):
    """返回 HTTP 状态码，异常时返回 None。"""
    p = urllib.parse.urlsplit(url)
    safe = urllib.parse.urlunsplit(
        (p.scheme, p.netloc, urllib.parse.quote(p.path), p.query, p.fragment)
    )
    try:
        req = urllib.request.Request(safe, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status
    except Exception as e:
        return getattr(e, "code", None)


def wait_online(url, max_wait=180, interval=15, log=print):
    """轮询直到文章页返回 200。返回 (ok, 用时秒)。"""
    t0 = time.time()
    attempt = 0
    while time.time() - t0 < max_wait:
        attempt += 1
        code = http_code(url)
        cost = int(time.time() - t0)
        log("  [等线上] 第 %d 次  %ss  HTTP %s" % (attempt, cost, code))
        if code == 200:
            return True, cost
        time.sleep(interval)
    return False, int(time.time() - t0)


def main():
    url = None
    args = sys.argv[1:]
    if "--url" in args:
        url = args[args.index("--url") + 1]
    max_wait = 180
    if "--wait" in args:
        max_wait = int(args[args.index("--wait") + 1])

    nudge()
    if url:
        ok, cost = wait_online(url, max_wait=max_wait)
        print("线上恢复:" if ok else "仍未上线:", ok, "用时 %ss" % cost)
        return 0 if ok else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
