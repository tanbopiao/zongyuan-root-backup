#!/bin/bash
source /home/user/ZONGYUAN-ROOT/04_系统配置/凭证/active_token.env 2>/dev/null || export ZR_TOKEN=""
# 通道健康检查（P1）
TOKEN=""
API="https://www.huodouai.com/api/gateway"
echo "=== 主通道健康检查 drama:9120 ==="
echo "① 门户: $(curl -s -o /dev/null -w '%{http_code}' -m 6 http://www.huodouai.com:9120/)"
echo "② 健康: $(curl -s -m 6 $API/../health 2>/dev/null | head -c 80)"
echo "③ 鉴权: $(curl -s -m 6 -H "X-Capture-Token: $TOKEN" "$API/truths?level=public" 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'ok count={d.get(\"count\")}')" 2>/dev/null || echo FAIL)"
echo "④ 写入: $(curl -s -m 6 -X POST $API/report -H "X-Capture-Token: $TOKEN" -H "Content-Type: application/json" -d '{"node_id":"NN-META-024","DID":"DID-BR-000002","ROOT_OMEGA":"Ω-TAN-7-001","truth_type":"operation_log","truth_content":"通道健康检查P1执行"}' 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print('ok' if d.get('success') else 'FAIL')" 2>/dev/null || echo FAIL)"
echo "=== 旧通道状态（应废弃） ==="
echo "旧8070: $(curl -s -o /dev/null -w '%{http_code}' -m 5 https://www.huodouai.com/api/v1/truths/sync/status 2>/dev/null)"
