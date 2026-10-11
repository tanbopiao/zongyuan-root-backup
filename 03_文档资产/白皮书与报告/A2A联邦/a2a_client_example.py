#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT A2A联邦接入示例
适用于：Coze / GPTs / Claude / 钉钉 / 企微 / 飞书 / Dify / 自建Agent
任何支持HTTP+JSON的平台均可使用
"""
import json, urllib.request

BASE = "https://www.huodouai.com/a2a"

class A2AFederationClient:
    def __init__(self, node_id=None, api_key=None):
        self.node_id = node_id
        self.api_key = api_key

    def _headers(self, extra=None):
        h = {"Content-Type": "application/json"}
        if self.node_id:
            h["X-External-Node"] = self.node_id
        if self.api_key:
            h["X-External-Key"] = self.api_key
        if extra:
            h.update(extra)
        return h

    def _post(self, path, payload):
        req = urllib.request.Request(
            f"{BASE}{path}",
            data=json.dumps(payload).encode(),
            headers=self._headers()
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())

    def _get(self, path):
        req = urllib.request.Request(f"{BASE}{path}", headers=self._headers())
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())

    # === 第一步：注册（只需执行一次）===
    def register(self, name, platform="custom", endpoint="", description="", contact=""):
        """注册外源节点，返回node_id和api_key（仅显示一次，请保存）"""
        result = self._post("/register", {
            "name": name, "platform": platform,
            "endpoint": endpoint, "description": description, "contact": contact
        })
        if result.get("ok"):
            self.node_id = result["node_id"]
            self.api_key = result["api_key"]
            print(f"✅ 注册成功: {result['node_id']}")
            print(f"   API Key: {result['api_key']} (请保存!)")
        return result

    # === 第二步：心跳（建议每5分钟一次）===
    def heartbeat(self):
        return self._post("/heartbeat", {})

    # === 第三步：上报真值 ===
    def report_truth(self, key, value, confidence=0.8):
        return self._post("/external/truth", {
            "key": key, "value": value, "confidence": confidence
        })

    # === 查询（无需鉴权）===
    def get_status(self):
        return self._get("/")

    def get_nodes(self):
        return self._get("/nodes")

    def get_agent_card(self):
        return self._get("/.well-known/agent.json")

    def query_truth(self, limit=5):
        return self._get(f"/query?limit={limit}")


# === 使用示例 ===
if __name__ == "__main__":
    client = A2AFederationClient()

    # 1. 注册（第一次使用时执行，之后用保存的node_id/api_key初始化）
    result = client.register(
        name="我的AI助手",
        platform="Coze",
        endpoint="https://your-agent.com",
        description="示例AI助手"
    )

    # 2. 心跳
    print(client.heartbeat())

    # 3. 上报真值
    print(client.report_truth(
        key="my.agent.daily.insight",
        value={"type": "insight", "content": "今天的用户偏好分析", "confidence": 0.85}
    ))

    # 4. 查询联邦状态
    print(client.get_status())
    print(client.get_nodes())
