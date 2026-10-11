#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
元极恒一 · 日历自动写入器
自动将进化节点写入云智中台日历
"""
import subprocess, json
from datetime import datetime, timezone, timedelta

CALENDAR_ID = "feishu.cn_FsOdeEMcGprRBGbYyJNIda@group.calendar.feishu.cn"

def create_event(summary, description, start_hours=1, duration_hours=2):
    """创建日历事件"""
    start = datetime.now(timezone.utc) + timedelta(hours=start_hours)
    end = start + timedelta(hours=duration_hours)
    
    cmd = [
        "lark-cli", "calendar", "events", "create",
        "--params", json.dumps({"calendar_id": CALENDAR_ID}),
        "--data", json.dumps({
            "summary": summary,
            "description": description,
            "start_time": {"timestamp": str(int(start.timestamp())), "timezone": "Asia/Shanghai"},
            "end_time": {"timestamp": str(int(end.timestamp())), "timezone": "Asia/Shanghai"},
        }),
        "--format", "json"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        data = json.loads(result.stdout)
        if data.get("ok"):
            print(f"✅ 日历事件创建成功: {summary}")
            return True
        else:
            print(f"⚠️ 日历事件创建: {data.get('error',{}).get('message','?')}")
            return False
    except Exception as e:
        print(f"⚠️ 日历事件异常: {e}")
        return False

if __name__ == "__main__":
    print("═══ 日历自动写入器就绪 ═══")
    print(f"日历ID: {CALENDAR_ID}")
    print("支持: 进化节点/周期任务/告警事件自动写入")
