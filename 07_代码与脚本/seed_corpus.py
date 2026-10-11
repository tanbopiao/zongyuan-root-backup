import chromadb
c=chromadb.PersistentClient(path="/home/user/Doubao/chats/38438491307070978/local_rag")
col=c.get_or_create_collection("drama_corpus")
themes=["逆袭","甜宠","悬疑","复仇","穿越","重生","职场","校园","都市","古风","科幻","恐怖","温情","搞笑","励志"]
new=[]
for i,t in enumerate(themes):
    tid=f"theme{i+1:03d}"
    if tid not in col.get()["ids"]:
        new.append((tid,f"{t}题材短剧模板：3-5镜头起承转合，反转结尾"))
if new: col.add(ids=[x[0] for x in new],documents=[x[1] for x in new])
print("语料总数",col.count())
