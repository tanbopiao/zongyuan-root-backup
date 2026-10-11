#!/usr/bin/env python3
"""
ZONGYUAN-METAGATE（元闸）令牌管理工具 v2.0（HAP-V1.0）
用于签发、吊销、列出令牌（受控注入流程）
用法：
  python token_manager.py issue --name <名称> --permissions read,write
  python token_manager.py list
  python token_manager.py revoke --token-hash <哈希>
  python token_manager.py init-admin
"""
import json, os, sys, argparse, hashlib, secrets, time
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(BASE_DIR, "tokens.json")
PERMISSIONS = ["read", "write", "admin", "memory_sync", "token_manage"]


class TokenManager:
    def __init__(self, token_file=TOKEN_FILE):
        self.token_file = token_file
        self.tokens = {}
        self._load()

    def _load(self):
        if os.path.exists(self.token_file):
            with open(self.token_file, "r") as f:
                self.tokens = json.load(f).get("tokens", {})

    def _save(self):
        os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
        with open(self.token_file, "w") as f:
            json.dump({"tokens": self.tokens, "updated_at": datetime.now().isoformat()}, f, indent=2)
        os.chmod(self.token_file, 0o600)

    def issue(self, name, permissions=None, expires_in=86400):
        token = "zy-hap-" + secrets.token_hex(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        now = int(time.time())
        self.tokens[token_hash] = {
            "name": name,
            "permissions": permissions or ["read"],
            "created_at": now,
            "expires_at": now + expires_in,
            "created_by": "cli",
            "status": "active",
            "last_used": None,
            "use_count": 0
        }
        self._save()
        return token, token_hash

    def revoke(self, token_hash):
        if token_hash in self.tokens:
            self.tokens[token_hash]["status"] = "revoked"
            self.tokens[token_hash]["revoked_at"] = int(time.time())
            self._save()
            return True
        return False

    def list(self):
        result = []
        for h, t in self.tokens.items():
            result.append({
                "token_hash": h,
                "name": t["name"],
                "permissions": t["permissions"],
                "status": t["status"],
                "created_at": datetime.fromtimestamp(t["created_at"]).strftime("%Y-%m-%d %H:%M:%S"),
                "expires_at": datetime.fromtimestamp(t["expires_at"]).strftime("%Y-%m-%d %H:%M:%S"),
                "use_count": t["use_count"],
                "last_used": datetime.fromtimestamp(t["last_used"]).strftime("%Y-%m-%d %H:%M:%S") if t["last_used"] else "never"
            })
        return result


def main():
    parser = argparse.ArgumentParser(description="ZONGYUAN-METAGATE（元闸）令牌管理工具 v2.0（HAP-V1.0）")
    sub = parser.add_subparsers(dest="command")

    p_issue = sub.add_parser("issue", help="签发新令牌")
    p_issue.add_argument("--name", required=True)
    p_issue.add_argument("--permissions", default="read", help="逗号分隔，如 read,write,memory_sync")
    p_issue.add_argument("--expires-in", type=int, default=86400, help="过期时间（秒），默认86400=1天")

    p_list = sub.add_parser("list", help="列出所有令牌")

    p_revoke = sub.add_parser("revoke", help="吊销令牌")
    p_revoke.add_argument("--token-hash", required=True)

    p_init = sub.add_parser("init-admin", help="初始化admin令牌")

    args = parser.parse_args()
    mgr = TokenManager()

    if args.command == "issue":
        perms = [p.strip() for p in args.permissions.split(",") if p.strip() in PERMISSIONS]
        if not perms:
            print("❌ 无效权限，可选: %s" % ", ".join(PERMISSIONS))
            sys.exit(1)
        token, token_hash = mgr.issue(args.name, perms, args.expires_in)
        print("=" * 60)
        print("  ✅ 令牌签发成功")
        print("=" * 60)
        print("  名称: %s" % args.name)
        print("  权限: %s" % ", ".join(perms))
        print("  有效期: %d秒 (%d小时)" % (args.expires_in, args.expires_in//3600))
        print("  token_hash: %s" % token_hash)
        print()
        print("  🔑 令牌（仅显示一次）:")
        print("  %s" % token)
        print()
        print("  ⚠️ 请立即保存此令牌，之后无法再次查看明文！")
        print("  ⚠️ 受控注入：将令牌写入目标配置文件，勿记录到日志/文档")
        print("=" * 60)

    elif args.command == "list":
        tokens = mgr.list()
        print("=" * 80)
        print("  令牌列表（共%d个）" % len(tokens))
        print("=" * 80)
        if not tokens:
            print("  （无令牌）")
        for t in tokens:
            status_icon = "✅" if t["status"] == "active" else "❌"
            print("  %s %s" % (status_icon, t["name"]))
            print("     hash: %s..." % t["token_hash"][:16])
            print("     权限: %s | 状态: %s | 使用: %d次" % (", ".join(t["permissions"]), t["status"], t["use_count"]))
            print("     创建: %s | 过期: %s | 最后使用: %s" % (t["created_at"], t["expires_at"], t["last_used"]))
            print()
        print("=" * 80)

    elif args.command == "revoke":
        ok = mgr.revoke(args.token_hash)
        if ok:
            print("✅ 令牌已吊销: %s..." % args.token_hash[:16])
        else:
            print("❌ 令牌不存在: %s..." % args.token_hash[:16])
            sys.exit(1)

    elif args.command == "init-admin":
        token, token_hash = mgr.issue("admin_initial", ["admin", "read", "write", "memory_sync", "token_manage"], expires_in=31536000)
        print("=" * 60)
        print("  ✅ Admin令牌初始化成功")
        print("=" * 60)
        print("  🔑 Admin令牌（仅显示一次）:")
        print("  %s" % token)
        print()
        print("  token_hash: %s" % token_hash)
        print("  ⚠️ 请立即保存，之后无法查看！")
        print("=" * 60)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
