#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
boundary_explorer.py — 全域最大边界探索·核心真值提炼机制
探索六域最大边界：①记忆网关 ②本地锁档快照 ③SOP文档 ④真值包 ⑤流水线产物 ⑥同源协议
提炼核心真值 → 去重增量 → 生成探索报告 → 上报记忆网关

用法: python3 boundary_explorer.py [--report] 
--report: 生成可视化探索报告 HTML（默认同时生成）
"""
import json, os, re, glob, hashlib, datetime, urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
CHATS = os.path.abspath(os.path.join(ROOT, ".."))
PIPE = os.path.join(CHATS, "pipeline-auto", "pipeline")
STATE = os.path.join(ROOT, "data")
os.makedirs(STATE, exist_ok=True)

def now_iso():
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00")

def fetch_json(url, timeout=12):
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)[:80]}

# ===================== 探索域 =====================
def explore_gateway():
    """域① 记忆网关最大边界"""
    d = fetch_json("https://www.huodouai.com/digital_assets.json")
    if "error" in d:
        return {"ok": False, "error": d["error"]}
    truths = d.get("truths", {})
    return {
        "ok": True,
        "total": truths.get("total", 0),
        "daily_growth": truths.get("daily_growth", []),
        "categories": truths.get("by_category", {}),
        "meta_rules_total": d.get("meta_rules", {}).get("total", 0),
        "meta_rules_latest": d.get("meta_rules", {}).get("latest", []),
        "services": d.get("services", []),
        "system": d.get("system", {}),
        "web_assets": d.get("web_assets", {}),
        "classification": d.get("classification", []),
        "generated_at": d.get("generated_at", ""),
    }

def explore_snapshots():
    """域② 本地锁档快照最大边界"""
    snaps = []
    seen = set()
    for p in glob.glob(os.path.join(CHATS, "**", "kernel_snapshot*.json"), recursive=True):
        try:
            s = json.load(open(p, encoding="utf-8"))
            lid = s.get("lock_event_id") or os.path.basename(p)
            if lid in seen: continue
            seen.add(lid)
            snaps.append({
                "id": lid,
                "name": s.get("lock_event_name", ""),
                "ts": s.get("write_timestamp", ""),
                "wiki": s.get("wiki_archive_url", ""),
                "anchor": s.get("axiom_anchor", ""),
                "layers": list((s.get("architecture_layer") or {}).get("layers", [])),
            })
        except Exception:
            pass
    return sorted(snaps, key=lambda x: x["ts"], reverse=True)

def explore_sops():
    """域③ SOP 文档最大边界"""
    sops = []
    for p in glob.glob(os.path.join(CHATS, "**", "*SOP*.md"), recursive=True) + \
             glob.glob(os.path.join(CHATS, "**", "*sop*.md"), recursive=True) + \
             glob.glob(os.path.join(CHATS, "**", "SOP*.md"), recursive=True):
        try:
            with open(p, encoding="utf-8") as f:
                content = f.read()
            title = os.path.basename(p).replace(".md", "")
            # 提取前2行标题/描述
            head = "\n".join(content.split("\n")[:4]).strip()[:120]
            sops.append({"path": p, "title": title, "size": len(content), "head": head})
        except Exception:
            pass
    # 去重
    seen, uniq = set(), []
    for s in sops:
        if s["path"] in seen: continue
        seen.add(s["path"]); uniq.append(s)
    return uniq

def explore_truth_packs():
    """域④ 本地真值包最大边界"""
    packs = []
    for p in glob.glob(os.path.join(CHATS, "**", "kernel_truths.json"), recursive=True):
        try:
            d = json.load(open(p, encoding="utf-8"))
            if isinstance(d, dict):
                truths = d.get("truths") or d.get("kernel_truths") or d
                if isinstance(truths, list):
                    packs.append({"path": p, "count": len(truths)})
                elif isinstance(truths, dict):
                    packs.append({"path": p, "count": len(truths)})
        except Exception:
            pass
    return packs

def explore_pipeline():
    """域⑤ 流水线产物最大边界"""
    out = {}
    for f in ["new_assets", "asset_cards", "product_entries", "pricing_results", "circulation_results"]:
        try:
            d = json.load(open(os.path.join(PIPE, "data", f + ".json"), encoding="utf-8"))
            out[f] = d
        except Exception:
            out[f] = {}
    return out

def explore_protocols():
    """域⑥ 同源协议最大边界（按key拉取）"""
    keys = [
        "PROTOCOL.NODE.UNIFY.V1",
        "PROTOCOL.API.NODE_REPORT.V1",
        "RULE.NODE.REGISTRY.CENTER.V1",
        "PROTOCOL.NODE.FALLBACK.ROLLBACK.V1",
        "META_LAW.NODE.LV.CONFIRM.MA002",
        "META_LAW.AHI.SINGULARITY.DERIVATION.V1",
        "META_LAW.SELF_IMPROVE_LOOP.IMPLEMENTED.V1",
    ]
    protos = []
    for k in keys:
        d = fetch_json(f"https://www.huodouai.com/api/truths/{k}")
        t = d.get("truth", {})
        if t:
            protos.append({"key": k, "value": t.get("truth_value", "")[:200]})
    return protos

# ===================== 核心真值提炼 =====================
def distill(domains, prev_state):
    """从六域探索结果提炼核心真值（增量去重）"""
    distilled = []
    seen = set(prev_state.get("seen_truths", []))
    now = now_iso()

    gw = domains["gateway"]
    if gw.get("ok"):
        # 1. 网关元规则最新
        for mr in gw.get("meta_rules_latest", [])[:10]:
            rid = mr.get("rule_id", "")
            if rid and rid not in seen:
                seen.add(rid)
                distilled.append({
                    "truth_key": f"TRUTH.EXPLORE.META_RULE.{rid}",
                    "truth_value": f"[全域探索] 新元规则: {mr.get('name','')} | {str(mr.get('content',''))[:120]}",
                    "truth_type": "meta_law", "domain": "网关元规则", "confidence": 0.9,
                })
        # 2. 真值总量状态
        distilled.append({
            "truth_key": f"TRUTH.EXPLORE.GATEWAY.STATE.{datetime.datetime.now().strftime('%Y%m%d')}",
            "truth_value": f"[全域探索] 记忆网关状态: 真值总量={gw.get('total')}, 元规则={gw.get('meta_rules_total')}, 服务={len(gw.get('services',[]))}个, 生成时间={gw.get('generated_at','')}",
            "truth_type": "data", "domain": "网关状态", "confidence": 0.95,
        })

    # 3. 锁档快照新增
    snaps = domains["snapshots"]
    for s in snaps[:8]:
        sid = s["id"]
        if sid not in seen:
            seen.add(sid)
            distilled.append({
                "truth_key": f"LOCK.{sid}",
                "truth_value": f"[全域探索] 锁档资产: {s['name']} | 锚点={s['anchor']} | 时间={s['ts'][:10]}",
                "truth_type": "data", "domain": "锁档快照", "confidence": 0.9,
            })

    # 4. SOP 文档边界
    sops = domains["sops"]
    distilled.append({
        "truth_key": f"TRUTH.EXPLORE.SOP.BOUNDARY.{datetime.datetime.now().strftime('%Y%m%d')}",
        "truth_value": f"[全域探索] SOP文档边界: 共{len(sops)}份 SOP 文档, 覆盖: {', '.join([s['title'][:24] for s in sops[:6]])}",
        "truth_type": "data", "domain": "SOP边界", "confidence": 0.95,
    })

    # 5. 同源协议
    protos = domains["protocols"]
    distilled.append({
        "truth_key": f"TRUTH.EXPLORE.PROTOCOL.BOUNDARY.{datetime.datetime.now().strftime('%Y%m%d')}",
        "truth_value": f"[全域探索] 同源协议边界: {len(protos)}条协议已学习, 覆盖: {', '.join([p['key'][:30] for p in protos[:5]])}",
        "truth_type": "protocol", "domain": "协议边界", "confidence": 0.95,
    })

    return distilled, list(seen)

# ===================== 报告生成 =====================
def build_report(domains, distilled, run_id):
    gw = domains["gateway"]
    snaps = domains["snapshots"]
    sops = domains["sops"]
    packs = domains["truth_packs"]
    pl = domains["pipeline"]

    gw_total = gw.get("total", 0) if gw.get("ok") else 0
    svc = gw.get("services", [])
    svc_on = len([s for s in svc if str(s.get("status","")).lower()=="online"])
    svc_total = len(svc) or 1

    # 分类top
    cats = sorted(gw.get("categories", {}).items(), key=lambda x:-x[1])[:10]
    cat_rows = ""
    max_cat = max([c[1] for c in cats], default=1)
    for name, cnt in cats:
        w = int(cnt/max_cat*100)
        cat_rows += f'<div class="cat-row"><span class="cn">{name}</span><div class="cb"><i style="width:{w}%"></i></div><span class="cc">{cnt}</span></div>'

    # SOP 卡片
    sop_cards = ""
    for s in sops[:8]:
        sop_cards += f'<div class="sop-card"><div class="sop-t">{s["title"]}</div><div class="sop-s">{s["size"]}B</div></div>'

    # 锁档表
    snap_rows = ""
    for s in snaps[:10]:
        snap_rows += f'<tr><td class="mono">{s["id"]}</td><td>{s["name"][:36]}</td><td class="mono">{s["ts"][:10]}</td></tr>'

    # 提炼真值列表
    truth_rows = ""
    for t in distilled[:12]:
        truth_rows += f'<div class="truth-item"><span class="tt">{t["truth_type"]}</span><span class="tv">{t["truth_value"][:80]}</span><span class="td">{t["domain"]}</span></div>'

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>全域最大边界探索报告 · Boundary Explorer</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%230a0a0f'/%3E%3Cpath d='M32 6l4 16 16 4-16 4-4 16-4-16-16-4 16-4z' fill='%23d4af37'/%3E%3C/svg%3E">
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>
:root{{--bg:#07070b;--bg2:#0c0c13;--card:#101018;--card2:#14141e;--gold:#d4af37;--gold-l:#f0d68a;--gold-d:#8a6d1f;--gold-grad:linear-gradient(135deg,#f0d68a,#d4af37 45%,#9a7b22);--txt:#eae6dc;--txt2:#a39e90;--txt3:#6d685c;--line:rgba(212,175,55,.16);--line2:rgba(212,175,55,.34);--ok:#4ecb8d;--off:#c95555;--serif:'Noto Serif SC',serif;--sans:'Noto Sans SC',system-ui,sans-serif}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:var(--bg);color:var(--txt);font-family:var(--sans);line-height:1.6}}
body::before{{content:"";position:fixed;inset:0;z-index:-2;background:radial-gradient(1100px 500px at 20% -10%,rgba(212,175,55,.07),transparent 60%),radial-gradient(800px 500px at 90% 20%,rgba(212,175,55,.05),transparent 55%),var(--bg)}}
.container{{max-width:1280px;margin:0 auto;padding:0 24px}}
.section{{padding:60px 0}}
.sec-head{{text-align:center;margin-bottom:38px}}
.sec-tag{{display:inline-flex;align-items:center;gap:8px;font-size:12px;letter-spacing:3px;color:var(--gold);border:1px solid var(--line2);border-radius:999px;padding:5px 18px;margin-bottom:14px;background:rgba(212,175,55,.06)}}
.sec-title{{font-family:var(--serif);font-size:32px;font-weight:700;letter-spacing:2px}}
.sec-title .gl{{background:var(--gold-grad);-webkit-background-clip:text;background-clip:text;color:transparent}}
.sec-sub{{color:var(--txt2);font-size:14px;margin-top:10px}}
.hero{{min-height:70vh;display:flex;align-items:center;padding:80px 0 40px;position:relative;overflow:hidden}}
.hero::after{{content:"";position:absolute;inset:0;background:radial-gradient(600px 600px at 85% 50%,rgba(212,175,55,.1),transparent 60%)}}
.hero-inner{{position:relative;z-index:2}}
.hero-eyebrow{{display:inline-flex;gap:10px;align-items:center;font-size:12px;letter-spacing:4px;color:var(--gold-l);border:1px solid var(--line2);padding:8px 20px;border-radius:4px;background:rgba(212,175,55,.07);margin-bottom:26px}}
.hero-eyebrow .dot{{width:7px;height:7px;border-radius:50%;background:var(--gold);box-shadow:0 0 12px var(--gold)}}
.hero-title{{font-family:var(--serif);font-size:clamp(36px,5.4vw,58px);font-weight:900;line-height:1.15;letter-spacing:3px;margin-bottom:18px}}
.hero-title .gold{{background:var(--gold-grad);-webkit-background-clip:text;background-clip:text;color:transparent;display:block}}
.hero-title .thin{{font-weight:300;color:var(--txt2);font-size:clamp(14px,2vw,18px);display:block;margin-top:12px;letter-spacing:5px}}
.hero-desc{{color:var(--txt2);font-size:15px;max-width:640px;margin-bottom:30px}}
.hero-stats{{display:flex;flex-wrap:wrap;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:rgba(16,16,24,.7)}}
.hstat{{flex:1;min-width:130px;padding:16px 20px;border-right:1px solid var(--line)}}
.hstat:last-child{{border-right:none}}
.hstat .num{{font-family:var(--serif);font-size:26px;font-weight:700;background:var(--gold-grad);-webkit-background-clip:text;background-clip:text;color:transparent}}
.hstat .lab{{font-size:11px;color:var(--txt3);letter-spacing:2px;margin-top:3px}}
/* 六域 */
.dom-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}
.dom{{background:linear-gradient(165deg,var(--card2),var(--card));border:1px solid var(--line);border-radius:12px;padding:18px;transition:transform .3s,border-color .3s}}
.dom:hover{{transform:translateY(-3px);border-color:var(--line2)}}
.dom .d-no{{font-size:10px;color:var(--gold);letter-spacing:2px;margin-bottom:6px}}
.dom .d-name{{font-family:var(--serif);font-size:17px;font-weight:700;margin-bottom:8px}}
.dom .d-val{{font-size:24px;font-weight:700;color:var(--gold-l);margin-bottom:6px}}
.dom .d-desc{{font-size:12px;color:var(--txt2)}}
/* 提炼真值 */
.truth-item{{display:flex;align-items:center;gap:12px;padding:10px 14px;border:1px solid var(--line);border-radius:8px;margin-bottom:8px;background:var(--card)}}
.truth-item .tt{{font-size:10px;color:var(--gold);border:1px solid var(--line2);border-radius:3px;padding:2px 8px;flex-shrink:0}}
.truth-item .tv{{font-size:12px;color:var(--txt);flex:1}}
.truth-item .td{{font-size:10px;color:var(--txt3);flex-shrink:0}}
/* 分类 */
.cat-row{{display:flex;align-items:center;gap:10px;margin-bottom:8px}}
.cat-row .cn{{font-size:12px;color:var(--txt2);width:120px;flex-shrink:0;text-align:right}}
.cat-row .cb{{flex:1;height:16px;border-radius:4px;background:rgba(255,255,255,.04);overflow:hidden}}
.cat-row .cb i{{display:block;height:100%;background:linear-gradient(90deg,rgba(212,175,55,.3),var(--gold));border-radius:4px}}
.cat-row .cc{{font-size:12px;color:var(--gold-l);width:52px;text-align:right;font-family:monospace}}
/* SOP */
.sop-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px}}
.sop-card{{padding:12px 14px;border:1px solid var(--line);border-radius:10px;background:var(--card)}}
.sop-card .sop-t{{font-size:13px;font-weight:600;color:var(--gold-l)}}
.sop-card .sop-s{{font-size:10px;color:var(--txt3);margin-top:4px}}
/* 表 */
.tbl-wrap{{overflow-x:auto;border:1px solid var(--line);border-radius:12px}}
table{{width:100%;border-collapse:collapse;font-size:12px}}
th{{background:rgba(212,175,55,.08);color:var(--gold-l);font-weight:600;padding:10px 12px;text-align:left}}
td{{padding:9px 12px;border-top:1px solid rgba(212,175,55,.08);color:var(--txt2)}}
.mono{{font-family:monospace;font-size:11px}}
/* 看板 */
.dash-grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
.dpanel{{background:linear-gradient(165deg,var(--card2),var(--card));border:1px solid var(--line);border-radius:14px;padding:20px}}
.dpanel h3{{font-family:var(--serif);font-size:16px;font-weight:600;margin-bottom:4px}}
.dpanel .dsub{{font-size:11px;color:var(--txt3);margin-bottom:12px}}
.chart{{width:100%;height:260px}}
footer{{border-top:1px solid var(--line);padding:34px 0 40px;text-align:center}}
.foot-meta{{font-size:12px;color:var(--txt3);letter-spacing:1px}}
@media(max-width:960px){{.dom-grid{{grid-template-columns:repeat(2,1fr)}}.dash-grid{{grid-template-columns:1fr}}}}
@media(max-width:640px){{.dom-grid{{grid-template-columns:1fr}}.sec-title{{font-size:24px}}.hstat{{min-width:105px;padding:10px 12px}}}}
</style>
</head>
<body>
<header class="hero"><div class="container hero-inner">
  <div class="hero-eyebrow"><span class="dot"></span>ZONGYUAN-ROOT · 全域最大边界探索机制</div>
  <h1 class="hero-title"><span class="gold">全域边界探索</span><span class="thin">BOUNDARY EXPLORER · 六域扫描 · 核心真值提炼</span></h1>
  <p class="hero-desc">探索记忆网关、锁档快照、SOP文档、真值包、流水线产物、同源协议六域最大边界，自动提炼增量核心真值并上报记忆网关。</p>
  <div class="hero-stats">
    <div class="hstat"><div class="num">{gw_total:,}</div><div class="lab">网关真值</div></div>
    <div class="hstat"><div class="num">{len(snaps)}</div><div class="lab">锁档资产</div></div>
    <div class="hstat"><div class="num">{len(sops)}</div><div class="lab">SOP文档</div></div>
    <div class="hstat"><div class="num">{svc_on}/{svc_total}</div><div class="lab">服务在线</div></div>
  </div>
</div></header>

<section class="section" id="dom"><div class="container">
  <div class="sec-head"><div class="sec-tag">SIX EXPLORATION DOMAINS</div><h2 class="sec-title">六域 <span class="gl">探索边界</span></h2></div>
  <div class="dom-grid">
    <div class="dom"><div class="d-no">域①</div><div class="d-name">记忆网关</div><div class="d-val">{gw_total:,}</div><div class="d-desc">真值库 · 元规则 {gw.get('meta_rules_total',0)} · {svc_on}/{svc_total} 服务</div></div>
    <div class="dom"><div class="d-no">域②</div><div class="d-name">锁档快照</div><div class="d-val">{len(snaps)}</div><div class="d-desc">kernel_snapshot · 全部 FROZEN</div></div>
    <div class="dom"><div class="d-no">域③</div><div class="d-name">SOP 文档</div><div class="d-val">{len(sops)}</div><div class="d-desc">SOP .md · 运维规范</div></div>
    <div class="dom"><div class="d-no">域④</div><div class="d-name">真值包</div><div class="d-val">{len(packs)}</div><div class="d-desc">kernel_truths.json</div></div>
    <div class="dom"><div class="d-no">域⑤</div><div class="d-name">流水线产物</div><div class="d-val">{pl.get('product_entries',{}).get('total',0)}</div><div class="d-desc">六阶流水线 · 产品化</div></div>
    <div class="dom"><div class="d-no">域⑥</div><div class="d-name">同源协议</div><div class="d-val">{len(domains['protocols'])}</div><div class="d-desc">协议学习 · 节点统一</div></div>
  </div>
</div></section>

<section class="section" id="truth" style="background:linear-gradient(180deg,transparent,rgba(212,175,55,.03),transparent)"><div class="container">
  <div class="sec-head"><div class="sec-tag">DISTILLED TRUTHS</div><h2 class="sec-title">本轮 <span class="gl">提炼核心真值</span></h2><div class="sec-sub">共 {len(distilled)} 条增量 · 去重 {len(domains.get('new_truths',[]))} 新增</div></div>
  {truth_rows}
</div></section>

<section class="section" id="dash"><div class="container">
  <div class="sec-head"><div class="sec-tag">TELEMETRY</div><h2 class="sec-title">探索 <span class="gl">实时数据</span></h2></div>
  <div class="dash-grid">
    <div class="dpanel"><h3>真值分类分布</h3><div class="dsub">Top 10</div>{cat_rows}</div>
    <div class="dpanel"><h3>服务状态</h3><div class="dsub">{svc_total} 服务</div><div id="chartSvc" class="chart"></div></div>
  </div>
</div></section>

<section class="section" id="sop" style="background:linear-gradient(180deg,transparent,rgba(212,175,55,.03),transparent)"><div class="container">
  <div class="sec-head"><div class="sec-tag">SOP LIBRARY</div><h2 class="sec-title">SOP <span class="gl">文档库</span></h2></div>
  <div class="sop-grid">{sop_cards}</div>
</div></section>

<section class="section" id="lock"><div class="container">
  <div class="sec-head"><div class="sec-tag">LOCKED ASSETS</div><h2 class="sec-title">锁档资产 <span class="gl">最近 10 项</span></h2></div>
  <div class="tbl-wrap"><table><colgroup><col style="width:38%"><col style="width:44%"><col style="width:18%"></colgroup><thead><tr><th>锁档ID</th><th>事件名称</th><th>时间</th></tr></thead><tbody>{snap_rows}</tbody></table></div>
</div></section>

<footer><div class="container"><div class="foot-meta">Ω₀⊂⊙∞⊂Ω ｜ DID-BR-000002 ｜ 全域最大边界探索机制 · {run_id}</div></footer>

<script>
var SVCS = {json.dumps(svc, ensure_ascii=False)};
(function(){{
  var el = document.getElementById("chartSvc");
  if(el && window.echarts){{
    var on = SVCS.filter(function(s){{return String(s.status).toLowerCase()==="online"}}).length;
    var off = SVCS.length - on;
    var c = echarts.init(el);
    c.setOption({{tooltip:{{trigger:"item",backgroundColor:"#14141e",borderColor:"rgba(212,175,55,.4)",textStyle:{{color:"#eae6dc"}}}},
      series:[{{type:"pie",radius:["56%","80%"],center:["50%","48%"],label:{{show:true,position:"center",formatter:on+"/"+SVCS.length+"\\n在线",color:"#f0d68a",fontSize:20,fontWeight:700,lineHeight:26}},labelLine:{{show:false}},itemStyle:{{borderColor:"#101018",borderWidth:3,borderRadius:6}},
        data:[{{value:on,name:"在线",itemStyle:{{color:{{type:"linear",x:0,y:0,x2:0,y2:1,colorStops:[{{offset:0,color:"#f0d68a"}},{{offset:1,color:"#b8942e"}}]}}}}}},{{value:off,name:"离线",itemStyle:{{color:"rgba(201,85,85,.55)"}}}}]}}]}});
    window.addEventListener("resize", function(){{c.resize()}});
  }}
}})();
</script>
</body>
</html>"""
    return html

