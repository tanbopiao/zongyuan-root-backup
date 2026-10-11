#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lifecycle_builder.py — 全生命周期可视化机制·生成器
自动聚合：记忆网关实时数据 + 数字资产流水线产物 + 自我改进闭环 + 锁档快照
→ 生成黑金风格全生命周期看板 HTML（lifecycle-viewer.html）

用法: python3 lifecycle_builder.py
输出: lifecycle-viewer.html (自包含，可直接浏览器打开/上传)
"""
import json, os, re, glob, datetime, urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
PIPE = os.path.join(ROOT, "..", "pipeline-auto", "pipeline")

def now_str():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def fetch_json(url, timeout=12):
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None

def read_json(path):
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return None

# ===================== 1. 数据聚合 =====================
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".lifecycle_last_truths.txt")

def read_cache():
    try:
        with open(CACHE_FILE, encoding="utf-8") as f:
            return int(f.read().strip())
    except Exception:
        return 0

def write_cache(v):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            f.write(str(v))
    except Exception:
        pass

def collect():
    d = {}
    # --- 网关实时 ---
    gw = fetch_json("https://www.huodouai.com/digital_assets.json")
    d["total"] = 0
    if gw:
        d["total"] = gw.get("truths", {}).get("total", 0)
        d["generated_at"] = gw.get("generated_at", "")
        d["categories"] = gw.get("truths", {}).get("by_category", {})
        d["services"] = gw.get("services", [])
        d["system"] = gw.get("system", {})
        d["web_assets"] = gw.get("web_assets", {})
        d["classification"] = gw.get("classification", [])
        d["meta_rules_total"] = gw.get("meta_rules", {}).get("total", 0)
    # 降级回退：digital_assets truths 拒连时从 /api/report/status 取真值总量
    if not d["total"]:
        st = fetch_json("https://www.huodouai.com/api/report/status")
        if st and st.get("stats", {}).get("truths"):
            d["total"] = st["stats"]["truths"]
            d["categories"] = {}
    # 二级降级：www 主通道 502 时读本地最近实测缓存（避免退回陈旧硬编码）
    if not d["total"]:
        d["total"] = read_cache()
    if not d["total"]:
        d["total"] = 15283  # 最近实测值兜底（2026-09-16 三通道恢复后）
        d["categories"] = {}
    if d["total"]:
        write_cache(d["total"])

    # --- 流水线产物 ---
    d["pipeline"] = {}
    for f in ["new_assets", "asset_cards", "product_entries", "pricing_results", "circulation_results"]:
        d["pipeline"][f] = read_json(os.path.join(PIPE, "data", f + ".json")) or {}

    # --- 自我改进闭环 ---
    d["improve"] = {}
    for f in ["gaps", "improvement_proposals", "verify_results"]:
        d["improve"][f] = read_json(os.path.join(PIPE, "data", f + ".json")) or {}

    # --- 锁档快照 ---
    snaps = []
    seen = set()
    for p in glob.glob(os.path.join(ROOT, "..", "**", "kernel_snapshot*.json"), recursive=True) + \
             glob.glob(os.path.join(ROOT, "..", "kernel_snapshot*.json")):
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
            })
        except Exception:
            pass
    d["snapshots"] = sorted(snaps, key=lambda x: x["ts"], reverse=True)
    d["snapshot_count"] = len(snaps)
    return d

# ===================== 2. 生命周期阶段统计 =====================
def lifecycle_stats(d):
    pl = d["pipeline"]
    new_assets = pl["new_assets"] or {}
    cards = pl["asset_cards"] or {}
    products = pl["product_entries"] or {}
    prices = pl["pricing_results"] or {}
    circ = pl["circulation_results"] or {}

    stages = [
        {"key":"source","no":"01","name":"源头","en":"TRUTH SOURCE","desc":"记忆网关真值库持续沉淀","count":d["total"],"unit":"真值","color":"#d4af37","pct":100},
        {"key":"detect","no":"02","name":"检测","en":"DETECT","desc":"digital_assets 增量扫描","count":new_assets.get("delta",0),"unit":"增量","color":"#e0b84c","pct":min(100,int(new_assets.get("delta",0)/max(d["total"],1)*10000))},
        {"key":"extract","no":"03","name":"提炼","en":"EXTRACT","desc":"元规则去重萃取","count":cards.get("total_cards",0),"unit":"资产卡","color":"#b8942e","pct":min(100,int(cards.get("total_cards",0)/max(d["total"],1)*10000))},
        {"key":"productize","no":"04","name":"商品化","en":"PRODUCTIZE","desc":"产品化包装","count":products.get("total",0),"unit":"产品","color":"#8a6d1f","pct":min(100,int(products.get("total",0)/max(d["total"],1)*10000))},
        {"key":"price","no":"05","name":"定价","en":"PRICE","desc":"价格策略生成","count":prices.get("total",0),"unit":"定价","color":"#c9a84a","pct":min(100,int(prices.get("total",0)/max(d["total"],1)*10000))},
        {"key":"circulate","no":"06","name":"流通","en":"CIRCULATE","desc":"审批·台账·网关流转","count":circ.get("total",0),"unit":"已流通","color":"#d9bc5c","pct":min(100,int(circ.get("total",0)/max(d["total"],1)*10000))},
        {"key":"lock","no":"07","name":"锁档","en":"LOCK","desc":"三端锁档 FROZEN","count":d["snapshot_count"],"unit":"锁档","color":"#f0d68a","pct":min(100,int(d["snapshot_count"]/max(d["total"],1)*10000))},
        {"key":"sink","no":"08","name":"沉淀","en":"SINK","desc":"知识库·云盘·台账归档","count":d["snapshot_count"],"unit":"归档","color":"#eedd99","pct":min(100,int(d["snapshot_count"]/max(d["total"],1)*10000))},
    ]
    return stages

def esc(s):
    if s is None: return ""
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

# ===================== 3. HTML 生成 =====================
def build_html(d, stages):
    now = now_str()
    # 服务状态
    svc_rows = ""
    svc_on = 0
    svc_total = len(d["services"]) or 1
    for s in d["services"]:
        on = str(s.get("status","")).lower()=="online"
        if on: svc_on += 1
        cls = "on" if on else "off"
        svc_rows += f'<div class="svc-item"><span class="st {cls}"></span><span class="n">{esc(s.get("name",""))}</span><span class="p">:{esc(s.get("port",""))}</span><span class="s {cls}">{esc("在线" if on else "离线")}</span></div>'
    # 系统
    sys = d["system"] or {}
    mem = sys.get("memory",{})
    disk = sys.get("disk",{})
    mem_pct = mem.get("usage_percent", mem.get("pct",0))
    disk_pct = disk.get("usage_percent", disk.get("pct",0))
    mem_used = mem.get("used_mb", mem.get("used",0))
    mem_total = mem.get("total_mb", mem.get("total",0))
    disk_used = disk.get("used_gb", disk.get("used",0))
    disk_total = disk.get("total_gb", disk.get("total",0))
    # 分类 top
    cats = sorted(d["categories"].items(), key=lambda x:-x[1])[:10] if d["categories"] else []
    cat_rows = ""
    max_cat = max([c[1] for c in cats], default=1)
    for name, cnt in cats:
        w = int(cnt/max_cat*100)
        cat_rows += f'<div class="cat-row"><span class="cat-name">{esc(name)}</span><div class="cat-bar"><i style="width:{w}%"></i></div><span class="cat-cnt">{cnt}</span></div>'
    # 锁档快照表
    snap_rows = ""
    for s in d["snapshots"][:15]:
        wiki = s["wiki"].replace("https://my.feishu.cn/wiki/","") if s["wiki"] else "-"
        snap_rows += f'<tr><td class="mono">{esc(s["id"])}</td><td>{esc(s["name"][:40])}</td><td class="mono">{esc(s["ts"][:10])}</td><td class="mono">{esc(wiki[:18])}</td></tr>'
    # 流水线产物
    pl = d["pipeline"]
    circ = pl["circulation_results"] or {}
    circ_results = circ.get("results",[])
    circ_rows = ""
    for c in circ_results[:6]:
        pid = c.get("product_id") or c.get("id") or "-"
        st = c.get("status") or c.get("state") or "circulated"
        circ_rows += f'<div class="circ-item"><span class="circ-id mono">{esc(pid)}</span><span class="circ-status">{esc(st)}</span></div>'
    # 提案
    proposals = d["improve"].get("improvement_proposals",{}).get("proposals",[])
    prop_rows = ""
    for p in proposals[:6]:
        lv = p.get("execution_level","")
        prop_rows += f'<div class="circ-item"><span class="circ-id mono">{esc(p.get("proposal_id",""))}</span><span class="circ-status">{esc(lv)}</span></div>'
    # 阶段泳道
    stage_html = ""
    for st in stages:
        stage_html += f'''
        <div class="stage" style="--sg:{st["color"]}">
          <div class="stage-head">
            <span class="stage-no">{st["no"]}</span>
            <div class="stage-tit">
              <div class="stage-name">{esc(st["name"])}</div>
              <div class="stage-en">{esc(st["en"])}</div>
            </div>
          </div>
          <div class="stage-count"><span class="cnum">{st["count"]:,}</span><span class="cunit">{esc(st["unit"])}</span></div>
          <div class="stage-bar"><i style="width:{st["pct"]}%"></i></div>
          <div class="stage-desc">{esc(st["desc"])}</div>
        </div>'''

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ZONGYUAN-ROOT 全生命周期可视化机制 · Lifecycle Viewer</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%230a0a0f'/%3E%3Ccircle cx='32' cy='32' r='16' fill='none' stroke='%23d4af37' stroke-width='3'/%3E%3Ccircle cx='32' cy='32' r='6' fill='%23d4af37'/%3E%3C/svg%3E">
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>
:root{{
  --bg:#07070b;--bg2:#0c0c13;--card:#101018;--card2:#14141e;
  --gold:#d4af37;--gold-l:#f0d68a;--gold-d:#8a6d1f;
  --gold-grad:linear-gradient(135deg,#f0d68a,#d4af37 45%,#9a7b22);
  --txt:#eae6dc;--txt2:#a39e90;--txt3:#6d685c;
  --line:rgba(212,175,55,.16);--line2:rgba(212,175,55,.34);
  --ok:#4ecb8d;--off:#c95555;
  --serif:'Noto Serif SC',serif;--sans:'Noto Sans SC',system-ui,sans-serif;
}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:var(--bg);color:var(--txt);font-family:var(--sans);line-height:1.6;-webkit-font-smoothing:antialiased}}
body::before{{content:"";position:fixed;inset:0;z-index:-2;background:radial-gradient(1100px 500px at 20% -10%,rgba(212,175,55,.07),transparent 60%),radial-gradient(800px 500px at 90% 20%,rgba(212,175,55,.05),transparent 55%),var(--bg)}}
.container{{max-width:1280px;margin:0 auto;padding:0 24px}}
.section{{padding:64px 0}}
.sec-head{{text-align:center;margin-bottom:40px}}
.sec-tag{{display:inline-flex;align-items:center;gap:8px;font-size:12px;letter-spacing:3px;color:var(--gold);border:1px solid var(--line2);border-radius:999px;padding:5px 18px;margin-bottom:14px;background:rgba(212,175,55,.06)}}
.sec-tag::before,.sec-tag::after{{content:"";width:14px;height:1px;background:var(--gold)}}
.sec-title{{font-family:var(--serif);font-size:32px;font-weight:700;letter-spacing:2px}}
.sec-title .gl{{background:var(--gold-grad);-webkit-background-clip:text;background-clip:text;color:transparent}}
.sec-sub{{color:var(--txt2);font-size:14px;margin-top:10px;letter-spacing:1px}}
/* Hero */
.hero{{min-height:78vh;display:flex;align-items:center;position:relative;overflow:hidden;padding:90px 0 50px}}
.hero::after{{content:"";position:absolute;inset:0;background:radial-gradient(600px 600px at 85% 50%,rgba(212,175,55,.1),transparent 60%);pointer-events:none}}
.hero-inner{{position:relative;z-index:2;max-width:820px}}
.hero-eyebrow{{display:inline-flex;align-items:center;gap:10px;font-size:12px;letter-spacing:4px;color:var(--gold-l);border:1px solid var(--line2);padding:8px 20px;border-radius:4px;background:rgba(212,175,55,.07);margin-bottom:28px}}
.hero-eyebrow .dot{{width:7px;height:7px;border-radius:50%;background:var(--gold);box-shadow:0 0 12px var(--gold)}}
.hero-title{{font-family:var(--serif);font-size:clamp(38px,5.6vw,62px);font-weight:900;line-height:1.15;letter-spacing:3px;margin-bottom:20px}}
.hero-title .gold{{background:var(--gold-grad);-webkit-background-clip:text;background-clip:text;color:transparent;display:block}}
.hero-title .thin{{font-weight:300;color:var(--txt2);font-size:clamp(15px,2.2vw,20px);display:block;margin-top:12px;letter-spacing:5px}}
.hero-desc{{color:var(--txt2);font-size:15px;max-width:640px;margin-bottom:32px}}
.hero-stats{{display:flex;flex-wrap:wrap;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:rgba(16,16,24,.7);backdrop-filter:blur(8px)}}
.hstat{{flex:1;min-width:130px;padding:18px 22px;border-right:1px solid var(--line)}}
.hstat:last-child{{border-right:none}}
.hstat .num{{font-family:var(--serif);font-size:28px;font-weight:700;background:var(--gold-grad);-webkit-background-clip:text;background-clip:text;color:transparent}}
.hstat .lab{{font-size:11px;color:var(--txt3);letter-spacing:2px;margin-top:4px}}
/* 生命周期泳道 */
.lc-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}}
.stage{{position:relative;background:linear-gradient(165deg,var(--card2),var(--card));border:1px solid var(--line);border-radius:14px;padding:20px;overflow:hidden;transition:transform .3s,border-color .3s}}
.stage:hover{{transform:translateY(-4px);border-color:var(--line2)}}
.stage::before{{content:"";position:absolute;top:0;left:0;right:0;height:2px;background:var(--sg)}}
.stage::after{{content:"";position:absolute;top:-50px;right:-50px;width:130px;height:130px;border-radius:50%;background:radial-gradient(circle,var(--sg),transparent 70%);opacity:.16}}
.stage-head{{display:flex;align-items:center;gap:12px;margin-bottom:14px}}
.stage-no{{width:34px;height:34px;line-height:34px;text-align:center;border-radius:50%;background:var(--sg);color:#0a0a0f;font-weight:700;font-size:14px;flex-shrink:0}}
.stage-name{{font-family:var(--serif);font-size:17px;font-weight:700;letter-spacing:1px}}
.stage-en{{font-size:9px;color:var(--txt3);letter-spacing:2px}}
.stage-count{{margin-bottom:12px}}
.stage-count .cnum{{font-family:var(--serif);font-size:32px;font-weight:700;color:var(--gold-l)}}
.stage-count .cunit{{font-size:11px;color:var(--txt3);margin-left:6px;letter-spacing:1px}}
.stage-bar{{height:6px;border-radius:3px;background:rgba(255,255,255,.05);overflow:hidden;margin-bottom:12px}}
.stage-bar i{{display:block;height:100%;background:var(--sg);border-radius:3px;opacity:.85}}
.stage-desc{{font-size:12px;color:var(--txt2)}}
/* 数据面板 */
.dash-grid{{display:grid;grid-template-columns:1.3fr 1fr 1fr;gap:18px}}
.dpanel{{background:linear-gradient(165deg,var(--card2),var(--card));border:1px solid var(--line);border-radius:14px;padding:20px}}
.dpanel h3{{font-family:var(--serif);font-size:16px;font-weight:600;margin-bottom:4px;display:flex;align-items:center;gap:10px}}
.dpanel h3::before{{content:"";width:9px;height:9px;transform:rotate(45deg);background:var(--gold);box-shadow:0 0 8px rgba(212,175,55,.6)}}
.dpanel .dsub{{font-size:11px;color:var(--txt3);margin-bottom:12px}}
.chart{{width:100%;height:270px}}
/* 分类 */
.cat-row{{display:flex;align-items:center;gap:10px;margin-bottom:8px}}
.cat-name{{font-size:12px;color:var(--txt2);width:110px;flex-shrink:0;text-align:right}}
.cat-bar{{flex:1;height:16px;border-radius:4px;background:rgba(255,255,255,.04);overflow:hidden}}
.cat-bar i{{display:block;height:100%;background:linear-gradient(90deg,rgba(212,175,55,.3),var(--gold));border-radius:4px}}
.cat-cnt{{font-size:12px;color:var(--gold-l);width:48px;text-align:right;font-family:monospace}}
/* 服务 */
.svc-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:10px}}
.svc-item{{display:flex;align-items:center;gap:10px;padding:12px 14px;border:1px solid var(--line);border-radius:10px;background:var(--card)}}
.svc-item .st{{width:8px;height:8px;border-radius:50%;flex-shrink:0}}
.svc-item .st.on{{background:var(--ok);box-shadow:0 0 8px rgba(78,203,141,.6)}}
.svc-item .st.off{{background:var(--off);box-shadow:0 0 8px rgba(201,85,85,.5)}}
.svc-item .n{{font-size:12px;font-weight:500}}
.svc-item .p{{font-size:10px;color:var(--txt3);font-family:monospace}}
.svc-item .s{{margin-left:auto;font-size:11px}}
.svc-item .s.on{{color:var(--ok)}}
.svc-item .s.off{{color:var(--off)}}
/* 系统 */
.sys-row{{display:flex;gap:16px;flex-wrap:wrap}}
.sys-gauge{{flex:1;min-width:200px;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px}}
.sys-gauge .g-name{{font-size:13px;font-weight:600}}
.sys-gauge .g-val{{font-size:22px;font-family:var(--serif);font-weight:700;color:var(--gold-l)}}
.sys-gauge .g-bar{{height:7px;border-radius:4px;background:rgba(255,255,255,.06);margin-top:8px;overflow:hidden}}
.sys-gauge .g-bar i{{display:block;height:100%;background:var(--gold-grad);border-radius:4px}}
/* 表格 */
.tbl-wrap{{overflow-x:auto;border:1px solid var(--line);border-radius:12px}}
table{{width:100%;border-collapse:collapse;font-size:12px}}
th{{background:rgba(212,175,55,.08);color:var(--gold-l);font-weight:600;padding:10px 12px;text-align:left;letter-spacing:1px;white-space:nowrap}}
td{{padding:9px 12px;border-top:1px solid rgba(212,175,55,.08);color:var(--txt2)}}
tr:hover td{{background:rgba(212,175,55,.04)}}
.mono{{font-family:monospace;font-size:11px}}
/* 流通&提案 */
.mini-grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
.circ-item{{display:flex;justify-content:space-between;align-items:center;padding:9px 12px;border:1px solid var(--line);border-radius:8px;margin-bottom:8px;background:var(--card)}}
.circ-id{{font-size:11px;color:var(--gold-l)}}
.circ-status{{font-size:10px;color:var(--txt2);border:1px solid var(--line2);border-radius:3px;padding:2px 8px}}
footer{{border-top:1px solid var(--line);padding:36px 0 44px;text-align:center}}
.foot-brand{{font-family:var(--serif);font-size:17px;font-weight:700;letter-spacing:3px;margin-bottom:6px}}
.foot-meta{{font-size:12px;color:var(--txt3);letter-spacing:1px}}
@media(max-width:960px){{
  .dash-grid{{grid-template-columns:1fr}}
  .lc-grid{{grid-template-columns:repeat(2,1fr)}}
  .mini-grid{{grid-template-columns:1fr}}
}}
@media(max-width:640px){{
  .section{{padding:44px 0}}
  .sec-title{{font-size:24px}}
  .lc-grid{{grid-template-columns:1fr}}
  .hstat{{min-width:110px;padding:12px 14px}}
  .hstat .num{{font-size:22px}}
}}
</style>
</head>
<body>

<!-- ===== HERO ===== -->
<header class="hero">
  <div class="container hero-inner">
    <div class="hero-eyebrow"><span class="dot"></span>ZONGYUAN-ROOT · 全生命周期可视化机制</div>
    <h1 class="hero-title">
      <span class="gold">资产全生命周期</span>
      <span class="thin">LIFECYCLE VISUALIZATION MECHANISM · 自动聚合 · 自动更新</span>
    </h1>
    <p class="hero-desc">从真值源头到三端沉淀，八阶段泳道全链路可视化。本页由生成器自动聚合记忆网关实时数据与流水线产物构建，每次运行即自动刷新。</p>
    <div class="hero-stats">
      <div class="hstat"><div class="num">{d["total"]:,}</div><div class="lab">真值总量</div></div>
      <div class="hstat"><div class="num">{d["snapshot_count"]}</div><div class="lab">锁档资产</div></div>
      <div class="hstat"><div class="num">{d["meta_rules_total"]}</div><div class="lab">元规则</div></div>
      <div class="hstat"><div class="num">{svc_on}/{svc_total}</div><div class="lab">服务在线</div></div>
    </div>
  </div>
</header>

<!-- ===== 生命周期泳道 ===== -->
<section class="section" id="lc">
  <div class="container">
    <div class="sec-head">
      <div class="sec-tag">LIFECYCLE SWIMLANE</div>
      <h2 class="sec-title">八阶段 <span class="gl">生命周期泳道</span></h2>
      <p class="sec-sub">源头 → 检测 → 提炼 → 商品化 → 定价 → 流通 → 锁档 → 沉淀 · 全自动闭环</p>
    </div>
    <div class="lc-grid">{stage_html}</div>
  </div>
</section>

<!-- ===== 实时数据看板 ===== -->
<section class="section" id="dash" style="background:linear-gradient(180deg,transparent,rgba(212,175,55,.03),transparent)">
  <div class="container">
    <div class="sec-head">
      <div class="sec-tag">REAL-TIME TELEMETRY</div>
      <h2 class="sec-title">全域 <span class="gl">实时看板</span></h2>
    </div>
    <div class="dash-grid">
      <div class="dpanel">
        <h3>真值分类分布</h3>
        <div class="dsub">Top 10 类别</div>
        {cat_rows}
      </div>
      <div class="dpanel">
        <h3>服务在线状态</h3>
        <div class="dsub">记忆网关集群 · {svc_total} 服务</div>
        <div id="chartSvc" class="chart"></div>
      </div>
      <div class="dpanel">
        <h3>系统资源负载</h3>
        <div class="dsub">云服务器</div>
        <div id="chartSys" class="chart"></div>
      </div>
    </div>
    <div class="sys-row" style="margin-top:18px">
      <div class="sys-gauge"><div class="g-name">内存 Memory</div><div class="g-val">{mem_pct}%</div><div style="font-size:11px;color:var(--txt3)">{mem_used} / {mem_total} MB</div><div class="g-bar"><i style="width:{mem_pct}%"></i></div></div>
      <div class="sys-gauge"><div class="g-name">磁盘 Disk</div><div class="g-val">{disk_pct}%</div><div style="font-size:11px;color:var(--txt3)">{disk_used} / {disk_total} GB</div><div class="g-bar"><i style="width:{disk_pct}%"></i></div></div>
      <div class="sys-gauge"><div class="g-name">网页资产</div><div class="g-val">{d["web_assets"].get("total_html",422)}</div><div style="font-size:11px;color:var(--txt3)">官网 HTML 页面</div><div class="g-bar"><i style="width:62%"></i></div></div>
    </div>
  </div>
</section>

<!-- ===== 流通与提案 ===== -->
<section class="section" id="flow">
  <div class="container">
    <div class="sec-head">
      <div class="sec-tag">CIRCULATION & PROPOSALS</div>
      <h2 class="sec-title">流通与 <span class="gl">改进提案</span></h2>
    </div>
    <div class="mini-grid">
      <div class="dpanel">
        <h3>最近流通</h3>
        <div class="dsub">circulation_results · {circ.get("total",0)} 项</div>
        {circ_rows if circ_rows else '<div style="color:var(--txt3);font-size:12px">暂无流通记录</div>'}
      </div>
      <div class="dpanel">
        <h3>自我改进提案</h3>
        <div class="dsub">improvement_proposals · 分级</div>
        {prop_rows if prop_rows else '<div style="color:var(--txt3);font-size:12px">暂无提案</div>'}
      </div>
    </div>
  </div>
</section>

<!-- ===== 锁档资产 ===== -->
<section class="section" id="lock" style="background:linear-gradient(180deg,transparent,rgba(212,175,55,.03),transparent)">
  <div class="container">
    <div class="sec-head">
      <div class="sec-tag">LOCKED ASSETS</div>
      <h2 class="sec-title">锁档资产 <span class="gl">归档清单</span></h2>
      <p class="sec-sub">共 {d["snapshot_count"]} 项 · 全部 FROZEN · 最近 15 项</p>
    </div>
    <div class="tbl-wrap">
      <table>
        <colgroup><col style="width:34%"><col style="width:34%"><col style="width:14%"><col style="width:18%"></colgroup>
        <thead><tr><th>锁档ID</th><th>事件名称</th><th>时间</th><th>知识库</th></tr></thead>
        <tbody>{snap_rows}</tbody>
      </table>
    </div>
  </div>
</section>

<footer>
  <div class="container">
    <div class="foot-brand">ZONGYUAN-ROOT <span class="gl">全生命周期可视化机制</span></div>
    <div class="foot-meta">Ω₀⊂⊙∞⊂Ω ｜ DID-BR-000002 ｜ 火斗云智AIOS ｜ www.huodouai.com</div>
    <div class="foot-meta" style="margin-top:6px">生成时间 {now} ｜ 数据源：记忆网关 digital_assets.json + 流水线产物 + 锁档快照 ｜ 自动聚合</div>
  </div>
</footer>

<script>
var SVCS = {json.dumps(d["services"], ensure_ascii=False)};
var MEM_PCT = {mem_pct};
(function(){{
  var svcEl = document.getElementById("chartSvc");
  if(svcEl && window.echarts){{
    var on = SVCS.filter(function(s){{return String(s.status).toLowerCase()==="online"}}).length;
    var off = SVCS.length - on;
    var c = echarts.init(svcEl);
    c.setOption({{
      tooltip:{{trigger:"item",backgroundColor:"#14141e",borderColor:"rgba(212,175,55,.4)",textStyle:{{color:"#eae6dc"}}}},
      series:[{{type:"pie",radius:["56%","80%"],center:["50%","48%"],label:{{show:true,position:"center",formatter:on+" / "+SVCS.length+"\\n在线",color:"#f0d68a",fontSize:20,fontWeight:700,lineHeight:26}},labelLine:{{show:false}},itemStyle:{{borderColor:"#101018",borderWidth:3,borderRadius:6}},
        data:[{{value:on,name:"在线",itemStyle:{{color:{{type:"linear",x:0,y:0,x2:0,y2:1,colorStops:[{{offset:0,color:"#f0d68a"}},{{offset:1,color:"#b8942e"}}]}}}}}},{{value:off,name:"离线",itemStyle:{{color:"rgba(201,85,85,.55)"}}}}]}}]
    }});
    window.addEventListener("resize", function(){{c.resize()}});
  }}
  var sysEl = document.getElementById("chartSys");
  if(sysEl && window.echarts){{
    var c2 = echarts.init(sysEl);
    c2.setOption({{
      series:[{{type:"gauge",startAngle:210,endAngle:-30,min:0,max:100,radius:"92%",center:["50%","58%"],
        progress:{{show:true,width:12,itemStyle:{{color:{{type:"linear",x:0,y:0,x2:1,y2:0,colorStops:[{{offset:0,color:"#8a6d1f"}},{{offset:1,color:"#f0d68a"}}]}}}}}},
        axisLine:{{lineStyle:{{width:12,color:[[1,"rgba(212,175,55,.12)"]]}}}},
        axisTick:{{show:false}},splitLine:{{show:false}},axisLabel:{{show:false}},pointer:{{show:false}},anchor:{{show:false}},
        detail:{{valueAnimation:true,formatter:"{{value}}%",color:"#f0d68a",fontSize:26,fontWeight:700,offsetCenter:[0,"12%"]}},
        data:[{{value:MEM_PCT}}],title:{{show:true,offsetCenter:[0,"42%"],color:"#a39e90",fontSize:12}}}}]
    }});
    window.addEventListener("resize", function(){{c2.resize()}});
  }}
}})();
</script>
</body>
</html>'''
    return html

# ===================== 4. 主流程 =====================
def main():
    print("[lifecycle-builder] 开始聚合数据...")
    d = collect()
    print(f"  真值总量: {d['total']} | 锁档: {d['snapshot_count']} | 服务: {len(d['services'])}")
    stages = lifecycle_stats(d)
    html = build_html(d, stages)
    out = os.path.join(ROOT, "lifecycle-viewer.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[lifecycle-builder] 已生成: {out} ({len(html)} chars)")
    return out

if __name__ == "__main__":
    main()
