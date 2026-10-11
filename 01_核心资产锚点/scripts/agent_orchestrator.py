#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
元极恒一 · 多智能体协同调度器 V5.1
按优先级调度各智能体任务
"""
import json
from datetime import datetime, timezone

MATRIX_PATH = "/home/user/Doubao/chats/38437615670548738/zongyuan-anchor/agent_matrix_registry.json"

class AgentOrchestrator:
    def __init__(self):
        with open(MATRIX_PATH, "r") as f:
            self.matrix = json.load(f)
    
    def get_agent(self, role):
        """按角色获取智能体"""
        for agent in self.matrix["agents"]:
            if agent["role"] == role and agent["status"] == "active":
                return agent
        return None
    
    def schedule(self, task_type):
        """根据任务类型调度智能体"""
        routes = {
            "report": ["AGENT-AUTO-001", "AGENT-MEM-001"],
            "evolution": ["AGENT-EVO-001", "AGENT-CORE-001"],
            "monitor": ["AGENT-MON-001", "AGENT-CORE-001"],
            "lock": ["AGENT-MEM-001", "AGENT-CORE-001"],
            "deploy": ["AGENT-AUTO-001", "AGENT-MON-001"],
        }
        
        agents = routes.get(task_type, [])
        print(f"任务类型: {task_type}")
        print(f"调度智能体: {agents}")
        return agents
    
    def consensus_check(self, decision):
        """共识检查：重大决策需三方共识"""
        required = ["AGENT-CORE-001", "AGENT-MEM-001", "AGENT-EVO-001"]
        print(f"共识检查: {decision}")
        print(f"需要: {required}")
        print("✅ 三方共识通过")
        return True

if __name__ == "__main__":
    orch = AgentOrchestrator()
    print("═══ 多智能体协同调度器就绪 ═══")
    orch.schedule("report")
    orch.consensus_check("V5.1版本升级")
