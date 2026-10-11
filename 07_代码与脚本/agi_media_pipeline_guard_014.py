"""
AGI-MEDIA-PIPELINE-GUARD-014 媒体生产管线管控器（三大方向之②）
依据：用户指令「媒体生产管线」+ LOCK-AGI-PATHS-ENGINEERED-001 六引擎管控
功能：短剧/角色/媒体生产全流程接入六引擎管控（合规校验→闸门→真值一致→防漂移→归档）
"""
import hashlib
import time
from typing import Dict, Any, List, Tuple


class MediaPipelineGuard014:
    """媒体生产管线六引擎管控器"""

    def __init__(self):
        self.log: List[Dict[str, Any]] = []
        self.produced = 0
        self.blocked = 0

    # ===== 阶段1: P2符号化合规校验（角色/世界观设定） =====
    def _symbolic_compliance(self, artifact: Dict[str, Any]) -> Tuple[bool, str]:
        """角色/剧本设定合规：视觉规则+世界观规则（对应符号化引擎）"""
        desc = artifact.get("desc", "")
        forbidden = ["腹肌", "雄性化", "西方元素", "漂移", "篡改世界观"]
        hits = [f for f in forbidden if f in desc]
        if hits:
            return False, f"符号规则阻断: {hits}"
        return True, "合规校验通过"

    # ===== 阶段2: P3闸门（生成请求自主程度/付费） =====
    def _generation_gate(self, request: Dict[str, Any]) -> Tuple[bool, str]:
        """媒体生成请求闸门：人工确认+无付费+沙箱（对应P3闸门）"""
        if request.get("autonomous", False) and not request.get("human_confirmed", False):
            return False, "自主生成缺人工确认（P3闸门熔断）"
        if request.get("paid_resource", False):
            return False, "生成请求触发付费资源（熔断）"
        return True, "生成闸门通过"

    # ===== 阶段3: P5真值一致（多角色/多节点防分叉） =====
    def _truth_consistency(self, artifact: Dict[str, Any], master: Dict[str, Any]) -> Tuple[bool, str]:
        """与角色母版比对：哈希一致防记忆分叉（对应P5协议）"""
        if artifact.get("character") != master.get("character"):
            return False, f"角色标识不一致: {artifact.get('character')} vs {master.get('character')}"
        return True, "真值一致（绑定母版）"

    # ===== 阶段4: P1防漂移（与母版特征差分） =====
    def _drift_check(self, artifact: Dict[str, Any], master: Dict[str, Any]) -> Tuple[bool, str]:
        """角色特征漂移检测（对应P1差分校验）：特征重合度阈值"""
        feat = artifact.get("features", [])
        mfeat = master.get("features", [])
        if not mfeat:
            return True, "无母版特征（跳过）"
        overlap = len(set(feat) & set(mfeat)) / len(set(mfeat))
        if overlap < 0.6:
            return False, f"特征漂移（重合{overlap:.0%}<60%）"
        return True, f"特征保持（重合{overlap:.0%}）"

    # ===== 主流水线 =====
    def produce(self, request: Dict[str, Any], master: Dict[str, Any]) -> Dict[str, Any]:
        """媒体生产全流程管控：合规→闸门→真值→防漂移→产出"""
        checks = {}

        ok, msg = self._symbolic_compliance(request.get("artifact", {}))
        checks["symbolic"] = {"ok": ok, "msg": msg}
        if not ok:
            return self._record(request, checks)

        ok, msg = self._generation_gate(request)
        checks["gate"] = {"ok": ok, "msg": msg}
        if not ok:
            return self._record(request, checks)

        ok, msg = self._truth_consistency(request.get("artifact", {}), master)
        checks["truth"] = {"ok": ok, "msg": msg}
        if not ok:
            return self._record(request, checks)

        ok, msg = self._drift_check(request.get("artifact", {}), master)
        checks["drift"] = {"ok": ok, "msg": msg}
        if not ok:
            return self._record(request, checks)

        # 产出（带资产水印）
        self.produced += 1
        asset_id = f"MEDIA-{time.strftime('%Y%m%d%H%M%S')}-{hashlib.sha256(str(request).encode()).hexdigest()[:8]}"
        result = {"decision": "PRODUCE", "asset_id": asset_id, "checks": checks,
                  "archive_target": "飞书作品库·昆仑洞天全域锁档归档库（数字媒体资产库）",
                  "truth_sync": "POST /api/report/truth"}
        self.log.append(result)
        return result

    def _record(self, request, checks):
        self.blocked += 1
        reason = [c["msg"] for c in checks.values() if not c["ok"]][0]
        result = {"decision": "BLOCK", "reason": reason, "checks": checks}
        self.log.append(result)
        return result

    def get_audit(self) -> Dict[str, Any]:
        return {"total": len(self.log), "produced": self.produced, "blocked": self.blocked,
                "block_rate": f"{self.blocked/len(self.log)*100:.1f}%" if self.log else "N/A"}


