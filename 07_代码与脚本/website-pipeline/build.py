#!/usr/bin/env python3
"""
ZONGYUAN-ROOT 白皮书构建器
Markdown → 玄黑鎏金风格 HTML（单文件，含侧边目录）
风格规范: STYLE-GOLD-BLACK-V1.0 (FROZEN)
"""
import markdown
import re
import sys
import os
from datetime import datetime

def build_html(md_path, output_path, version=None):
    with open(md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()

    # 提取标题（第一个 # 行）
    title_match = re.search(r'^#\s+(.+)$', md_text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else "ZONGYUAN-ROOT 技术白皮书"

    # Markdown → HTML
    md = markdown.Markdown(extensions=[
        'tables', 'fenced_code', 'toc', 'attr_list',
        'def_list', 'footnotes', 'md_in_html'
    ])
    body_html = md.convert(md_text)

    # 生成 TOC（从 h2/h3 提取）
    toc_items = []
    for m in re.finditer(r'<h([23])\s+id="([^"]+)">(.+?)</h\1>', body_html):
        level, hid, text = m.group(1), m.group(2), re.sub(r'<[^>]+>', '', m.group(3))
        toc_items.append((level, hid, text))

    toc_html = ""
    for level, hid, text in toc_items:
        indent = "padding-left:16px;" if level == '3' else ""
        toc_html += f'<a href="#{hid}" class="toc-l{level}" style="{indent}">{text}</a>\n'

    if not version:
        version = datetime.now().strftime('%Y%m%d-%H%M%S')

    template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} · ZONGYUAN-ROOT</title>
<style>
:root {{
  --gold: #c9a962; --gold-light: #e8d5a3; --gold-dark: #8a6d3b;
  --ink: #0b0b0f; --ink-2: #12121a; --ink-3: #1a1a24;
  --text: #d6d6dc; --text-dim: #8a8a94; --line: rgba(201,169,98,0.25);
  --green: #7fb069; --red: #c05c4e; --blue: #5b8db8;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html {{ scroll-behavior:smooth; }}
body {{
  background: var(--ink); color: var(--text);
  font-family: "Songti SC","Noto Serif SC","STSong",serif;
  line-height: 1.75; padding: 0;
}}
/* 顶部导航 */
.topbar {{
  position:sticky; top:0; z-index:100;
  background: rgba(11,11,15,0.92); backdrop-filter:blur(10px);
  border-bottom: 1px solid var(--line);
  padding: 12px 0;
}}
.topbar-in {{ max-width:1200px; margin:0 auto; padding:0 24px; display:flex; align-items:center; justify-content:space-between; }}
.topbar .logo {{ color:var(--gold); font-size:14px; letter-spacing:0.3em; font-weight:600; }}
.topbar .nav {{ display:flex; gap:24px; font-size:13px; }}
.topbar .nav a {{ color:var(--text-dim); text-decoration:none; letter-spacing:0.1em; }}
.topbar .nav a:hover {{ color:var(--gold); }}
.topbar .ver {{ color:var(--text-dim); font-size:11px; letter-spacing:0.15em; font-family:"JetBrains Mono",monospace; }}
/* 布局 */
.layout {{ max-width:1200px; margin:0 auto; display:grid; grid-template-columns:220px 1fr; gap:32px; padding:32px 24px 60px; }}
/* 侧边目录 */
.sidebar {{ position:sticky; top:72px; align-self:start; max-height:calc(100vh - 90px); overflow-y:auto; }}
.sidebar h4 {{ color:var(--gold); font-size:12px; letter-spacing:0.3em; margin-bottom:14px; font-weight:600; }}
.sidebar a {{ display:block; color:var(--text-dim); text-decoration:none; font-size:13px; padding:5px 0; border-bottom:1px solid transparent; transition:all 0.2s; }}
.sidebar a:hover {{ color:var(--gold); border-bottom-color:var(--line); padding-left:4px; }}
.sidebar .toc-l3 {{ font-size:12px; color:var(--text-dim); opacity:0.7; }}
/* 正文 */
.content {{ min-width:0; }}
.content .hero {{ text-align:center; margin-bottom:36px; padding:40px 0 20px; }}
.content .hero .kicker {{ color:var(--gold); font-size:12px; letter-spacing:0.6em; margin-bottom:10px; }}
.content .hero h1 {{
  font-size:clamp(24px,4vw,34px); font-weight:600; color:var(--gold-light);
  letter-spacing:0.08em; text-shadow:0 0 24px rgba(201,169,98,0.35); margin-bottom:10px;
}}
.content .hero .meta {{ color:var(--text-dim); font-size:13px; letter-spacing:0.15em; }}
.divider {{
  height:1px; background:linear-gradient(90deg,transparent,var(--gold),transparent);
  margin:28px 0; position:relative;
}}
.divider::after {{
  content:"Ω₀⊂⊙∞⊂Ω"; position:absolute; left:50%; top:-11px; transform:translateX(-50%);
  background:var(--ink); color:var(--gold); font-size:11px; padding:0 14px; letter-spacing:0.3em;
}}
/* Markdown 内容样式 */
.content h2 {{
  color:var(--gold); font-size:20px; font-weight:600; margin:36px 0 16px;
  padding-left:12px; border-left:3px solid var(--gold); letter-spacing:0.06em;
}}
.content h3 {{ color:var(--gold-light); font-size:17px; margin:24px 0 12px; font-weight:600; }}
.content p {{ margin-bottom:14px; font-size:15px; }}
.content strong {{ color:var(--gold-light); }}
.content a {{ color:var(--blue); text-decoration:none; border-bottom:1px dotted var(--blue); }}
.content blockquote {{
  background:var(--ink-2); border-left:3px solid var(--gold); padding:14px 18px;
  margin:16px 0; border-radius:0 8px 8px 0; color:var(--text-dim); font-size:14px;
}}
.content ul, .content ol {{ margin:12px 0 14px 24px; }}
.content li {{ margin-bottom:6px; font-size:14.5px; }}
.content table {{
  width:100%; border-collapse:collapse; margin:16px 0; font-size:13.5px;
  background:var(--ink-2); border-radius:8px; overflow:hidden;
}}
.content th {{
  color:var(--gold-light); text-align:left; padding:10px 14px;
  border-bottom:1px solid var(--gold); letter-spacing:0.05em; font-weight:600;
}}
.content td {{ padding:9px 14px; border-bottom:1px solid var(--line); }}
.content tr:hover td {{ background:var(--ink-3); }}
.content code {{
  background:#08080c; border:1px solid var(--line); padding:2px 7px;
  border-radius:4px; font-size:13px; color:#c8d6c8; font-family:"JetBrains Mono","Fira Code",monospace;
}}
.content pre {{
  background:#08080c; border:1px solid var(--line); border-radius:8px;
  padding:16px 18px; overflow-x:auto; margin:16px 0;
}}
.content pre code {{ background:none; border:none; padding:0; font-size:13px; line-height:1.6; }}
.content hr {{ border:none; height:1px; background:var(--line); margin:28px 0; }}
/* 指标卡 */
.metric-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:12px; margin:16px 0; }}
.metric-card {{
  background:var(--ink-2); border:1px solid var(--line); border-radius:8px;
  padding:16px; text-align:center;
}}
.metric-card .num {{ font-size:26px; font-weight:700; color:var(--gold-light); }}
.metric-card .lab {{ font-size:12px; color:var(--text-dim); margin-top:4px; }}
/* 页脚 */
.footer {{
  text-align:center; padding:32px 0 24px; border-top:1px solid var(--line); margin-top:48px;
}}
.footer .anchor {{ color:var(--gold); font-size:12px; letter-spacing:0.4em; }}
.footer .info {{ color:var(--text-dim); font-size:11px; letter-spacing:0.2em; margin-top:8px; font-family:"JetBrains Mono",monospace; }}
/* 响应式 */
@media (max-width:860px) {{
  .layout {{ grid-template-columns:1fr; }}
  .sidebar {{ display:none; }}
  .topbar .nav {{ display:none; }}
}}
</style>
</head>
<body>

<div class="topbar">
  <div class="topbar-in">
    <div class="logo">Ω ZONGYUAN-ROOT</div>
    <div class="nav">
      <a href="https://www.huodouai.com/">首页</a>
      <a href="https://www.huodouai.com/sgsa-sop.html">技术SOP</a>
      <a href="#top">白皮书</a>
    </div>
    <div class="ver">v{version}</div>
  </div>
</div>

<div class="layout" id="top">
  <aside class="sidebar">
    <h4>目 录</h4>
    {toc_html}
  </aside>
  <main class="content">
    <div class="hero">
      <div class="kicker">Ω₀⊂⊙∞⊂Ω · 技术白皮书</div>
      <h1>{title}</h1>
      <div class="meta">元极恒一 · 超认知永恒自治 ｜ DID-BR-000002</div>
    </div>
    <div class="divider"></div>
    {body_html}
    <div class="footer">
      <div class="anchor">Ω₀⊂⊙∞⊂Ω</div>
      <div class="info">ZONGYUAN-ROOT ｜ DID-BR-000002 ｜ WHITEPAPER v{version} ｜ 玄黑鎏金 V1.0</div>
    </div>
  </main>
</div>

<script>
// 侧边目录滚动高亮
const tocLinks = document.querySelectorAll('.sidebar a');
const sections = [];
tocLinks.forEach(a => {{
  const id = a.getAttribute('href').slice(1);
  const el = document.getElementById(id);
  if (el) sections.push({{el, a}});
}});
window.addEventListener('scroll', () => {{
  let current = null;
  sections.forEach(s => {{
    if (s.el.getBoundingClientRect().top < 120) current = s;
  }});
  tocLinks.forEach(a => a.style.color = '');
  if (current) current.a.style.color = 'var(--gold)';
}});
</script>
</body>
</html>"""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(template)

    print(f"✅ HTML 已生成: {output_path}")
    print(f"   标题: {title}")
    print(f"   版本: {version}")
    print(f"   目录项: {len(toc_items)}")
    print(f"   文件大小: {os.path.getsize(output_path)} bytes")
    return output_path

if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else 'src/whitepaper.md'
    out = sys.argv[2] if len(sys.argv) > 2 else 'dist/whitepaper.html'
    ver = sys.argv[3] if len(sys.argv) > 3 else None
    build_html(src, out, ver)
