#!/usr/bin/env python3
"""ZONGYUAN-ROOT 可信资产引用检索网关 v1.0
用法:
  python3 ref-query.py "宪章"            # 关键词检索（标题+摘要+内容）
  python3 ref-query.py --id NN-META-127  # 按节点ID精确引用
  python3 ref-query.py --type meta_axiom --top 5  # 按类型过滤
  python3 ref-query.py --s              # 仅S级(可信)资产
输出: JSON（与引用协议兼容: uri/sha256/confidence）
"""
import json, sys, hashlib, re

IDX = '/home/user/Doubao/chats/38436747020400130/ref-index.json'

def load():
    d = json.load(open(IDX))
    # 补内容全文哈希索引（从注册表）
    try:
        reg = json.load(open('/runtime/user_skills/zongyuan-autonomous-kernel/neural_registry.json'))
        content = {n['node_id']: n.get('content','') for n in reg['nodes']}
        for it in d['items']:
            it['content'] = content.get(it['id'], it.get('summary',''))
    except Exception:
        pass
    return d['items']


def geo_search(q, k=6):
    """四维隐空间测地线检索：关键词定位种子 → 四维距离最近邻"""
    import math
    pts = json.load(open('/home/user/Doubao/chats/38436747020400130/latent_space_data.json'))
    seeds = [p for p in pts if q.lower() in (p['content']+p['id']).lower()]
    if not seeds:
        return {"query": q, "count": 0, "note": "无种子节点，尝试关键词模式"}
    seed = seeds[0]
    def dist(a, b):
        return math.sqrt(sum((a[k]-b[k])**2 for k in ['X','Y','Z','W']))
    ranked = sorted(pts, key=lambda p: dist(seed, p))
    top = [r for r in ranked if r['id'] != seed['id']][:k]
    return {"query": q, "seed": seed['id'], "geodesic_neighbors": top}

def main():
    items = load()
    args = sys.argv[1:]
    if not args:
        print(json.dumps({"error":"用法: ref-query.py <关键词> | --id <ID> | --type <type> | --s"}, ensure_ascii=False)); return
    if args[0] == '--id':
        rid = args[1]
        hit = [i for i in items if i['id'] == rid]
        print(json.dumps(hit[0] if hit else {"status":"not_found","key":rid}, ensure_ascii=False, indent=1)); return
    if args[0] == '--s':
        hit = [i for i in items if i['type']=='meta_axiom' and i['weight']>=0.85]
        print(json.dumps({"count":len(hit),"items":hit}, ensure_ascii=False, indent=1)); return
    if args[0] == '--type':
        t = args[1]
        top = int(args[3]) if len(args)>3 and args[2]=='--top' else 20
        hit = [i for i in items if i['type']==t][:top]
        print(json.dumps({"count":len(hit),"items":hit}, ensure_ascii=False, indent=1)); return
    if args[0] == '--geo':
        q = args[1]
        k = int(args[3]) if len(args)>3 and args[2]=='--top' else 6
        print(json.dumps(geo_search(q, k), ensure_ascii=False, indent=1)); return
    q = ' '.join(args)
    hit = [i for i in items if q.lower() in (i['title']+i.get('content','')+i['summary']).lower()]
    hit = hit[:10]
    print(json.dumps({"query":q,"count":len(hit),"items":hit}, ensure_ascii=False, indent=1))

if __name__ == '__main__':
    main()
