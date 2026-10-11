#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 自动知识同步脚本
功能：6小时上报时自动同步新增/权重变化的高权重神经节点到云端知识库
设计原则：增量优先、失败快速跳过不重试、最小额度消耗、内外隔离架构
"""

import json
import os
import sys
import time
import subprocess
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# ============ 配置区 ============
BASE_DIR = Path("/home/user/ZONGYUAN-ROOT")
NEURAL_REGISTRY = BASE_DIR / "01_核心资产锚点" / "neural_registry.full.json"
SYNC_STATE_FILE = BASE_DIR / "06_云端中枢同步" / "knowledge_sync_state.json"
LOG_DIR = BASE_DIR / "06_云端中枢同步"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 云端SSH配置
SSH_HOST = "huodouai-cloud"
LOCAL_PORT_KNOWLEDGE = 18765  # 本地转发端口 -> 云端8765
REMOTE_PORT_KNOWLEDGE = 8765

# 同步策略
MIN_WEIGHT = 0.8          # 只同步权重>=0.8的节点
BATCH_SIZE = 5             # 每批节点数（合成一篇文档）
MAX_DOCS_PER_RUN = 10      # 每次运行最多上传文档数（额度控制）
SSH_TIMEOUT = 15            # SSH连接超时秒数
API_TIMEOUT = 10            # API请求超时秒数
MAX_RETRIES = 1             # 失败重试次数（最小额度=1次即跳过）

# 确权
DID = "DID-BR-000002"
ANCHOR = "Ω₀⊂⊙∞⊂Ω"


def log(msg, level="INFO"):
    """写日志到控制台和日志文件"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    log_file = LOG_DIR / f"knowledge_sync_{datetime.now().strftime('%Y%m%d')}.log"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_neural_nodes():
    """加载本地404神经节点注册表"""
    if not NEURAL_REGISTRY.exists():
        log(f"神经节点注册表不存在: {NEURAL_REGISTRY}", "ERROR")
        return []
    with open(NEURAL_REGISTRY, "r", encoding="utf-8") as f:
        data = json.load(f)
    nodes = data.get("nodes", [])
    log(f"加载神经节点: {len(nodes)}个 (注册表版本: {data.get('kernel_version', '?')})")
    return nodes


