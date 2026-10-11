#!/bin/bash
# 真持久化：开机自启API服务+桥接器
cd /home/user/Doubao/chats/38438491307070978/mirror_hilbert
nohup python3 -m uvicorn openai_api:app --host 0.0.0.0 --port 8000 > /tmp/api.log 2>&1 &
echo "API服务已起:8000"

# 健康检查：每5分钟看API是否活着，挂了自动重启
while true; do
  sleep 300
  if ! curl -s -m 3 http://127.0.0.1:8000/v1/models > /dev/null; then
    pkill -f uvicorn
    cd /home/user/Doubao/chats/38438491307070978/mirror_hilbert
    nohup python3 -m uvicorn openai_api:app --host 0.0.0.0 --port 8000 > /tmp/api.log 2>&1 &
    echo "$(date) API重启" >> /tmp/api_guard.log
  fi
done
