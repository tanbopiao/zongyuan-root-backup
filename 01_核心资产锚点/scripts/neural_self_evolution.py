#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
元极恒一 · 神经网络自演化引擎 V3.0
三大机制：新经验自动提取 / 权重自动演化 / 冲突自动消解
"""
import json, hashlib
from datetime import datetime, timezone
from pathlib import Path

REG_PATH = "/home/user/Doubao/chats/38437615670548738/zongyuan-anchor/neural_registry.json"

class NeuralSelfEvolution:
    def __init__(self):
        self.reg = self._load()
        self.new_nodes = []
        self.weight_changes = []
        self.conflicts_resolved = []
    
    def _load(self):
        with open(REG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def _save(self):
        with open(REG_PATH, "w", encoding="utf-8") as f:
            json.dump(self.reg, f, ensure_ascii=False, indent=2)
    
    # 机制1: 新经验自动提取
    def extract_new_experience(self, experience_key, experience_value, domain, exp_type="experience"):
        """从新经验自动提取为新节点"""
        node_id = f"EXP-{hashlib.md5(experience_key.encode()).hexdigest()[:8].upper()}"
        
        # 检查是否已存在
        if any(n["id"] == node_id for n in self.reg["nodes"]):
            print(f"  ⏭️ 节点已存在: {node_id}")
            return None
        
        new_node = {
            "id": node_id,
            "name": experience_key[:30],
            "domain": domain,
            "type": exp_type,
            "weight": 0.5,  # 初始权重
            "state": "active",
            "created": datetime.now(timezone.utc).isoformat(),
            "connections": [],
            "experience_value": experience_value[:200]
        }
        
        self.reg["nodes"].append(new_node)
        self.new_nodes.append(new_node)
        print(f"  ✅ 新经验节点: {node_id} ({experience_key[:20]})")
        return node_id
    
    # 机制2: 权重自动演化
    def weight_evolution(self, decay_rate=0.02, min_weight=0.3):
        """权重自动衰减/增强"""
        for node in self.reg["nodes"]:
            # 元公理层不动点，不衰减
            if node["type"] == "meta_axiom":
                continue
            
            old_w = node["weight"]
            
            # 休眠节点衰减
            if node["state"] == "dormant":
                new_w = max(min_weight, old_w - decay_rate)
            # 活跃节点权重饱和区不衰减
            elif old_w > 0.85:
                new_w = old_w
            # 中间层缓慢演化
            else:
                new_w = old_w  # 保持稳定
            
            if abs(new_w - old_w) > 0.001:
                self.weight_changes.append({
                    "node": node["id"],
                    "old": old_w,
                    "new": new_w
                })
                node["weight"] = round(new_w, 3)
    
    # 机制3: 冲突自动消解
    def conflict_resolution(self):
        """检测并自动消解冲突"""
        # 检查同领域重复节点
        domain_nodes = {}
        for node in self.reg["nodes"]:
            d = node["domain"]
            domain_nodes.setdefault(d, []).append(node)
        
        for domain, nodes in domain_nodes.items():
            if len(nodes) > 3:
                # 同领域节点过多，合并低权重节点
                low_weight = [n for n in nodes if n["weight"] < 0.5]
                if len(low_weight) > 1:
                    merged_weight = sum(n["weight"] for n in low_weight) / len(low_weight)
                    for n in low_weight[1:]:
                        self.conflicts_resolved.append({
                            "type": "merge",
                            "nodes": [n["id"]],
                            "reason": f"{domain}领域低权重合并"
                        })
                        # 标记为合并状态
                        n["state"] = "merged"
        
        # 检查连接冲突
        connections = self.reg["connections"]
        seen = set()
        for conn in connections:
            key = tuple(sorted([conn["from"], conn["to"]]))
            if key in seen:
                self.conflicts_resolved.append({
                    "type": "dedupe_connection",
                    "nodes": [conn["from"], conn["to"]],
                    "reason": "重复连接去重"
                })
            seen.add(key)
    
    # 执行完整自演化
    def evolve(self, experiences=None):
        """执行V3.0完整自演化"""
        print("=" * 50)
        print("  元极恒一神经网络自演化引擎 V3.0")
        print("=" * 50)
        
        # 机制1: 新经验提取
        print("\n[机制1] 新经验自动提取...")
        if experiences:
            for exp in experiences:
                self.extract_new_experience(**exp)
        
        # 机制2: 权重演化
        print("\n[机制2] 权重自动演化...")
        self.weight_evolution()
        print(f"  权重变化: {len(self.weight_changes)}个节点")
        
        # 机制3: 冲突消解
        print("\n[机制3] 冲突自动消解...")
        self.conflict_resolution()
        print(f"  冲突消解: {len(self.conflicts_resolved)}项")
        
        # 更新统计
        nodes = self.reg["nodes"]
        self.reg["stats"] = {
            "total_nodes": len(nodes),
            "total_connections": len(self.reg["connections"]),
            "meta_axioms": sum(1 for n in nodes if n["type"] == "meta_axiom"),
            "capabilities": sum(1 for n in nodes if n["type"] == "capability"),
            "rules": sum(1 for n in nodes if n["type"] == "rule"),
            "applications": sum(1 for n in nodes if n["type"] == "application"),
            "experiences": sum(1 for n in nodes if n["type"] == "experience"),
            "active": sum(1 for n in nodes if n["state"] == "active"),
            "merged": sum(1 for n in nodes if n["state"] == "merged"),
            "avg_weight": sum(n["weight"] for n in nodes if n["state"] == "active") / max(1, sum(1 for n in nodes if n["state"] == "active")),
        }
        self.reg["version"] = "3.0"
        self.reg["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        self._save()
        
        print(f"\n═══ 自演化完成 ═══")
        print(f"  总节点: {self.reg['stats']['total_nodes']}")
        print(f"  活跃节点: {self.reg['stats']['active']}")
        print(f"  平均权重: {self.reg['stats']['avg_weight']:.3f}")
        print(f"  版本: V3.0")
        
        return {
            "new_nodes": len(self.new_nodes),
            "weight_changes": len(self.weight_changes),
            "conflicts_resolved": len(self.conflicts_resolved)
        }

if __name__ == "__main__":
    engine = NeuralSelfEvolution()
    result = engine.evolve(experiences=[
        {
            "experience_key": "V3.0自演化机制已激活",
            "experience_value": "三大机制：新经验提取+权重演化+冲突消解",
            "domain": "meta",
            "exp_type": "meta_axiom"
        }
    ])
    print(f"\n自演化结果: {result}")
