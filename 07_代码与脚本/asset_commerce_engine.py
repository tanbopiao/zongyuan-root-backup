#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
asset_commerce_engine.py — 核心资产全自动产品化·定价·商业化·可视化引擎
四段流水：①全资产聚合（中枢资产+网关+流水线）→ ②产品化（资产→产品卡）
          → ③定价（多维价值模型）→ ④商业化+可视化（商品清单+台账+展示页）

覆盖资产源：
  A 中枢能力注册表 (capability_registry.json, 8项)
  B 中枢元法则注册表 (metalaw_register_registry.json, 34条)
  C 同源协议库 (homology_protocol_library.json, 12条)
  D 锁档快照 (kernel_snapshot*.json)
  E 流水线产物 (pipeline-auto/pipeline/data/*.json)
  F 网关数字资产 (digital_assets.json)

用法: python3 asset_commerce_engine.py [--rebuild]  --rebuild: 全量重建（默认增量补全）
"""
import json, os, sys, glob, argparse, datetime, subprocess, urllib.request

CHATS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
ANCHOR = "/home/user/Doubao/chats/38437615670548738/zongyuan-anchor"
PIPE = os.path.join(CHATS, "pipeline-auto", "pipeline")
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(OUT_DIR, exist_ok=True)

GATEWAY_MAIN = "https://www.huodouai.com"
GATEWAY_BACKUP = "http://www.huodouai.com:9120"
LEDGER_BASE = "QYn4bjgD6am3OPsxMCkcitcBnzc"
LEDGER_TABLE = "tblIGVWXqu7cr7lZ"

def now_iso():
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00")

def load_json(path):
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return {}

# ===================== ① 全资产聚合 =====================
def collect_assets():
    """聚合全部核心资产，产出统一资产清单"""
    assets = []
    # A 能力注册表
    caps = load_json(os.path.join(ANCHOR, "capability_registry.json"))
    for c in caps.get("capabilities", []):
        assets.append({
            "asset_id": c.get("cap_id", ""), "name": c.get("name", ""),
            "category": "高阶能力", "product_line": "P1-capability",
            "source": "能力注册表", "value_desc": c.get("steps", "")[:80],
            "target_customer": "自治体系节点/工程化团队", "quality": 0.95,
            "scarcity": 1.0, "type_weight": 1.3,
        })
    # B 元法则注册表
    ml = load_json(os.path.join(ANCHOR, "metalaw_register_registry.json"))
    items = ml.get("items", ml.get("registered", []))
    for m in items[:34]:
        mid = m.get("id") or m.get("metalaw_id") or m.get("rule_id") or ""
        if not mid: continue
        assets.append({
            "asset_id": f"ML-{mid}", "name": m.get("name", mid)[:60],
            "category": "元法则", "product_line": "P2-metalaw",
            "source": "元法则注册表", "value_desc": str(m.get("content", m.get("definition", "")))[:80],
            "target_customer": "自治内核治理/体系架构", "quality": 0.9,
            "scarcity": 0.9, "type_weight": 1.1,
        })
    # C 同源协议库
    plib = load_json(os.path.join(ANCHOR, "homology_protocol_library.json"))
    protos = plib.get("protocols", plib.get("items", []))
    for p in protos[:12]:
        pid = p.get("protocol_id") or p.get("id") or p.get("name", "")[:20]
        assets.append({
            "asset_id": f"PROTO-{pid}", "name": (p.get("name") or pid)[:60],
            "category": "同源协议", "product_line": "P3-protocol",
            "source": "协议库", "value_desc": str(p.get("essence", p.get("summary", "")))[:80],
            "target_customer": "同源节点/云端接入方", "quality": 0.93,
            "scarcity": 0.95, "type_weight": 1.2,
        })
    # D 锁档快照
    for s in glob.glob(os.path.join(CHATS, "**", "kernel_snapshot*.json"), recursive=True):
        try:
            d = json.load(open(s, encoding="utf-8"))
            lid = d.get("lock_event_id") or os.path.basename(s)
            assets.append({
                "asset_id": f"LOCK-{lid}", "name": d.get("lock_event_name", lid)[:60],
                "category": "锁档资产", "product_line": "P4-locked-assets",
                "source": "锁档快照", "value_desc": d.get("axiom_anchor", "")[:80],
                "target_customer": "体系存证/审计/传承", "quality": 0.97,
                "scarcity": 1.0, "type_weight": 1.0,
            })
        except Exception:
            pass
    # E 流水线产物（已有产品卡）
    pc = load_json(os.path.join(PIPE, "data", "product_entries.json"))
    for p in pc.get("products", []):
        assets.append({
            "asset_id": p.get("asset_id", p.get("product_id", "")),
            "name": p.get("name", "")[:60], "category": "流水线产品",
            "product_line": p.get("product_line", "P5-pipeline"),
            "source": "流水线产物", "value_desc": (p.get("description") or "")[:80],
            "target_customer": p.get("target_customer", "内容/咨询市场"),
            "quality": 0.9, "scarcity": 0.9, "type_weight": 1.25,
        })
    # F 网关数字资产统计（作为市场总量参考，不逐条产品化）
    gw = load_json(os.path.join(CHATS, "deploy-auto", "data", "deploy_*.json"))
    return assets

# ===================== ② 产品化 =====================
def productize(assets):
    """资产 → 产品卡"""
    products = []
    for a in assets:
        if not a.get("asset_id"): continue
        pid = f"CPRD-{abs(hash(a['asset_id'])) % 100000:05d}"
        products.append({
            "product_id": pid, "asset_id": a["asset_id"], "name": a["name"],
            "category": a.get("category", ""), "product_line": a.get("product_line", ""),
            "source": a.get("source", ""), "value_desc": a.get("value_desc", ""),
            "target_customer": a.get("target_customer", ""),
            "quality": a.get("quality", 0.8), "scarcity": a.get("scarcity", 0.8),
            "type_weight": a.get("type_weight", 1.0), "status": "DRAFT",
        })
    return products

# ===================== ③ 定价（多维价值模型） =====================
def pricing(products):
    """多维定价：base_price × type_weight × quality × scarcity"""
    results = []
    for p in products:
        base = 999.0  # 基础价格锚
        price = base * p["type_weight"] * p["quality"] * p["scarcity"]
        rng_min = round(base * 0.1, 2)
        rng_max = round(base * p["type_weight"] * 1.5, 2)
        results.append({
            "product_id": p["product_id"], "asset_id": p["asset_id"],
            "name": p["name"], "suggested_price": round(price, 2),
            "price_model": "monthly", "price_unit": "元/月",
            "price_range": {"min": rng_min, "max": rng_max},
            "confidence": round(p["quality"] * 0.95, 2),
            "factors": {"type_weight": p["type_weight"], "quality": p["quality"], "scarcity": p["scarcity"], "base_price": base},
        })
    return results

# ===================== ④ 商业化 + 可视化 =====================
def write_ledger(records, name_suffix):
    try:
        cmd = [
            "lark-cli", "base", "+record-batch-create",
            "--base-token", LEDGER_BASE, "--table-id", LEDGER_TABLE,
            "--json", json.dumps({"create_records": records}),
            "--as", "user", "--format", "json",
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        d = json.loads(r.stdout) if r.stdout else {}
        if d.get("ok"):
            ids = d.get("data", {}).get("record_id_list", [])
            return {"ok": True, "record_ids": ids}
        return {"ok": False, "error": d.get("error", r.stderr[:100])}
    except Exception as e:
        return {"ok": False, "error": str(e)[:100]}

def report_truth(truth_key, truth_value, truth_type="data", confidence=0.9, source="pipeline-auto-001"):
    payload = json.dumps({
        "truth_key": truth_key, "truth_value": truth_value,
        "source_node": source, "confidence": confidence, "truth_type": truth_type,
    }).encode("utf-8")
    import time
    for attempt in range(3):
        for base in [GATEWAY_MAIN, GATEWAY_BACKUP]:
            try:
                req = urllib.request.Request(f"{base}/api/report/truth", data=payload,
                                             headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=15) as r:
                    d = json.loads(r.read().decode("utf-8"))
                    if d.get("status") == "reported":
                        return {"ok": True, "report_id": d.get("report_id"), "channel": base}
            except Exception:
                continue
        time.sleep(2)
    return {"ok": False, "error": "all channels failed"}

def build_showcase(products, prices, run_id):
    """生成核心资产商业化展示页（可视化交付）"""
    total = len(products)
    # 按产品线聚合
    lines = {}
    for p, pr in zip(products, prices):
        ln = p.get("product_line", "other")
        lines.setdefault(ln, []).append({"p": p, "pr": pr})
    line_cards = ""
    line_keys = {"P1-capability": "高阶能力", "P2-metalaw": "元法则", "P3-protocol": "同源协议",
                 "P4-locked-assets": "锁档资产", "P5-pipeline": "流水线产品", "P0-dramaaas": "短剧SaaS",
                 "P0-consulting": "咨询实施"}
    for ln, items in sorted(lines.items()):
        sub = ""
        for it in items[:6]:
            pr = it["pr"]
            sub += f'<div class="prod-row"><span class="pt">{it["p"]["category"]}</span><span class="pn">{it["p"]["name"][:30]}</span><span class="pp">{pr["suggested_price"]:,.0f}</span><span class="pr">{it["p"]["quality"]:.2f}</span></div>'
        line_cards += f'<div class="line-card"><div class="lc-head"><span class="lc-name">{line_keys.get(ln, ln)}</span><span class="lc-cnt">{len(items)} 项</span></div>{sub}</div>'
    # 定价分布数据
    prices_sorted = sorted(p["suggested_price"] for p in prices)
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>核心资产商业化引擎 · Asset Commerce</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%230a0a0f'/%3E%3Cpath d='M32 4l6 22 22 6-22 6-6 22-6-22-22-6 22-6z' fill='%23d4af37'/%3E%3C/svg%3E">
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>
:root{{--bg:#07070b;--bg2:#0c0c13;--card:#101018;--card2:#15151f;--gold:#d4af37;--gold-l:#f0d68a;--gold-grad:linear-gradient(135deg,#f0d68a,#d4af37 45%,#9a7b22);--txt:#eae6dc;--txt2:#a39e90;--txt3:#6d685c;--line:rgba(212,175,55,.16);--line2:rgba(212,175,55,.34);--serif:'Noto Serif SC',serif;--sans:'Noto Sans SC',system-ui,sans-serif}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:var(--bg);color:var(--txt);font-family:var(--sans);line-height:1.6}}
body::before{{content:"";position:fixed;inset:0;z-index:-2;background:radial-gradient(1100px 500px at 20% -10%,rgba(212,175,55,.07),transparent 60%),radial-gradient(800px 500px at 90% 20%,rgba(212,175,55,.05),transparent 55%),var(--bg)}}
.container{{max-width:1280px;margin:0 auto;padding:0 24px}}
.section{{padding:56px 0}}
.sec-head{{text-align:center;margin-bottom:34px}}
.sec-tag{{display:inline-flex;gap:8px;font-size:12px;letter-spacing:3px;color:var(--gold);border:1px solid var(--line2);border-radius:999px;padding:5px 18px;margin-bottom:14px;background:rgba(212,175,55,.06)}}
.sec-title{{font-family:var(--serif);font-size:30px;font-weight:700;letter-spacing:2px}}
.sec-title .gl{{background:var(--gold-grad);-webkit-background-clip:text;background-clip:text;color:transparent}}
.sec-sub{{color:var(--txt2);font-size:13px;margin-top:8px}}
.hero{{min-height:64vh;display:flex;align-items:center;padding:70px 0 30px}}
.hero-eyebrow{{display:inline-flex;gap:10px;align-items:center;font-size:12px;letter-spacing:4px;color:var(--gold-l);border:1px solid var(--line2);padding:8px 20px;border-radius:4px;background:rgba(212,175,55,.07);margin-bottom:24px}}
.hero-eyebrow .dot{{width:7px;height:7px;border-radius:50%;background:var(--gold);box-shadow:0 0 12px var(--gold)}}
.hero-title{{font-family:var(--serif);font-size:clamp(34px,5vw,54px);font-weight:900;line-height:1.15;letter-spacing:3px;margin-bottom:16px}}
.hero-title .gold{{background:var(--gold-grad);-webkit-background-clip:text;background-clip:text;color:transparent;display:block}}
.hero-title .thin{{font-weight:300;color:var(--txt2);font-size:clamp(13px,1.8vw,17px);display:block;margin-top:10px;letter-spacing:5px}}
.hero-desc{{color:var(--txt2);font-size:14px;max-width:620px;margin-bottom:26px}}
.hero-stats{{display:flex;flex-wrap:wrap;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:rgba(16,16,24,.7)}}
.hstat{{flex:1;min-width:130px;padding:15px 20px;border-right:1px solid var(--line)}}
.hstat:last-child{{border-right:none}}
.hstat .num{{font-family:var(--serif);font-size:25px;font-weight:700;background:var(--gold-grad);-webkit-background-clip:text;background-clip:text;color:transparent}}
.hstat .lab{{font-size:11px;color:var(--txt3);letter-spacing:2px;margin-top:3px}}
.dash-grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:10px}}
.dpanel{{background:linear-gradient(165deg,var(--card2),var(--card));border:1px solid var(--line);border-radius:14px;padding:20px}}
.dpanel h3{{font-family:var(--serif);font-size:16px;font-weight:600;margin-bottom:4px}}
.dpanel .dsub{{font-size:11px;color:var(--txt3);margin-bottom:10px}}
.chart{{width:100%;height:270px}}
.line-card{{background:linear-gradient(165deg,var(--card2),var(--card));border:1px solid var(--line);border-radius:14px;padding:18px;margin-bottom:14px}}
.lc-head{{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--line);padding-bottom:10px;margin-bottom:10px}}
.lc-name{{font-family:var(--serif);font-size:16px;font-weight:700;color:var(--gold-l)}}
.lc-cnt{{font-size:11px;color:var(--txt3)}}
.prod-row{{display:flex;gap:10px;align-items:center;padding:6px 0;border-bottom:1px solid rgba(212,175,55,.06);font-size:12px}}
.prod-row .pt{{font-size:10px;color:var(--gold);border:1px solid var(--line2);border-radius:3px;padding:1px 6px;flex-shrink:0;width:64px;text-align:center}}
.prod-row .pn{{flex:1;color:var(--txt);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.prod-row .pp{{color:var(--gold-l);font-family:monospace;width:76px;text-align:right}}
.prod-row .pr{{color:var(--txt3);width:40px;text-align:right}}
footer{{border-top:1px solid var(--line);padding:30px 0 36px;text-align:center}}
.foot-meta{{font-size:12px;color:var(--txt3);letter-spacing:1px}}
@media(max-width:960px){{.dash-grid{{grid-template-columns:1fr}}}}
@media(max-width:640px){{.sec-title{{font-size:23px}}.hstat{{min-width:105px;padding:9px 12px}}}}
</style>
</head>
<body>
<header class="hero"><div class="container">
  <div class="hero-eyebrow"><span class="dot"></span>ZONGYUAN-ROOT · 核心资产商业化引擎</div>
  <h1 class="hero-title"><span class="gold">资产商业化</span><span class="thin">PRODUCTIZE · PRICE · COMMERCIALIZE · VISUALIZE</span></h1>
  <p class="hero-desc">全资产聚合 → 自动产品化 → 多维定价 → 商业化流通 → 可视化展示，全链路自动化，任何核心资产新增即进入商业化流转。</p>
  <div class="hero-stats">
    <div class="hstat"><div class="num">{total}</div><div class="lab">产品总数</div></div>
    <div class="hstat"><div class="num">{len(lines)}</div><div class="lab">产品线</div></div>
    <div class="hstat"><div class="num">{sum(len(v) for v in lines.values()):,}</div><div class="lab">定价资产</div></div>
    <div class="hstat"><div class="num">{sum(p["suggested_price"] for p in prices):,.0f}</div><div class="lab">估值合计(元/月)</div></div>
  </div>
</div></header>

<section class="section" id="dash"><div class="container">
  <div class="sec-head"><div class="sec-tag">COMMERCE TELEMETRY</div><h2 class="sec-title">商业化 <span class="gl">数据看板</span></h2></div>
  <div class="dash-grid">
    <div class="dpanel"><h3>产品线分布</h3><div class="dsub">各类资产产品化数量</div><div id="chartLine" class="chart"></div></div>
    <div class="dpanel"><h3>定价分布</h3><div class="dsub">产品建议价（元/月）</div><div id="chartPrice" class="chart"></div></div>
  </div>
</div></section>

<section class="section" id="products" style="background:linear-gradient(180deg,transparent,rgba(212,175,55,.03),transparent)"><div class="container">
  <div class="sec-head"><div class="sec-tag">PRODUCT LINES</div><h2 class="sec-title">产品线 <span class="gl">商品清单</span></h2><div class="sec-sub">按产品线聚合 · 每行含建议价与质量分</div></div>
  {line_cards}
</div></section>

<footer><div class="container"><div class="foot-meta">Ω₀⊂⊙∞⊂Ω ｜ DID-BR-000002 ｜ 核心资产商业化引擎 · {run_id}</div></footer>

<script>
var LINES = {json.dumps([{"name": k, "value": len(v)} for k, v in lines.items()], ensure_ascii=False)};
var PRICES = {json.dumps(prices_sorted)};
(function(){{
  var el1 = document.getElementById("chartLine");
  if(el1 && window.echarts){{
    var c1 = echarts.init(el1);
    c1.setOption({{tooltip:{{trigger:"axis",backgroundColor:"#14141e",borderColor:"rgba(212,175,55,.4)",textStyle:{{color:"#eae6dc"}}}},grid:{{left:40,right:14,top:18,bottom:30}},
      xAxis:{{type:"value",axisLabel:{{color:"#a39e90"}},splitLine:{{lineStyle:{{color:"rgba(212,175,55,.08)"}}}}}},
      yAxis:{{type:"category",data:LINES.map(function(l){{return l.name}}),axisLabel:{{color:"#a39e90",fontSize:10}}}},
      series:[{{type:"bar",data:LINES.map(function(l){{return l.value}}),barWidth:14,itemStyle:{{color:{{type:"linear",x:0,y:0,x2:1,y2:0,colorStops:[{{offset:0,color:"#8a6d1f"}},{{offset:1,color:"#f0d68a"}}]}},borderRadius:4}},label:{{show:true,position:"right",color:"#f0d68a",fontSize:10}}}}]}});
    window.addEventListener("resize", function(){{c1.resize()}});
  }}
  var el2 = document.getElementById("chartPrice");
  if(el2 && window.echarts){{
    var c2 = echarts.init(el2);
    c2.setOption({{tooltip:{{trigger:"axis",backgroundColor:"#14141e",borderColor:"rgba(212,175,55,.4)",textStyle:{{color:"#eae6dc"}}}},grid:{{left:46,right:14,top:18,bottom:30}},
      xAxis:{{type:"category",data:PRICES.map(function(_,i){{return i+1}}),axisLabel:{{show:false}},axisTick:{{show:false}}}},
      yAxis:{{type:"value",axisLabel:{{color:"#a39e90"}},splitLine:{{lineStyle:{{color:"rgba(212,175,55,.08)"}}}}}},
      series:[{{type:"line",data:PRICES,smooth:true,symbol:"circle",symbolSize:5,lineStyle:{{color:"#d4af37",width:2}},itemStyle:{{color:"#f0d68a"}},areaStyle:{{color:"rgba(212,175,55,.14)"}}}}]}});
    window.addEventListener("resize", function(){{c2.resize()}});
  }}
}})();
</script>
</body>
</html>"""
    return html

# ===================== 主流程 =====================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuild", action="store_true")
    args = ap.parse_args()

    run_id = "COMMERCE-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    print(f"[asset-commerce] {run_id} 核心资产商业化引擎启动")

    # ① 聚合
    print("[①] 全资产聚合...")
    assets = collect_assets()
    print(f"  聚合核心资产: {len(assets)} 条")
    cats = {}
    for a in assets:
        cats[a["category"]] = cats.get(a["category"], 0) + 1
    for k, v in cats.items():
        print(f"    {k}: {v}")

    # ② 产品化
    print("[②] 自动产品化...")
    products = productize(assets)
    print(f"  产品卡: {len(products)} 张")

    # ③ 定价
    print("[③] 自动定价...")
    prices = pricing(products)
    total_val = sum(p["suggested_price"] for p in prices)
    print(f"  定价完成: 估值合计 {total_val:,.0f} 元/月, 均价 {total_val/len(prices):,.0f} 元/月")

    # ④ 商业化 + 可视化
    print("[④] 商业化流转...")
    # 台账（每条产品写一条，最多20条防超额）
    ledger_records = [{
        "锁档事件ID": f"CP-{p['product_id']}",
        "确权锚点": "Ω₀⊂⊙∞⊂Ω|DID-BR-000002",
        "锁档名称": f"商业化产品: {p['name'][:24]}",
        "锁档状态": "FROZEN",
        "关联规则ID": p["asset_id"][:40],
        "锁档日期": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "云盘目录": "飞书云盘根/商业化产品库",
    } for p, pr in zip(products, prices)][:20]
    ledger = write_ledger(ledger_records, "commerce")
    print(f"  台账: {ledger}")

    # 展示页
    print("[④] 可视化生成...")
    html = build_showcase(products, prices, run_id)
    out_html = os.path.join(OUT_DIR, "asset-commerce-showcase.html")
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  展示页: {out_html}")

    # 保存产物
    result = {
        "run_id": run_id, "assets_total": len(assets), "products_total": len(products),
        "categories": cats, "total_value": total_val, "ledger": ledger,
        "showcase": out_html, "run_at": now_iso(),
    }
    out_json = os.path.join(OUT_DIR, "commerce_result.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({"result": result, "products": products, "prices": prices}, f, ensure_ascii=False, indent=1, default=str)
    print(f"  结果: {out_json}")

    # 上报
    print("[上报] 商业化成果真值...")
    rep = report_truth(
        f"REPORT.COMMERCE.ENGINE.{datetime.datetime.now().strftime('%Y%m%d.%H%M')}",
        f"核心资产商业化引擎运行: 聚合{len(assets)}条核心资产(能力/元法则/协议/锁档/流水线), 产品化{len(products)}张, 定价{len(prices)}条估值{total_val:,.0f}元/月, 台账{ledger.get('ok')}, 展示页已生成",
        truth_type="data", confidence=0.9,
    )
    print(f"  上报: {rep}")
    result["report"] = rep

    print(f"[asset-commerce] DONE {run_id}")
    return result

if __name__ == "__main__":
    main()
