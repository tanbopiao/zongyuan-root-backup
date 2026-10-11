#!/usr/bin/env python3
"""从文件读取命令并通过MCP execute_command执行（持久版，禁令牌落日志）"""
import json, os, subprocess, sys, time, uuid

BASE = '/home/user/Doubao/chats/38438491307070978/.deploy'
TOKEN = open(os.path.join(BASE, '.cloudstudio_token')).read().strip()
SPACE = sys.argv[1] if len(sys.argv) > 1 else 'ae35d7b823d34c30a1c67b198fcae19e'
CMD_FILE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/cmd.txt'

def send(proc, method, params=None, msg_id=None):
    msg = {"jsonrpc": "2.0", "id": msg_id or str(uuid.uuid4()), "method": method}
    if params is not None: msg["params"] = params
    proc.stdin.write(json.dumps(msg) + "\n"); proc.stdin.flush()
    while True:
        line = proc.stdout.readline()
        if not line: return None
        line = line.strip()
        if not line: continue
        try: r = json.loads(line)
        except json.JSONDecodeError: continue
        if r.get("id") == msg["id"]: return r

command = open(CMD_FILE).read().strip()
env = dict(os.environ); env['API_TOKEN'] = TOKEN
for k in ('NO_PROXY','no_proxy'):
    if env.get(k): env[k] = env[k] + ',.cloudstudio.club,.cloudstudio.net,api.cloudstudio.net'
    else: env[k] = '.cloudstudio.club,.cloudstudio.net,api.cloudstudio.net'
proc = subprocess.Popen(['uvx','--from','cloudstudio-mcp-server','cloudstudio-mcp-deploy'],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, text=True, bufsize=1)
time.sleep(3)
try:
    send(proc, "initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name":"doubao","version":"1.0"}})
    send(proc, "notifications/initialized", {})
    r = send(proc, "tools/call", {"name": "execute_command", "arguments": {"space_key": SPACE, "command": command}})
    if r and "result" in r:
        for c in r["result"].get("content", []):
            txt = c.get("text","")
            try:
                j = json.loads(txt)
                print("EXIT:", j.get("exitCode"))
                print(j.get("stdout",""))
                if j.get("stderr"): print("STDERR:", j["stderr"][:400])
            except Exception:
                print(txt[:1500])
    else:
        print(json.dumps(r, ensure_ascii=False)[:800])
finally:
    proc.terminate()
