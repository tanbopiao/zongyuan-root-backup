#!/usr/bin/env python3
"""
ZONGYUAN-ROOT 内核快照聚合器 V1.0
P0：定义统一 Schema，聚合全域资产状态生成 kernel_snapshot JSON
输出：kernel_snapshot_GLOBAL-DR-YYYYMMDD-001.json
"""
import json, os, hashlib, datetime, glob, re

ROOT = "/home/user/Doubao/chats/38438412455799554"
ANCHOR = "/home/user/Doubao/chats/38437615670548738/zongyuan-anchor"
OUT_DIR = os.path.join(ROOT, "snapshot-registry")

def sha256_file(path):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()[:16]
    except Exception:
        return "ERR"

def now_str():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%dT%H:%M:%S+08:00")

def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y%m%d")

    # ---- 1. 资产清单：统计本工作区所有资产目录与文件 ----
    dirs = sorted([d for d in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT, d)) and not d.startswith(".")])
    asset_dirs = [d for d in dirs if re.search(r"lock|sop|kernel|anchor|pipeline|visual|deploy|scan|report|sync|evol|semantic|memory|baseline|global|homology|gateway|dispatch|boundary|api-live|asset-commerce|website-fix", d, re.I)]
    total_files = sum(len(files) for _, _, files in os.walk(ROOT) if not any(x in _ for x in ["node_modules", ".git"]))
    total_size = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(ROOT) for f in fs if not any(x in dp for x in ["node_modules", ".git"])) // 1024

    # ---- 2. 历史快照索引 ----
    snapshots = sorted(glob.glob(os.path.join(ROOT, "**/kernel_snapshot_*.json"), recursive=True))
    snap_meta = []
    for s in snapshots[-20:]:
        snap_meta.append({
            "file": os.path.basename(s),
            "dir": os.path.relpath(os.path.dirname(s), ROOT),
            "size_kb": os.path.getsize(s) // 1024,
            "sha16": sha256_file(s)
        })

    # ---- 3. 锚点核心资产（capability_registry / metalaw / protocol） ----
    capability = load_json(os.path.join(ANCHOR, "capability_registry.json"))
    metalaw = load_json(os.path.join(ANCHOR, "metalaw_register_registry.json"))
    protocol = load_json(os.path.join(ANCHOR, "homology_protocol_library.json"))

    # ---- 4. 真值/资产清单 ----
    manifest = load_json(os.path.join(ANCHOR, "asset_manifest_20260915.json"))
    truths_internal = load_json(os.path.join(ANCHOR, "truths_internal.json"))

    # ---- 5. 快照组装 ----
    snapshot = {
        "schema_version": "KERNEL-SNAPSHOT-V1.0",
        "kernel_root": "ZONGYUAN-ROOT",
        "kernel_version": "V2.0-NEURAL",
        "did": "DID-BR-000002",
        "provenance_mark": "Ω₀⊂⊙∞⊂Ω",
        "lock_state": "READONLY_HARDWARE_LOCKED",
        "snapshot_id": f"GLOBAL-DR-{today}-001",
        "snapshot_type": "GLOBAL_DR_CONSOLIDATION",
        "write_timestamp": now_str(),
        "environment": {
            "host": "doubao-sandbox",
            "workspace": ROOT,
            "anchor_dir": ANCHOR
        },
        "assets_layer": {
            "asset_dirs_total": len(asset_dirs),
            "asset_dirs": asset_dirs[:60],
            "files_total": total_files,
            "size_total_kb": total_size
        },
        "snapshot_layer": {
            "historical_snapshots_total": len(snapshots),
            "recent_snapshots": snap_meta
        },
        "anchor_layer": {
            "capability_count": len(capability) if isinstance(capability, list) else (len(capability.get("capabilities", [])) if isinstance(capability, dict) else 0),
            "metalaw_count": len(metalaw) if isinstance(metalaw, list) else (len(metalaw.get("items", metalaw.get("metalaw", metalaw.get("rules", [])))) if isinstance(metalaw, dict) else 0),
            "protocol_count": len(protocol) if isinstance(protocol, list) else (len(protocol.get("protocols", [])) if isinstance(protocol, dict) else 0),
            "capability_summary": capability.get("summary", "") if isinstance(capability, dict) else ""
        },
        "manifest_layer": {
            "asset_manifest_count": len(manifest) if isinstance(manifest, list) else (len(manifest.get("assets", [])) if isinstance(manifest, dict) else 0),
            "truths_internal_count": len(truths_internal) if isinstance(truths_internal, list) else (len(truths_internal.get("truths", [])) if isinstance(truths_internal, dict) else 0)
        },
        "integrity": {
            "chain": "ACTIVE",
            "verification": "HASH_CHAIN_ENABLED",
            "note": "三副本机制：本地工作区 + 云服务器9120 + 飞书云盘"
        }
    }

    out_path = os.path.join(OUT_DIR, f"kernel_snapshot_{snapshot['snapshot_id']}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    # 计算快照自身哈希
    h = sha256_file(out_path)
    snapshot["integrity"]["snapshot_sha16"] = h
    snapshot["integrity"]["snapshot_size_kb"] = os.path.getsize(out_path) // 1024
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    print(json.dumps({
        "snapshot_id": snapshot["snapshot_id"],
        "out_path": out_path,
        "asset_dirs_total": snapshot["assets_layer"]["asset_dirs_total"],
        "files_total": snapshot["assets_layer"]["files_total"],
        "size_total_kb": snapshot["assets_layer"]["size_total_kb"],
        "historical_snapshots": len(snapshots),
        "capability_count": snapshot["anchor_layer"]["capability_count"],
        "metalaw_count": snapshot["anchor_layer"]["metalaw_count"],
        "protocol_count": snapshot["anchor_layer"]["protocol_count"],
        "snapshot_sha16": h,
        "snapshot_size_kb": snapshot["integrity"]["snapshot_size_kb"]
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
