#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 真值库持续治理引擎 V1.0
====================================
核心使命：让记忆网关真值库不断"完善·提炼·净化"。
四阶段闭环：
  ① 体检：拉取云端实时全量(key索引)+report/status，做类别分布/覆盖率/结构失衡分析
  ② 提炼：从本地最新增值资产提炼认知类真值(rule/meta_law/protocol/decision/risk/creative/data/config)，
          按"有语义价值、云端缺失"原则补缺上报(走主域名写通道)
  ③ 净化：识别无效条目(探针/测试/空key/重复运行观测) → 生成清理提案真值，提交中枢智能处理
  ④ 固化：输出治理报告(JSON+Markdown)，汇总真值上报，形成持续闭环

确权锚点：Ω₀⊂⊙∞⊂Ω ｜ DID-BR-000002 ｜ 锚定云内核
"""
import json
import time
import urllib.request
import os
import re
from collections import Counter
# --- ZR token 安全加载 ---
def _zr_load_token():
    import os
    t = os.environ.get("ZR_TOKEN")
    if t: return t
    try:
        envp = '/home/user/ZONGYUAN-ROOT/04_系统配置/凭证/active_token.env'
        for line in open(envp):
            if line.startswith("ZR_TOKEN="):
                return line.strip().split("=",1)[1].strip('"')
    except Exception:
        pass
    return None
ZR_TOKEN = _zr_load_token()
# --- end ---


# ---------- 配置 ----------
BASE_WRITE = "https://www.huodouai.com/api/report/truth"
BASE_STATUS = "https://www.huodouai.com/api/report/status"
BASE_DIGITAL = "https://www.huodouai.com/digital_assets.json"
GATEWAY_READ = "https://drama.huodouai.com/api/gateway/truths?level=public"
TOKEN = os.environ.get("ZR_CAPTURE_TOKEN") or ZR_TOKEN
SOURCE_NODE = "ZR-NODE-DC2E51C0"
ANCHOR_DIR = "/home/user/Doubao/chats/38437615670548738/zongyuan-anchor"
OUT_DIR = "/home/user/Doubao/chats/38438412455799554/truth-governance"
STATE_FILE = os.path.join(OUT_DIR, "governance_state.json")

LEGAL_TYPES = ["meta_law", "rule", "config", "decision", "data", "creative", "risk", "protocol", "unknown"]
# 运行观测类前缀（净化对象：不作为有效认知资产）
RUN_OBS_PREFIXES = ["PERCEPTION", "predictive-engine", "INTELLIGENCE_CALL_MONITOR", "HEARTBEAT",
                    "HEALTH", "observation", "auto_scaling", "SVC", "HEALING", "DISSIPATIVE",
                    "COGNITIVE", "COMPUTE_INJECTION", "CTE", "CLASSIFICATION", "AUTO", "self-healing",
                    "STABILITY", "EXT", "theory", "EXP", "TRACE", "monitor", "METRIC", "probe"]
# 无效条目特征（清理提案对象）
INVALID_PATTERNS = [r"\.PROBE\.", r"PROBE\.", r"test\.", r"TEST\.", r"\.tmp", r"\.TMP", r"example", r"EXAMPLE", r"^\.", r"\.\."]


def http_get(url, headers=None, timeout=25):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def report_truth(key, content, ttype, conf=0.97):
    body = json.dumps({"key": key, "content": content, "truth_type": ttype,
                       "source_node": SOURCE_NODE, "confidence": conf}).encode()
    req = urllib.request.Request(BASE_WRITE, data=body,
                                 headers={"Content-Type": "application/json", "X-Capture-Token": TOKEN})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)
    except Exception as e:
        return {"error": str(e)}


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            return json.load(open(STATE_FILE, encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_state(s):
    json.dump(s, open(STATE_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def collect_cloud():
    """① 拉取云端实时状态 + 全量key索引"""
    status = http_get(BASE_STATUS)
    keys = []
    try:
        gw = http_get(GATEWAY_READ, headers={"X-Capture-Token": TOKEN})
        keys = [k for k in gw.get("truths", []) if isinstance(k, str) and k]
    except Exception as e:
        print(f"  [warn] gateway拉取失败: {str(e)[:60]}")
    return status, keys


def collect_local():
    """② 收集本地真值 key（与云端对账）"""
    local_keys = set()
    for f in glob_files(ANCHOR_DIR, "*.json"):
        try:
            d = json.load(open(f, encoding="utf-8"))
            if isinstance(d, dict):
                for fld in ["truth_keys", "registry_id", "trace_id", "did"]:
                    v = d.get(fld)
                    if isinstance(v, list):
                        local_keys.update(str(x) for x in v if x)
                    elif v:
                        local_keys.add(str(v))
        except Exception:
            pass
    return local_keys


def glob_files(d, pat):
    import glob
    return glob.glob(os.path.join(d, pat))


def analyze(cats):
    """③ 覆盖率/结构分析"""
    total = sum(cats.values())
    run_obs = sum(v for k, v in cats.items() if k in RUN_OBS_PREFIXES or any(k.startswith(p) for p in RUN_OBS_PREFIXES))
    legal_coverage = {}
    for t in LEGAL_TYPES:
        hits = [c for c in cats if t in c.lower()]
        legal_coverage[t] = sum(cats[c] for c in hits)
    return {
        "total": total,
        "prefix_kinds": len(cats),
        "run_observation_share": round(run_obs / total * 100, 1) if total else 0,
        "legal_coverage": legal_coverage,
        "top10": cats.most_common(10),
    }


def detect_invalid(keys):
    """④ 识别无效条目（探针/测试/异常key）"""
    invalid = []
    for k in keys:
        if not k or not k.strip():
            invalid.append({"key": k, "reason": "空key"})
            continue
        if k == k.lower() and len(k) < 8:
            invalid.append({"key": k, "reason": "疑似乱码短key"})
            continue
        for p in INVALID_PATTERNS:
            if re.search(p, k):
                invalid.append({"key": k, "reason": f"匹配模式 {p}"})
                break
    return invalid[:200]


def main():
    print("[truth-governance] === 真值库持续治理引擎启动 ===")
    state = load_state()
    last_run = state.get("last_run_at", "")
    now = time.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    today = now[:10].replace("-", "")

    # ① 体检
    print("[1/4] 云端体检...")
    status, cloud_keys = collect_cloud()
    cats = Counter()
    for k in cloud_keys:
        cats[k.split(".")[0] if "." in k else k.split("-")[0]] += 1
    health = analyze(cats)
    print(f"  云端: {health['total']} 条 | 前缀 {health['prefix_kinds']} 类 | 运行观测占比 {health['run_observation_share']}%")
    print(f"  九大类覆盖: {health['legal_coverage']}")

    # ② 提炼补缺
    print("[2/4] 本地提炼补缺...")
    local_keys = collect_local()
    missing = sorted(local_keys - set(cloud_keys))
    print(f"  本地独有(云端缺): {len(missing)} 条")
    filled = []
    if missing:
        locks = [k for k in missing if k.startswith(("LOCK", "lock"))]
        others = [k for k in missing if not k.startswith(("LOCK", "lock"))]
        if locks:
            r = report_truth(f"ASSET.LOCK-INDEX.GOVERNANCE.{today}",
                             f"治理引擎补缺·本地锁档索引({len(locks)}条):" + "、".join(locks[:60]), "data")
            filled.append(r.get("action"))
        if others:
            r = report_truth(f"ASSET.LOCAL-MISSING.GOVERNANCE.{today}",
                             f"治理引擎补缺·本地独有真值({len(others)}条):" + "、".join(others[:60]), "data")
            filled.append(r.get("action"))

    # ③ 净化提案
    print("[3/4] 无效条目识别...")
    invalid = detect_invalid(cloud_keys)
    print(f"  识别无效/可疑条目: {len(invalid)} 条")
    cleanup_proposal = None
    if invalid:
        samples = "、".join([f"{x['key']}({x['reason']})" for x in invalid[:40]])
        r = report_truth(f"PROPOSAL.CLEANUP.INVALID-TRUTHS.{today}",
                         f"真值库净化提案(提交中枢智能处理·{len(invalid)}条): " + samples, "risk")
        cleanup_proposal = r.get("action")
        print(f"  清理提案已提交中枢: {cleanup_proposal}")

    # ④ 固化报告
    print("[4/4] 固化治理报告...")
    report = {
        "report_id": f"GOVERNANCE-{today}",
        "generated_at": now,
        "last_run": last_run,
        "health": health,
        "reconcile": {"cloud": len(cloud_keys), "local": len(local_keys),
                      "local_missing": len(missing), "filled": filled},
        "cleanup": {"invalid_count": len(invalid), "proposal": cleanup_proposal,
                    "invalid_samples": invalid[:10]},
        "next_actions": ["本地决策记录批量提炼DECISION类", "云端独有增量纳入训练数据",
                         "9120挂载主域名后全量读并回", "持续观察风险/创意/数据类覆盖"],
    }
    report_path = os.path.join(OUT_DIR, f"governance_report_{today}.json")
    json.dump(report, open(report_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    state["last_run_at"] = now
    state["last_report"] = report_path
    save_state(state)

    # 汇总真值
    summary = (f"真值库治理引擎巡检完成：云端{health['total']}条/运行观测{health['run_observation_share']}%/九大类覆盖"
               f"{health['legal_coverage']}；本地独有{len(missing)}条已补缺；无效/可疑{len(invalid)}条已提交中枢清理提案；"
               f"报告{report_path}")
    r = report_truth(f"REPORT.TRUTH-GOVERNANCE.{today}", summary, "data")
    print(f"[done] 治理完成 | 报告: {report_path}")
    print(f"[done] 汇总上报: {r.get('action')} | truth_count {r.get('truth_count')}")
    return report


if __name__ == "__main__":
    main()
