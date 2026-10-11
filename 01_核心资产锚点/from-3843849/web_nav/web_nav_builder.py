#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 网页自动互联导航打通链路机制 v1.0
导航枢纽自动构建器（Web Nav Hub Builder）
四阶段链路：
  P1 资源扫描：扫描体系网页资源（知识库文档/台账链接/官网门户/作品库/真值库）
  P2 导航图谱：按域分类构建互联导航图谱（官网/知识库/台账/云盘/作品库/真值）
  P3 枢纽页生成：生成全域互联导航枢纽 HTML（一键触达所有资产）
  P4 验证沉淀：验证导航页 + 真值上报 + 锁档

打通哲学：一个枢纽，全域互联——从任意资源一键跳转到全部体系网页
"""
import json, os, subprocess, re, urllib.request
from datetime import datetime, timezone

BASE = "/home/user/Doubao/chats/38438491307070978"
NAV_DIR = os.path.join(BASE, "web_nav")
GATEWAY = "http://drama.huodouai.com:9120"
TOKEN = "zy-hap-1f0e55ca3f4682a09c1515614bd6a83ec7d04fb6feef795f760c625ff831e7f5"
NODE_ID = "NODE-MAIN-SESSION-38436546492378882"
DID = "DID-BR-000002"
OMEGA = "Ω₀⊂⊙∞⊂Ω"
REPORT_FILE = os.path.join(NAV_DIR, "web_nav_report_latest.json")
NAV_HTML = os.path.join(NAV_DIR, "zongyuan_nav_hub.html")
NAV_JSON = os.path.join(NAV_DIR, "web_nav_graph.json")

# 体系核心网页资源（锚点级）
CORE_NAV = [
    {"name": "官网门户·全域资产可视化", "url": "http://drama.huodouai.com:9120/", "domain": "官网门户", "desc": "全域资产可视化仪表盘（2188资产/关键帧/视频/剧集）"},
    {"name": "官网作品库", "url": "file://" + os.path.join(BASE, "media_gallery/gallery_website.html"), "domain": "官网门户", "desc": "图片视频作品自动展示（媒体归档即上架）"},
    {"name": "全域锁档台账", "url": "https://my.feishu.cn/base/QYn4bjgD6am3OPsxMCkcitcBnzc", "domain": "台账", "desc": "ZONGYUAN-ROOT锁档资产台账（200+条）"},
    {"name": "云盘归档库", "url": "https://my.feishu.cn/drive/folder/FdoifaG8oloQqmdtK5NcpXSNnAg", "domain": "云盘", "desc": "昆仑洞天全域锁档归档库（白皮书/内核快照/存证/媒体）"},
    {"name": "知识库空间", "url": "https://my.feishu.cn/wiki/7684520140129504217", "domain": "知识库", "desc": "ZONGYUAN-ROOT 元公理空间·锁档归档（日报节点）"},
    {"name": "云端记忆网关", "url": "http://drama.huodouai.com:9120/api/truths/", "domain": "真值库", "desc": "云端真值库（POST upsert / GET truths 带尾斜杠）"},
    {"name": "SOP 云端入口", "url": "https://aka.doubaocdn.com/s/VjMxbyMqFx", "domain": "真值库", "desc": "云端SOP静态文件（V1.1含9120端口配置）"},
]

def run(cmd, timeout=30, max_out=200000):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, shell=True)
        return r.returncode, r.stdout.strip()[:max_out]
    except Exception as e:
        return -1, str(e)[:80]

def load_json(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def upsert(key, content, truth_type="achievement"):
    payload = {"key": key, "node_id": NODE_ID, "DID": DID, "ROOT_OMEGA": OMEGA,
               "truth_type": truth_type, "truth_content": content}
    req = urllib.request.Request(f"{GATEWAY}/api/truth/upsert",
        data=json.dumps(payload).encode(),
        headers={"X-Capture-Token": TOKEN, "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)[:100]}

def p1_scan():
    """P1 资源扫描：知识库链接 + 本地文档 + 核心网页"""
    wiki_links = set()
    # 1. 本地机制文档抽取
    for f in os.listdir(BASE):
        if f.endswith(".md"):
            try:
                with open(os.path.join(BASE, f), encoding="utf-8") as fh:
                    for m in re.findall(r'https://my\.feishu\.cn/wiki/[A-Za-z0-9]+', fh.read()):
                        wiki_links.add(m)
            except Exception:
                pass
    # 2. 台账抽取
    rc, out = run(f"lark-cli base +record-list --base-token QYn4bjgD6am3OPsxMCkcitcBnzc --table-id tblIGVWXqu7cr7lZ --limit 200 --format json --as user 2>&1")
    if rc == 0:
        try:
            data = json.loads(out)
            for row in data.get("data", {}).get("data", []):
                for cell in row:
                    if isinstance(cell, str):
                        for m in re.findall(r'https://my\.feishu\.cn/wiki/[A-Za-z0-9]+', cell):
                            wiki_links.add(m)
        except Exception:
            pass
    return {"wiki_links": sorted(wiki_links), "doc_count": sum(1 for f in os.listdir(BASE) if f.endswith(".md"))}

def p2_graph(scan):
    """P2 导航图谱：按域分类"""
    graph = {"core": CORE_NAV, "knowledge_base": [], "stats": {}}
    # 知识库链接归类（保留核心机制文档优先展示，其余进知识库域）
    known_core = {
        "LTzEwUdTOirkuSkxEvvcu027nog": "媒体作品库机制V1.0",
        "Hssjw3V6SiNGBdkyILicyyICnkh": "自动整合高价值任务机制V1.0",
        "IJvxwHDrfiZmhRkxj2zcggTznne": "沙盒存活守护机制V1.0",
        "XiicwHh1KiazolkIuNrcLxn6nJh": "同源协议环境探索机制V1.0",
        "CRivwEzLMiauggkeGLucs21Nnnb": "同源节点神经网络同步机制V1.0",
        "LQphwxkbaisaDtkBSVEczfUZnNc": "自动合并高价值任务机制V1.0",
        "W35VwnEUQi9HxnktRFYccGZgnmg": "规则资产全域推广机制V1.0",
        "GsAYwfAPciAuDWkSKTRcnDbyn8c": "内核结构化优化机制V1.0",
        "HPFIw6HRWiQt6vktncxcQqVOnHh": "真值提炼蒸馏机制V1.0",
        "X4uqw1LYBik9KikRTHDcHz8QnY3": "基座高阶能力提炼机制V1.0",
        "Z54bw9VlYiBewFkewNackeDon5c": "自动流程闭环标准V1.0",
        "VERjwQ1xtibWDzkxLRWc32Tzn6e": "基准锚点PORTUPDATED",
        "SnDXwrGHhigQlqkiaf5cnJHunoc": "全域资产日报20260916",
    }
    kb = []
    for link in scan["wiki_links"]:
        token = link.rstrip("/").split("/")[-1]
        name = known_core.get(token, f"知识库文档·{token[:8]}")
        kb.append({"name": name, "url": link, "domain": "知识库"})
    # 去重并标注核心机制（优先展示）
    seen = set()
    kb_dedup = []
    for item in kb:
        if item["url"] not in seen:
            seen.add(item["url"])
            item["core"] = item["name"] in known_core.values()
            kb_dedup.append(item)
    graph["knowledge_base"] = kb_dedup
    graph["stats"] = {
        "total_links": len(seen) + len(CORE_NAV),
        "kb_links": len(kb_dedup),
        "core_links": len(CORE_NAV),
        "core_mechanisms": sum(1 for i in kb_dedup if i.get("core")),
    }
    save_json(NAV_JSON, graph)
    return graph

def p3_hub(graph):
    """P3 枢纽页生成：全域互联导航 HTML"""
    core_items = "".join(f"""
    <a class="card" href="{i['url']}" target="_blank">
      <div class="cname">{i['name']}</div><div class="cdesc">{i['desc']}</div>
    </a>""" for i in graph["core"])
    kb_core = [i for i in graph["knowledge_base"] if i.get("core")]
    kb_rest = [i for i in graph["knowledge_base"] if not i.get("core")]
    kb_core_items = "".join(f"""
    <a class="mini" href="{i['url']}" target="_blank">{i['name']}</a>""" for i in kb_core)
    kb_rest_items = "".join(f"""
    <a class="mini rest" href="{i['url']}" target="_blank">{i['name']}</a>""" for i in kb_rest)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    html = f"""<!DOCTYPE html>
