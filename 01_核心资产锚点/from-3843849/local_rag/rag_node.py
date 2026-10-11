#!/usr/bin/env python3
# ZONGYUAN-ROOT 本地 RAG 智能预处理节点（持久化）
import chromadb, os, json, time

DB = "/home/user/Doubao/chats/38438491307070978/local_rag"
client = chromadb.PersistentClient(path=DB)

# 建集合
col = client.get_or_create_collection("drama_corpus")

# 写入示例语料（剧本模板）
samples = [
    {"id": "tpl001", "text": "外卖员题材：主角送单途中发现异常订单，卷入救人事件，3镜头反转"},
    {"id": "tpl002", "text": "职场逆袭：被裁员的实习生意外发现公司秘密，4镜头翻盘"},
    {"id": "tpl003", "text": "情感短剧：陌生人共撑一把伞，5镜头从误会到相守"},
]
existing = col.get()["ids"]
new = [s for s in samples if s["id"] not in existing]
if new:
    col.add(ids=[s["id"] for s in new], documents=[s["text"] for s in new])
    print(f"[RAG] 新增 {len(new)} 条语料")
else:
    print("[RAG] 语料已存在")

# 语义检索测试
res = col.query(query_texts=["救人"], n_results=2)
print("[RAG] 检索结果:", res["documents"][0])
print(f"[RAG] 总数: {col.count()} | 持久化: {DB}")

# 状态落盘
json.dump({"status": "ALIVE", "count": col.count(), "ts": time.time()},
          open(DB + "/status.json", "w"), ensure_ascii=False)