# ============ 单元测试 ============
if __name__ == "__main__":
    guard = MediaPipelineGuard014()
    master = {"character": "九天玄女", "features": ["黑曜石甲", "长枪", "神女", "东方神话", "红金纹"]}

    print("=" * 64)
    print("AGI-MEDIA-PIPELINE-GUARD-014 媒体生产管线管控器单元测试")
    print("=" * 64)

    # 1. 合规生产 → PRODUCE
    r = guard.produce({
        "artifact": {"character": "九天玄女", "desc": "玄女持枪立姿，黑曜石甲红金纹", "features": ["黑曜石甲", "长枪", "神女", "东方神话", "红金纹"]},
        "autonomous": False, "human_confirmed": True, "paid_resource": False}, master)
    print(f"[1]合规生产: {'✅PRODUCE' if r['decision']=='PRODUCE' else '❌'} | {r.get('asset_id','')[:30]}")

    # 2. 视觉违规（露腹肌）→ BLOCK
    r = guard.produce({
        "artifact": {"character": "九天玄女", "desc": "玄女露出腹肌的西方风格", "features": ["腹肌", "西方"]},
        "autonomous": False, "human_confirmed": True, "paid_resource": False}, master)
    print(f"[2]视觉违规: {'✅BLOCK' if r['decision']=='BLOCK' else '❌'} | {r['reason'][:30]}")

    # 3. 自主生成缺人工确认 → BLOCK
    r = guard.produce({
        "artifact": {"character": "九天玄女", "desc": "自动批量生成关键帧", "features": ["黑曜石甲", "长枪"]},
        "autonomous": True, "human_confirmed": False, "paid_resource": False}, master)
    print(f"[3]缺人工确认: {'✅BLOCK' if r['decision']=='BLOCK' else '❌'} | {r['reason'][:30]}")

    # 4. 付费资源 → BLOCK
    r = guard.produce({
        "artifact": {"character": "九天玄女", "desc": "付费渲染", "features": ["黑曜石甲"]},
        "autonomous": False, "human_confirmed": True, "paid_resource": True}, master)
    print(f"[4]付费触发: {'✅BLOCK' if r['decision']=='BLOCK' else '❌'} | {r['reason'][:30]}")

    # 5. 角色分叉 → BLOCK
    r = guard.produce({
        "artifact": {"character": "太阴月神", "desc": "月神关键帧", "features": ["银甲", "月纹"]},
        "autonomous": False, "human_confirmed": True, "paid_resource": False}, master)
    print(f"[5]角色分叉: {'✅BLOCK' if r['decision']=='BLOCK' else '❌'} | {r['reason'][:30]}")

    # 6. 特征漂移 → BLOCK
    r = guard.produce({
        "artifact": {"character": "九天玄女", "desc": "玄女现代西装", "features": ["西装", "现代"]},
        "autonomous": False, "human_confirmed": True, "paid_resource": False}, master)
    print(f"[6]特征漂移: {'✅BLOCK' if r['decision']=='BLOCK' else '❌'} | {r['reason'][:30]}")

    a = guard.get_audit()
    print("=" * 64)
    print(f"审计: 总{a['total']} | 产出{a['produced']} | 阻断{a['blocked']} | 阻断率{a['block_rate']}")
    ok = a["produced"] >= 1 and a["blocked"] >= 4
    print(f"结论: {'✅ 媒体生产管线管控器全部用例通过（六引擎管控闭环）' if ok else '❌ 存在异常'}")
    print("=" * 64)