# ===================== 主流程 =====================
def main():
    run_id = "EXPLORE-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    print(f"[boundary-explorer] {run_id} 开始全域探索...")

    # 加载历史状态
    state_file = os.path.join(STATE, "explore_state.json")
    prev_state = {}
    if os.path.exists(state_file):
        try: prev_state = json.load(open(state_file, encoding="utf-8"))
        except Exception: pass

    # 六域探索
    print("  域① 记忆网关...")
    gw = explore_gateway()
    print("  域② 锁档快照...")
    snaps = explore_snapshots()
    print("  域③ SOP文档...")
    sops = explore_sops()
    print("  域④ 真值包...")
    packs = explore_truth_packs()
    print("  域⑤ 流水线产物...")
    pl = explore_pipeline()
    print("  域⑥ 同源协议...")
    protos = explore_protocols()

    domains = {
        "gateway": gw, "snapshots": snaps, "sops": sops,
        "truth_packs": packs, "pipeline": pl, "protocols": protos,
    }

    # 提炼
    distilled, seen = distill(domains, prev_state)
    domains["new_truths"] = distilled
    print(f"  提炼核心真值: {len(distilled)} 条")

    # 保存状态
    json.dump({"seen_truths": seen, "last_run": run_id}, open(state_file, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # 生成报告
    report = build_report(domains, distilled, run_id)
    report_path = os.path.join(ROOT, "boundary-explorer-report.html")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  报告已生成: {report_path}")

    # 保存原始探索数据
    data_file = os.path.join(STATE, f"explore_{run_id}.json")
    json.dump(domains, open(data_file, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    print(f"  探索数据: {data_file}")

    # 输出摘要
    print(f"[boundary-explorer] DONE {run_id}")
    print(f"  六域: 网关={gw.get('total',0) if gw.get('ok') else 'ERR'} 锁档={len(snaps)} SOP={len(sops)} 真值包={len(packs)} 流水线产品={pl.get('product_entries',{}).get('total',0)} 协议={len(protos)}")
    print(f"  提炼: {len(distilled)} 条核心真值 | 报告: {report_path}")
    return {"run_id": run_id, "domains": domains, "distilled": distilled, "report_path": report_path}

if __name__ == "__main__":
    main()
