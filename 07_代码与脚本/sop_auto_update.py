#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT SOP 自动更新补全机制 v1.0
双向补全：
  A方向（云端→本地）：云端 SOP 有、本地缺失的章节/命令 → 自动补全到本地
  B方向（本地→云端）：本地有、云端缺失的新配置（9120端口） → 生成补丁清单，标记待部署
  C维度（版本/结构审计）：版本号、章节完整性、端口引用一致性审计
输出：补全报告 JSON + 补丁文件 + 同步真值
"""
import json, os, re, hashlib, urllib.request, subprocess
from datetime import datetime, timezone

BASE = "/home/user/Doubao/chats/38438491307070978"
AUDIT_DIR = os.path.join(BASE, "sop_audit")
LOCAL_SOP = os.path.join(BASE, "CLOUD-ACCESS-SOP-V1.1-LOCAL.md")
CLOUD_SOP = os.path.join(BASE, "sop_cloud_v11.md")
HANDSHAKE_SOP = os.path.join(BASE, "sop_cloud_handshake.md")
GATEWAY = "http://drama.huodouai.com:9120"
TOKEN = "zy-hap-1f0e55ca3f4682a09c1515614bd6a83ec7d04fb6feef795f760c625ff831e7f5"
REPORT_FILE = os.path.join(AUDIT_DIR, "sop_audit_report_latest.json")
PATCH_FILE = os.path.join(AUDIT_DIR, "sop_patch_cloud_deploy.md")

# 关键配置锚点（用于B方向补丁检测）
NEW_CONFIG_ANCHORS = [
    ("9120 上报端点", "POST :9120/api/truth/upsert"),
    ("9120 读取端点", "GET :9120/api/truths/"),
    ("9120 单条读取", "GET :9120/api/truth/<key>"),
    ("旧通道废弃", "/api/gateway/report 已废弃(502)"),
]

def read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""

def extract_sections(md):
    """提取 ## 章节标题"""
    return re.findall(r"^##\s+(.+)$", md, re.M)

def sha256_text(t):
    return hashlib.sha256(t.encode()).hexdigest()

def audit():
    local = read(LOCAL_SOP)
    cloud = read(CLOUD_SOP)
    handshake = read(HANDSHAKE_SOP)
    now = datetime.now(timezone.utc).isoformat()

    local_sections = extract_sections(local)
    cloud_sections = extract_sections(cloud)

    # A方向：云端有、本地缺的章节
    missing_in_local = [s for s in cloud_sections if s not in local_sections]
    # B方向：本地新配置在云端缺失
    cloud_missing_configs = []
    for name, anchor in NEW_CONFIG_ANCHORS:
        if anchor.replace(":9120", "") not in cloud.replace(":9120", ""):
            cloud_missing_configs.append(name)

    # 版本审计
    local_ver = re.search(r"版本[:：]\s*(V[\d.]+[^\s|]*)", local)
    cloud_ver = re.search(r"版本[:：]\s*(V[\d.]+[^\s|]*)", cloud)
    local_version = local_ver.group(1) if local_ver else "?"
    cloud_version = cloud_ver.group(1) if cloud_ver else "?"

    # 端口引用一致性
    local_has_9120 = "9120" in local
    cloud_has_9120 = "9120" in cloud

    report = {
        "audit_time": now,
        "local_version": local_version,
        "cloud_version": cloud_version,
        "local_sha256": sha256_text(local)[:16],
        "cloud_sha256": sha256_text(cloud)[:16],
        "local_size": len(local),
        "cloud_size": len(cloud),
        "direction_a_missing_in_local": missing_in_local,
        "direction_b_cloud_missing_configs": cloud_missing_configs,
        "port_9120_local": local_has_9120,
        "port_9120_cloud": cloud_has_9120,
        "action_needed": bool(missing_in_local or cloud_missing_configs),
        "verdict": "SYNCED" if (not missing_in_local and not cloud_missing_configs) else "PATCH_NEEDED"
    }

    # 生成B方向补丁（本地→云端待部署）
    if cloud_missing_configs:
        patch = [
            "# SOP V1.1 云端补丁（自动生成）｜ZONGYUAN-ROOT",
            "",
            f"生成时间：{now}",
            f"本地版本：{local_version}（已含9120新端口）",
            f"云端版本：{cloud_version}（仍引用旧通道）",
            "",
            "## 待部署变更（已通过飞书审批 7C334BA8-160E-4276-8EFF-4143BDFC71DD）",
            "",
        ]
        for name in cloud_missing_configs:
            patch.append(f"- [ ] {name}")
        patch.append("")
        patch.append("## 完整新SOP全文")
        patch.append("```")
        patch.append(local)
        patch.append("```")
        with open(PATCH_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(patch))

    # A方向自动补全：本地缺云端章节 → 提取云端章节全文并入本地（非仅引用）
    if missing_in_local:
        local_patch = [
            "",
            "---",
            f"## 附：云端SOP补全章节（{now[:10]} 自动补全）",
            "",
        ]
        # 按标题切分云端全文，提取每个缺失章节的完整内容
        cloud_lines = cloud.split("\n")
        heading_positions = []
        for i, line in enumerate(cloud_lines):
            if re.match(r"^##\s+", line):
                heading_positions.append(i)
        for sec in missing_in_local:
            start = None
            for j, pos in enumerate(heading_positions):
                title = re.sub(r"^##\s+", "", cloud_lines[pos]).strip()
                if title.strip() == sec.strip():
                    start = pos
                    end = heading_positions[j+1] if j+1 < len(heading_positions) else len(cloud_lines)
                    break
            if start is not None:
                section_content = "\n".join(cloud_lines[start:end]).strip()
                local_patch.append(f"### {sec}")
                local_patch.append("")
                local_patch.append("> 以下内容自动补全自云端 SOP：")
                local_patch.append(section_content)
                local_patch.append("")
            else:
                local_patch.append(f"### {sec}（云端原文未定位到，跳过）")
        with open(LOCAL_SOP, "a", encoding="utf-8") as f:
            f.write("\n".join(local_patch))

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return report

def report_cloud(report):
    payload = {
        "key": "SOP-AUTO-AUDIT-20260916",
        "node_id": "local-dev-001",
        "DID": "DID-BR-000002",
        "ROOT_OMEGA": "Ω-TAN-7-001",
        "truth_type": "operation_log",
        "truth_content": f"SOP自动更新补全机制v1.0审计：本地V{report['local_version']} vs 云端V{report['cloud_version']}，A方向缺失{len(report['direction_a_missing_in_local'])}章，B方向云端缺{len(report['direction_b_cloud_missing_configs'])}项新配置，结论{report['verdict']}"
    }
    req = urllib.request.Request(
        f"{GATEWAY}/api/truth/upsert",
        data=json.dumps(payload).encode(),
        headers={"X-Capture-Token": TOKEN, "Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)[:100]}

if __name__ == "__main__":
    report = audit()
    print(json.dumps({k: v for k, v in report.items() if k not in ("direction_a_missing_in_local", "direction_b_cloud_missing_configs")}, ensure_ascii=False, indent=2))
    print("A方向缺失章节:", report["direction_a_missing_in_local"])
    print("B方向云端缺配置:", report["direction_b_cloud_missing_configs"])
    r = report_cloud(report)
    print("云端上报:", json.dumps(r, ensure_ascii=False)[:150])
