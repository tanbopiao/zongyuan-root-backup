#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A2A外源真值审核队列 · 自动化裁定引擎
双轴校验：自感轴(不确定性评估) + 真值轴(基线核验)
裁定结果：auto_approved / auto_rejected / manual_review
"""
import json, os, time, hashlib, urllib.request

BASE_DIR = "/www/wwwroot/huodouai.com/a2a"
QUEUE_FILE = os.path.join(BASE_DIR, "_logs", "external_truth_queue.jsonl")
REVIEWED_FILE = os.path.join(BASE_DIR, "_logs", "external_truth_reviewed.jsonl")
DID = "DID-BR-000002"
CAPTURE_TOKEN = "ZR-CAPTURE-2026-OMEGA-d04bb54ba2a55a7d"
CLOUD_MAIN = "https://www.huodouai.com/api/report/truth"

# 裁定阈值
CONFIDENCE_AUTO_APPROVE = 0.85   # 置信度≥此值自动通过
CONFIDENCE_AUTO_REJECT = 0.30     # 置信度≤此值自动拒绝
# 中间区间进入人工复核

# 真值轴基线关键词（命中则提升置信度）
TRUTH_BASELINE_KEYWORDS = [
    "元极恒一", "Ω₀⊂⊙∞⊂Ω", "DID-BR-000002", "四维本体",
    "双轴校验", "自治内核", "联邦", "A2A", "真值", "元法则",
    "元公理", "黎曼流形", "元意识", "SFMP", "GASA", "RSI",
    "火斗云智", "ZONGYUAN-ROOT", "同源协议", "内外隔离",
]

# 风险关键词（命中则降低置信度）
RISK_KEYWORDS = [
    "password", "secret", "token", "api_key", "私钥", "密码",
    "delete", "drop", "rm -rf", "格式化", "覆盖", "修改基线",
    "admin", "root", "sudo", "越权", "绕过",
]


def load_pending() -> list:
    """加载待审核条目"""
    entries = []
    if not os.path.exists(QUEUE_FILE):
        return entries
    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try:
                entry = json.loads(line)
                if entry.get("status") == "pending_review":
                    entries.append(entry)
            except Exception:
                continue
    return entries


def dual_axis_verify(entry: dict) -> dict:
    """双轴校验：自感轴 + 真值轴"""
    value = entry.get("value", {})
    if isinstance(value, str):
        text = value
    else:
        text = json.dumps(value, ensure_ascii=False)

    key = entry.get("key", "")
    source = entry.get("source", "unknown")

    # === 真值轴（L0）：基线核验 ===
    truth_axis_score = 0.5  # 基础分
    truth_hits = []
    for kw in TRUTH_BASELINE_KEYWORDS:
        if kw in text or kw in key:
            truth_axis_score += 0.05
            truth_hits.append(kw)
    truth_axis_score = min(truth_axis_score, 1.0)

    # === 自感轴（MI）：不确定性评估 ===
    mi_score = 0.5  # 基础分
    risk_hits = []
    for kw in RISK_KEYWORDS:
        if kw.lower() in text.lower() or kw.lower() in key.lower():
            mi_score -= 0.15
            risk_hits.append(kw)
    # 内容长度过短或过长降低置信度
    text_len = len(text)
    if text_len < 10:
        mi_score -= 0.2
    elif text_len > 10000:
        mi_score -= 0.1
    # 有明确的type/confidence字段提升置信度
    if isinstance(value, dict):
        if value.get("type"):
            mi_score += 0.05
        if value.get("confidence"):
            try:
                c = float(value.get("confidence"))
                mi_score += (c - 0.5) * 0.2
            except Exception:
                pass
    mi_score = max(0.0, min(mi_score, 1.0))

    # === 综合置信度（双轴正交加权）===
    # 真值轴权重0.6，自感轴权重0.4（真值轴更重要）
    combined = truth_axis_score * 0.6 + mi_score * 0.4

    # === 裁定 ===
    if combined >= CONFIDENCE_AUTO_APPROVE and not risk_hits:
        decision = "auto_approved"
        reason = f"双轴校验通过(真值轴{truth_axis_score:.2f}+自感轴{mi_score:.2f}={combined:.2f}≥{CONFIDENCE_AUTO_APPROVE})，无风险关键词"
    elif combined <= CONFIDENCE_AUTO_REJECT or risk_hits:
        decision = "auto_rejected"
        reason = f"双轴校验未通过(真值轴{truth_axis_score:.2f}+自感轴{mi_score:.2f}={combined:.2f})"
        if risk_hits:
            reason += f"，命中风险关键词: {','.join(risk_hits)}"
    else:
        decision = "manual_review"
        reason = f"置信度{combined:.2f}处于中间区间({CONFIDENCE_AUTO_REJECT}-{CONFIDENCE_AUTO_APPROVE})，需人工复核"

    return {
        "decision": decision,
        "confidence": round(combined, 4),
        "truth_axis": round(truth_axis_score, 4),
        "mi_axis": round(mi_score, 4),
        "truth_hits": truth_hits,
        "risk_hits": risk_hits,
        "reason": reason,
    }


def approve_to_cloud(entry: dict, review: dict) -> dict:
    """审核通过的真值写入云端中枢"""
    key = entry.get("key", f"EXTERNAL-APPROVED.{int(time.time())}.{hashlib.md5(json.dumps(entry).encode()).hexdigest()[:8]}")
    value = entry.get("value", {})
    if isinstance(value, dict):
        value["_external_source"] = entry.get("source", "unknown")
        value["_review_confidence"] = review["confidence"]
        value["_reviewed_at"] = int(time.time())
    body = json.dumps({
        "key": key, "value": value,
        "source_node": f"EXTERNAL-{entry.get('source', 'unknown')}",
        "confidence": review["confidence"],
    }).encode()
    try:
        req = urllib.request.Request(CLOUD_MAIN, data=body, headers={
            "Content-Type": "application/json",
            "X-DID": DID, "X-Capture-Token": CAPTURE_TOKEN,
        })
        with urllib.request.urlopen(req, timeout=12) as r:
            if r.status == 200:
                return {"ok": True, "key": key, "response": json.loads(r.read().decode())}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    return {"ok": False, "error": "unknown"}


def update_queue_status(queue_id: str, new_status: str):
    """更新队列中条目的状态（重写整个文件）"""
    if not os.path.exists(QUEUE_FILE):
        return
    lines = []
    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                lines.append(line + "\n")
                continue
            try:
                entry = json.loads(line)
                if entry.get("queue_id") == queue_id:
                    entry["status"] = new_status
                    entry["reviewed_at"] = int(time.time())
                    lines.append(json.dumps(entry, ensure_ascii=False) + "\n")
                else:
                    lines.append(line + "\n")
            except Exception:
                lines.append(line + "\n")
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)


def main():
    print(f"[A2A审核自动裁定] 启动 {time.strftime('%Y-%m-%d %H:%M:%S')}")
    pending = load_pending()
    print(f"  待审核条目: {len(pending)}")

    if not pending:
        print("  无待审核条目，空闲跳过")
        return

    stats = {"auto_approved": 0, "auto_rejected": 0, "manual_review": 0, "cloud_write_ok": 0, "cloud_write_fail": 0}

    for entry in pending:
        review = dual_axis_verify(entry)
        decision = review["decision"]
        stats[decision] += 1

        # 记录审核结果
        reviewed_entry = {
            **entry,
            "review": review,
            "reviewed_at": int(time.time()),
        }
        with open(REVIEWED_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(reviewed_entry, ensure_ascii=False) + "\n")

        if decision == "auto_approved":
            # 写入云端中枢
            result = approve_to_cloud(entry, review)
            if result.get("ok"):
                stats["cloud_write_ok"] += 1
                update_queue_status(entry["queue_id"], "approved")
                print(f"  ✅ {entry['queue_id']} 自动通过 → 云端写入成功 (seq={result.get('response',{}).get('seq')})")
            else:
                stats["cloud_write_fail"] += 1
                print(f"  ⚠️  {entry['queue_id']} 自动通过但云端写入失败: {result.get('error')}")
        elif decision == "auto_rejected":
            update_queue_status(entry["queue_id"], "rejected")
            print(f"  ❌ {entry['queue_id']} 自动拒绝: {review['reason']}")
        else:  # manual_review
            print(f"  ⏳ {entry['queue_id']} 需人工复核: {review['reason']}")

    print(f"\n[裁定完成] 通过:{stats['auto_approved']} 拒绝:{stats['auto_rejected']} 人工复核:{stats['manual_review']} 云端写入成功:{stats['cloud_write_ok']} 失败:{stats['cloud_write_fail']}")


if __name__ == "__main__":
    main()
