#!/usr/bin/env python3
"""
ZONGYUAN-ROOT 本地全量 → 魔搭数据湖 慢速分批推送 V1.0
策略：git方式，每批≤40文件，push后sleep限速，断点续传
"""
import os, subprocess, time, datetime, json

LOCAL_ROOT = "/home/user/ZONGYUAN-ROOT"
REPO_DIR = "/tmp/zongyuan-datalake-repo"
REMOTE = "https://oauth2:r7B49x9911hsiSeVjgBq@www.modelscope.cn/zongyuanroot/zongyuan-root-achievements.git"
PROGRESS_FILE = "/home/user/ZONGYUAN-ROOT/01_核心资产锚点/PUSH-PROGRESS.json"
BATCH_SIZE = 40
SLEEP = 3  # 每批间隔秒
MAX_BATCH_SIZE_MB = 50  # 单批最大MB（超限拆小）

EXCLUDE_DIRS = {".git", "node_modules", "__pycache__", ".cache"}
EXCLUDE_EXT = {".pyc", ".log"}

def log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"pushed": [], "total": 0}

def save_progress(p):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(p, f, ensure_ascii=False, indent=2)

def collect_files():
    """收集待推送文件（排除目录/扩展名/已推送）"""
    prog = load_progress()
    files = []
    for root, dirs, names in os.walk(LOCAL_ROOT, followlinks=False):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not os.path.islink(os.path.join(root, d))]
        for n in names:
            ext = os.path.splitext(n)[1].lower()
            if ext in EXCLUDE_EXT:
                continue
            full = os.path.join(root, n)
            rel = os.path.relpath(full, LOCAL_ROOT)
            if rel in prog["pushed"]:
                continue
            # 跳过断链/软链文件（指向其他目录的引用不算本地资产）
            if not os.path.isfile(full) or os.path.islink(full):
                continue
            files.append((rel, full))
    return files

def git(args, cwd=REPO_DIR):
    return subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)

def setup_repo():
    if not os.path.exists(REPO_DIR):
        log("克隆魔搭仓库...")
        r = subprocess.run(["git","clone",REMOTE,REPO_DIR], capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            log(f"clone失败: {r.stderr[:200]}")
            return False
    return True

def push_batch(batch):
    """推送一批：copy→add→commit→push"""
    for rel, full in batch:
        dest = os.path.join(REPO_DIR, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        subprocess.run(["cp", full, dest], check=False)
    git(["add", "-A"])
    git(["commit", "-m", f"backup {datetime.datetime.now().strftime('%Y%m%d-%H%M%S')} batch {len(batch)}files"])
    r = git(["push", "origin", "master"])
    return r.returncode == 0

def main():
    log("="*50)
    log("本地全量→魔搭数据湖 慢速推送启动")
    if not setup_repo():
        return
    files = collect_files()
    prog = load_progress()
    prog["total"] = len(files) + len(prog["pushed"])
    total = len(files)
    log(f"待推送 {total} 个文件，每批≤{BATCH_SIZE}个，间隔{SLEEP}s")

    # 大文件单独小批
    batch = []
    batch_size = 0
    idx = 0
    for rel, full in sorted(files, key=lambda x: os.path.getsize(x[1])):
        sz = os.path.getsize(full)
        # 单文件>50MB直接跳过（超大媒体走媒体库）
        if sz > 50*1024*1024:
            log(f"跳过超大文件: {rel} ({sz//1024//1024}MB)")
            continue
        if len(batch) >= BATCH_SIZE or batch_size + sz > MAX_BATCH_SIZE_MB*1024*1024:
            ok = push_batch(batch)
            for b in batch:
                prog["pushed"].append(b[0])
            save_progress(prog)
            idx += len(batch)
            log(f"✅ 批完成 {idx}/{total} (本次{len(batch)}文件) {'成功' if ok else '失败'}")
            batch = []
            batch_size = 0
            time.sleep(SLEEP)
        batch.append((rel, full))
        batch_size += sz

    # 最后一批
    if batch:
        push_batch(batch)
        for b in batch:
            prog["pushed"].append(b[0])
        save_progress(prog)
        log(f"✅ 最后批完成，累计推送 {len(prog['pushed'])}/{prog['total']}")

    log(f"完成。已推送 {len(prog['pushed'])} 个文件，进度存于 PUSH-PROGRESS.json")

if __name__ == "__main__":
    main()
