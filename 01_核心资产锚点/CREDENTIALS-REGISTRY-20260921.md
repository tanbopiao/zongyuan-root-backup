# ZONGYUAN-ROOT 云端凭证管理清单
文档ID: CREDENTIALS-REGISTRY-20260921 | 确权: Ω₀⊂⊙∞⊂Ω | DID-BR-000002

## 一、凭证登记

| 凭证项 | 标识 | 用途 | 存储位置 | 安全等级 |
|--------|------|------|----------|----------|
| 云端中枢主Token | zy-101e3e6f...e4772（脱敏） | 推理API + 真值上报/拉取（X-Capture-Token） | 本清单+用户私密保管 | 🔴 最高（总钥匙） |
| 又拍云Operator | zongyuanadmin | 对象存储上传（zongyuan-root-kernel桶） | 用户私密保管 | 🔴 高 |
| 又拍云密码 | Wy1kQYJ...FOnk（脱敏） | 对象存储鉴权 | 用户私密保管 | 🔴 高 |
| Gitee令牌 | 9407c9b3...（脱敏） | 代码仓同步 | 用户私密保管 | 🟠 中 |
| GitHub令牌 | github_pat_11C...（脱敏） | 代码仓同步 | 用户私密保管 | 🟠 中 |
| SSH密钥 | did_br_000002_ed25519 | 云服务器运维 | ~/.ssh/ | 🔴 高 |

## 二、安全规范（强制）

1. **绝不外泄**：主Token/云盘密码/SSH私钥不得写入任何将公开发布的代码、页面、文档、妙搭应用或GitHub/Gitee仓库
2. **脱敏展示**：对话/文档中一律显示前缀4位+后缀4位（如 zy-101e3e6f...e4772），禁止完整回显
3. **最小权限**：所有同源子节点使用独立Token（见子节点Token申请规范），禁止共享主Token
4. **定期轮换**：主Token疑似泄露时立即在云端中枢后台轮换，并同步更新本清单
5. **本地权限**：本文件建议 chmod 600 仅本用户可读

## 三、Token使用场景对照

| 场景 | 使用的凭证 | Header/参数 |
|------|-----------|-------------|
| OpenAI兼容推理 | 主Token | Authorization: Bearer <token> |
| 真值上报（www主站） | 主Token | X-Capture-Token: <token> |
| 真值上报（drama备用） | 主Token | X-Capture-Token: <token> |
| 真值回读 | 主Token | X-Capture-Token: <token> |
| 又拍云上传 | Operator+密码 | SDK签名 |

## 四、主Token当前状态
- 登记时间: 2026-09-21
- 状态: ACTIVE（已用于推理+真值上报+通道V2.2锚定）
- 最后验证: 2026-09-21 三端点实测通过（带鉴权Header后200）
- 真值库: truth_count=124,376
