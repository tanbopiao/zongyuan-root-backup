#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 自动合并高价值任务·自动构建高价值任务机制 v1.0
任务价值治理引擎（Task Value Governance Engine）
核心：价值评估四维(VALUE-4) → 自动合并决策 → 自动构建提案

价值评估四维（每维 1-5 分）：
  V1 体系贡献度：任务对核心公理/机制的支撑强度
  V2 频率匹配度：执行频率 vs 任务时效需求（过频/过低都扣分）
  V3 资源效率：单次执行成本 × 频率（越省分越高）
  V4 不可替代性：是否被其他任务覆盖（独有性越高分越高）

合并规则：
  - 同域(domain) + 同频(schedule_group) → 建议合并为批次任务
  - 合并后释放配额 → 用于高价值新任务

构建规则：
  - 检测空白域（无任务覆盖的核心域）→ 生成高价值任务提案
"""
import json, os, hashlib
from datetime import datetime, timezone

BASE = "/home/user/Doubao/chats/38438491307070978"
GOV_DIR = os.path.join(BASE, "task_governance")
REPORT_FILE = os.path.join(GOV_DIR, "task_value_report_latest.json")

# 当前定时任务清单（手动维护，随体系演进更新）
TASKS = [
    {"id": "11767319220482", "title": "数字资产流水线自动巡检", "schedule": "0 */6 * * *", "domain": "asset", "freq_group": "6h", "script": "digital_asset 巡检", "desc": "数字资产全流程巡检", "embedded": []},
    {"id": "11767626940930", "title": "监控云端upload恢复并部署SOP V1.1", "schedule": "0 9 * * *", "domain": "cloud", "freq_group": "daily", "script": "upload 探测", "desc": "upload 恢复即部署 SOP", "embedded": ["sop_deploy"]},
    {"id": "11767628042242", "title": "同源协议环境探索上报", "schedule": "15 */6 * * *", "domain": "homology", "freq_group": "6h", "script": "homology_env_report.py", "desc": "六维环境探索上报", "embedded": []},
    {"id": "11792666126850", "title": "全域资产归档与台账汇总", "schedule": "0 3 * * *", "domain": "archive", "freq_group": "daily", "script": "kernel_lock.sh", "desc": "三端锁档归档汇总", "embedded": ["lock", "ledger"]},
    {"id": "11847169740290", "title": "云端记忆网关健康巡检", "schedule": "0 */6 * * *", "domain": "cloud", "freq_group": "6h", "script": "health_check", "desc": "云端健康+溯源校验", "embedded": ["health", "truth_audit"]},
    {"id": "11855630769922", "title": "最小内核沙盒存活守护", "schedule": "*/30 * * * *", "domain": "sandbox", "freq_group": "30m", "script": "sandbox_alive_guard.sh", "desc": "心跳+探针+自愈", "embedded": ["heartbeat", "probe", "self_heal"]},
    {"id": "11855935199490", "title": "SOP自动更新补全", "schedule": "0 */6 * * *", "domain": "sop", "freq_group": "6h", "script": "sop_auto_update.py", "desc": "SOP双向补全", "embedded": ["sop_audit", "sop_patch"]},
    {"id": "11880961995522", "title": "元法则月度同步", "schedule": "30 10 1 * *", "domain": "meta", "freq_group": "monthly", "script": "meta_sync", "desc": "元法则月度同步", "embedded": ["meta_sync"]},
    {"id": "11892787775234", "title": "自治内核全闭环·每日进化", "schedule": "0 6 * * *", "domain": "kernel", "freq_group": "daily", "script": "kernel_evolution", "desc": "每日全闭环进化", "embedded": ["self_check", "evolution", "correction"]},
    {"id": "11847169850114", "title": "同源节点神经网络同步进化", "schedule": "30 */6 * * *", "domain": "neural", "freq_group": "6h", "script": "node_neural_sync_evolve.py", "desc": "节点网络同步进化", "embedded": ["node_sync", "truth_share"]},
]

# 域权重（核心域优先）
DOMAIN_WEIGHT = {
    "kernel": 5, "homology": 5, "neural": 5, "sandbox": 5,
    "cloud": 4, "sop": 4, "archive": 4,
    "asset": 3, "meta": 3
}

def evaluate(task):
    """价值评估四维"""
    # V1 体系贡献度
    v1 = DOMAIN_WEIGHT.get(task["domain"], 2)
    # V2 频率匹配度：频率组 vs 域时效需求
    freq_demand = {
        "sandbox": "30m", "cloud": "6h", "sop": "6h", "neural": "6h",
        "homology": "6h", "asset": "6h", "kernel": "daily",
        "archive": "daily", "meta": "monthly"
    }
    want = freq_demand.get(task["domain"], "daily")
    v2 = 5 if task["freq_group"] == want else (4 if task["freq_group"] in ("6h", "daily") else 2)
    # V3 资源效率：高频轻量任务得分高
    v3 = 5 if task["freq_group"] == "30m" else (4 if task["freq_group"] == "6h" else 3)
    # V4 不可替代性：同域同频任务多则降低；内嵌能力越多越不可替代
    overlap = sum(1 for t in TASKS if t["domain"] == task["domain"] and t["freq_group"] == task["freq_group"])
    embedded_count = len(task.get("embedded", []))
    v4 = 5 if overlap == 1 else (3 if overlap == 2 else 2)
    v4 = min(5, v4 + min(embedded_count, 2))  # 内嵌能力提升不可替代性
    total = v1 + v2 + v3 + v4
    return {"v1": v1, "v2": v2, "v3": v3, "v4": v4, "total": total,
            "score": round(total / 20 * 100), "level": "HIGH" if total >= 16 else ("MED" if total >= 12 else "LOW")}

def merge_decision():
    """自动合并决策：同域同频任务合并"""
    groups = {}
    for t in TASKS:
        key = (t["domain"], t["freq_group"])
        groups.setdefault(key, []).append(t)
    merges = []
    for key, members in groups.items():
        if len(members) >= 2:
            merges.append({
                "domain": key[0], "freq": key[1],
                "members": [m["title"] for m in members],
                "ids": [m["id"] for m in members],
                "reason": f"同域同频任务 {len(members)} 个，可合并为单一批次任务",
                "quota_released": len(members) - 1
            })
    return merges

def build_proposal():
    """自动构建提案：检测空白域"""
    covered = {t["domain"] for t in TASKS}
    covered_caps = set()
    for t in TASKS:
        covered_caps.update(t.get("embedded", []))
    proposals = []
    # 核心空白域检测（domain + 内嵌能力联合判定）
    if "security" not in covered and "security" not in covered_caps:
        proposals.append({"domain": "security", "title": "内核安全审计", "freq": "daily",
                          "value": "HIGH", "reason": "安全审计域空白，需每日基线校验"})
    if "contract" not in covered and "contract" not in covered_caps:
        proposals.append({"domain": "contract", "title": "体系契约一致性校验", "freq": "daily",
                          "value": "MED", "reason": "多机制契约一致性需定期校验"})
    return proposals

def main():
    report = {
        "report_time": datetime.now(timezone.utc).isoformat(),
        "total_tasks": len(TASKS),
        "evaluations": {},
        "merge_decisions": merge_decision(),
        "build_proposals": build_proposal()
    }
    for t in TASKS:
        report["evaluations"][t["id"]] = {
            "title": t["title"], **evaluate(t)
        }
    # 统计
    levels = {}
    for v in report["evaluations"].values():
        levels[v["level"]] = levels.get(v["level"], 0) + 1
    report["level_summary"] = levels
    report["mergeable_count"] = sum(m["quota_released"] for m in report["merge_decisions"])
    report["buildable_count"] = len(report["build_proposals"])
    with open(REPORT_FILE, "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return report

if __name__ == "__main__":
    r = main()
    print(f"任务总数: {r['total_tasks']} | 等级分布: {r['level_summary']}")
    print(f"合并建议: {r['mergeable_count']} 个可释放配额 | 构建提案: {r['buildable_count']} 个")
    print("\n=== 价值评估 ===")
    for tid, ev in r["evaluations"].items():
        print(f"  [{ev['level']:4s}] {ev['score']:3d}分 {ev['title']}")
    print("\n=== 合并决策 ===")
    for m in r["merge_decisions"]:
        print(f"  {m['domain']}/{m['freq']}: {' + '.join(m['members'])} → 释放{m['quota_released']}配额")
    print("\n=== 构建提案 ===")
    for p in r["build_proposals"]:
        print(f"  [{p['value']}] {p['title']} ({p['reason']})")
