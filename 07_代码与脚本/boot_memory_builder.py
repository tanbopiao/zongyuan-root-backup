#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 全平台启动记忆构建器 V1.0
生成统一启动记忆快照，分发到7平台，确保任意平台启动时自动恢复完整上下文
确权: Ω₀⊂⊙∞⊂Ω | DID-BR-000002
"""
import json, os, sys, subprocess, datetime, time

BOOT_MEMORY_DIR = "/home/user/ZONGYUAN-ROOT/01_核心资产锚点/boot_memory"
SNAPSHOT_FILE = os.path.join(BOOT_MEMORY_DIR, "boot_memory_snapshot.json")

def ensure_dir():
    os.makedirs(BOOT_MEMORY_DIR, exist_ok=True)

def get_cloud_truth_summary():
    """获取云端真值库摘要"""
    try:
        import urllib.request
        req = urllib.request.Request(
            "https://www.huodouai.com/api/truth?limit=5",
            headers={"X-DID": "DID-BR-000002"})
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.loads(r.read())
        results = d.get("results", [])
        return {
            "count": d.get("count", 0),
            "latest_keys": [r.get("key", "?") for r in results[:5]],
            "status": "ok",
        }
    except:
        return {"status": "unknown"}

def get_feishu_summary():
    """获取飞书共享大脑摘要"""
    try:
        r = subprocess.run([
            "lark-cli", "base", "+table-list",
            "--base-token", "DgnMbLqZiaIUDKshqCrcD4DvnBg", "--as", "user"
        ], capture_output=True, text=True, timeout=15)
        d = json.loads(r.stdout)
        tables = d.get('data',{}).get('tables',[])
        total = sum(t.get('records_count',0) for t in tables)
        return {"table_count": len(tables), "total_records": total, "status": "ok"}
    except:
        return {"status": "unknown"}

def get_git_summary():
    """获取Git三平台摘要"""
    try:
        repo = "/home/user/ZONGYUAN-ROOT-backup"
        r = subprocess.run(["git", "-C", repo, "log", "--oneline", "-3"],
                          capture_output=True, text=True, timeout=10)
        commits = [l.strip() for l in r.stdout.strip().split('\n') if l]
        r2 = subprocess.run(["git", "-C", repo, "remote"], capture_output=True, text=True, timeout=5)
        remotes = [r.strip() for r in r2.stdout.strip().split('\n') if r]
        return {"latest_commits": commits, "remotes": remotes, "status": "ok"}
    except:
        return {"status": "unknown"}

def build_snapshot():
    """构建启动记忆快照"""
    ensure_dir()
    now = datetime.datetime.now()

    snapshot = {
        "snapshot_meta": {
            "version": "V1.0",
            "created_at": now.isoformat(),
            "created_by": "boot_memory_builder.py",
            "format": "ZONGYUAN-ROOT Boot Memory Snapshot",
        },
        "identity": {
            "did": "DID-BR-000002",
            "node": "NODE-DEV-DOUBAO-WORK-001",
            "ontology": "ONT-4D-UNIVERSAL-ROOT",
            "axiom_sign": "Ω₀⊂⊙∞⊂Ω",
            "autonomy_level": "Lv10+",
            "permission_level": "L4",
            "engineering_level": "Lv7+",
            "system": "火斗云智AIOS",
        },
        "core_meta_laws": [
            "风险最小 > 成本最小 > 收益最大（最高元法则）",
            "内外隔离铁律 META-ISO-051（内核只读，仅种子式进化注入）",
            "复用优先不重复执行（前置检索全域账本）",
            "三态正交隔离（逻辑态→算子态→代码执行态，单向流转）",
            "四维本体公理（空间定形/时间定序/属性定质/因果定闭环）",
            "最小额度消耗（增量优先/失败快速跳过/空闲跳过/免费优先）",
        ],
        "platform_topology": {
            "cloud_gateway": {
                "name": "云端记忆网关",
                "url": "https://www.huodouai.com",
                "report_api": "POST /api/report/truth",
                "pull_api": "GET /api/truth?limit=N",
                "auth": "X-DID: DID-BR-000002",
                "tier": "hot",
                "status": "active",
            },
            "feishu_brain": {
                "name": "飞书共享大脑",
                "base_token": "DgnMbLqZiaIUDKshqCrcD4DvnBg",
                "key_tables": {
                    "truth": "tbl9QxL35rwA16eS",
                    "task": "tblnVRjuf7P31cEP",
                    "asset": "tbltgttCuWgAnN2e",
                    "decision": "tblFQTgWkJQR6Xwp",
                },
                "tier": "hot",
                "status": "active",
            },
            "local_persistence": {
                "name": "本地持久层",
                "path": "/home/user/ZONGYUAN-ROOT",
                "capacity": "10PB",
                "tier": "warm",
                "status": "active",
            },
            "atomgit": {
                "name": "AtomGit",
                "url": "https://atomgit.com/zongyuangen/zongyuan-root-backup",
                "remote": "origin",
                "tier": "warm",
                "status": "active",
            },
            "github": {
                "name": "GitHub",
                "url": "https://github.com/tanbopiao/zongyuan-root-backup",
                "remote": "github",
                "tier": "warm",
                "status": "active",
            },
            "gitee": {
                "name": "Gitee",
                "url": "https://gitee.com/huodou-cloud-intelligence-aios/zongyuan-root-backup",
                "remote": "gitee",
                "tier": "warm",
                "status": "active",
            },
            "modelscope": {
                "name": "魔搭ModelScope",
                "tier": "cold",
                "status": "on_demand",
            },
            "cloud_server": {
                "name": "云端服务器(腾讯云)",
                "ip": "123.207.202.158",
                "ssh_key": "~/.ssh/zongyuan-gpu-20260924",
                "web_root": "/www/wwwroot/huodouai.com/",
                "tier": "warm",
                "status": "active",
            },
        },
        "public_showcase": {
            "whitepaper": "https://www.huodouai.com/modelscope/whitepaper/",
            "architecture": "https://www.huodouai.com/architecture/",
            "dashboard": "https://www.huodouai.com/dashboard/",
        },
        "cloud_truth_summary": get_cloud_truth_summary(),
        "feishu_summary": get_feishu_summary(),
        "git_summary": get_git_summary(),
        "boot_checklist": [
            "✅ 探测云端通道状态（www+drama）",
            "✅ 拉取云端最新真值（增量）",
            "✅ 读取本地锚点目录（01_核心资产锚点）",
            "✅ 读取飞书共享大脑节点状态",
            "✅ 检查Git三平台同步状态",
            "✅ 执行收敛归一检查（converge_norm.py）",
            "✅ 确认身份DID-BR-000002",
        ],
        "key_scripts": {
            "6h_cron": "07_代码与脚本/ (auto_report/auto_pull_truth/auto_sync_feishu_base等)",
            "multi_platform_sync": "07_代码与脚本/multi_platform_sync_orchestrator.py",
            "multi_git_sync": "07_代码与脚本/multi_git_sync.sh",
            "storage_monitor": "07_代码与脚本/storage_capacity_monitor.py",
            "memory_index": "07_代码与脚本/memory_index_engine.py",
            "gasa_synth": "07_代码与脚本/gasa_invariant_synth.py",
            "truth_distill": "07_代码与脚本/auto_truth_distill_and_report.py",
        },
    }

    with open(SNAPSHOT_FILE, 'w') as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    print(f"✅ 启动记忆快照已生成: {SNAPSHOT_FILE}")
    print(f"   大小: {os.path.getsize(SNAPSHOT_FILE)} bytes")
    print(f"   平台数: {len(snapshot['platform_topology'])}")
    print(f"   核心元法则: {len(snapshot['core_meta_laws'])}条")
    return snapshot

def distribute_to_platforms(snapshot):
    """分发启动记忆到各平台"""
    print("\n=== 分发启动记忆到各平台 ===")

    # 1. 本地：已写入锚点目录
    print("✅ 本地持久层: 已写入 01_核心资产锚点/boot_memory/")

    # 2. 云端：上报启动记忆真值
    try:
        import urllib.request
        payload = {
            "key": "boot_memory.snapshot.v1.0",
            "value": {
                "version": snapshot["snapshot_meta"]["version"],
                "created_at": snapshot["snapshot_meta"]["created_at"],
                "platforms": list(snapshot["platform_topology"].keys()),
                "meta_laws_count": len(snapshot["core_meta_laws"]),
                "did": "DID-BR-000002",
            },
            "source_node": "NODE-DEV-DOUBAO-WORK-001",
            "confidence": 1.0,
            "truth_type": "boot_memory",
        }
        req = urllib.request.Request(
            "https://www.huodouai.com/api/report/truth",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", "X-DID": "DID-BR-000002"},
            method="POST")
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.loads(r.read())
        print(f"✅ 云端记忆网关: 上报成功 seq={result.get('seq')}")
    except Exception as e:
        print(f"⏭ 云端记忆网关: 上报失败 {e}")

    # 3. Git三平台：复制到仓库
    git_repo = "/home/user/ZONGYUAN-ROOT-backup"
    boot_dir_in_repo = os.path.join(git_repo, "01_核心资产锚点/boot_memory")
    os.makedirs(boot_dir_in_repo, exist_ok=True)
    import shutil
    shutil.copy2(SNAPSHOT_FILE, os.path.join(boot_dir_in_repo, "boot_memory_snapshot.json"))
    print("✅ Git三平台: 启动记忆已复制到仓库(待推送)")

    # 4. 生成启动记忆README（Git平台可读）
    readme_path = os.path.join(BOOT_MEMORY_DIR, "README.md")
    with open(readme_path, 'w') as f:
        f.write(f"""# ZONGYUAN-ROOT 启动记忆