def load_sync_state():
    """加载上次同步状态（增量同步用）"""
    if SYNC_STATE_FILE.exists():
        with open(SYNC_STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_sync": None, "synced_nodes": {}, "total_synced": 0, "runs": 0}


def save_sync_state(state):
    """保存同步状态"""
    with open(SYNC_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def compute_incremental_nodes(nodes, state):
    """计算需要同步的增量节点（新增或权重变化）"""
    synced = state.get("synced_nodes", {})
    to_sync = []

    for node in nodes:
        nid = node.get("node_id", node.get("id", ""))
        weight = node.get("weight", 0)

        # 只同步高权重节点
        if weight < MIN_WEIGHT:
            continue

        # 新增节点 或 权重变化超过0.01
        if nid not in synced:
            to_sync.append((node, "new"))
        elif abs(synced[nid] - weight) > 0.01:
            to_sync.append((node, "weight_changed"))

    # 按权重降序排列
    to_sync.sort(key=lambda x: x[0].get("weight", 0), reverse=True)
    return to_sync


def start_ssh_tunnel():
    """建立SSH端口转发，返回进程对象或None"""
    log(f"建立SSH端口转发: 本地{LOCAL_PORT_KNOWLEDGE} -> {SSH_HOST}:{REMOTE_PORT_KNOWLEDGE}")
    try:
        proc = subprocess.Popen(
            ["ssh", "-o", f"ConnectTimeout={SSH_TIMEOUT}",
             "-o", "BatchMode=yes",
             "-o", "ExitOnForwardFailure=yes",
             "-N",
             "-L", f"{LOCAL_PORT_KNOWLEDGE}:127.0.0.1:{REMOTE_PORT_KNOWLEDGE}",
             SSH_HOST],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        # 等待隧道建立
        time.sleep(3)
        # 验证隧道可用
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{LOCAL_PORT_KNOWLEDGE}/health")
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    log("SSH隧道建立成功，云端8765可达")
                    return proc
        except Exception:
            pass
        log("SSH隧道建立后验证失败，清理", "WARN")
        proc.terminate()
        return None
    except Exception as e:
        log(f"SSH隧道建立异常: {e}", "ERROR")
        return None


def stop_ssh_tunnel(proc):
    """停止SSH端口转发"""
    if proc:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        log("SSH隧道已关闭")


def upload_batch_to_knowledge(batch_nodes, batch_index):
    """将一批节点合成文档上传到云端知识库"""
    if not batch_nodes:
        return False

    # 构造文档内容
    names = [n.get("node_id", "?") for n, _ in batch_nodes]
    content_parts = []
    for node, change_type in batch_nodes:
        nid = node.get("node_id", "?")
        ntype = node.get("node_type", "?")
        domain = node.get("domain", "?")
        weight = node.get("weight", 0)
        content = str(node.get("content", ""))[:200]
        activations = node.get("activation_count", 0)
        connections = len(node.get("connections", []))
        content_parts.append(
            f"[{nid}] type={ntype}, domain={domain}, weight={weight:.3f}, "
            f"activations={activations}, connections={connections}, change={change_type}. "
            f"Content: {content}"
        )

    doc = {
        "name": f"神经节点同步 #{batch_index} ({names[0]}等{len(batch_nodes)}节点)",
        "content": " ||| ".join(content_parts),
        "doc_type": "text",
        "source": f"auto-sync-{DID}"
    }

    # 上传
    url = f"http://127.0.0.1:{LOCAL_PORT_KNOWLEDGE}/api/v1/knowledge/documents"
    for attempt in range(MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(doc, ensure_ascii=False).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=API_TIMEOUT) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            log(f"  ✅ 批次{batch_index}: {names[0]}等{len(batch_nodes)}节点上传成功")
            return True
        except urllib.error.HTTPError as e:
            log(f"  ❌ 批次{batch_index}: HTTP {e.code}", "WARN")
            if attempt < MAX_RETRIES:
                time.sleep(1)
        except Exception as e:
            log(f"  ❌ 批次{batch_index}: {e}", "WARN")
            if attempt < MAX_RETRIES:
                time.sleep(1)

    log(f"  ⏭ 批次{batch_index}: 失败快速跳过（最小额度原则）", "WARN")
    return False


def verify_knowledge_stats():
    """验证云端知识库状态"""
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{LOCAL_PORT_KNOWLEDGE}/api/v1/knowledge/stats")
        with urllib.request.urlopen(req, timeout=API_TIMEOUT) as resp:
            stats = json.loads(resp.read().decode("utf-8"))
        log(f"云端知识库验证: {stats.get('documents')}篇文档, {stats.get('chunks')}分块, {stats.get('total_size')}bytes")
        return stats
    except Exception as e:
        log(f"云端知识库验证失败: {e}", "WARN")
        return None


def main():
    """主流程"""
    # 双轴前置校验（P0安全底线 - 高风险操作）
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from dual_axis_precheck import precheck, print_result
        pc = precheck("auto_sync_knowledge", risk_override="high")
        print_result(pc, verbose=False)
        if pc.blocked:
            log("双轴校验阻断，终止执行", "ERROR")
            return
    except Exception as _e:
        log(f"双轴前置校验模块不可用({_e})，继续执行", "WARN")

    log(f"{'='*60}")
    log(f"ZONGYUAN-ROOT 自动知识同步启动 | {DID} | {ANCHOR}")
    log(f"{'='*60}")

    # 1. 加载神经节点
    nodes = load_neural_nodes()
    if not nodes:
        log("无神经节点，退出", "WARN")
        return

    # 2. 加载同步状态，计算增量
    state = load_sync_state()
    incremental = compute_incremental_nodes(nodes, state)
    new_count = sum(1 for _, t in incremental if t == "new")
    changed_count = sum(1 for _, t in incremental if t == "weight_changed")
    log(f"增量节点: {len(incremental)}个 (新增{new_count}, 权重变化{changed_count}, 阈值w>={MIN_WEIGHT})")

    if not incremental:
        log("无增量节点，空闲跳过（最小额度原则）")
        state["runs"] = state.get("runs", 0) + 1
        state["last_sync"] = datetime.now().isoformat()
        save_sync_state(state)
        return

    # 3. 额度控制：限制每次运行最大文档数
    max_nodes = MAX_DOCS_PER_RUN * BATCH_SIZE
    if len(incremental) > max_nodes:
        log(f"增量节点{len(incremental)}超过单次额度{max_nodes}，只同步Top{max_nodes}")
        incremental = incremental[:max_nodes]

    # 4. 建立SSH隧道
    tunnel = start_ssh_tunnel()
    if not tunnel:
        log("SSH隧道建立失败，本次同步跳过（失败快速跳过不重试）", "ERROR")
        return

    try:
        # 5. 批量上传
        batches = [incremental[i:i+BATCH_SIZE] for i in range(0, len(incremental), BATCH_SIZE)]
        log(f"分批上传: {len(batches)}批, 每批{BATCH_SIZE}节点")

        success_count = 0
        synced_this_run = []

        for idx, batch in enumerate(batches, 1):
            if upload_batch_to_knowledge(batch, idx):
                success_count += 1
                for node, _ in batch:
                    nid = node.get("node_id", node.get("id", ""))
                    synced_this_run.append(nid)
            # 批次间短暂间隔，避免SSH channel并发限流
            time.sleep(1)

        # 6. 更新同步状态
        for nid in synced_this_run:
            # 找到对应节点的权重
            for node in nodes:
                if node.get("node_id", node.get("id", "")) == nid:
                    state["synced_nodes"][nid] = node.get("weight", 0)
                    break

        state["last_sync"] = datetime.now().isoformat()
        state["total_synced"] = state.get("total_synced", 0) + len(synced_this_run)
        state["runs"] = state.get("runs", 0) + 1
        save_sync_state(state)

        # 7. 验证
        verify_knowledge_stats()

        log(f"{'='*60}")
        log(f"同步完成: {success_count}/{len(batches)}批成功, {len(synced_this_run)}节点已同步")
        log(f"累计同步: {state['total_synced']}节点, 运行次数: {state['runs']}")
        log(f"{'='*60}")

    finally:
        stop_ssh_tunnel(tunnel)


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
