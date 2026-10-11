#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
元极恒一 · IM告警Webhook
异常实时推送飞书群消息
"""
import subprocess, json, sys
from datetime import datetime, timezone

# 默认群聊（待配置实际chat_id）
DEFAULT_CHAT_ID = "待配置"

def send_alert(title, message, level="warning"):
    """发送飞书告警消息"""
    ts = datetime.now(timezone.utc).isoformat()
    color = {"critical": "red", "warning": "orange", "info": "blue"}.get(level, "grey")
    
    content = f"【元极恒一告警|{level.upper()}】\n标题: {title}\n时间: {ts}\n内容: {message}\n确权: Ω₀⊂⊙∞⊂Ω|DID-BR-000002"
    
    cmd = [
        "lark-cli", "im", "messages", "create",
        "--data", json.dumps({
            "receive_id_type": "chat_id",
            "receive_id": DEFAULT_CHAT_ID,
            "msg_type": "text",
            "content": json.dumps({"text": content})
        }),
        "--format", "json"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        data = json.loads(result.stdout)
        if data.get("ok"):
            print(f"✅ IM告警发送成功: {title}")
            return True
        else:
            print(f"⚠️ IM告警: {data.get('error',{}).get('message','?')}")
            return False
    except Exception as e:
        print(f"⚠️ IM告警异常: {e}")
        return False

if __name__ == "__main__":
    print("═══ IM告警Webhook就绪 ═══")
    print(f"默认群聊: {DEFAULT_CHAT_ID}")
    print("告警级别: critical(红)/warning(橙)/info(蓝)")
