#!/bin/bash
# 全域统一锁档：固定身份+固定目录+中枢账本，杜绝跨窗口分散
ROOT=/home/user/Doubao/chats/38438491307070978
FOLDER=FdoifaG8oloQqmdtK5NcpXSNnAg
TS=$(date +%Y%m%d-%H%M)
# 1. 打包关键资产
tar -czf $ROOT/LOCK-UNIFIED-$TS.tar.gz $(ls $ROOT/*.md $ROOT/*.json $ROOT/*.sh 2>/dev/null) 2>/dev/null
# 2. 统一身份+固定目录上传（同系统user，登录态共享）
OUT=$(lark-cli drive +upload --file $ROOT/LOCK-UNIFIED-$TS.tar.gz --folder-token $FOLDER --as user 2>&1)
FT=$(echo "$OUT" | grep -o '"file_token": "[^"]*"' | head -1 | cut -d'"' -f4)
# 3. 中枢统一账本：记录file_token，新窗口从中枢拉
curl -s -m 10 -X POST "https://www.huodouai.com/api/report/truth" \
  -H "Content-Type: application/json" -H "X-Capture-Token: DID-BR-000002" \
  -d "{\"key\":\"LOCK.UNIFIED-$TS\",\"content\":\"统一锁档：file_token=$FT，固定目录FdoifaG8，身份user，跨窗口共享\"}" >/dev/null 2>&1
echo "统一锁档 $TS file_token=$FT"
