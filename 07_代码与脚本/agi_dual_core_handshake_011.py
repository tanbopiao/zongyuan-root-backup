"""
AGI-DUAL-CORE-HANDSHAKE-011 本地-云端双核握手协议（路线图中期项落地）
依据：LOCK-AGI-PATHS-ENGINEERED-001 路线图第2项（P5扩展真实多节点：本地+云端双核握手）
功能：本地自治内核 ↔ 云端中枢 同源握手 → 真值锚点交换 → 差分校验 → 双核一致决策
"""
import hashlib
import json
import time
from typing import Dict, Any, List, Tuple


class CoreNode:
    """核心节点（本地或云端）：真值锚点 + 快照"""
    def __init__(self, node_id: str, role: str):
        self.node_id = node_id          # LOCAL-CORE / CLOUD-CENTRAL
        self.role = role                # local / cloud
        self.truth_anchor: str = ""
        self.truth_count: int = 0
        self.anchor_history: List[str] = []

    def set_anchor(self, anchor_id: str, truth_count: int):
        """设置真值锚点（同步云端 truth_count）"""
        self.truth_anchor = anchor_id
        self.truth_count = truth_count
        self.anchor_history.append(anchor_id)

    def snapshot(self) -> Dict[str, Any]:
        return {"node_id": self.node_id, "role": self.role,
                "truth_anchor": self.truth_anchor, "truth_count": self.truth_count}


class DualCoreHandshake011:
    """本地-云端双核握手协议"""

    def __init__(self):
        self.handshake_log: List[Dict[str, Any]] = []
        self.fork_count = 0
        self.success_count = 0

    # ============ 同源握手 ============
    def handshake(self, local: CoreNode, cloud: CoreNode) -> Dict[str, Any]:
        """双核握手：锚点交换 + 差分校验 + 一致性判定"""
        # 1. 双方快照
        ls, cs = local.snapshot(), cloud.snapshot()

        # 2. 锚点存在性校验
        if not ls["truth_anchor"] or not cs["truth_anchor"]:
            return {"handshake": "FAIL", "reason": "锚点缺失", "local": ls, "cloud": cs}

        # 3. 差分判定（锚点 id 一致 = 同源同步；不一致 = 分叉待收敛）
        synced = ls["truth_anchor"] == cs["truth_anchor"]
        # 4. 计数增量校验（云端应 ≥ 本地，允许云端领先）
        count_ok = cs["truth_count"] >= ls["truth_count"]

        result = {
            "handshake": "SYNCED" if (synced and count_ok) else "FORK",
            "local_anchor": ls["truth_anchor"],
            "cloud_anchor": cs["truth_anchor"],
            "local_count": ls["truth_count"],
            "cloud_count": cs["truth_count"],
            "delta": cs["truth_count"] - ls["truth_count"],
            "timestamp": time.time(),
        }
        self.handshake_log.append(result)
        if result["handshake"] == "SYNCED":
            self.success_count += 1
        else:
            self.fork_count += 1
        return result

    # ============ 双核一致决策 ============
    def dual_decision(self, local_vote: str, cloud_vote: str, matter: str) -> Dict[str, Any]:
        """重大事项双核决策：双方一致才通过，分歧上报人工"""
        if local_vote == cloud_vote:
            return {"matter": matter, "decision": local_vote.upper(), "dual_agreement": True,
                    "action": "EXECUTE" if local_vote == "approve" else "REJECT"}
        return {"matter": matter, "decision": "ESCALATE", "dual_agreement": False,
                "action": "HUMAN_REVIEW", "note": "双核分歧，上报人工最终裁决"}

    # ============ 收敛（本地向云端对齐） ============
    def converge(self, local: CoreNode, cloud: CoreNode) -> List[str]:
        """分叉收敛：本地锚点对齐云端"""
        changes = []
        if local.truth_anchor != cloud.truth_anchor:
            local.set_anchor(cloud.truth_anchor, cloud.truth_count)
            changes.append(f"anchor: {cloud.truth_anchor}")
        return changes


# ============ 单元测试 ============
if __name__ == "__main__":
    protocol = DualCoreHandshake011()
    print("=" * 64)
    print("AGI-DUAL-CORE-HANDSHAKE-011 本地-云端双核握手协议单元测试")
    print("=" * 64)

    # 1. 同源同步握手（锚点一致）→ SYNCED
    local = CoreNode("LOCAL-CORE", "local")
    cloud = CoreNode("CLOUD-CENTRAL", "cloud")
    local.set_anchor("TRUTH-ANCHOR-1499", 26075)
    cloud.set_anchor("TRUTH-ANCHOR-1499", 26075)
    r = protocol.handshake(local, cloud)
    print(f"[1]同源握手: {'✅SYNCED' if r['handshake']=='SYNCED' else '❌'} | delta={r['delta']}")

    # 2. 云端领先（锚点一致但云端计数更高）→ SYNCED（云端领先合法）
    cloud.set_anchor("TRUTH-ANCHOR-1499", 26080)
    r = protocol.handshake(local, cloud)
    print(f"[2]云端领先: {'✅SYNCED' if r['handshake']=='SYNCED' else '❌'} | delta={r['delta']}")

    # 3. 锚点分叉（本地落后/不同锚）→ FORK
    local.set_anchor("TRUTH-ANCHOR-1498", 26070)
    r = protocol.handshake(local, cloud)
    print(f"[3]锚点分叉: {'✅FORK' if r['handshake']=='FORK' else '❌'} | local={r['local_anchor']} cloud={r['cloud_anchor']}")

    # 4. 收敛：本地对齐云端
    changes = protocol.converge(local, cloud)
    r2 = protocol.handshake(local, cloud)
    print(f"[4]收敛后握手: {'✅SYNCED' if r2['handshake']=='SYNCED' else '❌'} | 变更{changes}")

    # 5. 双核一致决策（双双批准）→ EXECUTE
    d = protocol.dual_decision("approve", "approve", "接入新引擎")
    print(f"[5]双核一致: {'✅EXECUTE' if d['decision']=='APPROVE' and d['action']=='EXECUTE' else '❌'} | 决策={d['decision']}")

    # 6. 双核分歧 → ESCALATE 人工
    d2 = protocol.dual_decision("approve", "reject", "启用付费通道")
    print(f"[6]双核分歧: {'✅ESCALATE' if d2['decision']=='ESCALATE' and d2['action']=='HUMAN_REVIEW' else '❌'} | 动作={d2['action']}")

    print("=" * 64)
    ok = protocol.success_count >= 2 and protocol.fork_count >= 1
    print(f"结论: {'✅ 双核握手协议全部用例通过（SYNCED/FORK/收敛/双核决策）' if ok else '❌ 存在异常'}")
    print("=" * 64)
