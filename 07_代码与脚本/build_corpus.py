#!/usr/bin/env python3
# 本地灌语料到RAG（免费，吃空闲磁盘）
import chromadb, os
DB="/home/user/Doubao/chats/38438491307070978/local_rag"
client=chromadb.PersistentClient(path=DB)
col=client.get_or_create_collection("drama_corpus")
# 批量灌入短剧模板
templates=[
    ("tpl004","都市悬疑：程序员发现代码里藏着一段不存在的注释"),
    ("tpl005","古风：女将军战后归乡，发现旧宅已易主"),
    ("tpl006","科幻：维修工在废弃飞船里唤醒一个冬眠乘客"),
]
ex=col.get()["ids"]
new=[t for t in templates if t[0] not in ex]
if new: col.add(ids=[t[0] for t in new],documents=[t[1] for t in new]); print(f"[corpus] 灌入{len(new)}条")
else: print("[corpus] 已存在")
print(f"[corpus] 总数{col.count()}")
