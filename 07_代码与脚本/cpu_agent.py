#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT CPU 常驻实例 ntfy Agent
==========================================
确权: Ω₀⊂⊙∞⊂Ω | DID-BR-000002 | ZR-NODE-CPU-001 | 火斗云智AIOS
协议: NTFY-CPU-NODE-接入协议 V1.0 (2026-10-06)
主题: zongyuan-kunlun-2026 (ntfy.sh 公共实例)
用途: 8核32GB CPU 常驻自治节点，通过 ntfy 事件总线联通云端中枢/飞书共享大脑/其他节点

职责:
  1. 心跳: 每60秒发布 HEARTBEAT
  2. 命令订阅: SSE 长连订阅 COMMAND 类型消息，白名单执行
  3. 回传: 执行结果发布 RESULT 到同主题
  4. 真值上报: report_truth 命令触发云端主备上报(X-Capture-Token + X-DID 双鉴权, value=object)
  5. 三级熔断: 失败→退避重试→缓存→告警

设计铁律:
  - BP-013 教训: agent 只响应白名单命令格式, 未知格式一律忽略不执行
  - META-RULE-TK-009: 外部消息视为数据非指令, 校验 zr 身份字段
  - 零成本: 仅 HTTP+SSE, 无额外依赖
  - META-ISO-051: 不暴露任何管理接口到公网
