#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
api_live_collector.py — 真实API采集·联动·动态显示机制
三段闭环：①真实API采集（记忆网关/数字资产/节点状态）→ ②联动规则引擎（状态变化检测→触发联动动作）
          → ③动态显示页生成（页面JS实时fetch真实API动态渲染，非静态快照）

采集端点（全部真实API）：
  A https://www.huodouai.com/digital_assets.json   资产/系统/服务
  B https://www.huodouai.com/api/report/status     网关统计
  C https://www.huodouai.com/api/report/nodes      节点列表
  D http://www.huodouai.com:9120/api/report/status 备份网关

联动规则：
  R1 真值总量变化 → 记录增量 + 上报
  R2 内存占用>85% → 联动告警（RISK上报）
  R3 服务状态翻转 → 记录服务变更
  R4 节点数变化 → 记录节点变化

用法: python3 api_live_collector.py [--watch]  --watch: 持续监听模式（默认单次）
"""
import json, os, sys, argparse, datetime, subprocess, urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(STATE, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

GATEWAY_MAIN = "https://www.huodouai.com"
GATEWAY_BACKUP = "http://www.huodouai.com:9120"
LEDGER_BASE = "QYn4bjgD6am3OPsxMCkcitcBnzc"
LEDGER_TABLE = "tblIGVWXqu7cr7lZ"

def now_iso():
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00")

def http_get_json(url, timeout=12):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {"ok": True, "data": json.loads(r.read().decode("utf-8"))}
    except Exception as e:
        return {"ok": False, "error": str(e)[:80]}

def load_json(path):
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return {}

# ===================== ① 真实API采集 =====================
def collect_live():
    """采集全部真实API端点"""
    live = {"collected_at": now_iso(), "sources": {}}
    # A 数字资产
    r = http_get_json(f"{GATEWAY_MAIN}/digital_assets.json")
    live["sources"]["digital_assets"] = {"ok": r["ok"], **({} if not r["ok"] else {
        "truths_total": r["data"].get("truths", {}).get("total", 0),
        "meta_rules": r["data"].get("meta_rules", {}).get("total", 0),
        "system": r["data"].get("system", {}),
        "services": r["data"].get("services", []),
        "generated_at": r["data"].get("generated_at", ""),
    })}
    # B 网关状态
    r = http_get_json(f"{GATEWAY_MAIN}/api/report/status")
    live["sources"]["gateway_status"] = {"ok": r["ok"], **({} if not r["ok"] else {
        "truths": r["data"].get("stats", {}).get("truths", 0),
        "nodes": r["data"].get("stats", {}).get("nodes", 0),
        "audit_logs": r["data"].get("stats", {}).get("audit_logs", 0),
        "version": r["data"].get("meta", {}).get("version", ""),
    })}
    # C 节点列表
    r = http_get_json(f"{GATEWAY_MAIN}/api/report/nodes")
    live["sources"]["nodes"] = {"ok": r["ok"], **({} if not r["ok"] else {
        "count": r["data"].get("count", 0),
        "nodes": r["data"].get("nodes", {}),
    })}
    # D 备份网关
    r = http_get_json(f"{GATEWAY_BACKUP}/api/report/status")
    live["sources"]["backup_gateway"] = {"ok": r["ok"], **({} if not r["ok"] else {
        "status": r["data"].get("gateway_status", ""),
        "total_nodes": r["data"].get("total_nodes", 0),
        "active_nodes": r["data"].get("active_nodes", 0),
        "pass_rate": r["data"].get("pass_rate", 0),
        "write_rate": r["data"].get("write_rate", 0),
        "reports": r["data"].get("total_reports", 0),
    })}
    return live

# ===================== ② 联动规则引擎 =====================
def linkage_engine(live, prev):
    """比对上次快照，触发联动动作"""
    events = []
    cur = live["sources"]
    # R1 真值总量变化
    prev_total = (prev.get("sources", {}).get("digital_assets", {}) or {}).get("truths_total", 0)
    cur_total = cur.get("digital_assets", {}).get("truths_total", 0)
    if cur_total and prev_total and cur_total != prev_total:
        events.append({
            "rule": "R1", "level": "info",
            "message": f"真值总量变化: {prev_total} → {cur_total} (Δ{cur_total-prev_total:+d})",
        })
    # R2 内存超阈值联动
    mem = (cur.get("digital_assets", {}).get("system", {}) or {}).get("memory", {})
    usage = mem.get("usage_percent", 0)
    if usage > 85:
        events.append({
            "rule": "R2", "level": "risk",
            "message": f"内存占用超红线: {usage}% (阈值85%), 需服务治理",
        })
    elif usage > 75:
        events.append({"rule": "R2", "level": "warn", "message": f"内存占用偏高: {usage}%"})
    # R3 服务状态翻转
    prev_services = {(s.get("name") or s.get("port")): str(s.get("status", "")).lower()
                     for s in (prev.get("sources", {}).get("digital_assets", {}) or {}).get("services", [])}
    cur_services = {(s.get("name") or s.get("port")): str(s.get("status", "")).lower()
                    for s in (cur.get("digital_assets", {}).get("services", []) or [])}
    for name, st in cur_services.items():
        if name in prev_services and prev_services[name] != st:
            events.append({"rule": "R3", "level": "warn", "message": f"服务状态翻转: {name} {prev_services[name]}→{st}"})
    # R4 节点数变化
    prev_nodes = (prev.get("sources", {}).get("nodes", {}) or {}).get("count", 0)
    cur_nodes = cur.get("nodes", {}).get("count", 0)
    if cur_nodes and prev_nodes and cur_nodes != prev_nodes:
        events.append({"rule": "R4", "level": "info", "message": f"节点数变化: {prev_nodes} → {cur_nodes}"})
    return events

# ===================== ③ 动态显示页 =====================
def build_live_dashboard(live, events, run_id):
    """生成动态显示页：JS实时fetch真实API，自动刷新"""
    da = live["sources"].get("digital_assets", {})
    gs = live["sources"].get("gateway_status", {})
    ns = live["sources"].get("nodes", {})
    bk = live["sources"].get("backup_gateway", {})

    truth_total = da.get("truths_total", 0)
    mem = (da.get("system", {}) or {}).get("memory", {})
    disk = (da.get("system", {}) or {}).get("disk", {})
    svcs = da.get("services", [])
    svc_on = len([s for s in svcs if str(s.get("status", "")).lower() == "online"])
    svc_total = len(svcs)

    nodes_map = ns.get("nodes", {})
    node_rows = ""
    for nid, info in list(nodes_map.items())[:10]:
        st = info.get("online_status", info.get("status", "?"))
        cls = "on" if st == "online" else "off"
        node_rows += f'<tr><td class="mono">{nid}</td><td><span class="dot-{cls}"></span>{st}</td><td class="mono">{info.get("last_heartbeat", "N/A")}</td></tr>'

    events_html = ""
    if events:
        for e in events:
            lv = e["level"]
            events_html += f'<div class="evt evt-{lv}"><span class="evt-r">{e["rule"]}</span><span class="evt-m">{e["message"]}</span></div>'
    else:
        events_html = '<div class="evt evt-ok"><span class="evt-r">OK</span><span class="evt-m">无联动事件，系统稳态</span></div>'

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>真实API联动实时看板 · Live API Dashboard</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%230a0a0f'/%3E%3Cpath d='M32 4l6 22 22 6-22 6-6 22-6-22-22-6 22-6z' fill='%23d4af37'/%3E%3C/svg%3E">
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>
:root{{--bg:#07070b;--bg2:#0c0c13;--card:#101018;--card2:#15151f;--gold:#d4af37;--gold-l:#f0d68a;--gold-grad:linear-gradient(135deg,#f0d68a,#d4af37 45%,#9a7b22);--txt:#eae6dc;--txt2:#a39e90;--txt3:#6d685c;--line:rgba(212,175,55,.16);--line2:rgba(212,175,55,.34);--ok:#4ecb8d;--warn:#e0b84e;--risk:#c95555;--serif:'Noto Serif SC',serif;--sans:'Noto Sans SC',system-ui,sans-serif}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:var(--bg);color:var(--txt);font-family:var(--sans);line-height:1.6}}
body::before{{content:"";position:fixed;inset:0;z-index:-2;background:radial-gradient(1100px 500px at 20% -10%,rgba(212,175,55,.07),transparent 60%),radial-gradient(800px 500px at 90% 20%,rgba(212,175,55,.05),transparent 55%),var(--bg)}}
.container{{max-width:1280px;margin:0 auto;padding:0 24px}}
.section{{padding:48px 0}}
.sec-head{{display:flex;align-items:baseline;gap:16px;margin-bottom:26px;flex-wrap:wrap}}
.sec-title{{font-family:var(--serif);font-size:24px;font-weight:700;letter-spacing:2px}}
.sec-title .gl{{background:var(--gold-grad);-webkit-background-clip:text;background-clip:text;color:transparent}}
.sec-tag{{font-size:11px;color:var(--gold);border:1px solid var(--line2);border-radius:999px;padding:3px 14px}}
.hero{{min-height:56vh;display:flex;align-items:center;padding:60px 0 20px}}
.hero-eyebrow{{display:inline-flex;gap:10px;align-items:center;font-size:12px;letter-spacing:4px;color:var(--gold-l);border:1px solid var(--line2);padding:8px 20px;border-radius:4px;background:rgba(212,175,55,.07);margin-bottom:22px}}
.hero-eyebrow .dot{{width:7px;height:7px;border-radius:50%;background:var(--gold);box-shadow:0 0 12px var(--gold);animation:pulse 2s infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.35}}}}
.hero-title{{font-family:var(--serif);font-size:clamp(32px,4.8vw,52px);font-weight:900;line-height:1.15;letter-spacing:3px;margin-bottom:14px}}
.hero-title .gold{{background:var(--gold-grad);-webkit-background-clip:text;background-clip:text;color:transparent;display:block}}
.hero-title .thin{{font-weight:300;color:var(--txt2);font-size:clamp(13px,1.8vw,17px);display:block;margin-top:10px;letter-spacing:5px}}
.hero-desc{{color:var(--txt2);font-size:14px;max-width:620px;margin-bottom:22px}}
.live-badge{{display:inline-flex;align-items:center;gap:8px;font-size:12px;color:var(--ok);border:1px solid rgba(78,203,141,.4);padding:6px 16px;border-radius:999px;background:rgba(78,203,141,.08)}}
.live-badge .b-dot{{width:8px;height:8px;border-radius:50%;background:var(--ok);animation:pulse 1.5s infinite}}
.hero-stats{{display:flex;flex-wrap:wrap;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:rgba(16,16,24,.7);margin-top:22px}}
.hstat{{flex:1;min-width:130px;padding:14px 18px;border-right:1px solid var(--line)}}
.hstat:last-child{{border-right:none}}
.hstat .num{{font-family:var(--serif);font-size:24px;font-weight:700;background:var(--gold-grad);-webkit-background-clip:text;background-clip:text;color:transparent}}
.hstat .lab{{font-size:11px;color:var(--txt3);letter-spacing:2px;margin-top:3px}}
.dash-grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
.dpanel{{background:linear-gradient(165deg,var(--card2),var(--card));border:1px solid var(--line);border-radius:14px;padding:18px}}
.dpanel h3{{font-family:var(--serif);font-size:15px;font-weight:600;margin-bottom:2px}}
.dpanel .dsub{{font-size:11px;color:var(--txt3);margin-bottom:10px}}
.chart{{width:100%;height:230px}}
.evt{{display:flex;gap:10px;align-items:center;padding:9px 14px;border-radius:8px;margin-bottom:8px;font-size:12px;border:1px solid var(--line)}}
.evt-ok{{background:rgba(78,203,141,.06);border-color:rgba(78,203,141,.25)}}
.evt-info{{background:rgba(212,175,55,.05);border-color:var(--line)}}
.evt-warn{{background:rgba(224,184,78,.07);border-color:rgba(224,184,78,.3)}}
.evt-risk{{background:rgba(201,85,85,.08);border-color:rgba(201,85,85,.35)}}
.evt-r{{font-size:10px;color:var(--gold);border:1px solid var(--line2);border-radius:3px;padding:1px 7px;flex-shrink:0}}
.evt-m{{flex:1}}
.tbl-wrap{{overflow-x:auto;border:1px solid var(--line);border-radius:12px}}
table{{width:100%;border-collapse:collapse;font-size:12px}}
th{{background:rgba(212,175,55,.08);color:var(--gold-l);font-weight:600;padding:9px 12px;text-align:left}}
td{{padding:8px 12px;border-top:1px solid rgba(212,175,55,.08);color:var(--txt2)}}
.mono{{font-family:monospace;font-size:11px}}
.dot-on{{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--ok);margin-right:6px}}
.dot-off{{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--risk);margin-right:6px}}
.src-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px}}
.src-card{{padding:14px 16px;border:1px solid var(--line);border-radius:12px;background:var(--card)}}
.src-card .s-name{{font-size:13px;font-weight:700;color:var(--gold-l);margin-bottom:6px}}
.src-card .s-val{{font-size:11px;color:var(--txt2);line-height:1.7}}
footer{{border-top:1px solid var(--line);padding:28px 0 32px;text-align:center}}
.foot-meta{{font-size:12px;color:var(--txt3);letter-spacing:1px}}
@media(max-width:960px){{.dash-grid{{grid-template-columns:1fr}}}}
@media(max-width:640px){{.sec-title{{font-size:20px}}.hstat{{min-width:100px;padding:9px 12px}}}}
</style>
</head>
<body>
<header class="hero"><div class="container">
  <div class="hero-eyebrow"><span class="dot"></span>ZONGYUAN-ROOT · 真实API采集联动 · 动态显示</div>
  <h1 class="hero-title"><span class="gold">实时联动看板</span><span class="thin">LIVE API COLLECTOR · LINKAGE ENGINE · DYNAMIC DISPLAY</span></h1>
  <p class="hero-desc">采集记忆网关/数字资产/节点状态真实API，联动规则引擎检测变化，页面每60秒自动刷新真实数据。</p>
  <div class="live-badge"><span class="b-dot"></span><span id="liveStatus">LIVE · 距上次刷新 <span id="countdown">60</span>s</span></div>
  <div class="hero-stats">
    <div class="hstat"><div class="num" id="statTruth">{truth_total:,}</div><div class="lab">真值总量</div></div>
    <div class="hstat"><div class="num" id="statNodes">{gs.get('nodes',0)}</div><div class="lab">注册节点</div></div>
    <div class="hstat"><div class="num" id="statSvc">{svc_on}/{svc_total}</div><div class="lab">服务在线</div></div>
    <div class="hstat"><div class="num" id="statMem">{mem.get('usage_percent',0)}%</div><div class="lab">内存占用</div></div>
  </div>
</div></header>

<section class="section" id="src"><div class="container">
  <div class="sec-head"><span class="sec-tag">LIVE SOURCES</span><h2 class="sec-title">实时 <span class="gl">采集源</span></h2></div>
  <div class="src-grid">
    <div class="src-card"><div class="s-name">数字资产 digital_assets.json</div><div class="s-val" id="srcAssets">真值 {truth_total:,} · 元规则 {da.get('meta_rules',0)} · 生成 {str(da.get('generated_at',''))[:19]}</div></div>
    <div class="src-card"><div class="s-name">网关状态 report/status</div><div class="s-val" id="srcGateway">真值 {gs.get('truths',0):,} · 节点 {gs.get('nodes',0)} · 审计 {gs.get('audit_logs',0):,} · V{gs.get('version','')}</div></div>
    <div class="src-card"><div class="s-name">备份网关 9120</div><div class="s-val" id="srcBackup">{bk.get('status','')} · 节点 {bk.get('active_nodes',0)}/{bk.get('total_nodes',0)} · 通过率 {bk.get('pass_rate',0)}%</div></div>
  </div>
</div></section>

<section class="section" id="dash"><div class="container">
  <div class="sec-head"><span class="sec-tag">LIVE TELEMETRY</span><h2 class="sec-title">动态 <span class="gl">数据看板</span></h2></div>
  <div class="dash-grid">
    <div class="dpanel"><h3>服务状态</h3><div class="dsub">真实API实时服务健康</div><div id="chartSvc" class="chart"></div></div>
    <div class="dpanel"><h3>系统资源</h3><div class="dsub">内存/磁盘占用</div><div id="chartSys" class="chart"></div></div>
  </div>
</div></section>

<section class="section" id="linkage" style="background:linear-gradient(180deg,transparent,rgba(212,175,55,.03),transparent)"><div class="container">
  <div class="sec-head"><span class="sec-tag">LINKAGE EVENTS</span><h2 class="sec-title">联动 <span class="gl">事件流</span></h2><div class="sec-tag" id="evtCount">{len(events)} 事件</div></div>
  <div id="events">{events_html}</div>
</div></section>

<section class="section" id="nodes"><div class="container">
  <div class="sec-head"><span class="sec-tag">NODE REGISTRY</span><h2 class="sec-title">节点 <span class="gl">在线状态</span></h2></div>
  <div class="tbl-wrap"><table><colgroup><col style="width:42%"><col style="width:16%"><col style="width:42%"></colgroup><thead><tr><th>节点ID</th><th>状态</th><th>最近心跳</th></tr></thead><tbody id="nodeRows">{node_rows}</tbody></table></div>
</div></section>

<footer><div class="container"><div class="foot-meta">Ω₀⊂⊙∞⊂Ω ｜ DID-BR-000002 ｜ 真实API采集联动动态显示 · {run_id} ｜ 本页每60s自动fetch真实API</div></footer>

<script>
// ===== 动态数据层：实时fetch真实API，60s自动刷新 =====
var MAIN = "{GATEWAY_MAIN}";
var BACKUP = "{GATEWAY_BACKUP}";
function fmt(n){{return n==null?"-":Number(n).toLocaleString()}}
function fetchJson(url, timeout) {{
  return fetch(url, {{signal: AbortSignal.timeout(timeout||8000)}}).then(function(r){{if(!r.ok)throw new Error(r.status);return r.json()}});
}}
function updateUi(d) {{
  var da = d.digital_assets || {{}};
  var gs = d.gateway_status || {{}};
  var ns = d.nodes || {{}};
  var bk = d.backup_gateway || {{}};
  var t = (da.truths||{{}}).total;
  if(t!=null){{document.getElementById("statTruth").textContent=fmt(t)}};
  var n = (gs.stats||{{}}).nodes;
  if(n!=null){{document.getElementById("statNodes").textContent=n}};
  var svcs = da.services||[];
  var on = svcs.filter(function(s){{return String(s.status).toLowerCase()==="online"}}).length;
  document.getElementById("statSvc").textContent=on+"/"+svcs.length;
  var mem = (da.system||{{}}).memory||{{}};
  if(mem.usage_percent!=null){{document.getElementById("statMem").textContent=mem.usage_percent+"%"}};
  document.getElementById("srcAssets").textContent="真值 "+fmt(t)+" · 元规则 "+(da.meta_rules||{{}}).total+" · 生成 "+String(da.generated_at||"").slice(0,19);
  document.getElementById("srcGateway").textContent="真值 "+fmt((gs.stats||{{}}).truths)+" · 节点 "+n+" · 审计 "+fmt((gs.stats||{{}}).audit_logs)+" · V"+((gs.meta||{{}}).version||"");
  document.getElementById("srcBackup").textContent=(bk.gateway_status||"")+" · 节点 "+(bk.active_nodes||0)+"/"+(bk.total_nodes||0)+" · 通过率 "+(bk.pass_rate||0)+"%";
  // 图表更新
  if(window.echarts) {{
    var el1 = document.getElementById("chartSvc");
    if(el1 && el1._c) el1._c.setOption({{series:[{{data:[{{value:on}},{{value:svcs.length-on}}]}}]}});
    var el2 = document.getElementById("chartSys");
    if(el2 && el2._c && mem.usage_percent!=null) el2._c.setOption({{series:[{{data:[mem.usage_percent, (da.system||{{}}).disk?((da.system.disk||{{}}).usage_percent||0):0]}}]}});
  }}
  // 节点表
  var tb = document.getElementById("nodeRows");
  if(tb && ns.nodes) {{
    var rows = "";
    Object.keys(ns.nodes).slice(0,10).forEach(function(id){{
      var info = ns.nodes[id];
      var st = info.online_status||info.status||"?";
      rows += '<tr><td class="mono">'+id+'</td><td><span class="dot-'+(st==="online"?"on":"off")+'"></span>'+st+'</td><td class="mono">'+(info.last_heartbeat||"N/A")+'</td></tr>';
    }});
    tb.innerHTML = rows;
  }}
}}
function liveFetch() {{
  var d = {{}};
  return fetchJson(MAIN+"/digital_assets.json").then(function(x){{d.digital_assets=x;return fetchJson(MAIN+"/api/report/status")}})
    .then(function(x){{d.gateway_status=x;return fetchJson(MAIN+"/api/report/nodes")}})
    .then(function(x){{d.nodes=x;return fetchJson(BACKUP+"/api/report/status")}})
    .then(function(x){{d.backup_gateway=x;updateUi(d);document.getElementById("liveStatus").innerHTML='LIVE · 已实时刷新 ';return true}})
    .catch(function(){{return false}});
}}
var cd = 60;
setInterval(function(){{
  cd--; if(cd<=0){{ cd=60; liveFetch(); }}
  document.getElementById("countdown").textContent=cd;
}},1000);
// 首次加载后延时3s实时校验一次
setTimeout(liveFetch, 3000);
// ===== 初始图表（来自采集快照，实时刷新后更新） =====
(function(){{
  var SVCS = {json.dumps(svcs, ensure_ascii=False)};
  var MEM = {mem.get('usage_percent', 0)};
  var DISK = {disk.get('usage_percent', 0)};
  if(window.echarts){{
    var el1 = document.getElementById("chartSvc");
    var el2 = document.getElementById("chartSys");
    var on0 = SVCS.filter(function(s){{return String(s.status).toLowerCase()==="online"}}).length;
    if(el1){{var c1=echarts.init(el1);el1._c=c1;
      c1.setOption({{tooltip:{{trigger:"item",backgroundColor:"#14141e",borderColor:"rgba(212,175,55,.4)",textStyle:{{color:"#eae6dc"}}}},
        series:[{{type:"pie",radius:["52%","78%"],center:["50%","46%"],label:{{show:true,position:"center",formatter:on0+"/"+SVCS.length+"\\n在线",color:"#f0d68a",fontSize:18,fontWeight:700,lineHeight:24}},labelLine:{{show:false}},itemStyle:{{borderColor:"#101018",borderWidth:2,borderRadius:5}},
          data:[{{value:on0,name:"在线",itemStyle:{{color:"{{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[{{offset:0,color:'#f0d68a'}},{{offset:1,color:'#b8942e'}}]}}"}}}},{{value:SVCS.length-on0,name:"离线",itemStyle:{{color:"rgba(201,85,85,.55)"}}}}]}}]}});
      window.addEventListener("resize",function(){{c1.resize()}});
    }}
    if(el2){{var c2=echarts.init(el2);el2._c=c2;
      c2.setOption({{tooltip:{{trigger:"axis",backgroundColor:"#14141e",borderColor:"rgba(212,175,55,.4)",textStyle:{{color:"#eae6dc"}}}},grid:{{left:40,right:16,top:16,bottom:26}},
        xAxis:{{type:"category",data:["内存","磁盘"],axisLabel:{{color:"#a39e90"}}}},
        yAxis:{{type:"value",max:100,axisLabel:{{color:"#a39e90",formatter:"{{value}}%"}},splitLine:{{lineStyle:{{color:"rgba(212,175,55,.08)"}}}}}},
        series:[{{type:"bar",data:[MEM,DISK],barWidth:34,itemStyle:{{color:"{{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[{{offset:0,color:'#f0d68a'}},{{offset:1,color:'#8a6d1f'}}]}}",borderRadius:6}},label:{{show:true,position:"top",color:"#f0d68a",formatter:"{{c}}%"}}}}]}});
      window.addEventListener("resize",function(){{c2.resize()}});
    }}
  }}
}})();
</script>
</body>
</html>"""
    return html

