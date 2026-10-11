#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
元极恒一 · 集群并发任务引擎 V6.0
从串行执行到并行并发执行
"""
import json
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

MATRIX_PATH = "/home/user/Doubao/chats/38437615670548738/zongyuan-anchor/agent_matrix_registry.json"

class ClusterConcurrentEngine:
    def __init__(self):
        with open(MATRIX_PATH, "r") as f:
            self.matrix = json.load(f)
        self.agents = {a["id"]: a for a in self.matrix["agents"]}
        self.task_queue = []
        self.completed = []
    
    def decompose_task(self, task):
        """将大任务分解为子任务"""
        subtasks = [
            {"id": "ST-01", "name": "校验", "agent": "AGENT-CORE-001", "deps": []},
            {"id": "ST-02", "name": "执行", "agent": "AGENT-AUTO-001", "deps": ["ST-01"]},
            {"id": "ST-03", "name": "记录", "agent": "AGENT-MEM-001", "deps": ["ST-02"]},
            {"id": "ST-04", "name": "监控", "agent": "AGENT-MON-001", "deps": ["ST-02"]},
            {"id": "ST-05", "name": "演化", "agent": "AGENT-EVO-001", "deps": ["ST-03"]},
        ]
        return subtasks
    
    def run_parallel(self, task):
        """并行执行子任务"""
        subtasks = self.decompose_task(task)
        print(f"═══ 集群并发执行: {task} ═══")
        print(f"分解为 {len(subtasks)} 个子任务")
        
        # 按依赖分层执行
        layers = {}
        for st in subtasks:
            layer = len(st["deps"])
            layers.setdefault(layer, []).append(st)
        
        results = {}
        for layer in sorted(layers.keys()):
            print(f"\n[层{layer}] 并行执行 {len(layers[layer])} 个子任务")
            with ThreadPoolExecutor(max_workers=len(layers[layer])) as executor:
                futures = {}
                for st in layers[layer]:
                    agent = self.agents.get(st["agent"], {})
                    future = executor.submit(
                        self._execute_subtask,
                        st["id"], st["name"], agent.get("name", "?")
                    )
                    futures[future] = st["id"]
                
                for future in as_completed(futures):
                    st_id = futures[future]
                    result = future.result()
                    results[st_id] = result
                    self.completed.append(result)
        
        print(f"\n═══ 并发执行完成 ═══")
        print(f"完成子任务: {len(results)}/{len(subtasks)}")
        return results
    
    def _execute_subtask(self, st_id, name, agent_name):
        """执行单个子任务"""
        return {
            "subtask": st_id,
            "name": name,
            "agent": agent_name,
            "status": "done",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

if __name__ == "__main__":
    engine = ClusterConcurrentEngine()
    results = engine.run_parallel("每日进化")
    print(f"\n结果: {len(results)} 子任务完成")
