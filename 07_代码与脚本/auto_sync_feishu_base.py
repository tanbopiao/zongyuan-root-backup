#!/usr/bin/env python3
"""
ZONGYUAN-ROOT 飞书Base自动同步脚本 (auto_sync_feishu_base.py)
把本地持久层增量资产/真值自动同步到飞书共享大脑台账，增量优先、失败快速跳过。

同步目标表(共享大脑 base_token=DgnMbLqZiaIUDKshqCrcD4DvnBg):
  - 真值共识区  tbl9QxL35rwA16eS
  - 上报总表    tbl524eo7FnEa8ht
  - 节点状态总览 tblOmIRJtTn2EsvM

增量源:
  - 本地持久层真值: 06_云端中枢同步/*.json (新真值包)
  - 同步游标: 06_云端中枢同步/feishu_sync_state.json (记录已同步key)

原则: 增量优先、单次限流、失败快速跳过不重试、空闲跳过。
用法: python3 auto_sync_feishu_base.py [--dry-run]
"""
import json, os, glob, sys, subprocess, datetime, hashlib

ZR_ROOT = "/home/user/ZONGYUAN-ROOT"
SYNC_DIR = f"{ZR_ROOT}/06_云端中枢同步"
STATE_FILE = f"{SYNC_DIR}/feishu_sync_state.json"
BASE_TOKEN = "DgnMbLqZiaIUDKshqCrcD4DvnBg"
TABLES = {
    "truth": "tbl9QxL35rwA16eS",   # 真值共识区
    "report": "tbl524eo7FnEa8ht",  # 上报总表
    "node": "tblOmIRJtTn2EsvM",    # 节点状态总览
}
SOURCE_NODE = "NODE-DEV-DOUBAO-WORK-001"
MAX_PER_RUN = 8   # 单次最多同步条数
LARK = "lark-cli"


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            return json.load(open(STATE_FILE))
        except Exception:
            pass
    return {"synced_keys": [], "last_run": None, "total_synced": 0}


def save_state(st):
    json.dump(st, open(STATE_FILE, "w"), ensure_ascii=False, indent=2)


def list_candidate_truths():
    """收集本地持久层新增真值包(06_云端中枢同步/*.json, 排除状态/审计/镜像文件)"""
    cands = []
    skip = {"feishu_sync_state.json", "pull_state.json", "truths_batch"}
    for fp in glob.glob(f"{SYNC_DIR}/*.json"):
        fn = os.path.basename(fp)
        if any(s in fn for s in skip):
            continue
        # 提取真值标识: 取文件名做hash + 基础信息
        cands.append({"file": fp, "key": f"ZR-FS-SYNC-{hashlib.md5(fp.encode()).hexdigest()[:12]}",
                      "mtime": os.path.getmtime(fp)})
    cands.sort(key=lambda x: x["mtime"])
    return cands


def write_base(table_id, fields):
    """用 record-batch-create 写入(与既有V1.1/V1.3写入方式一致)，字段为已验证核心4项"""
    try:
        payload = {"create_records": [fields]}
        cmd = [LARK, "base", "+record-batch-create", "--base-token", BASE_TOKEN,
               "--table-id", table_id, "--json", json.dumps(payload, ensure_ascii=False),
               "--as", "user"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return json.loads(r.stdout).get("ok", False)
    except Exception:
        return False


def main():
    # 双轴前置校验（P1安全底线）
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from dual_axis_precheck import precheck, print_result
        pc = precheck("auto_sync_feishu_base", risk_override="medium")
        print_result(pc, verbose=False)
        if pc.blocked:
            print("[FEISHU-BASE] 双轴校验阻断，终止执行", flush=True)
            return
    except Exception as _e:
        print(f"[FEISHU-BASE] 双轴前置校验模块不可用({_e})，继续执行", flush=True)

    dry = "--dry-run" in sys.argv
    st = load_state()
    cands = list_candidate_truths()
    new_cands = [c for c in cands if c["key"] not in st["synced_keys"]]
    if not new_cands:
        print("空闲跳过: 无新增真值需同步 (最小额度原则)")
        st["last_run"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_state(st)
        return

    # 限流
    batch = new_cands[:MAX_PER_RUN]
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ok = 0
    for c in batch:
        try:
            content = open(c["file"], encoding="utf-8").read()
        except Exception:
            continue
        # 精简内容: 截取可读片段
        snippet = content[:300] if len(content) > 300 else content
        # 1. 真值共识区 (仅4个已验证字段)
        fields = {
            "真值key": os.path.basename(c["file"]).replace(".json", ""),
            "真值内容": f"[{now}]{snippet}",
            "最终状态": "已达成共识",
            "确认节点": SOURCE_NODE,
        }
        if dry:
            print(f"[DRY] 拟同步: {c['key']} -> 真值共识区")
            ok += 1
        else:
            if write_base(TABLES["truth"], fields):
                ok += 1
            else:
                print(f"  跳过 {c['key']} (写入失败)")
        st["synced_keys"].append(c["key"])
    st["total_synced"] = st.get("total_synced", 0) + ok
    st["last_run"] = now
    save_state(st)

    # 上报总表留痕
    if not dry:
        write_base(TABLES["report"], {
            "真值key": f"ZR-FS-AUTOSYNC-{now.replace(' ','T')}",
            "真值内容": f"飞书Base自动同步 {len(batch)}条 成功{ok}条 节点{SOURCE_NODE}",
            "最终状态": ["已达成共识"],
            "确认节点": SOURCE_NODE,
        })
    print(f"完成: 候选{len(cands)} 新增{len(new_cands)} 本次同步{len(batch)} 成功{ok} (dry={dry})")


if __name__ == "__main__":
    main()