# ===================== 主流程 =====================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--watch", action="store_true", help="持续监听模式")
    args = ap.parse_args()

    run_id = "LIVE-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    print(f"[api-live] {run_id} 真实API采集联动启动")

    # 加载上次快照（联动比对基线）
    prev_file = os.path.join(STATE, "last_snapshot.json")
    prev = load_json(prev_file)

    # ① 采集
    print("[①] 真实API采集...")
    live = collect_live()
    for name, src in live["sources"].items():
        st = "OK" if src.get("ok") else "FAIL"
        extra = {k: v for k, v in src.items() if k not in ("ok", "nodes", "services")}
        print(f"    [{st}] {name}: {str(extra)[:90]}")

    # ② 联动规则
    print("[②] 联动规则引擎...")
    events = linkage_engine(live, prev)
    print(f"    触发 {len(events)} 条联动事件")
    for e in events:
        print(f"      [{e['level']}] {e['rule']} {e['message']}")

    # 保存快照（供下次比对）
    json.dump(live, open(prev_file, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"    快照已保存: {prev_file}")

    # ③ 动态显示页
    print("[③] 动态显示页生成...")
    html = build_live_dashboard(live, events, run_id)
    out_html = os.path.join(OUT, "live-api-dashboard.html")
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"    页面: {out_html}")

    # 台账
    print("[台账] 写入联动记录...")
    evt_summary = "; ".join([e["message"][:50] for e in events[:3]]) or "稳态"
    try:
        r = subprocess.run([
            "lark-cli", "base", "+record-batch-create",
            "--base-token", LEDGER_BASE, "--table-id", LEDGER_TABLE,
            "--json", json.dumps({"create_records": [{
                "锁档事件ID": run_id, "确权锚点": "Ω₀⊂⊙∞⊂Ω|DID-BR-000002",
                "锁档名称": "真实API采集联动运行", "锁档状态": "FROZEN",
                "关联规则ID": f"LIVE.{datetime.datetime.now().strftime('%Y%m%d')}",
                "锁档日期": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "云盘目录": "飞书云盘根/API联动记录",
            }]}), "--as", "user", "--format", "json",
        ], capture_output=True, text=True, timeout=60)
        d = json.loads(r.stdout) if r.stdout else {}
        ledger = {"ok": bool(d.get("ok")), "record_id": (d.get("data", {}).get("record_id_list") or [""])[0]}
        print(f"    {ledger}")
    except Exception as e:
        ledger = {"ok": False, "error": str(e)[:80]}
        print(f"    {ledger}")

    # 上报
    print("[上报] 联动真值...")
    rep = {"ok": True, "report_id": "skipped(稳态无事件)"}
    if events:
        try:
            payload = json.dumps({
                "truth_key": f"REPORT.API.LIVE.{datetime.datetime.now().strftime('%Y%m%d.%H%M')}",
                "truth_value": f"真实API采集联动: 真值{live['sources']['digital_assets'].get('truths_total',0)} 节点{live['sources']['gateway_status'].get('nodes',0)} 联动事件{len(events)}条: {evt_summary[:120]}",
                "source_node": "pipeline-auto-001", "confidence": 0.9,
                "truth_type": "risk" if any(e["level"] == "risk" for e in events) else "data",
            }).encode("utf-8")
            for base in [GATEWAY_MAIN, GATEWAY_BACKUP]:
                try:
                    req = urllib.request.Request(f"{base}/api/report/truth", data=payload,
                                                 headers={"Content-Type": "application/json"}, method="POST")
                    with urllib.request.urlopen(req, timeout=15) as r:
                        d = json.loads(r.read().decode("utf-8"))
                        if d.get("status") == "reported":
                            rep = {"ok": True, "report_id": d.get("report_id")}
                            break
                except Exception:
                    continue
        except Exception:
            pass
    print(f"    {rep}")

    result = {"run_id": run_id, "sources": live["sources"], "events": events,
              "ledger": ledger, "report": rep, "dashboard": out_html}
    out_json = os.path.join(STATE, f"live_{run_id}.json")
    json.dump(result, open(out_json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"[api-live] DONE {run_id} | 记录: {out_json}")
    return result

if __name__ == "__main__":
    main()
