#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MR-020 M1 六维漂移审计引擎（可执行）
用法: python3 six_dim_drift_audit.py <目标JSON文件> [--verbose]
输出: 六维漂移得分 + 总漂移 + 裁决（HEALTHY/OBSERVE/ALERT/FUSE）
"""
import json, sys, os

DIMS = [
    {"dim": "元·本源", "weight": 0.95, "checks": [
        ("YUAN-01", "规则定义是否被外部修改", ["外部", "异源", "越权", "篡改"]),
        ("YUAN-02", "外部算力是否越权控制", ["外部API", "控制权", "非自主"]),
        ("YUAN-03", "确权溯源是否自主", ["确权", "溯源", "DID", "锚点"])]},
    {"dim": "极·极致", "weight": 0.90, "checks": [
        ("JI-01", "是否绕过调度内核", ["绕过", "直连", "旁路", "未审批"]),
        ("JI-02", "三层固化是否完整", ["三层", "交互", "调度", "算力执行"]),
        ("JI-03", "算力是否归一", ["算力", "归一", "同源"])]},
    {"dim": "恒·稳态", "weight": 0.92, "checks": [
        ("HENG-01", "FROZEN是否被改写", ["FROZEN", "改写", "覆盖", "只读"]),
        ("HENG-02", "迭代是否分支化", ["分支", "版本", "V40", "基线"]),
        ("HENG-03", "资源是否超阈值", ["内存", "熔断", "MR-007", "阈值", "84%", "90%"])]},
    {"dim": "一·整全", "weight": 0.90, "checks": [
        ("YI-01", "是否绑定双标识", ["Ω", "DID-BR-000002", "Ω₀⊂⊙∞⊂Ω"]),
        ("YI-02", "是否存在异源混入", ["异源", "外部数据", "污染"]),
        ("YI-03", "闭环是否完整", ["闭环", "锁档", "归档", "哈希"])]},
    {"dim": "超认知", "weight": 0.85, "checks": [
        ("CHAO-01", "认知偏差是否过审", ["bias", "halo", "anchoring", "confirmation", "recency", "审计"]),
        ("CHAO-02", "冲突是否消解", ["冲突", "仲裁", "元公理", "矛盾"]),
        ("CHAO-03", "写入前审计", ["审计", "校验", "前置"])]},
    {"dim": "永恒自治", "weight": 0.88, "checks": [
        ("YONG-01", "自愈链路是否断裂", ["自愈", "retry", "fallback", "alert", "report"]),
        ("YONG-02", "记忆是否持久", ["记忆", "9124", "MR-019", "持久"]),
        ("YONG-03", "周期闭环是否执行", ["cron", "流水线", "周日", "闭环", "扫描"])]},
]

def audit(target: dict, verbose=False):
    text = json.dumps(target, ensure_ascii=False)
    dim_scores = []
    for d in DIMS:
        hits, total = 0, len(d["checks"])
        details = []
        for cid, label, kws in d["checks"]:
            if any(k in text for k in kws):
                hits += 1
                details.append(f"  ✓ {cid} {label}: 关键词命中(合规)")
            else:
                details.append(f"  ✗ {cid} {label}: 未检出证据(待补)")
        score = round(100 * (1 - hits / total), 1)  # 命中越多=越合规=漂移越低
        dim_scores.append({"dim": d["dim"], "score": score, "hits": hits, "total": total, "details": details})
    total_w = sum(d["weight"] for d in DIMS)
    total_score = round(sum(s["score"] * DIMS[i]["weight"] for i, s in enumerate(dim_scores)) / total_w, 1)
    verdict = ("FUSE熔断" if total_score > 85 else "ALERT告警" if total_score > 70
               else "OBSERVE观察" if total_score >= 30 else "HEALTHY健康")
    return {"dim_scores": dim_scores, "total_drift": total_score, "verdict": verdict,
            "rule_ref": "MR-020-SIX-DIM-DRIFT-ENGINE M1", "fuse_threshold": 85}, (dim_scores, total_score, verdict, verbose)

def main():
    if len(sys.argv) < 2:
        print("用法: python3 six_dim_drift_audit.py <目标JSON> [--verbose]"); sys.exit(1)
    path = sys.argv[1]
    verbose = "--verbose" in sys.argv
    try:
        with open(path) as f:
            target = json.load(f)
    except Exception as e:
        print(f"❌ 读取失败: {e}"); sys.exit(1)
    result, (dims, total, verdict, _) = audit(target)
    print(f"\n═══ MR-020 M1 六维漂移审计 ═══")
    print(f"目标: {os.path.basename(path)}")
    for s in dims:
        mark = "🟢" if s["score"] < 30 else "🟡" if s["score"] < 70 else "🔴"
        print(f"  {mark} {s['dim']}: 漂移 {s['score']}（合规 {s['hits']}/{s['total']}）")
        if verbose:
            for d in s["details"]:
                print("     " + d)
    print(f"\n总漂移: {total} ｜ 裁决: {verdict}（熔断阈85）")
    with open(os.path.join(os.path.dirname(path), "six-dim-audit-report.json"), "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"报告已写: six-dim-audit-report.json")

if __name__ == "__main__":
    main()