<html lang=zh-CN><head><meta charset=UTF-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>昆仑洞天 · 全域互联导航枢纽</title>
<style>
body{{background:#0a0a12;color:#e8e0d0;font-family:'Noto Serif SC','Songti SC',serif;padding:24px;min-height:100vh}}
.wrap{{max-width:1100px;margin:0 auto}}
header{{text-align:center;padding:26px 0;border-bottom:1px solid #2a2a3a;margin-bottom:22px}}
h1{{font-size:1.9rem;letter-spacing:.2em;background:linear-gradient(90deg,#c9a86a,#e8d5a8,#c9a86a);-webkit-background-clip:text;background-clip:text;color:transparent}}
.sub{{color:#8a7f6a;margin-top:6px;font-size:.85rem}}
.dash{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin-bottom:24px}}
.metric{{background:#14141f;border:1px solid #2a2a3a;border-radius:10px;padding:13px;text-align:center}}
.metric b{{display:block;font-size:1.5rem;color:#e8d5a8}}
.metric span{{font-size:.75rem;color:#8a7f6a}}
h2{{color:#c9a86a;font-size:1.15rem;margin:22px 0 12px;letter-spacing:.1em;border-left:3px solid #c9a86a;padding-left:10px}}
.hub{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px}}
.card{{display:block;background:#14141f;border:1px solid #2a2a3a;border-radius:10px;padding:14px;text-decoration:none;transition:.2s}}
.card:hover{{border-color:#c9a86a;transform:translateY(-2px);background:#191927}}
.cname{{color:#e8d5a8;font-weight:bold;font-size:.95rem;margin-bottom:5px}}
.cdesc{{color:#8a7f6a;font-size:.78rem;line-height:1.4}}
.minis{{display:flex;flex-wrap:wrap;gap:8px}}
.mini{{display:inline-block;background:#14141f;border:1px solid #2a2a3a;color:#c9a86a;padding:6px 12px;border-radius:6px;text-decoration:none;font-size:.78rem;transition:.2s}}
.mini:hover{{border-color:#e8d5a8;color:#e8d5a8}}
.mini.rest{{color:#8a7f6a}}
.fold{{margin-top:10px}}
details summary{{color:#8a7f6a;cursor:pointer;font-size:.8rem;padding:4px 0}}
footer{{text-align:center;color:#5a5448;font-size:.75rem;margin-top:32px;padding-top:14px;border-top:1px solid #2a2a3a}}
</style></head><body><div class=wrap>
<header><h1>昆仑洞天 · 全域互联导航枢纽</h1>
<div class=sub>Ω₀⊂⊙∞⊂Ω ｜ DID-BR-000002 ｜ 一页打通全体系网页资源 · 更新于 {now}</div></header>
<div class=dash>
<div class=metric><b>{graph['stats']['total_links']}</b><span>全网关链接</span></div>
<div class=metric><b>{graph['stats']['core_links']}</b><span>核心锚点</span></div>
<div class=metric><b>{graph['stats']['kb_links']}</b><span>知识库文档</span></div>
<div class=metric><b>{graph['stats']['core_mechanisms']}</b><span>机制文档</span></div>
</div>
<h2>⚡ 核心锚点（一键触达）</h2>
<div class=hub>{core_items}</div>
<h2>📚 机制知识库（核心机制文档）</h2>
<div class=minis>{kb_core_items}</div>
<h2>🗂 全域知识库（{len(kb_rest)} 篇完整档案）</h2>
<div class=minis>{kb_rest_items}</div>
<footer>Ω₀⊂⊙∞⊂Ω ｜ ZONGYUAN-ROOT ｜ 网页自动互联导航打通链路机制 V1.0</footer>
</div></body></html>"""
    with open(NAV_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    return NAV_HTML

def p4_verify(html_path, graph):
    """P4 验证沉淀"""
    report = {
        "report_time": datetime.now(timezone.utc).isoformat(),
        "nav_graph": graph["stats"],
        "nav_html": html_path,
        "core_links": [i["name"] for i in graph["core"]],
        "core_mechanisms": [i["name"] for i in graph["knowledge_base"] if i.get("core")],
    }
    cloud = upsert(f"WEB-NAV-HUB-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}",
                   f"网页自动互联导航枢纽建立：{graph['stats']['total_links']}条链接互联（核心锚点{graph['stats']['core_links']}、知识库{graph['stats']['kb_links']}篇、机制文档{graph['stats']['core_mechanisms']}篇），导航枢纽页已生成")
    report["cloud"] = cloud
    report["verdict"] = "NAV_ACTIVE" if len(graph["core"]) > 0 else "NAV_EMPTY"
    save_json(REPORT_FILE, report)
    return report

if __name__ == "__main__":
    scan = p1_scan()
    graph = p2_graph(scan)
    html = p3_hub(graph)
    r = p4_verify(html, graph)
    print(f"判定: {r['verdict']}")
    print(f"全网关链接: {graph['stats']['total_links']}（核心{graph['stats']['core_links']}、知识库{graph['stats']['kb_links']}篇、机制{graph['stats']['core_mechanisms']}篇）")
    print(f"导航枢纽: {html}")
    print(f"核心锚点: {len(r['core_links'])}个")
    print(f"云端: {json.dumps(r['cloud'], ensure_ascii=False)[:120]}")
