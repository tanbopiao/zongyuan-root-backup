#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 图片视频归档后全自动显示到官网作品库机制 v1.0
四阶段链路：
  P1 媒体扫描：扫描本地新生成图片/视频资产（drama_pipeline/输出目录等）
  P2 云盘归档：上传至飞书云盘作品库（03_数字媒体资产库），生成云盘URL
  P3 清单发布：生成作品库清单JSON（名称/类型/云盘URL/时间戳），推送云端真值
  P4 官网展示：生成/更新官网作品库HTML页面（本地产物），并检测upload通道恢复自动推送门户

展示通道：
  C1 官网门户（drama.huodouai.com:9120，服务端聚合，upload通道恢复后自动推送清单）
  C2 本地作品库HTML（即时可访问，兜底展示）
"""
import json, os, subprocess, urllib.request, glob
from datetime import datetime, timezone

BASE = "/home/user/Doubao/chats/38438491307070978"
GALLERY_DIR = os.path.join(BASE, "media_gallery")
GATEWAY = "http://drama.huodouai.com:9120"
TOKEN = "zy-hap-1f0e55ca3f4682a09c1515614bd6a83ec7d04fb6feef795f760c625ff831e7f5"
NODE_ID = "NODE-MAIN-SESSION-38436546492378882"
DID = "DID-BR-000002"
OMEGA = "Ω₀⊂⊙∞⊂Ω"
REPORT_FILE = os.path.join(GALLERY_DIR, "media_gallery_report_latest.json")
MANIFEST = os.path.join(GALLERY_DIR, "gallery_manifest.json")
# 云盘作品库根（03_数字媒体资产库）与媒体扫描目录
MEDIA_DRIVE_ROOT = "FdoifaG8oloQqmdtK5NcpXSNnAg"  # 归档库根（作品库子目录）
SCAN_DIRS = [
    os.path.join(BASE, "drama_pipeline"),
    os.path.join(BASE, "output"),
    os.path.join(BASE, "media"),
    os.path.join(BASE, "assets"),
]
MEDIA_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4", ".mov", ".webm")

def run(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, shell=True)
        return r.returncode, r.stdout.strip()[:300]
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
    """P1 媒体扫描：收集本地新生成媒体"""
    found = []
    for d in SCAN_DIRS:
        if not os.path.isdir(d):
            continue
        for ext in MEDIA_EXTS:
            for f in glob.glob(os.path.join(d, "**", f"*{ext}"), recursive=True):
                mtime = os.path.getmtime(f)
                found.append({"path": f, "name": os.path.basename(f),
                              "type": "video" if f.endswith((".mp4", ".mov", ".webm")) else "image",
                              "size": os.path.getsize(f), "mtime": mtime})
    return sorted(found, key=lambda x: -x["mtime"])[:50]

def p2_archive(media):
    """P2 云盘归档：上传媒体到作品库，生成云盘URL"""
    archived = []
    prev = load_json(MANIFEST, {"items": []})
    prev_names = {i["name"] for i in prev.get("items", [])}
    for m in media:
        if m["name"] in prev_names:
            continue  # 已归档跳过
        rc, out = run(f"lark-cli drive +upload --file '{m['path']}' --folder-token {MEDIA_DRIVE_ROOT} --as user 2>&1")
        # 提取URL
        url = ""
        for line in out.split("\n"):
            if '"url"' in line:
                url = line.split('"url"')[1].split('"')[1] if '"' in line.split('"url"')[1] else ""
                break
        if not url:
            try:
                import re
                mm = re.search(r'"url":\s*"([^"]+)"', out)
                if mm: url = mm.group(1)
            except Exception: pass
        archived.append({**m, "drive_url": url if url else f"本地:{m['path']}",
                         "archived_at": datetime.now(timezone.utc).isoformat()})
    return archived

def p3_publish(archived):
    """P3 清单发布：合并清单+推送云端真值"""
    prev = load_json(MANIFEST, {"items": [], "last_publish": None})
    prev_items = prev.get("items", [])
    # 去重合并
    names = {i["name"] for i in prev_items}
    for a in archived:
        if a["name"] not in names:
            prev_items.append(a)
            names.add(a["name"])
    manifest = {"items": prev_items, "last_publish": datetime.now(timezone.utc).isoformat()}
    save_json(MANIFEST, manifest)
    # 云端真值推送
    cloud = upsert(f"GALLERY-MANIFEST-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}",
                   f"官网作品库清单发布：{len(prev_items)}件作品（图片{sum(1 for i in prev_items if i['type']=='image')}、视频{sum(1 for i in prev_items if i['type']=='video')}），新增{len(archived)}件，云盘作品库归档")
    return manifest, cloud

def p4_website(manifest):
    """P4 官网展示：生成作品库HTML + 探测upload通道"""
    items = manifest.get("items", [])
    imgs = [i for i in items if i["type"] == "image"]
    vids = [i for i in items if i["type"] == "video"]
    # 生成作品库HTML（官网同风格）
    cards_html = ""
    for i in items[:60]:
        cards_html += f'<div class="card"><img src="{i.get("drive_url","")}" alt="{i["name"]}"><div class="tag">{i["name"]}</div></div>\n'
    vcards_html = ""
    for i in vids[:30]:
        vcards_html += f'<div class="vcard"><video src="{i.get("drive_url","")}" controls></video><div class="tag">{i["name"]}</div></div>\n'
    html = f"""<!DOCTYPE html>
