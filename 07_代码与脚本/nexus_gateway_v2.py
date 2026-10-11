#!/usr/bin/env python3
"""
ZONGYUAN-METAGATE（元闸）Gateway v2.0 — 多令牌白名单鉴权网关
仿真版本：用于本地仿真验证
架构：SDK ↔ Nexus:9443 ↔ 记忆网关:9120
设计公理：AAB双隔离（Authentication通道与Business通道隔离）
"""
import json, os, sys, time, hashlib, secrets, ssl, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

# ============================================================
# 配置（仿真环境）
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NEXUS_DIR = os.path.join(BASE_DIR, "..", "..", "..", "..") if "engine/nexus" in BASE_DIR else BASE_DIR
TOKEN_FILE = os.path.join(BASE_DIR, "tokens.json")
CERT_FILE = os.path.join(BASE_DIR, "..", "..", "..", "..", "certs", "nexus.crt")
KEY_FILE = os.path.join(BASE_DIR, "..", "..", "..", "..", "certs", "nexus.key")
CA_FILE = os.path.join(BASE_DIR, "..", "..", "..", "..", "certs", "nexus_ca.crt")
LOG_FILE = os.path.join(BASE_DIR, "..", "..", "..", "..", "logs", "nexus_gateway.log")
MEM_GATEWAY_URL = "http://127.0.0.1:9120"  # 记忆网关（仿真）
NEXUS_PORT = 9443
MTLS_ENABLED = True  # mTLS 双向认证：要求客户端证书且由私有CA签发

# 令牌权限级别
PERMISSIONS = ["read", "write", "admin", "memory_sync", "token_manage"]

