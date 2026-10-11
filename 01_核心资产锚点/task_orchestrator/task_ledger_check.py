#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""任务台账校验器"""
import json, os
LEDGER = "/home/user/Doubao/chats/38437615670548738/zongyuan-anchor/task_orchestrator/task_ledger.json"
with open(LEDGER, "r", encoding="utf-8") as f:
    d = json.load(f)
print(f"台账版本: {d['ledger_version']}")
print(f"任务总数: {len(d['tasks'])}")
from collections import Counter
c = Counter(t["status"] for t in d["tasks"])
print(f"状态分布: {dict(c)}")
c2 = Counter(t["priority"] for t in d["tasks"])
print(f"优先级分布: {dict(c2)}")
missing = [t["task_id"] for t in d["tasks"] if not os.path.exists(t["script_path"])]
print(f"脚本缺失: {len(missing)}" + (f" -> {missing}" if missing else ""))
