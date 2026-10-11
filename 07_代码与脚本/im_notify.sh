#!/bin/bash
# ZONGYUAN-ROOT 机制结果IM推送器 v1.0
# 用法: bash im_push/im_notify.sh "<markdown内容>"
# 将机制结果主动推送到用户飞书
MARKDOWN="${1:-机制完成}"
USER_ID="ou_41b49aeaa69bca84bc65780805e65664"
lark-cli im +messages-send --user-id "$USER_ID" --markdown "$MARKDOWN" --as user 2>&1 | grep -o '"ok": [a-z]*' | head -1
