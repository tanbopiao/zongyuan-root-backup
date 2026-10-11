#!/usr/bin/env python3
"""
ZONGYUAN-ROOT 隐空间测地线任务路由引擎 v1.0
原理: 任务描述 → 域关键词定位种子 → 四维隐空间最近邻 → 匹配资产+路由决策
衔接: 调度器V1.2 (submit时附加 routed_domain/routed_assets 到payload)

用法:
  python3 task-router.py "渲染短剧第1集9:16竖屏关键帧"
  python3 task-router.py --list-domains
"""
import json, math, sys

LATENT = '/home/user/Doubao/chats/38436747020400130/latent_space_data.json'
REG = '/runtime/user_skills/zongyuan-autonomous-kernel/neural_registry.json'

DOMAIN_KEYWORDS = {
    'production': ['渲染','视频','竖屏','9:16','关键帧','短剧','分镜','素材','生成','镜头','流水线','量产'],
    'security': ['审计','锁档','校验','密钥','安全','鉴权','哈希','风控','熔断','告警','保密'],
    'ops': ['调度','同步','归档','上报','心跳','队列','部署','运维','监控','备份','恢复'],
    'meta': ['公理','法则','宪章','理论','哲学','数学','物理','元','隐空间','本体','认识论'],
    'education': ['课程','教育','普惠','教学','学习','知识','学生','通识'],
    'character': ['角色','神女','人设','母版','形象','造型','IP','世界观'],
    'user_experience': ['体验','交互','界面','反馈','可用性','感知','设计系统'],
}

def dist(a, b):
    return math.sqrt(sum((a[k]-b[k])**2 for k in ['X','Y','Z','W']))

def load():
    pts = json.load(open(LATENT))
    # 合并节点内容摘要
    reg = json.load(open(REG))
    content = {n['node_id']: str(n.get('content','')) for n in reg['nodes']}
    for p in pts:
        p['content_full'] = content.get(p['id'], p.get('content',''))
    return pts

def route(task_text, top_n=4):
    pts = load()
    # 1) 域命中评分
    scores = {}
    for dom, kws in DOMAIN_KEYWORDS.items():
        hit = sum(1 for k in kws if k in task_text)
        if hit: scores[dom] = hit
    if not scores:
        return {"task": task_text, "status": "no_domain_hit", "note": "未命中任何域关键词，默认meta", "recommended_domain": "meta"}
    best_dom = max(scores, key=scores.get)
    # 2) 该域种子：域内节点取真值度最高者
    dom_pts = [p for p in pts if p['domain'] == best_dom and p['state'] != 'superseded']
    seed = max(dom_pts, key=lambda p: p['X'])
    # 3) 四维最近邻（跨域，展示匹配资产）
    ranked = sorted(pts, key=lambda p: dist(seed, p))
    neighbors = [r for r in ranked if r['id'] != seed['id']][:top_n]
    # 4) 路由决策
    return {
        "task": task_text,
        "recommended_domain": best_dom,
        "domain_scores": scores,
        "seed_asset": {"id": seed['id'], "domain": seed['domain'], "X": seed['X']},
        "matched_assets": [{"id": n['id'], "domain": n['domain'], "type": n['type'],
                            "d": round(dist(seed, n), 3), "summary": n.get('content_full','')[:48]} for n in neighbors],
        "suggested_worker": {"capability": best_dom, "match_score": round(scores[best_dom]/max(scores.values()), 2)}
    }

def main():
    args = sys.argv[1:]
    if not args:
        print(json.dumps({"usage": "python3 task-router.py \"任务描述\" | --list-domains"}, ensure_ascii=False)); return
    if args[0] == '--list-domains':
        print(json.dumps(DOMAIN_KEYWORDS, ensure_ascii=False, indent=1)); return
    print(json.dumps(route(' '.join(args)), ensure_ascii=False, indent=1))

if __name__ == '__main__':
    main()
