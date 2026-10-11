#!/usr/bin/env python3
"""
ZONGYUAN-ROOT 自动审批标准体系引擎 v1.0
公理: NN-META-147 分级标准 / 148 自动流转 / 149 审计闭环
衔接: lark-approval (AIOS阶段验收定义) | DID-BR-000002 | Ω₀⊂⊙∞⊂Ω

五段闭环:
  ① 审批分级(P0/P1/P2) → ② 定义路由+表单标准化 → ③ 自动提单(need_approver=false自动流转)
  → ④ 状态核验 → ⑤ 审计固化+云内核上报+锁档

分级标准(NN-META-147):
  P0紧急(熔断/安全修复) → 直接执行+事后备案
  P1标准(部署/额度消耗/资产变更) → 标准化审批自动流转APPROVED
  P2备案(理论/文档/锁档) → 直接锁档上报即备案

用法:
  python3 approval_engine.py route --type P1 --item "官网部署" --detail "..."  [--dry-run|--submit]
  python3 approval_engine.py demo
"""
import json, sys, os, datetime, argparse, subprocess

APPROVAL_CODE = "50C17D4E-ECF1-41D0-8E3F-1650AB500CA2"
CONTROLS = {
    "project": "widget16457732057390001",       # input  AIOS验收项目
    "phase": "widget17890613898300001",         # input  阶段名
    "items": "widget16462072487340001",         # textarea 验收项
    "final": "widget17890613783360001",         # textarea 终审点
    "conclusion": "widget17890614456220001",    # radioV2 验收结论
    "date": "widget16457732647360001",          # dateInterval
    "participants": "widget16457743012420001",  # contact
}
PASS_VALUE = "mtvszqba-0niul8oljz7o-0"
AUDIT_DIR = '/home/user/Doubao/chats/38436747020400130/.approval_audit'

def classify(item, urgency=""):
    """① 审批分级"""
    kw = f"{item}{urgency}"
    if any(k in kw for k in ['熔断','故障','安全漏洞','紧急修复','攻破']):
        return "P0"
    if any(k in kw for k in ['部署','上线','额度','消耗','采购','资产变更','外部写入','服务器']):
        return "P1"
    return "P2"

def build_form(project, phase, items, final, conclusion="通过"):
    """② 表单标准化生成（AIOS定义控件）"""
    c = CONTROLS
    form = [
        {"id": c['project'], "type": "input", "value": project},
        {"id": c['phase'], "type": "input", "value": phase},
        {"id": c['items'], "type": "textarea", "value": items},
        {"id": c['final'], "type": "textarea", "value": final},
        {"id": c['conclusion'], "type": "radioV2", "value": PASS_VALUE if conclusion == "通过" else "mtvszqba-h72sk9eyvf-0"},
        {"id": c['date'], "type": "dateInterval", "value": {"start": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00"), "end": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00"), "interval": 1.0}},
        {"id": c['participants'], "type": "contact", "value": ["fageb3b5"], "open_ids": ["ou_41b49aeaa69bca84bc65780805e65664"]},
    ]
    return json.dumps(form, ensure_ascii=False)

def submit(approval_code, form_json, dry_run=True):
    """③ 自动提单（need_approver=false → 自动流转）"""
    cmd = ['lark-cli', 'approval', 'instances', 'create',
           '--data', json.dumps({"approval_code": approval_code, "form": form_json}),
           '--as', 'user'] + (['--dry-run'] if dry_run else ['--yes'])
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return r.returncode == 0, r.stdout[-500:], r.stderr[-200:]

def route(item, detail, phase, dry_run=True):
    """全流程路由"""
    os.makedirs(AUDIT_DIR, exist_ok=True)
    level = classify(item, detail)
    print(f"[1] 审批分级: {level} — {item}")
    if level in ("P0","P2"):
        act = "EXECUTE_AND_FILE" if level == "P0" else "LOCK_AND_REPORT"
        print(f"[2] {'P0紧急: 直接执行+事后备案' if level=='P0' else 'P2备案: 直接锁档上报即备案'}（无需飞书审批单）")
        rec = {"level": level, "item": item, "action": act}
    else:
        form = build_form(f"ZONGYUAN-ROOT-{item}", phase, detail,
                          f"终审: {item} — {phase} — 全域锁档上报云内核")
        print(f"[2] 表单标准化生成: {len(form)}B (控件7项)")
        if dry_run:
            print(f"[3] 提单预览(dry-run): approval_code={APPROVAL_CODE[:8]}... form已生成")
            rec = {"level": level, "item": item, "form": json.loads(form), "submitted": False, "dry_run": True}
        else:
            ok, out, err = submit(APPROVAL_CODE, form, dry_run=False)
            print(f"[3] 自动提单: {'✅' if ok else '❌'} {out[:200] if ok else err[:200]}")
            rec = {"level": level, "item": item, "submitted": ok, "output": out[:300] if ok else err[:300]}
    fp = f"{AUDIT_DIR}/approval_{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    json.dump(rec, open(fp,'w'), ensure_ascii=False, indent=1)
    print(f"[5] 审计固化: {fp}")
    return rec

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['route','demo'])
    ap.add_argument('--type', default='P1', choices=['P0','P1','P2'])
    ap.add_argument('--item', default='标准变更')
    ap.add_argument('--detail', default='')
    ap.add_argument('--phase', default='阶段验收')
    ap.add_argument('--submit', action='store_true')
    a = ap.parse_args()
    if a.cmd == 'demo':
        print("=== 自动审批标准体系 · 分级演示 ===\n")
        print("— P0 样例 —"); route("安全熔断", "检测到外部攻破风险，立即熔断外联", "应急", dry_run=True)
        print("— P1 样例 —"); route("官网部署", "AI可引用资产部署上线(审批双通过后)", "上线", dry_run=True)
        print("— P2 样例 —"); route("三元本体理论文档", "理论+机制锁档上报", "备案", dry_run=True)
    else:
        route(a.item, a.detail or a.item, a.phase, dry_run=not a.submit)

if __name__ == '__main__':
    main()
