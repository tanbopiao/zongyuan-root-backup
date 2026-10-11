#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN 本地侧 · ntfy 双向握手验证器 (handshake_ntfy.py)
==========================================================
确权: Ω₀⊂⊙∞⊂Ω | DID-BR-000002
用途: 与实例侧 OMEGA-BRAIN/boot.py 完成双向握手验证
  boot.py 订阅主主题(zongyuan-kunlun-2026) → 收到消息当shell命令执行
  boot.py 结果回发结果主题(zongyuan-kunlun-2026-result)
本脚本:
  [发] 向主主题发测试命令(echo/status)
  [收] 监听结果主题, 验证命令被执行并返回结果
用法:
  python3 handshake_ntfy.py --cmd "echo HELLO-ZR"   # 发一条命令
  python3 handshake_ntfy.py --watch 60              # 监听结果主题60秒
"""
import json, sys, time, urllib.request, urllib.parse

MAIN = "zongyuan-kunlun-2026"
RESULT = "zongyuan-kunlun-2026-result"
DID = "DID-BR-000002"

def publish(topic, text):
    """发命令到 ntfy 主题 — 纯文本 body (boot.py 直接取 message 当 shell 命令, 不做JSON二次解析)"""
    req = urllib.request.Request(f"https://ntfy.sh/{topic}", data=text.encode(),
                                 headers={"Content-Type": "text/plain"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.status

def listen(topic, since, timeout_sec):
    """轮询监听主题, 返回最近消息列表"""
    msgs = []
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            url = f"https://ntfy.sh/{topic}/json?poll=1&since={since}"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=15) as r:
                data = r.read().decode("utf-8", errors="replace")
            for line in data.strip().split("\n"):
                line = line.strip()
                if not line: continue
                try:
                    m = json.loads(line)
                    msgs.append({"time": m.get("time"), "title": m.get("title",""),
                                 "msg": m.get("message","")})
                except Exception: pass
            if msgs: return msgs
        except Exception:
            pass
        time.sleep(5)
    return msgs

def main():
    args = sys.argv[1:]
    if "--cmd" in args:
        cmd = args[args.index("--cmd")+1]
        # 命令注入 zr 身份标记(实例侧boot.py未校验, 保持无害命令)
        safe = cmd
        print(f"[发] 主主题 ← {safe}")
        st = publish(MAIN, safe)
        print(f"     HTTP {st} ✅ 命令已发出")
        print(f"[收] 监听结果主题 45秒 (等待 boot.py 执行回传)...")
        time.sleep(2)
        res = listen(RESULT, "2m", 45)
        if res:
            for m in res[-3:]:
                print(f"──[{m['time']}] {m['title']}: {m['msg'][:600]}")
        else:
            print("⚠️ 45秒未收到回传 — boot.py 可能未启动或执行超时")
    elif "--watch" in args:
        sec = int(args[args.index("--watch")+1]) if "--watch" in args and args.index("--watch")+1 < len(args) else 60
        print(f"[监听] 结果主题 {sec}秒...")
        res = listen(RESULT, "1h", sec)
        for m in res[-10:]:
            print(f"──[{m['time']}] {m['title']}: {m['msg'][:600]}")
        if not res:
            print("无消息")
    else:
        print(__doc__)

if __name__ == "__main__":
    main()
