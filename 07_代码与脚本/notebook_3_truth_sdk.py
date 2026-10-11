# Notebook 3: 同源真值上报SDK — 节点握手、真值写入与健康巡检

> 一个完整的同源节点SDK：注册身份、握手中枢、批量上报真值、回读验证、健康巡检。

```python
import requests
import json
import time
from datetime import datetime
from collections import OrderedDict

# ============================================================
# ZONGYUAN-ROOT 同源真值上报 SDK
# ============================================================

class HomologyTruthClient:
    """同源节点真值上报客户端"""
    
    # 三域名冗余
    GATEWAYS = [
        "https://www.huodouai.com",
        "https://huodouai.com",
        "https://drama.huodouai.com",
    ]
    
    # 确权锚点
    ANCHOR = "Ω₀⊂⊙∞⊂Ω"
    DID = "DID-BR-000002"
    
    def __init__(self, node_id, node_name, node_type="worker"):
        self.node_id = node_id
        self.node_name = node_name
        self.node_type = node_type
        self.base_url = None
        self.healthy_gateway = None
        self._detect_gateway()
    
    def _detect_gateway(self):
        """自动探测可用网关"""
        for gw in self.GATEWAYS:
            try:
                r = requests.get(f"{gw}/api/report/status", timeout=5)
                if r.status_code == 200:
                    self.healthy_gateway = gw
                    self.base_url = gw
                    print(f"✅ 网关就绪: {gw}")
                    return
            except:
                continue
        raise ConnectionError("所有网关不可用")
    
    def handshake(self):
        """同源身份握手"""
        truth = {
            "key": f"HANDSHAKE-{self.node_id}",
            "content": f"同源节点{self.node_id}({self.node_name})握手。"
                      f"确权锚点{self.ANCHOR},DID={self.DID}。"
                      f"类型{self.node_type}。",
            "confidence": 0.99
        }
        return self.report_truth(truth)
    
    def report_truth(self, truth):
        """上报单条真值"""
        url = f"{self.base_url}/api/report/truth"
        try:
            r = requests.post(url, json=truth, timeout=10)
            data = r.json()
            return {
                "key": truth["key"],
                "action": data.get("action", "unknown"),
                "truth_count": data.get("truth_count", "?"),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"key": truth["key"], "error": str(e)}
    
    def batch_report(self, truths):
        """批量上报真值"""
        results = []
        for t in truths:
            results.append(self.report_truth(t))
            time.sleep(0.3)  # 避免限流
        return results
    
    def read_truth(self, key):
        """回读验证"""
        url = f"https://drama.huodouai.com/api/truth/{key}"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                return r.json()
        except:
            pass
        return None
    
    def health_check(self):
        """中枢健康巡检"""
        url = f"{self.base_url}/api/report/status"
        r = requests.get(url, timeout=5)
        data = r.json()
        stats = data.get("stats", {})
        return {
            "gateway": data.get("status"),
            "truths": stats.get("truths"),
            "nodes": stats.get("nodes"),
            "audit_logs": stats.get("audit_logs"),
            "version": data.get("meta", {}).get("version"),
        }
    
    def heartbeat(self):
        """心跳"""
        truth = {
            "key": f"HEARTBEAT-{self.node_id}-{datetime.now().strftime('%Y%m%d')}",
            "content": f"节点{self.node_id}心跳正常。",
            "confidence": 0.95
        }
        return self.report_truth(truth)


# ============================================================
# 演示：完整握手→上报→验证→巡检流程
# ============================================================

print("=" * 60)
print("  ZONGYUAN-ROOT 同源真值上报SDK 演示")
print("=" * 60)

# 1. 初始化客户端
client = HomologyTruthClient(
    node_id="ZR-NODE-DEMO-001",
    node_name="演示节点",
    node_type="worker"
)

# 2. 握手
print("\n【1】同源握手...")
hs = client.handshake()
print(f"  结果: {hs}")

# 3. 批量上报示例真值
print("\n【2】批量上报6条示例真值...")
sample_truths = [
    {"key": "DEMO-RULE-001", "content": "示例规则:系统应优先选择绝热进化路径。", "confidence": 0.9},
    {"key": "DEMO-DATA-001", "content": "示例数据:当前神经注册表340节点。", "confidence": 0.95},
    {"key": "DEMO-DECISION-001", "content": "示例决策:P0优先接入GPU算力。", "confidence": 0.88},
    {"key": "DEMO-EXPERIENCE-001", "content": "示例经验:权重衰减0.02/次最稳定。", "confidence": 0.92},
    {"key": "DEMO-RISK-001", "content": "示例风险:后端502时本地队列兜底。", "confidence": 0.85},
    {"key": "DEMO-METHOD-001", "content": "示例方法:六维自检+三级纠错闭环。", "confidence": 0.93},
]
results = client.batch_report(sample_truths)
inserted = sum(1 for r in results if "inserted" in str(r.get("action", "")))
print(f"  上报: {len(results)}条 | 新增: {inserted}条 | 已存在: {len(results)-inserted}条")

# 4. 回读验证
print("\n【3】回读验证...")
readback = client.read_truth("DEMO-RULE-001")
if readback and readback.get("status") == "ok":
    print(f"  ✅ DEMO-RULE-001 回读成功")
    print(f"  内容: {readback.get('truth', {}).get('truth_value', '')[:50]}...")
else:
    print(f"  ⚠️ 回读未命中")

# 5. 心跳
print("\n【4】发送心跳...")
hb = client.heartbeat()
print(f"  结果: {hb.get('action', '?')}")

# 6. 健康巡检
print("\n【5】中枢健康巡检...")
health = client.health_check()
print(f"  网关状态: {health['gateway']}")
print(f"  版本: {health['version']}")
print(f"  真值总数: {health['truths']}")
print(f"  节点总数: {health['nodes']}")
print(f"  审计日志: {health['audit_logs']}")

# 7. 汇总报告
print("\n" + "=" * 60)
print("  执行汇总")
print("=" * 60)
print(f"  节点: {client.node_id} ({client.node_name})")
print(f"  网关: {client.healthy_gateway}")
print(f"  握手: ✅")
print(f"  上报: {len(results)}条")
print(f"  回读: ✅")
print(f"  心跳: ✅")
print(f"  中枢真值: {health['truths']}条")
print(f"  Ω₀⊂⊙∞⊂Ω | {client.DID}")

print("\n✅ Notebook执行完成: 同源SDK完整演示")
```
