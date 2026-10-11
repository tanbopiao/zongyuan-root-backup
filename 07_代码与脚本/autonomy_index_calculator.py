#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MR-020 M2 自治指数实时计算器
自治指数 = 自我纠错能力 × 自我演化速度 × 自我驱动强度 × (1 - 外部依赖度)
输入: JSON参数（可从六维审计/体系运行数据采集）
输出: 自治指数(0-100%) + 等级 + 分项明细
等级: <20他律 | 20-40初级 | 40-60中级 | 60-80高级 | 80-100永恒自治
"""
import json, sys, datetime

def calc(params: dict) -> dict:
    c = float(params.get("correction", 0))   # 自我纠错 0-100
    e = float(params.get("evolution", 0))    # 自我演化 0-100
    d = float(params.get("drive", 0))        # 自我驱动 0-100
    dep = min(max(float(params.get("dependency", 0)), 0), 1)  # 外部依赖 0-1
    raw = c * e * d * (1 - dep) / 10000.0    # 归一 0-100
    idx = round(raw, 1)
    level = ("永恒自治" if idx >= 80 else "高级自治" if idx >= 60
             else "中级自治" if idx >= 40 else "初级自治" if idx >= 20 else "他律系统")
    return {"autonomy_index": idx, "level": level,
            "components": {"correction": c, "evolution": e, "drive": d, "dependency": dep},
            "formula": "纠错×演化×驱动×(1-依赖)/10000", "timestamp": datetime.datetime.now().isoformat()}

def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            params = json.load(f)
    else:
        params = {"correction": 80, "evolution": 75, "drive": 70, "dependency": 0.25}
    r = calc(params)
    print(f"\n═══ MR-020 M2 自治指数 ═══")
    print(f"  纠错能力   : {r['components']['correction']}")
    print(f"  演化速度   : {r['components']['evolution']}")
    print(f"  驱动强度   : {r['components']['drive']}")
    print(f"  外部依赖度 : {r['components']['dependency']}")
    print(f"  ──────────────────────────")
    print(f"  自治指数   : {r['autonomy_index']}% ｜ 等级: {r['level']}")
    with open("/home/user/Doubao/chats/38438412455799554/mr020-kernel-bootstrap-20260915/m2-autonomy-closed-loop/autonomy-index-result.json", "w") as f:
        json.dump(r, f, ensure_ascii=False, indent=2)
    print("  结果已写: autonomy-index-result.json")

if __name__ == "__main__":
    main()
