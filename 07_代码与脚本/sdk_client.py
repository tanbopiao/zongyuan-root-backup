#!/usr/bin/env python3
"""
ZONGYUAN-METAGATE（元闸）SDK Client v2.0（HAP-V1.0）
用于与Nexus网关通信的SDK客户端（仿真验证用）
支持：多令牌鉴权、健康检查、业务调用、令牌管理（admin）
"""
import json, ssl, urllib.request, urllib.error


class NexusSDK:
    def __init__(self, base_url="https://127.0.0.1:9443", token=None, verify_ssl=False,
                 client_cert=None, client_key=None, ca_cert=None):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.verify_ssl = verify_ssl
        self.ctx = ssl.create_default_context()
        if ca_cert:
            self.ctx.load_verify_locations(ca_cert)
        if client_cert and client_key:
            self.ctx.load_cert_chain(client_cert, client_key)
        if not verify_ssl:
            self.ctx.check_hostname = False
            self.ctx.verify_mode = ssl.CERT_NONE

    def _request(self, method, path, body=None, admin=False):
        url = self.base_url + path
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, method=method, data=data, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10, context=self.ctx) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            try:
                return e.code, json.loads(e.read())
            except:
                return e.code, {"error": str(e)}
        except Exception as e:
            return 0, {"error": str(e)}

    # 健康检查（无需鉴权）
    def health(self):
        return self._request("GET", "/health")

    # 业务调用（需read/write权限）
    def call(self, path, body=None, method="POST"):
        return self._request(method, path, body)

    # 记忆同步（需memory_sync权限）
    def sync_memory(self, memory_data):
        return self._request("POST", "/v1/memory/sync", memory_data)

    # ===== 管理端点（需admin权限，仅本地） =====
    def list_tokens(self):
        return self._request("GET", "/v1/tokens")

    def issue_token(self, name, permissions=None, expires_in=86400):
        return self._request("POST", "/v1/tokens", {
            "name": name,
            "permissions": permissions or ["read"],
            "expires_in": expires_in
        })

    def revoke_token(self, token_hash):
        return self._request("POST", "/v1/tokens/revoke", {"token_hash": token_hash})


# ============================================================
# 命令行测试入口
# ============================================================
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python sdk_client.py <token> [health|call|list_tokens]")
        sys.exit(1)
    token = sys.argv[1]
    cmd = sys.argv[2] if len(sys.argv) > 2 else "health"
    sdk = NexusSDK(token=token)
    if cmd == "health":
        code, data = sdk.health()
        print("HTTP %d: %s" % (code, json.dumps(data, ensure_ascii=False, indent=2)))
    elif cmd == "call":
        code, data = sdk.call("/v1/test", {"test": "data"})
        print("HTTP %d: %s" % (code, json.dumps(data, ensure_ascii=False, indent=2)))
    elif cmd == "list_tokens":
        code, data = sdk.list_tokens()
        print("HTTP %d: %s" % (code, json.dumps(data, ensure_ascii=False, indent=2)))
