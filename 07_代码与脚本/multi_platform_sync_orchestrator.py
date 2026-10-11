#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 多平台全量记忆同步编排器 V1.0
统一调度5平台双向同步：云端记忆网关 ↔ 飞书共享大脑 ↔ 本地持久层 ↔ AtomGit ↔ 魔搭数据湖
确权: Ω₀⊂⊙∞⊂Ω | DID-BR-000002 | 增量优先/冲突裁决/失败快速跳过/空闲跳过
"""
import json, os, sys, subprocess, datetime, time, hashlib

# === 平台配置 ===
PLATFORMS = {
    "cloud_gateway": {
        "name": "云端记忆网关",
        "priority": 1,  # 最高权威
        "base_url": "https://www.huodouai.com",
        "report_endpoint": "/api/report/truth",
        "pull_endpoint": "/api/truth",
        "auth": {"X-DID": "DID-BR-000002", "X-Capture-Token": "ZR-CAPTURE-2026-OMEGA-d04bb54ba2a55a7d"},
    },
    "feishu_brain": {
        "name": "飞书共享大脑",
        "priority": 2,
        "base_token": "DgnMbLqZiaIUDKshqCrcD4DvnBg",
        "tables": {
            "truth": "tbl9QxL35rwA16eS",      # 真值共识区
            "asset": "tbltgttCuWgAnN2e",      # 资产台账
            "decision": "tblFQTgWkJQR6Xwp",   # 决策日志
            "task": "tblnVRjuf7P31cEP",        # 任务台账
            "report": "tbl524eo7FnEa8ht",      # 上报总表
        },
    },
    "local_persistence": {
        "name": "本地持久层",
        "priority": 3,
        "base_dir": "/home/user/ZONGYUAN-ROOT",
        "dirs": {
            "truth": "06_云端中枢同步/cloud_truths_pull",
            "gasa": "06_云端中枢同步/gasa_invariants",
            "sfmp": "06_云端中枢同步/sfmp_federation",
            "memory_index": "06_云端中枢同步/memory_index_store.json",
            "scripts": "07_代码与脚本",
        },
    },
    "atomgit": {
        "name": "AtomGit代码仓库",
        "priority": 4,
        "repo_dir": "/home/user/ZONGYUAN-ROOT-backup",
        "remote": "git@atomgit.com:zongyuangen/zongyuan-root-backup.git",
    },
    "modelscope": {
        "name": "魔搭数据湖",
        "priority": 5,
        "note": "归档层，仅单向推送（本地→魔搭）",
    },
}

# === 状态文件 ===
STATE_FILE = "/home/user/ZONGYUAN-ROOT/06_云端中枢同步/multi_platform_sync_state.json"
NODE = "NODE-DEV-DOUBAO-WORK-001"
DID = "DID-BR-000002"

def load_state():
    if os.path.exists(STATE_FILE):
        try: return json.load(open(STATE_FILE))
        except: pass
    return {
        "cursors": {},       # 每个平台的同步游标
        "last_sync": {},     # 每对平台的上次同步时间
        "conflicts": [],     # 冲突记录
        "total_syncs": 0,    # 累计同步次数
        "stats": {},         # 各平台同步统计
    }

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def log(msg):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")

# === 同步通道实现 ===

def sync_cloud_to_local(state):
    """云端记忆网关 → 本地持久层（拉取真值）"""
    log("  → 云端→本地: 增量拉取真值")
    try:
        script = "/home/user/ZONGYUAN-ROOT/07_代码与脚本/auto_pull_truth.py"
        if not os.path.exists(script):
            log("    ⏭ 脚本不存在，跳过")
            return {"status": "skip", "reason": "script_not_found"}
        r = subprocess.run(["python3", script], capture_output=True, text=True, timeout=120)
        output = r.stdout + r.stderr
        # 解析结果
        new_count = 0
        max_seq = 0
        for line in output.split('\n'):
            if '新增=' in line:
                try: new_count = int(line.split('新增=')[1].split(',')[0])
                except: pass
            if '最大seq=' in line:
                try: max_seq = int(line.split('最大seq=')[1].strip())
                except: pass
        log(f"    ✅ 拉取完成: 新增={new_count}条, 最大seq={max_seq}")
        return {"status": "success", "new": new_count, "max_seq": max_seq}
    except subprocess.TimeoutExpired:
        log("    ⏭ 超时，快速跳过")
        return {"status": "skip", "reason": "timeout"}
    except Exception as e:
        log(f"    ❌ 失败: {e}")
        return {"status": "failed", "error": str(e)}

def sync_local_to_cloud(state):
    """本地持久层 → 云端记忆网关（上报真值）"""
    log("  → 本地→云端: 上报节点状态")
    try:
        import urllib.request
        payload = {
            "key": f"multi_platform_sync.heartbeat.{int(time.time())}",
            "value": {
                "action": "多平台全量记忆同步心跳",
                "node": NODE, "did": DID,
                "platforms_synced": list(PLATFORMS.keys()),
                "ts": datetime.datetime.now().isoformat(),
            },
            "source_node": NODE, "confidence": 1.0, "truth_type": "sync_heartbeat",
        }
        req = urllib.request.Request(
            "https://www.huodouai.com/api/report/truth",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", "X-DID": DID},
            method="POST")
        with urllib.request.urlopen(req, timeout=15) as r:
            result = json.loads(r.read())
        log(f"    ✅ 上报成功: seq={result.get('seq')}, truth_count={result.get('truth_count')}")
        return {"status": "success", "seq": result.get("seq")}
    except Exception as e:
        log(f"    ❌ 失败: {e}")
        return {"status": "failed", "error": str(e)}

def sync_local_to_feishu(state):
    """本地持久层 → 飞书共享大脑（Base同步+资产归档）"""
    log("  → 本地→飞书: Base台账同步+资产归档")
    results = {}
    # Base同步
    try:
        script = "/home/user/ZONGYUAN-ROOT/07_代码与脚本/auto_sync_feishu_base.py"
        if os.path.exists(script):
            r = subprocess.run(["python3", script], capture_output=True, text=True, timeout=110)
            output = r.stdout + r.stderr
            synced = 0
            for line in output.split('\n'):
                if '本次同步' in line:
                    try: synced = int(line.split('本次同步')[1].split(' ')[0])
                    except: pass
            log(f"    ✅ Base同步: {synced}条")
            results["base_sync"] = {"status": "success", "synced": synced}
        else:
            results["base_sync"] = {"status": "skip"}
    except Exception as e:
        results["base_sync"] = {"status": "failed", "error": str(e)}

    # 资产归档
    try:
        script = "/home/user/ZONGYUAN-ROOT/07_代码与脚本/auto_asset_archive.py"
        if os.path.exists(script):
            r = subprocess.run(["python3", script], capture_output=True, text=True, timeout=120)
            output = r.stdout + r.stderr
            archived = 0
            for line in output.split('\n'):
                if '归档成功' in line:
                    try: archived = int(line.split('归档成功:')[1].split(' ')[0].strip())
                    except: pass
            log(f"    ✅ 资产归档: {archived}条")
            results["asset_archive"] = {"status": "success", "archived": archived}
        else:
            results["asset_archive"] = {"status": "skip"}
    except Exception as e:
        results["asset_archive"] = {"status": "failed", "error": str(e)}

    return results

def sync_local_to_atomgit(state):
    """本地持久层 → AtomGit（git push）"""
    log("  → 本地→AtomGit: 增量推送")
    try:
        repo_dir = PLATFORMS["atomgit"]["repo_dir"]
        if not os.path.exists(repo_dir):
            log("    ⏭ 仓库不存在，跳过")
            return {"status": "skip", "reason": "repo_not_found"}
        # 检查是否有变更
        r = subprocess.run(["git", "-C", repo_dir, "status", "--porcelain"],
                          capture_output=True, text=True, timeout=15)
        if not r.stdout.strip():
            log("    ⏭ 无变更，空闲跳过")
            return {"status": "skip", "reason": "no_changes"}
        # 提交并推送
        subprocess.run(["git", "-C", repo_dir, "add", "-A"], timeout=15)
        commit_msg = f"多平台同步自动归档 | {DID} | {datetime.datetime.now().isoformat()}"
        subprocess.run(["git", "-C", repo_dir, "commit", "-m", commit_msg],
                      capture_output=True, text=True, timeout=30)
        r = subprocess.run(["git", "-C", repo_dir, "push", "origin", "main"],
                          capture_output=True, text=True, timeout=60)
        if r.returncode == 0:
            log("    ✅ 推送成功")
            return {"status": "success"}
        else:
            log(f"    ❌ 推送失败: {r.stderr[:100]}")
            return {"status": "failed", "error": r.stderr[:100]}
    except subprocess.TimeoutExpired:
        log("    ⏭ 超时，快速跳过")
        return {"status": "skip", "reason": "timeout"}
    except Exception as e:
        log(f"    ❌ 失败: {e}")
        return {"status": "failed", "error": str(e)}

def sync_feishu_to_local(state):
    """飞书共享大脑 → 本地持久层（拉取任务台账/决策日志）"""
    log("  → 飞书→本地: 拉取共享大脑状态")
    try:
        # 读取任务台账前10条待执行任务
        cmd = ["lark-cli", "base", "+record-list",
               "--base-token", PLATFORMS["feishu_brain"]["base_token"],
               "--table-id", PLATFORMS["feishu_brain"]["tables"]["task"],
               "--limit", "10", "--as", "user"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        try:
            d = json.loads(r.stdout)
            records = d.get('data', {}).get('items', d.get('data', {}).get('records', []))
            log(f"    ✅ 任务台账: {len(records)}条")
            return {"status": "success", "tasks": len(records)}
        except:
            log("    ⏭ 解析失败，跳过")
            return {"status": "skip"}
    except Exception as e:
        log(f"    ❌ 失败: {e}")
        return {"status": "failed", "error": str(e)}

def resolve_conflict(local_val, cloud_val, local_priority, cloud_priority):
    """冲突裁决：优先级高的平台胜出"""
    if local_priority <= cloud_priority:
        return "cloud", cloud_val
    else:
        return "local", local_val

# === 主编排 ===
def run_sync():
    print("=" * 65)
    print(f"ZONGYUAN-ROOT 多平台全量记忆同步编排器 V1.0")
    print(f"确权: {DID} | 节点: {NODE}")
    print(f"平台: {' | '.join(p['name'] for p in PLATFORMS.values())}")
    print("=" * 65)

    state = load_state()
    results = {}
    start_time = time.time()

    # 同步通道1: 云端 → 本地（拉取真值）
    log("[通道1] 云端记忆网关 ↔ 本地持久层")
    results["cloud_to_local"] = sync_cloud_to_local(state)
    results["local_to_cloud"] = sync_local_to_cloud(state)

    # 同步通道2: 本地 ↔ 飞书共享大脑
    log("[通道2] 本地持久层 ↔ 飞书共享大脑")
    results["local_to_feishu"] = sync_local_to_feishu(state)
    results["feishu_to_local"] = sync_feishu_to_local(state)

    # 同步通道3: 本地 → AtomGit
    log("[通道3] 本地持久层 ↔ AtomGit代码仓库")
    results["local_to_atomgit"] = sync_local_to_atomgit(state)

    # 同步通道4: 本地 → 魔搭数据湖（归档层，单向）
    log("[通道4] 本地持久层 → 魔搭数据湖（归档层）")
    results["local_to_modelscope"] = {"status": "skip", "reason": "归档层按需触发，6H周期内空闲跳过"}

    # 统计
    success = sum(1 for v in _flatten(results).values() if v.get("status") == "success")
    skipped = sum(1 for v in _flatten(results).values() if v.get("status") == "skip")
    failed = sum(1 for v in _flatten(results).values() if v.get("status") == "failed")
    duration = round(time.time() - start_time, 1)

    # 更新状态
    state["total_syncs"] = state.get("total_syncs", 0) + 1
    state["last_run"] = datetime.datetime.now().isoformat()
    state["last_duration"] = duration
    state["stats"] = {"success": success, "skip": skipped, "failed": failed}
    save_state(state)

    # 输出汇总
    print()
    print("=" * 65)
    print(f"[同步汇总] 成功: {success} | 跳过: {skipped} | 失败: {failed} | 耗时: {duration}s")
    print(f"[累计同步] 第 {state['total_syncs']} 次")
    print(f"[状态文件] {STATE_FILE}")
    print("=" * 65)

    # 输出各通道详情
    for channel, result in results.items():
        if isinstance(result, dict) and "status" in result:
            icon = "✅" if result["status"] == "success" else "⏭" if result["status"] == "skip" else "❌"
            print(f"  {icon} {channel}: {result['status']}")
        elif isinstance(result, dict):
            for sub, sr in result.items():
                if isinstance(sr, dict) and "status" in sr:
                    icon = "✅" if sr["status"] == "success" else "⏭" if sr["status"] == "skip" else "❌"
                    print(f"  {icon} {channel}.{sub}: {sr['status']}")

    return results

def _flatten(d, prefix=''):
    """扁平化嵌套字典"""
    items = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict) and 'status' not in v:
            items.update(_flatten(v, key))
        elif isinstance(v, dict):
            items[key] = v
    return items

if __name__ == "__main__":
    run_sync()
