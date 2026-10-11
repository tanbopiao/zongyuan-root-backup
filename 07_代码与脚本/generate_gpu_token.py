#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT GPU 大脑 Token 签发器
用法:
  python generate_gpu_token.py add <备注>   # 签发新 token
  python generate_gpu_token.py list          # 列出 token（脱敏）
  python generate_gpu_token.py revoke <前8位> # 吊销
  python generate_gpu_token.py export        # 输出服务端 tokens.json（魔搭侧用）
Token 存储: ~/.zr_gpu_tokens.json (0600)
确权: Ω₀⊂⊙∞⊂Ω | DID-BR-000002
"""
import json, os, secrets, sys, time

TOK_FILE = os.path.expanduser("~/.zr_gpu_tokens.json")

def load():
    if os.path.exists(TOK_FILE):
        return json.load(open(TOK_FILE))
    return {"tokens": [], "version": "V1"}

def save(d):
    os.makedirs(os.path.dirname(TOK_FILE), exist_ok=True)
    with open(TOK_FILE, "w") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    os.chmod(TOK_FILE, 0o600)

def add(note):
    d = load()
    token = "ZR-GPU-" + secrets.token_hex(16)
    d["tokens"].append({"token": token, "note": note or "default",
                        "created": time.strftime("%Y-%m-%d %H:%M:%S"), "active": True})
    save(d)
    print(f"✅ 签发成功（仅显示一次，请安全保存）:")
    print(f"   {token}")
    print(f"   备注: {note or 'default'}")

def lst():
    d = load()
    print(f"Token 数: {len(d['tokens'])}")
    for t in d["tokens"]:
        mask = t["token"][:11] + "…" + t["token"][-4:]
        print(f"   {mask} | {t['note']} | {t['created']} | {'ON' if t['active'] else 'OFF'}")

def revoke(prefix):
    d = load()
    for t in d["tokens"]:
        if t["token"].startswith(prefix):
            t["active"] = False
            print(f"✅ 已吊销: {t['token'][:11]}…")
    save(d)

def export():
    d = load()
    active = [t["token"] for t in d["tokens"] if t["active"]]
    out = {"tokens": active, "version": "V1"}
    with open("gpu_tokens_server.json", "w") as f:
        json.dump(out, f)
    os.chmod("gpu_tokens_server.json", 0o600)
    print(f"✅ 已导出 gpu_tokens_server.json（{len(active)} 个活跃 token，0600 权限）")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(0)
    a = sys.argv[1]
    if a == "add": add(sys.argv[2] if len(sys.argv) > 2 else "")
    elif a == "list": lst()
    elif a == "revoke" and len(sys.argv) > 2: revoke(sys.argv[2])
    elif a == "export": export()
    else: print(__doc__)
