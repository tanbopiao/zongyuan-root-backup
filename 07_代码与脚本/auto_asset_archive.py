#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 全自动资产经验归档器 V1.0
扫描本地持久层新增/变更资产 → 分类 → 价值评估 → 自动写入共享大脑资产台账
同时将重要经验/教训写入决策日志
确权: Ω₀⊂⊙∞⊂Ω | DID-BR-000002 | 增量优先/失败快速跳过/空闲跳过
"""
import json, os, sys, subprocess, datetime, hashlib, time

# === 配置 ===
BASE_DIR = "/home/user/ZONGYUAN-ROOT"
STATE_FILE = "/home/user/ZONGYUAN-ROOT/06_云端中枢同步/asset_archive_state.json"
BASE_TOKEN = "DgnMbLqZiaIUDKshqCrcD4DvnBg"
ASSET_TABLE = "tbltgttCuWgAnN2e"   # 资产台账
DECISION_TABLE = "tblFQTgWkJQR6Xwp" # 决策日志
NODE = "NODE-DEV-DOUBAO-WORK-001"
DID = "DID-BR-000002"
MAX_ARCHIVE = 20  # 单次最多归档条数
SCAN_DAYS = 7     # 只扫描最近N天变更的文件

# 排除目录
EXCLUDE_DIRS = {'.git', '__pycache__', 'node_modules', '.ipynb_checkpoints', 'dist', 'build'}
# 高价值目录（优先归档）
HIGH_VALUE_DIRS = ['07_代码与脚本', '06_云端中枢同步', '01_核心资产锚点', '03_文档资产', '04_系统配置']
# 资产类型映射
TYPE_MAP = {
    '.py': '代码脚本', '.sh': '代码脚本', '.js': '代码脚本', '.ts': '代码脚本',
    '.html': '展示页面', '.md': '文档', '.txt': '文档', '.pdf': '文档',
    '.json': '配置/真值', '.yaml': '配置/真值', '.yml': '配置/真值', '.env': '配置/真值',
    '.png': '视觉资产', '.jpg': '视觉资产', '.webp': '视觉资产', '.svg': '视觉资产',
    '.mp4': '视频资产', '.webm': '视频资产',
}
# 元类分类
META_CLASS = {
    '07_代码与脚本': '工程资产', '06_云端中枢同步': '真值资产',
    '01_核心资产锚点': '内核资产', '03_文档资产': '文档资产',
    '04_系统配置': '配置资产', '02_知识库': '知识资产', '05_视觉资产': '视觉资产',
}

def load_state():
    if os.path.exists(STATE_FILE):
        try: return json.load(open(STATE_FILE))
        except: pass
    return {"archived": {}, "last_run": None, "total_archived": 0}

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def file_hash(path, mtime):
    """生成文件唯一标识（路径+mtime）"""
    return hashlib.md5(f"{path}:{mtime}".encode()).hexdigest()[:16]

def scan_new_assets(state):
    """扫描新增/变更资产"""
    now = time.time()
    cutoff = now - SCAN_DAYS * 86400
    candidates = []
    archived = state.get("archived", {})

    for root, dirs, files in os.walk(BASE_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for fname in files:
            fpath = os.path.join(root, fname)
            try:
                stat = os.stat(fpath)
                if stat.st_mtime < cutoff:
                    continue
                # 跳过空文件和超大文件(>50MB)
                if stat.st_size == 0 or stat.st_size > 50 * 1024 * 1024:
                    continue
                fh = file_hash(fpath, stat.st_mtime)
                if fh in archived:
                    continue
                # 计算价值分
                rel_path = os.path.relpath(fpath, BASE_DIR)
                value = calc_value(rel_path, stat.st_size, fname)
                candidates.append({
                    'path': fpath, 'rel_path': rel_path, 'name': fname,
                    'size': stat.st_size, 'mtime': stat.st_mtime,
                    'hash': fh, 'value': value,
                    'type': TYPE_MAP.get(os.path.splitext(fname)[1].lower(), '其他'),
                    'meta_class': get_meta_class(rel_path),
                })
            except (OSError, PermissionError):
                continue

    # 按价值分排序，高价值优先
    candidates.sort(key=lambda x: x['value'], reverse=True)
    return candidates[:MAX_ARCHIVE]

def calc_value(rel_path, size, fname):
    """计算资产价值分（0-100）"""
    score = 0
    # 目录权重
    for hd in HIGH_VALUE_DIRS:
        if rel_path.startswith(hd):
            score += 40
            break
    # 文件大小权重（适中大小价值高）
    if 1024 < size < 1024 * 1024:
        score += 20
    elif size >= 1024 * 1024:
        score += 15
    # 文件名关键词
    keywords = ['truth', 'gasa', 'sfmp', 'kernel', 'meta', 'whitepaper',
                'architecture', 'dashboard', 'bootstrap', 'sync', 'index',
                '真值', '不变量', '内核', '元法则', '白皮书', '架构', '仪表盘']
    for kw in keywords:
        if kw.lower() in fname.lower():
            score += 20
            break
    # 扩展名权重
    ext = os.path.splitext(fname)[1].lower()
    if ext in ['.py', '.sh', '.html', '.json']:
        score += 10
    return min(score, 100)

def get_meta_class(rel_path):
    """获取元类分类"""
    for prefix, cls in META_CLASS.items():
        if rel_path.startswith(prefix):
            return cls
    return '通用资产'

def write_asset_record(asset):
    """写入资产台账"""
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    fields = {
        "资产名称": asset['name'],
        "类型": asset['type'],
        "元类分类": asset['meta_class'],
        "状态": "已归档",
        "所属节点": NODE,
        "存储位置": asset['rel_path'],
        "更新时间": int(asset['mtime'] * 1000),
    }
    try:
        cmd = ["lark-cli", "base", "+record-upsert",
               "--base-token", BASE_TOKEN, "--table-id", ASSET_TABLE,
               "--json", json.dumps(fields, ensure_ascii=False), "--as", "user"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        return json.loads(r.stdout).get("ok", False)
    except Exception:
        return False

def write_experience_log(asset):
    """将高价值资产经验写入决策日志"""
    if asset['value'] < 60:
        return False  # 只记录高价值资产经验
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    fields = {
        "决策内容": f"资产自动归档: {asset['name']} ({asset['type']})",
        "决策类型": "资产归档",
        "状态": "已执行",
        "决策时间": int(time.time() * 1000),
        "决策依据": f"价值分={asset['value']}, 大小={asset['size']}B, 路径={asset['rel_path']}",
    }
    try:
        cmd = ["lark-cli", "base", "+record-upsert",
               "--base-token", BASE_TOKEN, "--table-id", DECISION_TABLE,
               "--json", json.dumps(fields, ensure_ascii=False), "--as", "user"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        return json.loads(r.stdout).get("ok", False)
    except Exception:
        return False

def main():
    print("=" * 60)
    print(f"ZONGYUAN-ROOT 全自动资产经验归档 V1.0")
    print(f"确权: {DID} | 节点: {NODE}")
    print("=" * 60)

    state = load_state()
    print(f"[状态] 已归档: {state.get('total_archived', 0)} 条 | 上次运行: {state.get('last_run', '首次')}")

    # 扫描新增资产
    candidates = scan_new_assets(state)
    print(f"[扫描] 发现 {len(candidates)} 条新增/变更资产（最近{SCAN_DAYS}天，价值排序Top{MAX_ARCHIVE}）")

    if not candidates:
        print("[结果] 无新增资产 → 空闲跳过，0消耗")
        state['last_run'] = datetime.datetime.now().isoformat()
        save_state(state)
        return

    # 逐一条目归档
    success = 0
    exp_logged = 0
    failed = 0
    for i, asset in enumerate(candidates):
        # 写入资产台账
        ok = write_asset_record(asset)
        if ok:
            success += 1
            state['archived'][asset['hash']] = {
                'path': asset['rel_path'], 'mtime': asset['mtime'],
                'archived_at': datetime.datetime.now().isoformat(),
                'value': asset['value'],
            }
            # 高价值资产同时写经验日志
            if write_experience_log(asset):
                exp_logged += 1
            print(f"  [{i+1}/{len(candidates)}] ✅ {asset['name']} | {asset['type']} | 价值={asset['value']}")
        else:
            failed += 1
            print(f"  [{i+1}/{len(candidates)}] ❌ {asset['name']} | 写入失败（快速跳过）")

    # 更新状态
    state['total_archived'] = state.get('total_archived', 0) + success
    state['last_run'] = datetime.datetime.now().isoformat()
    save_state(state)

    print()
    print("=" * 60)
    print(f"[汇总] 归档成功: {success} | 经验日志: {exp_logged} | 失败: {failed}")
    print(f"[汇总] 累计归档: {state['total_archived']} 条")
    print(f"[状态文件] {STATE_FILE}")
    print("=" * 60)

if __name__ == "__main__":
    main()
