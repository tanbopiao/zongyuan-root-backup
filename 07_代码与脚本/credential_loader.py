#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZONGYUAN-ROOT 统一凭证加载器
确权：DID-BR-000002 | 溯源：Ω₀⊂⊙∞⊂Ω
功能：自动识别加密(.enc)/明文(.env)格式，解密后仅返回内存字符串，不落临时文件
用法：
    from credential_loader import get_cred, load_env_file
    token = get_cred("ZR_TOKEN")           # 从active_token.env获取
    intern_key = get_cred("INTERN_API_KEY", file="intern_api_token.env")
    env_dict = load_env_file("ntfy_token.env")  # 返回全部键值对
环境变量：ZR_MASTER_KEY（主密码，定时任务env注入，不落盘）
"""

import os
import sys
import subprocess
from pathlib import Path

CRED_DIR = Path("/home/user/ZONGYUAN-ROOT/04_系统配置/凭证")
DEFAULT_FILE = "active_token.env"


def _master_key_file():
    """动态计算主密码文件路径（跟随CRED_DIR变化）"""
    return CRED_DIR / ".master_key"


def _get_master_key():
    """从环境变量获取主密码，不存在则从安全文件读取"""
    env_key = os.environ.get("ZR_MASTER_KEY", "").strip()
    if env_key:
        return env_key
    mkf = _master_key_file()
    if mkf.exists():
        try:
            return mkf.read_text(encoding="utf-8").strip()
        except Exception:
            pass
    return ""


def _decrypt_enc(enc_path, master_key=None):
    """解密.enc文件，返回明文内容字符串"""
    if master_key is None:
        master_key = _get_master_key()
    if not master_key:
        raise RuntimeError("ZR_MASTER_KEY未设置，无法解密凭证")
    result = subprocess.run(
        ["openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2",
         "-in", str(enc_path), "-pass", f"pass:{master_key}"],
        capture_output=True, timeout=10
    )
    if result.returncode != 0:
        err = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"解密失败: {err}")
    return result.stdout.decode("utf-8", errors="replace")


def load_env_file(filename=DEFAULT_FILE):
    """
    加载.env文件，自动识别加密(.enc)/明文(.env)格式
    返回dict: {key: value}
    """
    enc_path = CRED_DIR / f"{filename}.enc"
    plain_path = CRED_DIR / filename

    content = None
    if enc_path.exists():
        try:
            content = _decrypt_enc(enc_path)
        except RuntimeError as e:
            # 加密解密失败，尝试明文兜底
            if plain_path.exists():
                content = plain_path.read_text(encoding="utf-8")
            else:
                raise
    elif plain_path.exists():
        content = plain_path.read_text(encoding="utf-8")
    else:
        raise FileNotFoundError(f"凭证文件不存在: {filename}")

    # 解析env格式
    env = {}
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            env[key] = value
    return env


def get_cred(key, filename=DEFAULT_FILE):
    """
    获取单个凭证值
    key: 凭证键名（如 ZR_TOKEN, INTERN_API_KEY, NTFY_TOKEN）
    filename: 凭证文件名（默认 active_token.env）
    """
    env = load_env_file(filename)
    if key not in env:
        raise KeyError(f"凭证键不存在: {key} (文件: {filename}, 可用键: {list(env.keys())})")
    return env[key]


def list_creds(filename=DEFAULT_FILE):
    """列出凭证文件中的所有键名（不返回值）"""
    env = load_env_file(filename)
    return list(env.keys())


def encrypt_plaintext(filename, master_key=None):
    """将明文.env加密为.enc（用于新增凭证后加密）"""
    if master_key is None:
        master_key = _get_master_key()
    if not master_key:
        raise RuntimeError("ZR_MASTER_KEY未设置")
    plain_path = CRED_DIR / filename
    enc_path = CRED_DIR / f"{filename}.enc"
    if not plain_path.exists():
        raise FileNotFoundError(f"明文文件不存在: {filename}")
    subprocess.run(
        ["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-salt",
         "-in", str(plain_path), "-out", str(enc_path),
         "-pass", f"pass:{master_key}"],
        check=True, timeout=10
    )
    os.chmod(enc_path, 0o600)
    return enc_path


# ============ CLI入口 ============
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 credential_loader.py <命令> [参数]")
        print("  list [文件]          列出凭证键名")
        print("  get <键> [文件]      获取凭证值")
        print("  encrypt <文件>       加密明文文件")
        print("  check                检查凭证加密状态")
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd == "list":
        fname = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_FILE
        keys = list_creds(fname)
        print(f"凭证文件: {fname}")
        print(f"键名({len(keys)}): {keys}")
    elif cmd == "get":
        key = sys.argv[2]
        fname = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_FILE
        val = get_cred(key, fname)
        print(f"{key} = {val[:8]}...{val[-4:] if len(val)>12 else ''}")
    elif cmd == "encrypt":
        fname = sys.argv[2]
        path = encrypt_plaintext(fname)
        print(f"✅ 已加密: {path}")
    elif cmd == "check":
        print("=== 凭证加密状态检查 ===")
        for f in ["active_token.env", "intern_api_token.env", "ntfy_token.env"]:
            enc = (CRED_DIR / f"{f}.enc").exists()
            plain = (CRED_DIR / f).exists()
            status = "✅已加密" if enc else "❌未加密"
            plain_status = "明文仍在" if plain else "明文已删"
            print(f"  {f}: {status} | {plain_status}")
        mk = _get_master_key()
        print(f"\nZR_MASTER_KEY: {'✅已设置' if mk else '❌未设置(需export ZR_MASTER_KEY=xxx)'}")
    else:
        print(f"未知命令: {cmd}")
