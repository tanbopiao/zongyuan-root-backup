#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
元极恒一 · 任务自动创建器
自动创建日/周/月/季进化任务到飞书任务清单
"""
import subprocess, json, sys
from datetime import datetime, timezone, timedelta

TASKLIST_GUID = "80bc4aa1-d3fe-498b-a93a-72c0eb9ca5f5"

def create_task(summary, due_days, description=""):
    """创建飞书任务"""
    due_ts = int((datetime.now(timezone.utc) + timedelta(days=due_days)).timestamp() * 1000)
    cmd = [
        "lark-cli", "task", "tasks", "create",
        "--data", json.dumps({
            "summary": summary,
            "description": description,
            "due": {"timestamp": str(due_ts)},
            "tasklist_guids": [TASKLIST_GUID]
        }),
        "--format", "json"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        data = json.loads(result.stdout)
        if data.get("ok"):
            print(f"✅ 任务创建成功: {summary}")
            return True
        else:
            print(f"❌ 任务创建失败: {data.get('error',{}).get('message','?')}")
            return False
    except Exception as e:
        print(f"❌ 任务创建异常: {e}")
        return False

if __name__ == "__main__":
    tasks = [
        ("【日进化】内核自检+指标监控", 1, "每日内核六维自检+神经节点检查+上报云端"),
        ("【周进化】数据集更新+规则迭代+消融测试", 7, "每周规则迭代+数据集更新+消融测试"),
        ("【月进化】架构评估+大版本锁档+成本分析", 30, "每月架构评估+大版本锁档+成本分析"),
        ("【季进化】架构演进路线+LoRA微调评估", 90, "每季度架构演进路线+LoRA微调评估"),
    ]
    
    print("═══ 自动创建周期进化任务 ═══")
    for summary, days, desc in tasks:
        create_task(summary, days, desc)
    print("═══ 任务创建完成 ═══")