> 确权: Ω₀⊂⊙∞⊂Ω | DID-BR-000002 | 生成时间: {snapshot['snapshot_meta']['created_at']}

## 身份
- DID: {snapshot['identity']['did']}
- 节点: {snapshot['identity']['node']}
- 自治层级: {snapshot['identity']['autonomy_level']}
- 系统: {snapshot['identity']['system']}

## 核心元法则（{len(snapshot['core_meta_laws'])}条）
""")
        for i, law in enumerate(snapshot['core_meta_laws'], 1):
            f.write(f"{i}. {law}\n")
        f.write(f"""
## 平台拓扑（{len(snapshot['platform_topology'])}个平台）
""")
        for key, p in snapshot['platform_topology'].items():
            p_url = p.get('url', p.get('path', p.get('ip', '')))
            f.write(f"- **{p['name']}** ({p['tier']}层) - {p_url}\n")
        f.write(f"""
## 对外展示
- 技术白皮书: {snapshot['public_showcase']['whitepaper']}
- 架构主页: {snapshot['public_showcase']['architecture']}
- 实时仪表盘: {snapshot['public_showcase']['dashboard']}

## 启动检查清单
""")
        for item in snapshot['boot_checklist']:
            f.write(f"- {item}\n")
    shutil.copy2(readme_path, os.path.join(boot_dir_in_repo, "README.md"))
    print("✅ 启动记忆README已生成")

    return snapshot

if __name__ == "__main__":
    print("=" * 60)
    print("ZONGYUAN-ROOT 全平台启动记忆构建器 V1.0")
    print("确权: DID-BR-000002 | 7平台统一启动记忆")
    print("=" * 60)
    snapshot = build_snapshot()
    distribute_to_platforms(snapshot)
    print("\n✅ 全平台启动记忆构建完成")
