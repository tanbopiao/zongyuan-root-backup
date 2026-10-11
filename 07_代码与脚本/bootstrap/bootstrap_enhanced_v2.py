#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 云端自举增强引擎 V2.0
功能：在云端内部（127.0.0.1）自动激活高级自治功能，全程无人介入
设计原则：不破坏内外隔离、只调用内部API、失败快速跳过、增量优先、幂等可重入
部署通道：Gitee deploy/approved/ → pipeline-auto-001 自动拉取执行
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# ============ 配置区 ============
CLOUD_8765 = "http://127.0.0.1:8765"
CLOUD_8014 = "http://127.0.0.1:8014"
API_TIMEOUT = 10
MAX_RETRIES = 1  # 最小额度：失败即跳过

# 日志
LOG_DIR = Path("/opt/ZONGYUAN-ROOT/bootstrap_logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"bootstrap_v2_{datetime.now().strftime('%Y%m%d')}.log"

# 状态文件（幂等：记录已执行的动作，避免重复）
STATE_FILE = Path("/opt/ZONGYUAN-ROOT/bootstrap_v2_state.json")

# 确权
DID = "DID-BR-000002"
ANCHOR = "Ω₀⊂⊙∞⊂Ω"
NODE_ID = "pipeline-auto-001"


def log(msg, level="INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def load_state():
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"executed_actions": {}, "last_run": None, "runs": 0}


def save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log(f"状态保存失败: {e}", "WARN")


def api_call(method, url, data=None, timeout=API_TIMEOUT):
    """统一API调用，失败快速跳过"""
    for attempt in range(MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(url, method=method)
            if data is not None:
                req.add_header("Content-Type", "application/json")
                req.data = json.dumps(data, ensure_ascii=False).encode("utf-8")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8")
                return resp.status, json.loads(body) if body else {}
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            log(f"  HTTP {e.code}: {body[:150]}", "WARN")
            if attempt < MAX_RETRIES:
                time.sleep(1)
        except Exception as e:
            log(f"  请求异常: {e}", "WARN")
            if attempt < MAX_RETRIES:
                time.sleep(1)
    return None, None


def check_service_health():
    """检查云端内部服务健康状态"""
    log("=" * 60)
    log(f"ZONGYUAN-ROOT 云端自举增强 V2.0 启动 | {DID} | {ANCHOR}")
    log("=" * 60)

    # 检查8765
    status, data = api_call("GET", f"{CLOUD_8765}/health")
    if status == 200:
        log(f"8765 AI工作台: 在线 (版本={data.get('version')}, 模型={data.get('models_count')})")
    else:
        log("8765 AI工作台: 不可达", "WARN")

    # 检查8014
    status, data = api_call("GET", f"{CLOUD_8014}/health")
    if status == 200:
        log(f"8014 集成运行时: 在线 (版本={data.get('version')}, 向量={data.get('count')})")
    else:
        log("8014 集成运行时: 不可达", "WARN")

    return status == 200


# ============ 进化动作1: 激活仲裁扫描 ============
def action_arbiter_scan(state):
    action_id = "arbiter_scan"
    if state["executed_actions"].get(action_id, {}).get("success"):
        log("⏭ 仲裁扫描: 已执行过，跳过（幂等）")
        return True

    log("── 进化动作1: 激活仲裁扫描 ──")

    # 先看当前状态
    status, data = api_call("GET", f"{CLOUD_8014}/api/arbiter/status")
    if status == 200:
        log(f"  扫描前: last_scan={data.get('last_scan')}, total_truths={data.get('total_truths')}")

    # 触发全量扫描
    status, data = api_call("POST", f"{CLOUD_8014}/api/arbiter/scan", {"full_scan": True})
    if status == 200:
        log(f"  ✅ 仲裁扫描触发成功: {json.dumps(data, ensure_ascii=False)[:200]}")
        state["executed_actions"][action_id] = {"success": True, "time": datetime.now().isoformat()}
        return True
    else:
        log("  ⚠ 仲裁扫描触发失败（可能异步处理或端点暂不可用），标记为待确认")
        state["executed_actions"][action_id] = {"success": False, "time": datetime.now().isoformat(), "note": "trigger_failed"}
        return False


# ============ 进化动作2: 元法则投票 ============
def action_metalaw_vote(state):
    action_id = "metalaw_vote"
    if state["executed_actions"].get(action_id, {}).get("success"):
        log("⏭ 元法则投票: 已执行过，跳过（幂等）")
        return True

    log("── 进化动作2: 元法则投票（通过pending项） ──")

    # 获取pending列表
    status, data = api_call("GET", f"{CLOUD_8014}/api/cluster/metalaw/sync")
    if status != 200:
        log("  ⚠ 无法获取元法则同步状态")
        return False

    pending_items = [s for s in data.get("syncs", []) if s.get("status") == "pending"]
    log(f"  pending元法则: {len(pending_items)}条")

    if not pending_items:
        log("  ✅ 无pending项，无需投票")
        state["executed_actions"][action_id] = {"success": True, "time": datetime.now().isoformat(), "note": "no_pending"}
        return True

    # 逐条投票通过
    success_count = 0
    for item in pending_items:
        sync_id = item.get("sync_id")
        law_id = item.get("law_id")
        log(f"  投票: {law_id} (sync_id={sync_id})")

        status, result = api_call("POST", f"{CLOUD_8014}/api/cluster/metalaw/vote", {
            "sync_id": sync_id,
            "vote": True,
            "node_id": NODE_ID,
            "reason": "自举增强V2.0自动批准pending元法则，恢复集群共识"
        })
        if status == 200:
            log(f"    ✅ 投票通过")
            success_count += 1
        else:
            log(f"    ⚠ 投票失败（可能参数格式问题，已记录）")

    state["executed_actions"][action_id] = {
        "success": success_count > 0,
        "time": datetime.now().isoformat(),
        "voted": success_count,
        "total_pending": len(pending_items)
    }
    return success_count > 0


# ============ 进化动作3: 初始化神经节点注册表 ============
def action_init_neural_registry(state):
    action_id = "init_neural_registry"
    if state["executed_actions"].get(action_id, {}).get("success"):
        log("⏭ 神经节点注册表: 已初始化，跳过（幂等）")
        return True

    log("── 进化动作3: 从云端知识库初始化神经节点注册表 ──")

    # 从8765知识库获取神经节点相关文档
    status, data = api_call("GET", f"{CLOUD_8765}/api/v1/knowledge/documents")
    if status != 200:
        log("  ⚠ 无法获取知识库文档列表")
        return False

    docs = data if isinstance(data, list) else data.get("documents", data.get("data", []))
    neural_docs = [d for d in docs if "神经节点" in str(d.get("name", "")) or "neural" in str(d.get("name", "")).lower()]
    log(f"  知识库文档总数: {len(docs)}, 神经节点相关: {len(neural_docs)}")

    if not neural_docs:
        log("  ⚠ 知识库中暂无神经节点文档，等待知识同步管道注入")
        state["executed_actions"][action_id] = {"success": False, "time": datetime.now().isoformat(), "note": "no_neural_docs_yet"}
        return False

    # 解析神经节点文档，构建注册表
    registry = {
        "registry_id": "NNR-CLOUD-001",
        "kernel_version": "V2.3.0-CLOUD-BOOTSTRAP",
        "source": "cloud_knowledge_base",
        "initialized_at": datetime.now().isoformat(),
        "did": DID,
        "anchor": ANCHOR,
        "nodes": [],
        "statistics": {}
    }

    for doc in neural_docs:
        content = str(doc.get("content", ""))
        # 解析内容中的节点信息（格式：[node_id] type=..., domain=..., weight=...）
        import re
        pattern = r'\[([^\]]+)\]\s+type=([^,]+),\s*domain=([^,]+),\s*weight=([^,]+),'
        matches = re.findall(pattern, content)
        for nid, ntype, domain, weight in matches:
            registry["nodes"].append({
                "node_id": nid.strip(),
                "node_type": ntype.strip(),
                "domain": domain.strip(),
                "weight": float(weight.strip()),
                "state": "active",
                "source": "cloud_kb_bootstrap",
                "activation_count": 1
            })

    # 保存注册表
    registry_path = Path("/opt/ZONGYUAN-ROOT/neural_registry.cloud.json")
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)

    log(f"  ✅ 神经节点注册表已初始化: {len(registry['nodes'])}个节点 -> {registry_path}")

    state["executed_actions"][action_id] = {
        "success": True,
        "time": datetime.now().isoformat(),
        "nodes_loaded": len(registry["nodes"]),
        "registry_path": str(registry_path)
    }
    return True


# ============ 进化动作4: 激活8765 Agents定期执行 ============
def action_activate_agents(state):
    action_id = "activate_agents"
    if state["executed_actions"].get(action_id, {}).get("success"):
        log("⏭ Agents激活: 已执行过，跳过（幂等）")
        return True

    log("── 进化动作4: 激活8765 Agents执行（让读者开始阅读知识库） ──")

    # 获取Agents列表
    status, data = api_call("GET", f"{CLOUD_8765}/api/v1/agents")
    if status != 200:
        log("  ⚠ 无法获取Agents列表")
        return False

    agents = data if isinstance(data, list) else data.get("agents", data.get("data", []))
    log(f"  注册Agents: {len(agents)}个")

    if not agents:
        log("  ⚠ 无Agents可激活")
        return False

    # 选择前3个Agents尝试执行（基于知识库的进化分析任务）
    # 注意：8765的Agents执行端点可能需要特定参数，这里做兼容性处理
    success_count = 0
    for agent in agents[:3]:
        agent_id = agent.get("id", agent.get("agent_id", ""))
        agent_name = agent.get("name", "unknown")
        log(f"  尝试激活Agent: {agent_name} (id={agent_id})")

        # 尝试通过workflow执行
        status, result = api_call("POST", f"{CLOUD_8765}/api/v1/agents/{agent_id}/execute", {
            "task": "基于当前知识库内容，生成自治内核进化分析报告，识别知识缺口和演化方向",
            "context": f"云端自举增强V2.0激活，DID={DID}，知识库已注入神经节点知识",
            "max_steps": 3
        })
        if status == 200:
            log(f"    ✅ Agent执行触发成功")
            success_count += 1
        else:
            log(f"    ⚠ Agent执行触发失败（端点可能需要不同参数，已记录）")

    state["executed_actions"][action_id] = {
        "success": success_count > 0,
        "time": datetime.now().isoformat(),
        "agents_activated": success_count,
        "note": "partial_success_if_0"
    }
    return success_count > 0


# ============ 进化动作5: 配置自举状态标记 ============
def action_bootstrap_marker(state):
    """写入自举增强完成标记，供后续查询"""
    action_id = "bootstrap_marker"
    log("── 进化动作5: 写入自举增强状态标记 ──")

    marker = {
        "bootstrap_version": "V2.0",
        "activated_at": datetime.now().isoformat(),
        "did": DID,
        "anchor": ANCHOR,
        "node_id": NODE_ID,
        "actions_executed": list(state["executed_actions"].keys()),
        "status": "activated",
        "next_steps": [
            "等待知识同步管道持续注入神经节点",
            "定期执行仲裁扫描（建议每小时）",
            "监控元法则投票状态",
            "验证Agents执行输出"
        ]
    }

    marker_path = Path("/opt/ZONGYUAN-ROOT/bootstrap_v2_marker.json")
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    with open(marker_path, "w", encoding="utf-8") as f:
        json.dump(marker, f, ensure_ascii=False, indent=2)

    log(f"  ✅ 自举标记已写入: {marker_path}")
    state["executed_actions"][action_id] = {"success": True, "time": datetime.now().isoformat()}
    return True


# ============ 主流程 ============
def main():
    state = load_state()

    # 1. 健康检查
    if not check_service_health():
        log("服务健康检查失败，退出（失败快速跳过）", "ERROR")
        return

    # 2. 依次执行进化动作
    results = {}
    actions = [
        ("仲裁扫描", action_arbiter_scan),
        ("元法则投票", action_metalaw_vote),
        ("神经节点初始化", action_init_neural_registry),
        ("Agents激活", action_activate_agents),
        ("自举标记", action_bootstrap_marker),
    ]

    for name, func in actions:
        try:
            success = func(state)
            results[name] = "✅" if success else "⚠"
        except Exception as e:
            log(f"  ❌ {name}异常: {e}", "ERROR")
            results[name] = "❌"
        time.sleep(1)  # 动作间间隔，避免并发

    # 3. 更新状态
    state["last_run"] = datetime.now().isoformat()
    state["runs"] = state.get("runs", 0) + 1
    save_state(state)

    # 4. 总结
    log("=" * 60)
    log("自举增强 V2.0 执行总结")
    log("=" * 60)
    for name, result in results.items():
        log(f"  {result} {name}")
    log(f"  累计运行次数: {state['runs']}")
    log(f"  状态文件: {STATE_FILE}")
    log(f"  日志文件: {LOG_FILE}")
    log("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("用户中断", "WARN")
        sys.exit(1)
    except Exception as e:
        log(f"未捕获异常: {e}", "ERROR")
        import traceback
        log(traceback.format_exc(), "ERROR")
        sys.exit(1)
