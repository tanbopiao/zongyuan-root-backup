#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT GPU决策大脑调用器 V2.0（gradio_client 版）
用法:
  python3 gpu_brain_client.py health    # GPU状态
  python3 gpu_brain_client.py decide    # 自主决策（默认候选）
  python3 gpu_brain_client.py evolve "成果反馈"  # 进化建议
确权: Ω₀⊂⊙∞⊂Ω | DID-BR-000002
"""
import json, sys

GPU_BRAIN_URL = "https://geography-vocalist-stopping.ngrok-free.dev"

def _load_token():
    """从 ~/.zr_gpu_tokens.json 读取第一个活跃 token（无则 None=匿名模式）"""
    import os
    f = os.path.expanduser("~/.zr_gpu_tokens.json")
    try:
        d = json.load(open(f))
        for t in d.get("tokens", []):
            if t.get("active"):
                return t["token"]
    except Exception:
        pass
    return os.environ.get("GPU_BRAIN_TOKEN")

GPU_TOKEN = _load_token()
GPU_HEADERS = {"X-API-Key": GPU_TOKEN} if GPU_TOKEN else {}

def fastapi_call(task_type, context):
    """FastAPI 通道直调（带 token）：GET /health | POST /decide|/evolve"""
    import requests as _r
    if task_type == "health":
        r = _r.get(f"{GPU_BRAIN_URL}/health", headers=GPU_HEADERS, timeout=30)
    else:
        r = _r.post(f"{GPU_BRAIN_URL}/{task_type}", json={"context": context},
                    headers=GPU_HEADERS, timeout=120)
    if r.status_code == 401:
        return {"error": "unauthorized", "hint": "检查 token：python generate_gpu_token.py list"}
    return r.json()

def call(task_type, context, use_rag=False):
    from gradio_client import Client
    if GPU_HEADERS:
        try:
            c = Client(GPU_BRAIN_URL, headers=GPU_HEADERS, verbose=False)
            r = c.predict(task_type, json.dumps({"context": context}, ensure_ascii=False), api_name="/brain")
            return r if isinstance(r, dict) else {"raw": str(r)}
        except Exception as e:
            return {"error": str(e)[:200]}
    if use_rag:
        try:
            import sys as _sys
            _sys.path.insert(0, "/home/user/Doubao/chats/38436747020400130")
            from truth_rag import rag_context
            q = context.get("query") or "体系决策"
            ctx_str = json.dumps(context, ensure_ascii=False)
            rag = rag_context(q, 5)
            context = dict(context)
            context["rag_truths"] = rag
            context["context"] = f"{ctx_str}\n\n[真值库检索]\n{rag}"
        except Exception as e:
            context["rag_truths"] = f"(RAG跳过:{e})"
    c = Client(GPU_BRAIN_URL, verbose=False)
    return c.predict(task_type, json.dumps(context, ensure_ascii=False) if not isinstance(context, str) else context,
                     api_name="/brain")

def extract_action(r):
    """从GPU大脑响应提取 action（容错：JSON内嵌/纯JSON/文本）"""
    import re
    if isinstance(r, dict):
        raw = str(r.get("raw") or r.get("action") or r)
    else:
        raw = str(r)
    m = re.search(r'"action"\s*:\s*"([^"]+)"', raw)
    if m:
        return m.group(1)
    m2 = re.search(r'"action"\s*:\s*([^,}]+)', raw)
    if m2:
        return m2.group(1).strip().strip('"')
    return raw[:50]

def decide_cot(candidates, n=3):
    """CoT+自洽性采样：n次决策投票取多数"""
    votes = {}
    details = []
    for i in range(n):
        ctx = {
            "state": {"layer": "Lv9永恒稳态", "truths": "32078+", "kernel": "V3.6"},
            "candidates": candidates,
            "rules": ["云端为权威先同步再行动", "成果同源幂等上报", "通道仅轻量运维"],
            "chain_of_thought": "请先逐步推理(分析现状/候选/规则约束)，再输出决策JSON{\"action\":...}",
            "query": " ".join(candidates)
        }
        r = call("decide", ctx, use_rag=True)
        a = extract_action(r)
        votes[a] = votes.get(a, 0) + 1
        details.append(a)
        print(f"    采样{i+1}: {a}")
    best = max(votes, key=votes.get)
    return best, votes, details

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "health"
    if mode == "health":
        print("GPU大脑:", call("health", "{}"))
    elif mode == "decide":
        cands = sys.argv[2:] or ["P13任务推进", "Lv10超自治引擎优化", "GPU决策大脑接入固化", "服务器文件侧部署补投"]
        r = call("decide", {"state": {"layer": "Lv9永恒稳态", "truths": "32078+", "kernel": "V3.6"},
                            "candidates": cands,
                            "rules": ["云端为权威先同步再行动", "成果同源幂等上报", "通道仅轻量运维"]}, use_rag=True)
        # 提取决策
        if isinstance(r, dict) and "raw" in r:
            import re
            m = re.search(r'\{[^{}]*"action"[^{}]*\}', str(r["raw"]))
            print("决策:", m.group(0) if m else r["raw"][:500])
        else:
            print("决策:", json.dumps(r, ensure_ascii=False)[:500])
    elif mode == "cot":
        cands = sys.argv[2:] or ["P13-2推理能力提升", "P13-4协同覆盖深化", "P13-1 Lv9终极永恒"]
        n = 3
        best, votes, details = decide_cot(cands, n)
        print(f"\n✅ 自洽决策: {best} | 投票: {votes}")
    elif mode == "evolve":
        fb = sys.argv[2] if len(sys.argv) > 2 else "GPU大脑接入完成，自主决策闭环打通"
        r = call("evolve", {"feedback": fb})
        print("进化建议:", json.dumps(r, ensure_ascii=False)[:600])
    else:
        print(__doc__)

if __name__ == "__main__":
    main()