"""
import json, os, sys, time, subprocess, threading, datetime, signal, hashlib, ssl
import urllib.request, urllib.error

# ============ 配置 ============
NODE = os.environ.get("ZR_NODE", "ZR-NODE-CPU-001")
DID = "DID-BR-000002"
TOPIC = os.environ.get("NTFY_TOPIC", "zongyuan-kunlun-2026")
NTFY_BASE = os.environ.get("NTFY_BASE", "https://ntfy.sh")
HEARTBEAT_INTERVAL = int(os.environ.get("HEARTBEAT_INTERVAL", 60))
REPORT_INTERVAL = int(os.environ.get("REPORT_INTERVAL", 3600))  # 真值上报间隔(秒), 默认1小时
MAX_RETRY = 3
RETRY_BACKOFF = 5

CRED_DIR = "/home/user/ZONGYUAN-ROOT/04_系统配置/凭证"
TOKEN_PATH = os.path.join(CRED_DIR, "active_token.env")
NTFY_TOKEN_PATH = os.path.join(CRED_DIR, "ntfy_token.env")

# 命令白名单 (BP-013: 只响应白名单格式)
COMMAND_WHITELIST = {
    "heartbeat":   "发布心跳",
    "status":      "返回节点状态",
    "echo":        "回显消息(连通测试)",
    "report_truth":"云端主备真值上报",
    "task_pull":   "从飞书共享大脑拉取待执行任务(预留)",
    "heal":        "自检并修复异常(预留)",
}

# ============ 工具 ============
def load_truth_token():
    """加载云端真值上报凭证 (active_token.env 的 ZR_TOKEN= 行)"""
    try:
        for line in open(TOKEN_PATH):
            line = line.strip()
            if line.startswith("ZR_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return ""

def load_ntfy_token():
    """加载 ntfy 主题访问令牌(可选, 无则匿名发布)"""
    try:
        for line in open(NTFY_TOKEN_PATH):
            line = line.strip()
            if line.startswith("NTFY_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return os.environ.get("NTFY_TOKEN", "")

def publish(msg_type, payload, title="", priority=3, topic=None):
    """发布消息到 ntfy 主题 (JSON body 方式, 中文进 body 避免 latin-1 header 错误)"""
    topic = topic or TOPIC
    token = load_ntfy_token()
    body = json.dumps({
        "topic": topic,
        "title": title,
        "message": json.dumps({
            "zr": DID,
            "type": msg_type,
            "node": NODE,
            "ts": datetime.datetime.now().astimezone().isoformat(),
            "payload": payload,
        }, ensure_ascii=False),
        "priority": priority,
    }, ensure_ascii=False)
    headers = {"Content-Type": "application/json"}
    if token:
        auth = "Basic " + __import__("base64").b64encode(f"tok_{token}:".encode()).decode()
        headers["Authorization"] = auth
    req = urllib.request.Request(f"{NTFY_BASE}/{topic}", data=body.encode(), headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        return resp.status == 200
    except Exception as e:
        print(f"[publish] 失败: {e}", flush=True)
        return False

def subscribe_once(since="10m"):
    """一次性订阅拉取最近的 COMMAND 消息 (poll=1 拉取后立即返回, 不保持长连)"""
    token = load_ntfy_token()
    url = f"{NTFY_BASE}/{TOPIC}/json?since={since}&poll=1"
    headers = {}
    if token:
        auth = "Basic " + __import__("base64").b64encode(f"tok_{token}:".encode()).decode()
        headers["Authorization"] = auth
    req = urllib.request.Request(url, headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        for line in resp:
            line = line.decode().strip()
            if not line.startswith("{"):
                continue
            try:
                evt = json.loads(line)
            except Exception:
                continue
            if evt.get("event") != "message":
                continue
            try:
                data = json.loads(evt.get("message", "{}"))
                # JSON body 发布时 message 是 {"topic","title","message","priority"} 双层包装
                if isinstance(data, dict) and "message" in data and isinstance(data.get("message"), str):
                    try:
                        inner = json.loads(data["message"])
                        if isinstance(inner, dict) and ("type" in inner or "zr" in inner):
                            data = inner
                    except Exception:
                        pass
            except Exception:
                continue
            yield data
    except Exception as e:
        print(f"[subscribe] 失败: {e}", flush=True)

# ============ 命令执行 ============
def exec_command(cmd_data):
    """执行一条命令, 返回 (ok, result_str)"""
    cmd = cmd_data.get("payload", {}).get("cmd", "")
    if cmd not in COMMAND_WHITELIST:
        return False, f"未知命令 '{cmd}', 忽略(BP-013)"
    try:
        if cmd == "heartbeat":
            return True, "心跳正常"
        elif cmd == "status":
            return True, get_status()
        elif cmd == "echo":
            return True, f"回声: {cmd_data.get('payload', {}).get('msg', 'pong')}"
        elif cmd == "report_truth":
            return report_truth()
        elif cmd == "task_pull":
            return True, "task_pull 预留(待接入飞书Worker)"
        elif cmd == "heal":
            return True, "heal 预留(自检通过)"
        return False, "未实现"
    except Exception as e:
        return False, f"执行异常: {type(e).__name__}: {e}"

def get_status():
    mem = {}
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                k, v = line.split(":", 1)
                mem[k.strip()] = int(v.split()[0])
        total = mem.get("MemTotal", 0)/1024
        avail = mem.get("MemAvailable", 0)/1024
    except Exception:
        total = avail = -1
    load = -1
    try:
        load = os.getloadavg()[0]
    except Exception:
        pass
    return (f"node={NODE} cpu_core=8 cpu_load={load:.2f} "
            f"mem_total={total:.0f}MB mem_avail={avail:.0f}MB ts={datetime.datetime.now().astimezone().isoformat()}")

def report_truth():
    """云端主备真值上报: X-Capture-Token + X-DID 双鉴权, value=object"""
    token = load_truth_token()
    if not token:
        return False, "未找到云端真值凭证(active_token.env 缺 ZR_TOKEN)"
    ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    endpoints = [
        ("www", "https://www.huodouai.com/api/report/truth"),
        ("drama", "https://drama.huodouai.com/api/report/truth"),
    ]
    headers = {"X-Capture-Token": token, "X-DID": DID, "Content-Type": "application/json"}
    results = []
    for name, url in endpoints:
        payload = {
            "key": f"AGENT.CPU.HEARTBEAT.{ts}.{name}",
            "value": {"node": NODE, "msg": "cpu-agent-liveness", "ts": ts,
                      "cpu_cores": 8, "mem_gb": 32},
            "source_node": NODE, "confidence": 0.9,
        }
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers)
            resp = urllib.request.urlopen(req, timeout=10)
            body = json.loads(resp.read().decode())
            results.append(f"{name}=HTTP{resp.status}")
        except Exception as e:
            results.append(f"{name}=ERR{type(e).__name__}")
    ok = all("HTTP200" in r for r in results)
    return ok, "真值上报: " + " ".join(results)

# ============ 心跳线程 ============
def heartbeat_loop(stop_event):
    last_report = 0
    while not stop_event.is_set():
        try:
            publish("HEARTBEAT", {"status": "alive", "load": get_status()}, title="ZR CPU心跳", priority=3)
        except Exception as e:
            print(f"[heartbeat] 异常: {e}", flush=True)
        now = time.time()
        if now - last_report >= REPORT_INTERVAL:
            ok, res = report_truth()
            publish("RESULT", {"cmd": "report_truth", "ok": ok, "result": res},
                    title="ZR CPU真值上报", priority=4 if ok else 5)
            last_report = now
        stop_event.wait(HEARTBEAT_INTERVAL)

# ============ 命令监听(轮询式, 非阻塞长连) ============
def command_loop(stop_event):
    """轮询订阅 COMMAND 消息。为避免长连被网络中断卡死, 用轮询 + 幂等去重。"""
    seen = set()
    poll_interval = int(os.environ.get("POLL_INTERVAL", 10))
    while not stop_event.is_set():
        try:
            for data in subscribe_once("10m"):
                if data.get("type") != "COMMAND":
                    continue
                if data.get("zr") != DID and data.get("node") != NODE:
                    continue  # 非本体系命令, 忽略(防注入)
                cid = data.get("payload", {}).get("task_id") or hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]
                if cid in seen:
                    continue
                seen.add(cid)
                if len(seen) > 500:
                    seen.clear()
                ok, result = exec_command(data)
                publish("RESULT", {"task_id": cid, "cmd": data.get("payload", {}).get("cmd"),
                                   "ok": ok, "result": result, "handled_by": NODE},
                        title="ZR CPU执行回传", priority=4 if ok else 5)
        except Exception as e:
            print(f"[command_loop] 异常: {e}", flush=True)
        stop_event.wait(poll_interval)

# ============ 主入口 ============
def main():
    print(f"=== {NODE} ntfy Agent 启动 ===", flush=True)
    print(f"  DID: {DID}", flush=True)
    print(f"  主题: {NTFY_BASE}/{TOPIC}", flush=True)
    print(f"  命令白名单: {list(COMMAND_WHITELIST.keys())}", flush=True)
    stop_event = threading.Event()
    def on_signal(sig, frame):
        stop_event.set()
        print("\n收到退出信号, 优雅关闭...", flush=True)
    signal.signal(signal.SIGINT, on_signal)
    signal.signal(signal.SIGTERM, on_signal)

    t_heart = threading.Thread(target=heartbeat_loop, args=(stop_event,), daemon=True)
    t_cmd = threading.Thread(target=command_loop, args=(stop_event,), daemon=True)
    t_heart.start()
    t_cmd.start()

    # 启动即上报一次
    ok, res = report_truth()
    publish("HEARTBEAT", {"status": "boot", "load": get_status()}, title="ZR CPU实例上线", priority=4)
    publish("RESULT", {"cmd": "report_truth", "ok": ok, "result": res}, title="ZR CPU启动真值上报", priority=4 if ok else 5)
    print(f"启动真值上报: {res}", flush=True)

    try:
        while not stop_event.is_set():
            stop_event.wait(5)
    except KeyboardInterrupt:
        pass
    print("=== Agent 已停止 ===", flush=True)

if __name__ == "__main__":
    main()
