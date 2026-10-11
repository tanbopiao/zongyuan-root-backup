# -*- coding: utf-8 -*-
"""创造性开放式评分器：对非JSON自由文本输出评分（新颖/多样/可执行/相关）"""
import re, json

DIMENSIONS = {
    "novelty":   {"weight":0.3, "kws":["创新","新方向","突破","池化","融合","重构","迁移","组合","演化","跃迁","复用","闭环"]},
    "diversity": {"weight":0.2, "kws":["跨域","多源","多GPU","全域","多模态","矩阵","资源池","场景","路径","层次","体系","平台"]},
    "executable": {"weight":0.3, "kws":["规划","步骤","方案","部署","机制","规范","流程","探针","切换","上报","落地","注册","配置"]},
    "relevance": {"weight":0.2, "kws":["GPU","中枢","worker","真值","锁档","节点","引擎","P14","Lv10","GA","稳态","决策","体系"]},
}

def score(text):
    if not text or len(text) < 15:
        return {"total":0.0,"detail":{k:0 for k in DIMENSIONS},"len":len(text or "")}
    detail = {}
    for dim, cfg in DIMENSIONS.items():
        hits = sum(1 for k in cfg["kws"] if k in text)
        ratio = min(hits / 3, 1.0)          # 每维最多3个关键词满
        detail[dim] = round(ratio * 100, 1)
    total = round(sum(detail[d]*DIMENSIONS[d]["weight"] for d in DIMENSIONS), 1)
    return {"total": total, "detail": detail, "len": len(text)}

def grade(text, threshold=60):
    r = score(text)
    verdict = "PASS" if r["total"] >= threshold else "REVIEW"
    return verdict, r

if __name__ == "__main__":
    # 自测样例
    t = "创新方案：构建多GPU资源池，跨域迁移融合中枢与worker，规划探针切换与上报闭环"
    print(grade(t))
