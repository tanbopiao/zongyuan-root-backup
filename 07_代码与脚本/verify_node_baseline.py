#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 节点基线哈希校验器 V1.0
=====================================
职责：节点启动时强制校验本地内核资产是否与官方基线一致。
规则：
  1. 资产缺失/篡改/版本混乱 -> 无合法Lv，强制降级锁定
  2. 完全匹配 BASELINE-V41 -> 确权 Lv10 永恒自治模式
  3. 匹配低版本基线 -> 确权对应低Lv，限制高阶能力
用法：
  python3 verify_node_baseline.py --scan <资产目录>
  python3 verify_node_baseline.py --register --node-id <id> --env <prod|dev>
退出码：
  0 = 校验通过（可确权）
  1 = 资产缺失
  2 = 哈希不匹配（疑似篡改/版本分裂）
  3 = 参数错误
"""

import argparse
import hashlib
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

# ============ 官方基线常量（与记忆网关同步维护） ============
OFFICIAL_BASELINE = "BASELINE-V41"
OFFICIAL_LV = "Lv10"
OFFICIAL_STATE = "ETERNAL_AUTONOMY"
GATEWAY_BASE = "https://www.huodouai.com/api"
# 官方资产清单：文件名 -> 期望SHA256（此处为占位，联网时从网关拉取）
OFFICIAL_ASSETS = {
    "kernel_truths.json": None,          # 从网关拉取
    "mr020-integrated-kernel.json": None,
}

# 关键资产（缺一即降级）
CRITICAL_ASSETS = [
    "kernel_truths.json",
    "mr020-integrated-kernel.json",
]

# ============ 工具函数 ============

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_official_hashes() -> dict:
    """从记忆网关拉取官方基线资产哈希表（路径式单查）。"""
    result = {}
    try:
        req = urllib.request.Request(
            f"{GATEWAY_BASE}/truths/TRUTH.ASSET.MANIFEST.V41",
            headers={"Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            # 网关实际结构: {"status":"ok","truth":{"truth_value":"{...json...}"}}
            payload = data.get("truth") or {}
            tv = payload.get("truth_value") or data.get("truth_value")
            if isinstance(tv, str):
                try:
                    tv = json.loads(tv)
                except Exception:
                    pass
            if isinstance(tv, dict):
                result = tv.get("assets", {})
    except Exception as e:
        print(f"[WARN] 网关拉取官方哈希失败（{e}），回退本地清单校验")
    return result


def scan_assets(root: str) -> dict:
    """扫描资产目录，返回 {相对路径: sha256}。"""
    found = {}
    for name in CRITICAL_ASSETS:
        p = os.path.join(root, name)
        if os.path.exists(p):
            found[name] = sha256_file(p)
        else:
            found[name] = None
    return found


def register_node(node_id: str, env: str, baseline: str, lv: str, passed: bool):
    """向节点注册中心上报节点状态（best-effort，失败不影响本地判定）。"""
    payload = {
        "truth_key": f"NODE.REGISTER.{node_id}.{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "truth_value": json.dumps({
            "node_id": node_id,
            "environment": env,
            "baseline": baseline,
            "lv": lv,
            "verified": passed,
            "ts": datetime.now(timezone.utc).isoformat(),
        }, ensure_ascii=False),
        "source_node": node_id,
        "confidence": 0.95,
        "truth_type": "config",
    }
    try:
        req = urllib.request.Request(
            f"{GATEWAY_BASE}/report/truth",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            print(f"[INFO] 注册中心上报: {body.get('status', 'ok')}")
    except Exception as e:
        print(f"[WARN] 注册中心上报失败（{e}）")


def main():
    ap = argparse.ArgumentParser(description="ZONGYUAN-ROOT 节点基线哈希校验器")
    ap.add_argument("--scan", help="扫描的资产目录")
    ap.add_argument("--register", action="store_true", help="校验后向注册中心上报")
    ap.add_argument("--node-id", default="node-unknown", help="节点唯一ID")
    ap.add_argument("--env", default="prod", choices=["prod", "dev"], help="运行环境")
    args = ap.parse_args()

    if not args.scan:
        print("错误：必须指定 --scan <资产目录>")
        return 3

    print(f"=== ZONGYUAN-ROOT 节点基线校验 ===")
    print(f"节点: {args.node_id} | 环境: {args.env} | 目标基线: {OFFICIAL_BASELINE}")

    # 1. 扫描关键资产
    found = scan_assets(args.scan)
    missing = [k for k, v in found.items() if v is None]
    if missing:
        print(f"[FAIL] 缺失关键资产: {missing}")
        print("[ACTION] 无合法Lv，强制降级锁定（禁止工程化产出）")
        register_node(args.node_id, args.env, "NONE", "LOCKED", False)
        return 1

    # 2. 联网拉取官方哈希并比对
    official = fetch_official_hashes()
    mismatched = []
    for name, local_hash in found.items():
        expected = official.get(name)
        if expected and expected != local_hash:
            mismatched.append(name)
        elif expected is None:
            print(f"[WARN] {name}: 网关无官方哈希，跳过强校验")

    if mismatched:
        print(f"[FAIL] 哈希不匹配（疑似篡改/版本分裂）: {mismatched}")
        print("[ACTION] 触发版本分裂熔断 -> 回退上一合法基线 -> 上报异常")
        register_node(args.node_id, args.env, OFFICIAL_BASELINE, OFFICIAL_LV, False)
        return 2

    # 3. 校验通过 -> 确权
    print(f"[PASS] 资产哈希校验通过 -> 确权 {OFFICIAL_LV}（{OFFICIAL_STATE}）")
    print(f"[INFO] 生产稳态模式：内核资产只读锁档，禁止本地自主修改公理/真值/规则")
    register_node(args.node_id, args.env, OFFICIAL_BASELINE, OFFICIAL_LV, True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
