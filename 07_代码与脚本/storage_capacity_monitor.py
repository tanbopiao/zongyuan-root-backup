#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 多平台存储容量监控 V1.0
监控7平台存储容量，按热/温/冷/归档四层路由，超阈值告警
确权: Ω₀⊂⊙∞⊂Ω | DID-BR-000002
"""
import json, os, sys, subprocess, datetime, time

STATE_FILE = "/home/user/ZONGYUAN-ROOT/06_云端中枢同步/storage_capacity_state.json"

# === 平台容量基线 ===
PLATFORMS = {
    "cloud_gateway": {
        "name": "云端记忆网关",
        "tier": "hot",
        "capacity_gb": 5,        # 真值库预估5GB
        "warning_pct": 70,
        "unit": "真值条数",
        "max_records": 500000,
    },
    "feishu_brain": {
        "name": "飞书共享大脑",
        "tier": "hot",
        "capacity_gb": 10,       # 多维表格容量
        "warning_pct": 70,
        "unit": "记录条数",
        "max_records_per_table": 50000,
    },
    "local_persistence": {
        "name": "本地持久层",
        "tier": "warm",
        "capacity_gb": 10240,    # 10PB网络存储=10240GB
        "warning_pct": 50,
        "unit": "GB",
    },
    "cloud_server": {
        "name": "云端服务器(腾讯云)",
        "tier": "warm",
        "capacity_gb": 60,
        "warning_pct": 70,
        "unit": "GB",
    },
    "git_platforms": {
        "name": "Git三平台(AtomGit+GitHub+Gitee)",
        "tier": "warm",
        "capacity_gb": 5,         # 单仓库软限制5GB
        "warning_pct": 60,
        "unit": "GB",
        "max_file_size_mb": 100,
    },
    "modelscope": {
        "name": "魔搭ModelScope数据湖",
        "tier": "cold",
        "capacity_gb": 100,       # 数据集存储
        "warning_pct": 70,
        "unit": "GB",
    },
    "feishu_drive": {
        "name": "飞书云盘",
        "tier": "cold",
        "capacity_gb": 100,
        "warning_pct": 70,
        "unit": "GB",
    },
}

# === 四层存储路由规则 ===
TIER_ROUTING = {
    "hot": {
        "description": "热数据层：高频访问、低延迟、结构化",
        "platforms": ["云端记忆网关", "飞书共享大脑"],
        "content_types": ["真值JSON", "台账索引", "任务状态", "节点心跳", "决策日志"],
        "size_limit": "<1MB/条",
        "retention": "永久",
    },
    "warm": {
        "description": "温数据层：中频访问、代码文档、静态资源",
        "platforms": ["Git三平台", "官网静态页", "本地持久层文档"],
        "content_types": ["代码脚本", "技术文档", "HTML页面", "配置文件", "架构图"],
        "size_limit": "<100MB/文件",
        "retention": "永久(Git)",
    },
    "cold": {
        "description": "冷数据层：低频访问、大容量、多媒体资产",
        "platforms": ["魔搭ModelScope", "本地持久层视觉资产", "飞书云盘"],
        "content_types": ["视觉资产(PNG/WebP)", "视频资产(MP4)", "模型权重", "数据集", "大文件"],
        "size_limit": ">100MB/文件",
        "retention": "长期",
    },
    "archive": {
        "description": "归档层：几乎不访问、永久保存、审计合规",
        "platforms": ["魔搭归档数据集", "本地归档目录", "历史快照"],
        "content_types": ["历史真值快照", "GASA不变量历史", "审计日志", "过期版本", "熔断备份"],
        "size_limit": "不限",
        "retention": "永久只读",
    },
}

def load_state():
    if os.path.exists(STATE_FILE):
        try: return json.load(open(STATE_FILE))
        except: pass
    return {"history": [], "alerts": []}

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def check_local_storage():
    """检查本地持久层容量"""
    try:
        r = subprocess.run(["df", "-h", "/home/user/ZONGYUAN-ROOT"], capture_output=True, text=True, timeout=10)
        lines = r.stdout.strip().split('\n')
        if len(lines) >= 2:
            parts = lines[1].split()
            total = parts[1]
            used = parts[2]
            avail = parts[3]
            pct = int(parts[4].replace('%',''))
            return {"total": total, "used": used, "avail": avail, "used_pct": pct, "status": "ok"}
    except: pass
    return {"status": "unknown"}

def check_cloud_server():
    """检查云端服务器磁盘"""
    try:
        r = subprocess.run([
            "ssh", "-i", os.path.expanduser("~/.ssh/zongyuan-gpu-20260924"),
            "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
            "root@123.207.202.158", "df -h / | tail -1"
        ], capture_output=True, text=True, timeout=20)
        parts = r.stdout.strip().split()
        if len(parts) >= 5:
            pct = int(parts[4].replace('%',''))
            return {"total": parts[1], "used": parts[2], "avail": parts[3], "used_pct": pct, "status": "ok"}
    except: pass
    return {"status": "unknown"}

def check_feishu_brain():
    """检查飞书共享大脑记录数"""
    try:
        r = subprocess.run([
            "lark-cli", "base", "+table-list",
            "--base-token", "DgnMbLqZiaIUDKshqCrcD4DvnBg", "--as", "user"
        ], capture_output=True, text=True, timeout=20)
        d = json.loads(r.stdout)
        tables = d.get('data',{}).get('tables',[])
        total = sum(t.get('records_count',0) for t in tables)
        largest = max(tables, key=lambda x: x.get('records_count',0)) if tables else None
        return {
            "table_count": len(tables),
            "total_records": total,
            "largest_table": largest.get('name') if largest else None,
            "largest_count": largest.get('records_count') if largest else 0,
            "status": "ok",
        }
    except: pass
    return {"status": "unknown"}

def check_git_repo():
    """检查Git仓库大小和大文件"""
    try:
        repo = "/home/user/ZONGYUAN-ROOT-backup"
        r = subprocess.run(["du", "-sh", repo], capture_output=True, text=True, timeout=10)
        size = r.stdout.split()[0] if r.stdout else "unknown"
        # 大文件检查
        r2 = subprocess.run(["find", repo, "-type", "f", "-size", "+10M"],
                           capture_output=True, text=True, timeout=10)
        large_files = [f for f in r2.stdout.strip().split('\n') if f]
        return {"size": size, "large_files": len(large_files), "large_file_list": large_files[:5], "status": "ok"}
    except: pass
    return {"status": "unknown"}

def check_cloud_truth():
    """检查云端真值库条数"""
    try:
        import urllib.request
        req = urllib.request.Request(
            "https://www.huodouai.com/api/truth?limit=1",
            headers={"X-DID": "DID-BR-000002"})
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.loads(r.read())
        return {"count": d.get("count", 0), "status": "ok"}
    except: pass
    return {"status": "unknown"}

def run_monitor():
    print("=" * 65)
    print("ZONGYUAN-ROOT 多平台存储容量监控 V1.0")
    print("确权: DID-BR-000002 | 四层路由: 热/温/冷/归档")
    print("=" * 65)

    results = {}
    alerts = []

    # 1. 本地持久层
    print("\n[1/6] 本地持久层...")
    results["local"] = check_local_storage()
    if results["local"].get("used_pct", 0) >= 50:
        alerts.append(f"⚠️ 本地持久层使用 {results['local']['used_pct']}%")
    print(f"  总量: {results['local'].get('total','?')} | 已用: {results['local'].get('used','?')} | 可用: {results['local'].get('avail','?')} | {results['local'].get('used_pct','?')}%")

    # 2. 云端服务器
    print("\n[2/6] 云端服务器(腾讯云60GB)...")
    results["cloud_server"] = check_cloud_server()
    if results["cloud_server"].get("used_pct", 0) >= 70:
        alerts.append(f"🔴 云端服务器磁盘 {results['cloud_server']['used_pct']}% (阈值70%)，建议清理")
    print(f"  总量: {results['cloud_server'].get('total','?')} | 已用: {results['cloud_server'].get('used','?')} | 可用: {results['cloud_server'].get('avail','?')} | {results['cloud_server'].get('used_pct','?')}%")

    # 3. 飞书共享大脑
    print("\n[3/6] 飞书共享大脑...")
    results["feishu"] = check_feishu_brain()
    if results["feishu"].get("largest_count", 0) >= 40000:
        alerts.append(f"⚠️ 飞书表 '{results['feishu']['largest_table']}' {results['feishu']['largest_count']}条，接近5万上限")
    print(f"  表数: {results['feishu'].get('table_count','?')} | 总记录: {results['feishu'].get('total_records','?')} | 最大表: {results['feishu'].get('largest_table','?')}({results['feishu'].get('largest_count','?')}条)")

    # 4. Git三平台
    print("\n[4/6] Git三平台仓库...")
    results["git"] = check_git_repo()
    if results["git"].get("large_files", 0) > 0:
        alerts.append(f"⚠️ Git仓库有{results['git']['large_files']}个>10MB文件，建议迁移到魔搭(冷数据层)")
    print(f"  仓库大小: {results['git'].get('size','?')} | 大文件(>10MB): {results['git'].get('large_files','?')}个")

    # 5. 云端真值库
    print("\n[5/6] 云端真值库...")
    results["cloud_truth"] = check_cloud_truth()
    print(f"  真值条数: {results['cloud_truth'].get('count','?')}")

    # 6. 魔搭数据湖（预估）
    print("\n[6/6] 魔搭ModelScope数据湖...")
    results["modelscope"] = {"status": "ok", "note": "按需触发，当前空闲", "tier": "cold"}
    print(f"  状态: 按需触发(冷数据层) | 适合: >100MB大文件/模型/视频/视觉资产")

    # 四层路由汇总
    print("\n" + "=" * 65)
    print("四层存储路由规划")
    print("=" * 65)
    for tier, info in TIER_ROUTING.items():
        print(f"\n【{tier.upper()}】{info['description']}")
        print(f"  平台: {', '.join(info['platforms'])}")
        print(f"  内容: {', '.join(info['content_types'][:4])}")
        print(f"  大小限制: {info['size_limit']} | 保留: {info['retention']}")

    # 告警汇总
    print("\n" + "=" * 65)
    if alerts:
        print(f"⚠️ 告警 ({len(alerts)}条):")
        for a in alerts:
            print(f"  {a}")
    else:
        print("✅ 所有平台容量正常，无告警")
    print("=" * 65)

    # 保存状态
    state = load_state()
    snapshot = {
        "timestamp": datetime.datetime.now().isoformat(),
        "results": results,
        "alerts": alerts,
    }
    state["history"].append(snapshot)
    if len(state["history"]) > 30:
        state["history"] = state["history"][-30:]
    state["latest"] = snapshot
    save_state(state)

    return snapshot

if __name__ == "__main__":
    run_monitor()
