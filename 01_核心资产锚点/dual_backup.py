#!/usr/bin/env python3
"""
ZONGYUAN-ROOT 本地↔魔搭双向备份 V1.0
本地核心资产 → 魔搭 zongyuan-root-achievements 仓库
魔搭14个活跃仓库 → 本地备份目录
"""
import os, json, datetime, subprocess, glob

LOCAL_ANCHOR = "/home/user/ZONGYUAN-ROOT/01_核心资产锚点"
BACKUP_DIR = "/home/user/ZONGYUAN-ROOT/02_魔搭备份镜像"
MODELSCOPE_TOKEN = "ms-673547d6-508b-4242-a862-85de112a3ce7"
TARGET_REPO = "zongyuanroot/zongyuan-root-achievements"

KEEP_REPOS = [
    "zongyuan-root-achievements","zongyuan-whitepaper","kunlun-ip","kunlun-world",
    "nuwa","xiwangmu","taiyin","jiutian","zongyuan-agent-framework","inference-api",
    "deploy-guide","docker","git-gitee","git-github"
]

def log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def backup_local_to_modelscope():
    """本地核心资产 → 魔搭仓库"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    # 收集核心JSON文件
    core_files = glob.glob(f"{LOCAL_ANCHOR}/*.json")
    log(f"本地核心资产: {len(core_files)}个JSON文件")

    # 打包成tar
    tar_path = f"/tmp/zongyuan-core-{datetime.datetime.now().strftime('%Y%m%d')}.tar.gz"
    subprocess.run(["tar","-czf",tar_path] + core_files, check=False)
    log(f"打包完成: {tar_path} ({os.path.getsize(tar_path)//1024}KB)")

    # 上传到魔搭
    try:
        from modelscope.hub.file_upload import upload_file
        upload_file(
            path_in_repo=f"backups/{os.path.basename(tar_path)}",
            repo_id=TARGET_REPO,
            file_path=tar_path,
            repo_type="model",
            token=MODELSCOPE_TOKEN
        )
        log(f"✅ 已上传到魔搭: {TARGET_REPO}/backups/")
        return True
    except Exception as e:
        log(f"❌ 上传失败: {str(e)[:100]}")
        return False

def backup_modelscope_to_local():
    """魔搭14个活跃仓库 → 本地镜像"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    success = 0
    for repo in KEEP_REPOS:
        try:
            from modelscope.hub.snapshot_download import snapshot_download
            local_dir = snapshot_download(
                f"zongyuanroot/{repo}",
                cache_dir=BACKUP_DIR,
                token=MODELSCOPE_TOKEN
            )
            success += 1
            log(f"  ✅ {repo}")
        except Exception as e:
            log(f"  ⚠️ {repo}: {str(e)[:60]}")
    log(f"魔搭→本地备份完成: {success}/{len(KEEP_REPOS)}个仓库")

def main():
    log("="*50)
    log("双向备份启动")
    log("="*50)

    log("\n[1/2] 本地 → 魔搭")
    backup_local_to_modelscope()

    log("\n[2/2] 魔搭 → 本地")
    backup_modelscope_to_local()

    log("\n✅ 双向备份完成")

if __name__ == "__main__":
    main()
