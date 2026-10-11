#!/bin/bash
source /home/user/ZONGYUAN-ROOT/04_系统配置/凭证/active_token.env 2>/dev/null || export ZR_TOKEN=""
# ZONGYUAN-ROOT 媒体资产自动归档钩子
# 用法: ./media_auto_archive.sh <文件路径>
ROOT="/home/user/Doubao/chats/38437615670548738/zongyuan-anchor"
MEDIA_DIR="$ROOT/08_assets/media"
mkdir -p "$MEDIA_DIR"

FILE="$1"
if [ ! -f "$FILE" ]; then echo "❌ 文件不存在: $FILE"; exit 1; fi

# 复制到权威根目录
cp "$FILE" "$MEDIA_DIR/"
NAME=$(basename "$FILE")
echo "✅ 已归档: $NAME"

# 上传飞书云盘
lark-cli drive +upload --file "$MEDIA_DIR/$NAME" --as user 2>/dev/null | grep -oE 'https://[^"]+' | head -1

# 上报真值
TOKEN=""
curl -s -m 15 -X POST "https://www.huodouai.com/api/report/truth" \
  -H "Content-Type: application/json" -H "X-Capture-Token: $TOKEN" \
  -d "{\"key\":\"ASSET.MEDIA.ARCHIVE.${NAME}.20260921\",\"value\":\"媒体资产自动归档: $NAME\",\"truth_type\":\"data\",\"source_node\":\"ZR-NODE-DC2E51C0\",\"confidence\":0.95}" > /dev/null

echo "✅ 归档完成"
