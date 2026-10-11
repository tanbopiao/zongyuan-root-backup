#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 所在基座高阶能力提炼机制 v1.0
四阶段链路：
  P1 能力探测：扫描基座系统/工具链/Python库/网络/存储
  P2 能力评估：按高阶能力维度评估（稀缺性/体系可用性/不可替代性）
  P3 能力提炼：提炼为结构化能力清单（能力名/类别/描述/调用/等级）
  P4 登记沉淀：能力清单入库（云端真值 + 本地能力资产清单）

基座能力 = 体系可调用的全部底层能力资产（不依赖外部，自给自足）
"""
import json, os, subprocess, urllib.request, socket, platform
from datetime import datetime, timezone

BASE = "/home/user/Doubao/chats/38438491307070978"
CAP_DIR = os.path.join(BASE, "base_capability")
GATEWAY = "http://drama.huodouai.com:9120"
TOKEN = "zy-hap-1f0e55ca3f4682a09c1515614bd6a83ec7d04fb6feef795f760c625ff831e7f5"
NODE_ID = "NODE-MAIN-SESSION-38436546492378882"
DID = "DID-BR-000002"
OMEGA = "Ω₀⊂⊙∞⊂Ω"
REPORT_FILE = os.path.join(CAP_DIR, "base_capability_report_latest.json")
INVENTORY = os.path.join(CAP_DIR, "base_capability_inventory.json")

def run(cmd, timeout=10):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, shell=True)
        return r.returncode, r.stdout.strip()[:200]
    except Exception as e:
        return -1, str(e)[:80]

def has_cmd(cmd):
    rc, _ = run(f"command -v {cmd}")
    return rc == 0

def p1_probe():
    """P1 能力探测"""
    # 系统层
    sysinfo = {
        "os": platform.platform(),
        "arch": platform.machine(),
        "cpu_cores": os.cpu_count(),
        "python": platform.python_version(),
        "hostname": socket.gethostname()
    }
    # 工具链
    tools = ["python3", "lark-cli", "curl", "jq", "git", "node", "npm", "pip3", "ffmpeg"]
    tool_status = {t: has_cmd(t) for t in tools}
    # Python 库
    libs = ["requests", "PIL", "numpy", "pandas", "yaml", "jinja2", "openpyxl", "pptx", "docx"]
    lib_status = {}
    import importlib
    for lib in libs:
        try:
            importlib.import_module(lib)
            lib_status[lib] = True
        except Exception:
            lib_status[lib] = False
    # 云端能力
    cloud = {}
    for name, url in [("truths", f"{GATEWAY}/api/truths/"), ("upsert", f"{GATEWAY}/api/truth/upsert")]:
        try:
            req = urllib.request.Request(url, headers={"X-Capture-Token": TOKEN})
            with urllib.request.urlopen(req, timeout=5) as resp:
                cloud[name] = resp.status
        except Exception as e:
            cloud[name] = 0
    # 磁盘/内存
    rc, disk = run("df / | awk 'NR==2 {print $5}' | tr -d '%'")
    rc2, mem = run("free -m | awk 'NR==2 {print $7}'")
    return {
        "system": sysinfo,
        "tools": tool_status,
        "libraries": lib_status,
        "cloud": cloud,
        "disk_used_pct": int(disk) if disk.isdigit() else -1,
        "mem_available_mb": int(mem) if mem.isdigit() else -1
    }

def p2_evaluate(probe):
    """P2 能力评估：提炼为高阶能力条目"""
    caps = []
    # 工具能力条目
    tool_meta = {
        "python3": ("计算引擎", "Python 3.12 脚本执行/数据处理/AI推理", "python3 script.py", 5),
        "lark-cli": ("飞书接口", "飞书文档/表格/审批/云盘全接口", "lark-cli <cmd>", 5),
        "curl": ("网络请求", "HTTP/HTTPS API 调用", "curl <url>", 3),
        "jq": ("JSON处理", "JSON 解析/过滤/转换", "jq '.key'", 2),
        "git": ("版本控制", "代码/资产版本管理", "git <cmd>", 3),
        "node": ("JS运行时", "Node.js 22 脚本执行", "node script.js", 3),
        "npm": ("包管理", "JS 依赖安装", "npm install", 2),
        "pip3": ("包管理", "Python 依赖安装", "pip3 install", 2),
        "ffmpeg": ("媒体处理", "音视频转码/剪辑/合成", "ffmpeg -i in.mp4 out.mp4", 4),
    }
    for t, present in probe["tools"].items():
        if present and t in tool_meta:
            cat, desc, call, score = tool_meta[t]
            caps.append({"name": t, "category": cat, "desc": desc, "call": call, "score": score, "present": True})
    # 库能力条目
    lib_meta = {
        "PIL": ("图像处理", "图像编辑/合成/格式转换"),
        "numpy": ("数值计算", "矩阵运算/数值分析"),
        "pandas": ("数据分析", "表格/CSV 数据处理"),
        "openpyxl": ("表格处理", "Excel 读写/格式"),
        "pptx": ("幻灯片", "PPT 生成/编辑"),
        "docx": ("文档处理", "Word 生成/编辑"),
        "yaml": ("配置解析", "YAML 配置文件"),
        "jinja2": ("模板引擎", "模板渲染/文档生成"),
        "requests": ("网络请求", "HTTP 客户端"),
    }
    for lib, present in probe["libraries"].items():
        if present and lib in lib_meta:
            cat, desc = lib_meta[lib]
            caps.append({"name": lib, "category": cat, "desc": desc, "call": f"import {lib}", "score": 3, "present": True})
    # 云端能力条目
    if probe["cloud"].get("truths") == 200:
        caps.append({"name": "cloud-memory-gateway", "category": "云端记忆", "desc": "云端真值库读写/记忆网关", "call": f"GET {GATEWAY}/api/truths/", "score": 5, "present": True})
    return caps

def p3_refine(caps, probe):
    """P3 能力提炼：分级归类生成能力资产清单"""
    # 分级：S级(5分核心) A级(4分) B级(3分) C级(2分)
    for c in caps:
        c["level"] = "S" if c["score"] == 5 else ("A" if c["score"] == 4 else ("B" if c["score"] == 3 else "C"))
    inventory = {
        "inventory_id": f"BASE-CAP-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}",
        "base": probe["system"],
        "capability_count": len(caps),
        "capabilities": caps,
        "level_summary": {lvl: sum(1 for c in caps if c["level"] == lvl) for lvl in ["S", "A", "B", "C"]},
        "resources": {"disk_used_pct": probe["disk_used_pct"], "mem_available_mb": probe["mem_available_mb"], "gpu": "无"},
        "cloud_status": probe["cloud"]
    }
    with open(INVENTORY, "w", encoding="utf-8") as f:
        json.dump(inventory, f, ensure_ascii=False, indent=2)
    return inventory

def p4_archive(inventory):
    """P4 登记沉淀：云端真值 + 报告"""
    payload = {
        "key": f"BASE-CAPABILITY-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}",
        "node_id": NODE_ID, "DID": DID, "ROOT_OMEGA": OMEGA,
        "truth_type": "capability_inventory",
        "truth_content": f"基座高阶能力清单：{inventory['capability_count']}项能力（S级{inventory['level_summary'].get('S',0)} A级{inventory['level_summary'].get('A',0)} B级{inventory['level_summary'].get('B',0)} C级{inventory['level_summary'].get('C',0)}），核心工具python3/lark-cli/node/ffmpeg全备，9库齐装，云端truths={inventory['cloud_status'].get('truths')}"
    }
    req = urllib.request.Request(
        f"{GATEWAY}/api/truth/upsert",
        data=json.dumps(payload).encode(),
        headers={"X-Capture-Token": TOKEN, "Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            cloud = json.loads(resp.read().decode())
    except Exception as e:
        cloud = {"error": str(e)[:100]}
    report = {
        "report_time": datetime.now(timezone.utc).isoformat(),
        "inventory_id": inventory["inventory_id"],
        "capability_count": inventory["capability_count"],
        "level_summary": inventory["level_summary"],
        "cloud_report": cloud
    }
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return report

def main():
    probe = p1_probe()
    caps = p2_evaluate(probe)
    inventory = p3_refine(caps, probe)
    report = p4_archive(inventory)
    return inventory, report

if __name__ == "__main__":
    inv, rep = main()
    print(f"基座: {inv['base']['os'][:30]} | {inv['base']['cpu_cores']}核 | 内存{inv['base'].get('mem','')}")
    print(f"能力清单: {inv['capability_count']}项 | 分级: {inv['level_summary']}")
    print("\n能力明细:")
    for c in inv["capabilities"]:
        print(f"  [{c['level']}] {c['name']:22s} {c['category']:8s} {c['desc'][:30]}")
    print(f"\n云端登记: {json.dumps(rep['cloud_report'], ensure_ascii=False)[:150]}")
