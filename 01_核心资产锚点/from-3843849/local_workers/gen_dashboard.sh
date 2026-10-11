#!/bin/bash
ROOT=/home/user/Doubao/chats/38438491307070978
CPU=$(uptime | grep -o "load average.*")
MEM=$(free -m | awk '/Mem:/{print $3"/"$2"MB"}')
DISK=$(df -h /home | tail -1 | awk '{print $3"/"$2}')
COUNT=$(python3 -c "import chromadb;print(chromadb.PersistentClient(path='$ROOT/local_rag').get_or_create_collection('drama_corpus').count())" 2>/dev/null)
cat > $ROOT/web_nav/local_dashboard.html << HTML
<title>本地资源看板</title>
<body style="font-family:sans-serif;background:#0d1117;color:#e6edf3;padding:20px">
<h2>本地资源看板</h2>
<p>CPU: $CPU</p><p>内存: $MEM</p><p>磁盘: $DISK</p><p>RAG语料: $COUNT条</p>
</body>
HTML
echo "看板已生成"
