#!/bin/bash
# 短剧生产台一键部署到 123.207.202.158
# 在服务器上执行：bash deploy_drama.sh
set -e
echo "=== 1. 建目录 ==="
mkdir -p /opt/drama-studio/{web,api,output}
cd /opt/drama-studio

echo "=== 2. 装依赖 ==="
pip3 install -q fastapi uvicorn requests 2>&1 | tail -1

echo "=== 3. 写后端 API ==="
cat > api/main.py << 'PYEOF'
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import subprocess, os, time

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

OUT = "/opt/drama-studio/output"

@app.post("/api/produce")
async def produce(req: Request):
    data = await req.json()
    key = data.get("api_key","")
    topic = data.get("topic","")
    script = data.get("script","")
    print(f"[produce] topic={topic} key={key[:8]}...")
    # 编排：调豆包API出片（占位，实际接API）
    task_id = str(int(time.time()))
    return {"task_id": task_id, "status": "queued", "msg": "生产任务已接收"}

@app.get("/api/result/{task_id}")
def result(task_id: str):
    return {"task_id": task_id, "status": "done", "video_url": f"/output/{task_id}.mp4"}

@app.get("/")
def home():
    return {"msg": "drama-studio api running"}
PYEOF

echo "=== 4. 启动后端 ==="
cd /opt/drama-studio/api
nohup python3 main.py > /opt/drama-studio/api.log 2>&1 &
sleep 2
echo "后端 PID: $(pgrep -f main.py)"

echo "=== 5. 健康检查 ==="
curl -s http://127.0.0.1:8000/ && echo " <- API OK"

echo "=== 完成 ==="
echo "API: http://123.207.202.158:8000"
echo "日志: /opt/drama-studio/api.log"
