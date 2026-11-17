# -*- coding: utf-8 -*-
"""GitHub API 推送模块（绕过被干扰的 github.com）
背景：本机 github.com:443 常被重置，而 api.github.com 可达。
      git push 没超时就会永久挂起（2026-11-17 卡死 2 小时的根因）。
用法：
    from git_push_api import push_via_api
    sha = push_via_api(REPO)      # 成功返回 commit sha，已最新返回 "up-to-date"，失败抛异常
"""
import base64
import json
import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.github.com"
MIRROR_FILE = "api_mirror.json"


def _is_ancestor(repo, anc, desc):
    r = subprocess.run(["git", "merge-base", "--is-ancestor", anc, desc],
                       cwd=str(repo), capture_output=True)
    return r.returncode == 0


def _load_mirror(repo):
    p = Path(repo) / ".git" / MIRROR_FILE
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_mirror(repo, local_sha, remote_sha, branch):
    p = Path(repo) / ".git" / MIRROR_FILE
    p.write_text(json.dumps({"local": local_sha, "remote": remote_sha, "branch": branch},
                            ensure_ascii=False, indent=2), encoding="utf-8")


def _git(repo, *args, binary=False):
    r = subprocess.run(["git"] + list(args), cwd=str(repo),
                       capture_output=True, text=not binary, timeout=180)
    if r.returncode != 0:
        err = r.stderr if not binary else r.stderr.decode("utf-8", "ignore")
        raise RuntimeError(f"git {' '.join(args)} 失败: {err[:300]}")
    return r.stdout


def _token():
    """优先环境变量，其次 ~/.git-credentials"""
    import os
    for k in ("GITHUB_TOKEN", "GH_TOKEN"):
        v = os.environ.get(k)
        if v:
            return v.strip()
    cred = Path.home() / ".git-credentials"
    if cred.exists():
        txt = cred.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"https://[^:@\s]+:([^@\s]+)@github\.com", txt)
        if m:
            return m.group(1)
    raise RuntimeError("找不到 GitHub token（环境变量 GITHUB_TOKEN 或 ~/.git-credentials）")


def _repo_slug(repo):
    url = _git(repo, "remote", "get-url", "origin").strip()
    m = re.search(r"github\.com[:/]([^/]+)/([^/\s]+?)(?:\.git)?$", url)
    if not m:
        raise RuntimeError(f"无法从 remote 解析 owner/repo: {url}")
    return m.group(1), m.group(2)


def _api(path, method="GET", payload=None, tok=None):
    url = path if path.startswith("http") else API + path
    data = None
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "afeng-publish"}
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            body = r.read()
            return json.loads(body.decode("utf-8")) if body else {}
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {path} → HTTP {e.code}: {e.read().decode('utf-8', 'ignore')[:300]}")


def push_via_api(repo, branch="main", log=print):
    repo = Path(repo)
    owner, name = _repo_slug(repo)
    tok = _token()
    local = _git(repo, "rev-parse", "HEAD").strip()
    local_tree = _git(repo, "rev-parse", "HEAD^{tree}").strip()

    ref = _api(f"/repos/{owner}/{name}/git/ref/heads/{branch}", tok=tok)
    remote = ref["object"]["sha"]
    remote_tree = _api(f"/repos/{owner}/{name}/git/commits/{remote}", tok=tok)["tree"]["sha"]

    # 1) 内容已一致（tree 相同）→ 同步完成；API 建的提交与本地 SHA 不同但内容相同
    if remote_tree == local_tree:
        if remote != local:
            _save_mirror(repo, local, remote, branch)
            log(f"  ↳ API 推送：内容已一致（本地 {local[:7]} ≈ 远程 {remote[:7]}），已记录镜像")
        else:
            log("  ↳ API 推送：远程已是最新")
        return "up-to-date"

    # 2) 决定 diff 基线：优先镜像记录，其次"远程是本地祖先"
    mirror = _load_mirror(repo)
    if mirror.get("remote") == remote and mirror.get("local"):
        base = mirror["local"]
        if not _is_ancestor(repo, base, local):
            raise RuntimeError(f"镜像基线 {base[:7]} 不是本地 HEAD 的祖先，历史被改写，拒绝推送")
        log(f"  ↳ 用镜像基线 {base[:7]} 计算差异")
    elif _is_ancestor(repo, remote, local):
        base = remote
    else:
        raise RuntimeError(
            f"远程 {remote[:7]} 与本地 {local[:7]} 既不同内容也非祖先关系，"
            f"可能有人在别处推送，需人工处理，拒绝自动推送")

    diff = _git(repo, "-c", "core.quotepath=false",
                "diff", "--name-status", base, local).strip().splitlines()
    if not diff:
        _save_mirror(repo, local, remote, branch)
        log("  ↳ 无内容差异，已更新镜像记录")
        return "up-to-date"

    entries = []
    deleted = 0
    for line in diff:
        parts = line.split("\t")
        status, path = parts[0], parts[-1]
        if status.startswith("D"):
            entries.append({"path": path, "mode": "100644", "type": "blob", "sha": None})
            deleted += 1
            continue
        content = _git(repo, "show", f"{local}:{path}", binary=True)
        blob = _api(f"/repos/{owner}/{name}/git/blobs", method="POST",
                    payload={"content": base64.b64encode(content).decode("ascii"),
                             "encoding": "base64"}, tok=tok)
        entries.append({"path": path, "mode": "100644", "type": "blob", "sha": blob["sha"]})

    log(f"  ↳ API 推送：{len(entries)} 个文件（删除 {deleted}）→ {owner}/{name}")

    tree = _api(f"/repos/{owner}/{name}/git/trees", method="POST",
                payload={"base_tree": remote_tree, "tree": entries}, tok=tok)
    msg = _git(repo, "log", "-1", "--format=%B", local).strip() or "publish"
    commit = _api(f"/repos/{owner}/{name}/git/commits", method="POST",
                  payload={"message": msg, "tree": tree["sha"], "parents": [remote]}, tok=tok)
    _api(f"/repos/{owner}/{name}/git/refs/heads/{branch}", method="PATCH",
         payload={"sha": commit["sha"], "force": False}, tok=tok)

    verify = _api(f"/repos/{owner}/{name}/git/ref/heads/{branch}", tok=tok)["object"]["sha"]
    if verify != commit["sha"]:
        raise RuntimeError(f"API 推送后复核失败：远程 {verify[:7]} ≠ 新提交 {commit['sha'][:7]}")
    new_tree = _api(f"/repos/{owner}/{name}/git/commits/{verify}", tok=tok)["tree"]["sha"]
    if new_tree != local_tree:
        raise RuntimeError(f"API 推送后 tree 不一致：远程 {new_tree[:7]} ≠ 本地 {local_tree[:7]}")

    _save_mirror(repo, local, verify, branch)
    log(f"  ✓ API 推送成功：{commit['sha'][:7]}（远程 tree 与本地一致，已复核）")
    return commit["sha"]


if __name__ == "__main__":
    import sys
    print(push_via_api(sys.argv[1] if len(sys.argv) > 1 else r"C:\afeng_tea"))