# ============================================================
# 令牌存储（多令牌白名单模型）
# ============================================================
class TokenStore:
    def __init__(self, token_file):
        self.token_file = token_file
        self.tokens = {}
        self._load()

    def _load(self):
        if os.path.exists(self.token_file):
            with open(self.token_file, "r") as f:
                data = json.load(f)
                self.tokens = data.get("tokens", {})
        else:
            self.tokens = {}

    def _save(self):
        os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
        with open(self.token_file, "w") as f:
            json.dump({"tokens": self.tokens, "updated_at": datetime.now().isoformat()}, f, indent=2)
        os.chmod(self.token_file, 0o600)  # 令牌文件0600权限

    def issue(self, name, permissions=None, expires_in=86400, created_by="root"):
        """签发新令牌（仅显示一次）"""
        token = "zy-hap-" + secrets.token_hex(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        now = int(time.time())
        self.tokens[token_hash] = {
            "name": name,
            "permissions": permissions or ["read"],
            "created_at": now,
            "expires_at": now + expires_in,
            "created_by": created_by,
            "status": "active",
            "last_used": None,
            "use_count": 0
        }
        self._save()
        return token, token_hash

    def revoke(self, token_hash):
        """吊销令牌"""
        if token_hash in self.tokens:
            self.tokens[token_hash]["status"] = "revoked"
            self.tokens[token_hash]["revoked_at"] = int(time.time())
            self._save()
            return True
        return False

    def list_tokens(self):
        """列出所有令牌（不返回明文）"""
        return [{"token_hash": h, **{k:v for k,v in t.items() if k != "token"}}
                for h, t in self.tokens.items()]

    def verify_auth(self, token, required_permission=None):
        """
        verify_auth 鉴权流程
        返回: (success, token_hash, error_msg)
        """
        if not token:
            return False, None, "missing_token"
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        if token_hash not in self.tokens:
            return False, token_hash, "unknown_token"
        t = self.tokens[token_hash]
        if t["status"] != "active":
            return False, token_hash, "token_%s" % t["status"]
        if t["expires_at"] < int(time.time()):
            return False, token_hash, "token_expired"
        if required_permission and required_permission not in t["permissions"]:
            return False, token_hash, "permission_denied: need %s" % required_permission
        # 鉴权通过，更新使用记录
        t["last_used"] = int(time.time())
        t["use_count"] += 1
        self._save()
        return True, token_hash, None


# ============================================================
# 全局令牌存储实例
# ============================================================
token_store = TokenStore(TOKEN_FILE)


def log(level, msg):
    """安全日志（不记录令牌明文）"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = "[%s] [%s] %s" % (ts, level, msg)
    print(line)
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except:
        pass


# ============================================================
# HTTP请求处理器
# ============================================================
class NexusHandler(BaseHTTPRequestHandler):
    # 管理端点白名单（仅允许本地root访问）
    ADMIN_PATHS = ["/v1/tokens", "/v1/tokens/"]

    def log_message(self, format, *args):
        pass  # 禁用默认日志（安全：不记录请求详情）

    def _send_json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _get_token(self):
        """从请求头获取令牌（Authorization: Bearer <token> 或 X-Nexus-Token）"""
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return auth[7:]
        return self.headers.get("X-Nexus-Token", "")

    def _get_required_permission(self, path, method):
        """根据路径和方法动态判断所需权限（权限映射表）"""
        if method == "GET":
            return "read"
        # POST/PUT 权限映射
        if path.startswith("/v1/memory/sync"):
            return "memory_sync"
        return "write"

    def _is_admin_request(self):
        """判断是否为管理端点请求（AAB双隔离：管理通道独立）"""
        return any(self.path.startswith(p) for p in self.ADMIN_PATHS)

    def _verify_admin_access(self):
        """管理端点访问验证（仅root/本地+admin权限令牌）"""
        # 仿真环境：检查client_ip是否为127.0.0.1 + admin权限令牌
        client_ip = self.client_address[0]
        if client_ip not in ("127.0.0.1", "localhost"):
            return False, "admin_endpoint_local_only"
        token = self._get_token()
        ok, _, err = token_store.verify_auth(token, required_permission="admin")
        if not ok:
            return False, err or "admin_auth_failed"
        return True, None

    # ============================================================
    # GET 请求
    # ============================================================
    def do_GET(self):
        # 健康检查（无需鉴权）
        if self.path == "/health" or self.path == "/v1/health":
            self._send_json(200, {"status": "ok", "version": "2.0.0", "service": "zongyuan-metagate"})
            return

        # 管理端点：列出令牌
        if self.path.startswith("/v1/tokens"):
            ok, err = self._verify_admin_access()
            if not ok:
                log("WARN", "admin access denied: %s ip=%s" % (err, self.client_address[0]))
                self._send_json(403, {"error": err})
                return
            tokens = token_store.list_tokens()
            self._send_json(200, {"tokens": tokens, "count": len(tokens)})
            return

        # 业务端点：鉴权后代理到记忆网关（动态权限映射）
        token = self._get_token()
        required_perm = self._get_required_permission(self.path, "GET")
        ok, token_hash, err = token_store.verify_auth(token, required_permission=required_perm)
        if not ok:
            log("WARN", "auth failed: %s path=%s" % (err, self.path))
            self._send_json(401, {"error": err or "auth_failed"})
            return

        # 仿真：直接返回记忆网关响应（不实际代理）
        log("INFO", "auth ok token=%s path=%s" % (token_hash[:16], self.path))
        self._send_json(200, {
            "status": "ok",
            "service": "metagate-v2",
            "proxied_to": MEM_GATEWAY_URL,
            "path": self.path,
            "auth_token_hash": token_hash[:16] + "...",
            "timestamp": int(time.time())
        })

    # ============================================================
    # POST 请求
    # ============================================================
    def do_POST(self):
        # 管理端点：签发令牌
        if self.path == "/v1/tokens" or self.path == "/v1/tokens/":
            ok, err = self._verify_admin_access()
            if not ok:
                log("WARN", "admin token issue denied: %s" % err)
                self._send_json(403, {"error": err})
                return
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length)) if length > 0 else {}
            except:
                self._send_json(400, {"error": "invalid_json"})
                return
            name = body.get("name", "unnamed_token")
            perms = body.get("permissions", ["read"])
            expires_in = body.get("expires_in", 86400)
            token, token_hash = token_store.issue(name, perms, expires_in)
            log("INFO", "token issued: name=%s hash=%s perms=%s" % (name, token_hash[:16], perms))
            # 令牌仅显示一次
            self._send_json(201, {
                "token": token,
                "token_hash": token_hash,
                "name": name,
                "permissions": perms,
                "expires_in": expires_in,
                "warning": "此令牌仅显示一次，请立即保存"
            })
            return

        # 管理端点：吊销令牌
        if self.path.startswith("/v1/tokens/revoke"):
            ok, err = self._verify_admin_access()
            if not ok:
                self._send_json(403, {"error": err})
                return
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length)) if length > 0 else {}
            except:
                self._send_json(400, {"error": "invalid_json"})
                return
            token_hash = body.get("token_hash", "")
            ok = token_store.revoke(token_hash)
            self._send_json(200 if ok else 404, {"revoked": ok, "token_hash": token_hash})
            return

        # 业务端点：鉴权后处理（动态权限映射）
        token = self._get_token()
        required_perm = self._get_required_permission(self.path, "POST")
        ok, token_hash, err = token_store.verify_auth(token, required_permission=required_perm)
        if not ok:
            log("WARN", "auth failed: %s path=%s" % (err, self.path))
            self._send_json(401, {"error": err or "auth_failed"})
            return

        # 读取请求体（不记录到日志）
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length > 0 else b"{}"
        except:
            body = b"{}"

        log("INFO", "business request ok token=%s path=%s size=%d" % (token_hash[:16], self.path, len(body)))
        self._send_json(200, {
            "status": "ok",
            "service": "metagate-v2",
            "proxied_to": MEM_GATEWAY_URL,
            "path": self.path,
            "auth_token_hash": token_hash[:16] + "...",
            "request_size": len(body),
            "timestamp": int(time.time())
        })

    # ============================================================
    # DELETE 请求
    # ============================================================
    def do_DELETE(self):
        # 管理端点：吊销令牌（RESTful风格）
        if self.path.startswith("/v1/tokens/"):
            ok, err = self._verify_admin_access()
            if not ok:
                self._send_json(403, {"error": err})
                return
            token_hash = self.path.split("/")[-1]
            ok = token_store.revoke(token_hash)
            self._send_json(200 if ok else 404, {"revoked": ok, "token_hash": token_hash})
            return
        self._send_json(405, {"error": "method_not_allowed"})


# ============================================================
# 主入口
# ============================================================
def main():
    import argparse
    parser = argparse.ArgumentParser(description="ZONGYUAN-METAGATE（元闸）Gateway v2.0")
    parser.add_argument("--port", type=int, default=NEXUS_PORT)
    parser.add_argument("--no-ssl", action="store_true", help="禁用SSL（仅仿真用）")
    parser.add_argument("--init-admin", action="store_true", help="初始化admin令牌")
    args = parser.parse_args()

    print("=" * 60)
    print("  ZONGYUAN-METAGATE（元闸）Gateway v2.0 启动")
    print("  多令牌白名单鉴权 | AAB双隔离")
    print("=" * 60)

    # 初始化admin令牌（首次启动）
    if args.init_admin or len(token_store.tokens) == 0:
        print("\n[初始化] 签发admin令牌...")
        token, token_hash = token_store.issue("admin_initial", ["admin", "read", "write", "memory_sync", "token_manage"], expires_in=31536000)
        print("  admin令牌: %s" % token)
        print("  token_hash: %s" % token_hash)
        print("  ⚠️ 此令牌仅显示一次，请立即保存！\n")

    # 启动HTTP服务
    server = HTTPServer(("0.0.0.0", args.port), NexusHandler)

    if not args.no_ssl:
        cert_path = os.path.abspath(CERT_FILE)
        key_path = os.path.abspath(KEY_FILE)
        ca_path = os.path.abspath(CA_FILE)
        if os.path.exists(cert_path) and os.path.exists(key_path):
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ctx.load_cert_chain(cert_path, key_path)
            if MTLS_ENABLED and os.path.exists(ca_path):
                ctx.verify_mode = ssl.CERT_REQUIRED
                ctx.load_verify_locations(ca_path)
                server.socket = ctx.wrap_socket(server.socket, server_side=True)
                print("  SSL: 已启用 (mTLS双向认证, cert=%s, CA=%s)" % (cert_path, ca_path))
            else:
                server.socket = ctx.wrap_socket(server.socket, server_side=True)
                print("  SSL: 已启用 (单向TLS, cert=%s)" % cert_path)
        else:
            print("  ⚠️ 证书文件不存在，降级为HTTP（仅仿真）")

    print("  监听端口: %d" % args.port)
    print("  令牌文件: %s (0600)" % TOKEN_FILE)
    print("  管理端点: /v1/tokens (仅本地+admin权限)")
    print("  健康检查: /health")
    print("=" * 60)
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[停止] Nexus Gateway v2.0 已停止")
        server.server_close()


if __name__ == "__main__":
    main()