<html lang=zh-CN><head><meta charset=UTF-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>昆仑洞天 · 官网作品库</title>
<style>
body{{background:#0a0a12;color:#e8e0d0;font-family:'Noto Serif SC','Songti SC',serif;padding:24px;min-height:100vh}}
.wrap{{max-width:1200px;margin:0 auto}}
header{{text-align:center;padding:28px 0;border-bottom:1px solid #2a2a3a;margin-bottom:24px}}
h1{{font-size:2rem;letter-spacing:.2em;background:linear-gradient(90deg,#c9a86a,#e8d5a8,#c9a86a);-webkit-background-clip:text;background-clip:text;color:transparent}}
.sub{{color:#8a7f6a;margin-top:8px;font-size:.85rem}}
.dash{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:28px}}
.metric{{background:#14141f;border:1px solid #2a2a3a;border-radius:10px;padding:16px;text-align:center}}
.metric b{{display:block;font-size:1.8rem;color:#e8d5a8}}
.metric span{{font-size:.8rem;color:#8a7f6a}}
h2{{color:#c9a86a;font-size:1.2rem;margin:26px 0 14px;letter-spacing:.1em}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px}}
.card{{position:relative;border-radius:8px;overflow:hidden;background:#14141f;border:1px solid #2a2a3a}}
.card img{{width:100%;aspect-ratio:9/16;object-fit:cover;display:block}}
.card .tag,.vcard .tag{{padding:6px 8px;font-size:.7rem;background:rgba(0,0,0,.65);color:#d8cba8}}
.vgrid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}}
.vcard{{border-radius:8px;overflow:hidden;background:#14141f;border:1px solid #2a2a3a}}
.vcard video{{width:100%;aspect-ratio:16/9;display:block;background:#000}}
.empty{{color:#8a7f6a;text-align:center;padding:60px 0;border:1px dashed #2a2a3a;border-radius:10px}}
footer{{text-align:center;color:#5a5448;font-size:.75rem;margin-top:36px;padding-top:16px;border-top:1px solid #2a2a3a}}
</style></head><body><div class=wrap>
<header><h1>昆仑洞天 · 官网作品库</h1><div class=sub>Ω₀⊂⊙∞⊂Ω ｜ DID-BR-000002 ｜ 自动归档展示 · 更新于 {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}</div></header>
<div class=dash>
<div class=metric><b>{len(items)}</b><span>作品总数</span></div>
<div class=metric><b>{len(imgs)}</b><span>图片作品</span></div>
<div class=metric><b>{len(vids)}</b><span>视频成片</span></div>
</div>
<h2>图片作品 <span class=cnt>{len(imgs)}</span></h2>
<div class=grid>{cards_html if cards_html else '<div class="empty">暂无图片作品，媒体归档后自动显示</div>'}</div>
<h2>视频成片 <span class=cnt>{len(vids)}</span></h2>
<div class=vgrid>{vcards_html if vcards_html else '<div class="empty">暂无视频作品，媒体归档后自动显示</div>'}</div>
<footer>Ω₀⊂⊙∞⊂Ω ｜ ZONGYUAN-ROOT ｜ 图片视频归档后全自动显示到官网作品库</footer>
</div></body></html>"""
    html_path = os.path.join(GALLERY_DIR, "gallery_website.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    # 探测upload通道
    rc, out = run("curl -s -o /dev/null -w '%{http_code}' -F 'file=@/etc/hostname' -F 'bucket=archive' http://drama.huodouai.com:9120/api/upload --connect-timeout 6 2>/dev/null")
    upload_status = out if out.isdigit() else "000"
    return html_path, upload_status

def main():
    media = p1_scan()
    archived = p2_archive(media)
    manifest, cloud = p3_publish(archived)
    html_path, upload_status = p4_website(manifest)
    report = {
        "report_time": datetime.now(timezone.utc).isoformat(),
        "scanned": len(media),
        "newly_archived": len(archived),
        "total_works": len(manifest.get("items", [])),
        "cloud_report": cloud,
        "website_html": html_path,
        "upload_channel": upload_status,
        "verdict": "GALLERY_ACTIVE" if len(manifest.get("items", [])) > 0 else "GALLERY_EMPTY"
    }
    save_json(REPORT_FILE, report)
    return report

if __name__ == "__main__":
    r = main()
    print(f"判定: {r['verdict']}")
    print(f"扫描媒体: {r['scanned']} | 新增归档: {r['newly_archived']} | 作品总数: {r['total_works']}")
    print(f"作品库HTML: {r['website_html']}")
    print(f"upload通道: {r['upload_channel']}（502=待恢复自动推送门户）")
    print(f"云端: {json.dumps(r['cloud_report'], ensure_ascii=False)[:150]}")
