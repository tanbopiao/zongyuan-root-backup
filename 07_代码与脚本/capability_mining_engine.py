#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 高阶能力挖掘与自动化任务规划引擎 V1.0
用途：扫描 lark-cli 24域430+命令未激活能力，实测可用性，自动创建机制待办，规划高价值自动化任务
确权：Ω₀⊂⊙∞⊂Ω｜DID-BR-000002
"""
import subprocess, json, os, re
from datetime import datetime, timezone

BASE = "/home/user/Doubao/chats/38438491307070978"
OUT_DIR = os.path.join(BASE, "capability_miner")
os.makedirs(OUT_DIR, exist_ok=True)

# 24 能力域
DOMAINS = ["im", "docs", "drive", "base", "wiki", "calendar", "task", "mail", "minutes",
           "sheets", "slides", "approval", "contact", "okr", "vc", "whiteboard", "markdown",
           "mindnotes", "api", "apps", "attendance", "note", "schema", "lark-cli"]

# 已激活域（此前确认可用）
ACTIVATED = {"im", "docs", "drive", "base", "wiki", "calendar", "sheets", "contact", "approval", "task"}
# 环境受限域
RESTRICTED = {"mail"}  # 无邮箱配置

def scan_domains():
    results = []
    for d in DOMAINS:
        try:
            r = subprocess.run(["lark-cli", d, "--help"], capture_output=True, text=True, timeout=10)
            cmds = re.findall(r'^\s+\+([a-z-]+)', r.stdout, re.M)
            status = "ACTIVATED" if d in ACTIVATED else ("RESTRICTED" if d in RESTRICTED else "DORMANT")
            results.append({"domain": d, "commands": len(cmds), "status": status, "sample": cmds[:5]})
        except Exception:
            results.append({"domain": d, "commands": 0, "status": "UNKNOWN", "sample": []})
    return results

def create_tasks(plan):
    """把规划的高价值待办创建为飞书任务"""
    created = []
    for t in plan:
        try:
            r = subprocess.run(["lark-cli", "task", "+create", "--summary", t["title"],
                                "--description", t["desc"], "--as", "user"],
                               capture_output=True, text=True, timeout=15)
            d = json.loads(r.stdout)
            if d.get("ok"):
                created.append({"title": t["title"], "guid": d["data"]["guid"], "priority": t["priority"]})
        except Exception:
            pass
    return created

def main():
    print("=== 高阶能力挖掘与自动化任务规划引擎 V1.0 ===")
    print("[1/4] 扫描 lark-cli 能力域...")
    scan = scan_domains()
    total_cmds = sum(s["commands"] for s in scan)
    dormant = [s for s in scan if s["status"] == "DORMANT"]
    print(f"  24域总命令: {total_cmds} | 已激活: {sum(1 for s in scan if s['status']=='ACTIVATED')} | 待激活: {len(dormant)} | 受限: {sum(1 for s in scan if s['status']=='RESTRICTED')}")
    print(f"  待激活域: {', '.join(s['domain'] for s in dormant)}")

    print("[2/4] 规划高价值自动化任务...")
    plan = [
        {"title": "高价值能力逐域激活：slides周报PPT", "desc": "slides13命令：每周体系汇报自动生成PPT，P4逐域激活第2项", "priority": "HIGH"},
        {"title": "高价值能力逐域激活：minutes会议转写", "desc": "minutes10命令：会议录音自动转写归档知识库，P4逐域激活第3项", "priority": "MED"},
        {"title": "高价值能力逐域激活：okr目标对齐", "desc": "okr22命令：体系目标季度对齐与进度追踪，P4逐域激活第4项", "priority": "MED"},
        {"title": "mail能力待邮箱配置激活", "desc": "mail30命令：机制日报自动发邮件，当前环境无邮箱配置需用户补充", "priority": "LOW"},
        {"title": "vc/whiteboard能力探索", "desc": "vc8+whiteboard2：会议记录与架构画板能力探索", "priority": "LOW"},
    ]
    created = create_tasks(plan)
    print(f"  已创建待办: {len(created)} 个")
    for c in created:
        print(f"    ✅ {c['title']} (guid={c['guid'][:8]})")

    print("[3/4] 生成能力挖掘报告...")
    ts = datetime.now(timezone.utc).strftime("%Y%m%d")
    report = {
        "report_id": f"CAPABILITY-MINE-{ts}",
        "did": "DID-BR-000002", "omega": "Ω₀⊂⊙∞⊂Ω",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_domains": len(DOMAINS), "total_commands": total_cmds,
        "activated": [s["domain"] for s in scan if s["status"] == "ACTIVATED"],
        "dormant": [s["domain"] for s in scan if s["status"] == "DORMANT"],
        "restricted": [s["domain"] for s in scan if s["status"] == "RESTRICTED"],
        "tasks_created": created,
        "summary": f"扫描24域{total_cmds}命令：已激活{sum(1 for s in scan if s['status']=='ACTIVATED')}域/待激活{len(dormant)}域/受限1域，自动创建{len(created)}个高价值待办任务"
    }
    with open(os.path.join(OUT_DIR, f"capability_mining_{ts}.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"  报告: {OUT_DIR}/capability_mining_{ts}.json")

    print("[4/4] 完成")
    print("  汇总:", report["summary"])

if __name__ == "__main__":
    main()
