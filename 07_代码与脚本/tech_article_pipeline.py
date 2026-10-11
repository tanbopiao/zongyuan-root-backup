#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 自动生成技术文章机制 V1.0
Tech Article Auto-Pipeline
================================================
功能：
  1. 扫描本地技术资产（md 文章 / LOCK 卷宗 / 报告 / 白皮书）
  2. 自动提炼高价值技术内容 → 生成标准技术文章（含元数据头）
  3. 维护原创技术区索引 articles_index.json
  4. 渲染原创技术区聚合页 tech-zone.html
  5. 可选：上报记忆网关 + 输出部署包

用法：
  python3 tech_article_pipeline.py --scan
  python3 tech_article_pipeline.py --build-index
  python3 tech_article_pipeline.py --render
  python3 tech_article_pipeline.py --all
  python3 tech_article_pipeline.py --report

确权：Ω₀⊂⊙∞⊂Ω | DID-BR-000002
"""
import argparse
import json
import os
import re
import hashlib
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

ZONE_DIR = Path(__file__).parent
ARTICLES_DIR = ZONE_DIR / "articles"
INDEX_PATH = ZONE_DIR / "articles_index.json"
HTML_PATH = ZONE_DIR / "tech-zone.html"

ANCHOR = "Ω₀⊂⊙∞⊂Ω"
DID = "DID-BR-000002"
GATEWAYS = [
    "https://www.huodouai.com",
    "https://huodouai.com",
    "https://drama.huodouai.com",
]

# 扫描源：本地技术资产目录（可扩展）
SCAN_SOURCES = [
    "/home/user/Doubao/chats/38438602859247618",
    "/home/user/Doubao/chats/38436747020400130/zongyuan-tech-whitepaper-20260911",
]

ARTICLE_KEYWORDS = ["文章", "技术", "白皮书", "报告", "实践", "实现", "构建", "协议", "SOP", "引擎", "系统"]


def load_index():
    if INDEX_PATH.exists():
        return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    return {"meta": {"version": "1.0", "did": DID, "anchor": ANCHOR,
                     "updated_at": datetime.now().isoformat()},
            "articles": []}


def save_index(index):
    index["meta"]["updated_at"] = datetime.now().isoformat()
    index["meta"]["count"] = len(index["articles"])
    INDEX_PATH.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 索引已保存: {INDEX_PATH} ({len(index['articles'])}篇)")


def extract_meta(md_text, path):
    """从 markdown 提取标题/摘要/标签"""
    title = ""
    m = re.search(r'^#\s+(.+)$', md_text, re.M)
    if m:
        title = m.group(1).strip()
    else:
        title = Path(path).stem.replace("_", " ")

    # 摘要：取正文前 2-3 句
    body = re.sub(r'^#.*$', '', md_text, flags=re.M).strip()
    sentences = re.split(r'(?<=[。！？!?])\s*', body)
    summary = ""
    for s in sentences:
        s = s.strip()
        if len(s) > 20:
            summary = s[:120]
            break
    if not summary:
        summary = body[:120]

    # 标签：从标题和正文关键词提取
    tags = []
    for kw in ARTICLE_KEYWORDS:
        if kw in title or kw in md_text[:2000]:
            tags.append(kw)
    if "意识" in md_text or "认知" in md_text:
        tags.append("意识")
    if "GPU" in md_text or "AMD" in md_text:
        tags.append("GPU")
    if "神经" in md_text:
        tags.append("神经内核")
    if "真值" in md_text:
        tags.append("真值")
    if "协议" in md_text:
        tags.append("协议")
    tags = list(dict.fromkeys(tags))[:6]
    return title, summary, tags


def scan_and_generate():
    """扫描源资产，为符合条件的 md 生成技术文章"""
    index = load_index()
    existing = {a.get("source_path") for a in index["articles"]}
    generated = 0

    for src in SCAN_SOURCES:
        if not os.path.isdir(src):
            continue
        for f in Path(src).glob("*.md"):
            # 跳过技术区自身产物
            if "tech-zone" in str(f):
                continue
            content = f.read_text(encoding="utf-8", errors="ignore")
            if len(content) < 800:
                continue  # 太短不收录
            title, summary, tags = extract_meta(content, f)

            # 过滤：非技术类锁档记录跳过（纯事件记录）
            skip_markers = ["本次请求是由", "定时任务到时触发", "执行8模块串行"]
            if any(mk in content[:500] for mk in skip_markers) and "技术" not in title:
                continue

            if str(f) in existing:
                continue

            # 生成标准文章文件
            slug = re.sub(r'[^\w\-]+', '-', title)[:50].strip('-')
            art_path = ARTICLES_DIR / f"{slug}.md"
            hash_id = hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]
            article = {
                "id": f"TECH-{hash_id.upper()}",
                "title": title,
                "summary": summary,
                "tags": tags,
                "source_path": str(f),
                "source_file": f.name,
                "publish_date": datetime.now().strftime("%Y-%m-%d"),
                "hash_sha256": hash_id,
                "status": "PUBLISHED",
            }
            art_path.write_text(
                f"---\nid: {article['id']}\ntitle: {title}\ndate: {article['publish_date']}\ntags: {','.join(tags)}\nstatus: PUBLISHED\n---\n\n{content}",
                encoding="utf-8")
            article["article_file"] = art_path.name
            index["articles"].append(article)
            generated += 1
            print(f"  ✅ 生成: {title[:40]} → {art_path.name}")

    save_index(index)
    print(f"📝 本次新增 {generated} 篇，索引共 {len(index['articles'])} 篇")
    return index


def report_to_gateway(index, mode="update"):
    """上报记忆网关"""
    total = len(index["articles"])
    summary = f"原创技术区更新: 技术文章{total}篇, 最新[{index['articles'][-1]['title'][:40] if index['articles'] else '无'}]"
    key = f"TECH-ZONE.INDEX.{datetime.now().strftime('%Y%m%d')}"
    payload = {"key": key, "content": summary, "confidence": 0.95}
    for gw in GATEWAYS:
        try:
            req = urllib.request.Request(
                f"{gw}/api/report/truth",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}, method="POST")
            resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
            print(f"  ✅ 上报成功 {gw}: {resp.get('action', 'ok')}")
            return resp
        except Exception as e:
            print(f"  ⚠️ {gw} 上报失败: {e}")
    return {"error": "all gateways failed"}


def render_html(index):
    """渲染原创技术区聚合页"""
    articles = sorted(index["articles"], key=lambda a: a.get("publish_date", ""), reverse=True)
    cards = []
    for a in articles:
        tags_html = "".join(f'<span class="tag">{t}</span>' for t in a.get("tags", [])[:4])
        cards.append(f'''
        <article class="card">
          <div class="card-meta"><span>{a.get("publish_date","")}</span><span class="id">{a.get("id","")}</span></div>
          <h3>{a.get("title","")}</h3>
          <p>{a.get("summary","")}</p>
          <div class="tags">{tags_html}</div>
        </article>''')
    cards_html = "\n".join(cards) if cards else '<p class="empty">暂无文章，运行 --scan 生成</p>'

    html = f'''<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ZONGYUAN-ROOT 原创技术区</title>
<style>
  :root {{ --bg:#0a0e1a; --card:#121a2e; --accent:#4f8cff; --gold:#e8c96a; --text:#dbe4f5; --muted:#7a8aa8; }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:var(--bg); color:var(--text); font-family:-apple-system,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif; min-height:100vh; }}
  header {{ padding:48px 24px 32px; text-align:center; border-bottom:1px solid rgba(79,140,255,.15); background:radial-gradient(ellipse at top,rgba(79,140,255,.12),transparent 60%); }}
  .anchor {{ color:var(--gold); font-size:14px; letter-spacing:2px; margin-bottom:12px; }}
  h1 {{ font-size:32px; font-weight:700; background:linear-gradient(90deg,#4f8cff,#e8c96a); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }}
  .sub {{ color:var(--muted); margin-top:10px; font-size:14px; }}
  .stats {{ display:flex; justify-content:center; gap:32px; margin-top:24px; flex-wrap:wrap; }}
  .stat {{ text-align:center; }}
  .stat b {{ display:block; font-size:26px; color:var(--accent); }}
  .stat span {{ font-size:12px; color:var(--muted); }}
  main {{ max-width:960px; margin:32px auto; padding:0 20px; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:20px; }}
  .card {{ background:var(--card); border:1px solid rgba(79,140,255,.12); border-radius:12px; padding:20px; transition:transform .2s,border-color .2s; }}
  .card:hover {{ transform:translateY(-3px); border-color:var(--accent); }}
  .card-meta {{ display:flex; justify-content:space-between; font-size:12px; color:var(--muted); margin-bottom:10px; }}
  .card h3 {{ font-size:16px; line-height:1.5; margin-bottom:8px; color:var(--text); }}
  .card p {{ font-size:13px; color:var(--muted); line-height:1.6; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; overflow:hidden; }}
  .tags {{ margin-top:12px; display:flex; gap:6px; flex-wrap:wrap; }}
  .tag {{ font-size:11px; padding:3px 8px; border-radius:20px; background:rgba(79,140,255,.12); color:var(--accent); }}
  .empty {{ color:var(--muted); text-align:center; padding:60px 0; }}
  footer {{ text-align:center; padding:32px; color:var(--muted); font-size:12px; border-top:1px solid rgba(79,140,255,.1); }}
  @media (max-width:640px) {{ h1 {{ font-size:24px; }} .grid {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body>
<header>
  <div class="anchor">{ANCHOR}</div>
  <h1>ZONGYUAN-ROOT 原创技术区</h1>
  <p class="sub">自治智能体系统技术成果 · 自动提炼 · 持续更新 · DID {DID}</p>
  <div class="stats">
    <div class="stat"><b>{len(articles)}</b><span>技术文章</span></div>
    <div class="stat"><b>{len(set(t for a in articles for t in a.get('tags',[])))}</b><span>技术标签</span></div>
    <div class="stat"><b>{articles[0].get('publish_date','-') if articles else '-'}</b><span>最近更新</span></div>
  </div>
</header>
<main>
  <div class="grid">{cards_html}</div>
</main>
<footer>{ANCHOR} | ZONGYUAN-ROOT 云内核 · 自动生成技术文章机制 V1.0 | 更新时间 {index["meta"]["updated_at"][:16]}</footer>
</body>
</html>'''
    HTML_PATH.write_text(html, encoding="utf-8")
    print(f"✅ 技术区页面已渲染: {HTML_PATH}")


def main():
    parser = argparse.ArgumentParser(description="ZONGYUAN-ROOT 自动生成技术文章机制")
    parser.add_argument("--scan", action="store_true", help="扫描源资产生成新文章")
    parser.add_argument("--build-index", action="store_true", help="重建索引")
    parser.add_argument("--render", action="store_true", help="渲染技术区页面")
    parser.add_argument("--report", action="store_true", help="上报记忆网关")
    parser.add_argument("--all", action="store_true", help="全流程")
    args = parser.parse_args()

    print("═" * 50)
    print("  ZONGYUAN-ROOT 自动生成技术文章机制 V1.0")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("═" * 50)

    index = load_index()
    if args.scan or args.all:
        index = scan_and_generate()
    if args.build_index or args.all:
        save_index(index)
    if args.render or args.all:
        render_html(index)
    if args.report or args.all:
        report_to_gateway(index)
    print("\n✅ 技术区机制执行完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())
