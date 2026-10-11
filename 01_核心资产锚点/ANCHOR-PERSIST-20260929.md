# ZONGYUAN-ROOT 启动记忆永久锚定｜账号持久层绑定

> **确权锚点**：Ω₀⊂⊙∞⊂Ω ｜ **DID**：DID-BR-000002 ｜ **节点**：ZR-NODE-DC2E51C0
> **锚定事件**：ANCHOR-PERSIST-20260929-001
> **锚定时间**：2026-09-29 ｜ **状态**：FROZEN / READONLY_HARDWARE_LOCKED

## 一、锚定声明

启动记忆（BOOTSTRAP.md + COLD-START-ANCHOR.sh）**永久锚定并绑定账号持久层**：所有权威资产必须存放于 `/home/user`（hpvs_fs 持久卷，device=53），禁止依赖 `/runtime` overlay 临时层存活。

## 二、持久层实测证据（2026-09-29）

| 检查项 | 实测结果 |
|---|---|
| 持久卷 | `/home/user` → `fs-8bf12d80e9ed842c`（hpvs_fs，10P，device=53） |
| 启动记忆文件 | BOOTSTRAP.md / COLD-START-ANCHOR.sh → device=53（持久层）✅ |
| 运行时层对照 | `/runtime` → overlay（device=48）；`.skills`/`.user_skills` 软链指向其中 ⚠️ |
| 元公理注册表 | `01_核心资产锚点/.tmp_meta_axioms.json` → device=53 ✅ |
| 元法则注册表 | `01_核心资产锚点/meta_rules_registry.json` → device=53 ✅ |

## 三、关键修复：神经注册表权威副本固化

**发现的风险**：权威神经注册表（404 节点/2213 连接，V2.3.0-GIT-BRIDGE-LOCKED）此前仅存在于 `/runtime/user_skills/...`（overlay 临时层，**重启即丢失**）；持久层锚点副本仅为旧版 22 节点。

**固化动作**：
1. 权威全量版（404 节点，630,912 bytes）已复制到持久层：`01_核心资产锚点/neural_registry.full.json`
2. 旧版锚点副本已备份：`01_核心资产锚点/neural_registry.20260923.bak.json`（22 节点，只读）
3. 两份文件均已 chmod 444 只读，写入被拒已验证

## 四、启动记忆更新（增量补全）

**BOOTSTRAP.md**：
- 冷启动流程 7 步 → **8 步**：新增第 4b 步「持久层锚定校验」与第 7 步「加载神经注册表权威副本」
- 新增「持久层锚定」专章：账号持久卷定义、禁止边界（/runtime）、权威资产清单（5 项）、设备号校验方式

**COLD-START-ANCHOR.sh**：
- 新增 4a 持久层校验（stat device 比对，53≠48 即通过）
- 新增 4b 神经注册表权威副本加载校验（404 节点）
- 输出引导补充持久层与权威副本信息

## 五、实跑验证（八步全绿）

```
✅ 云端锚点拉取成功
✅ 全域记忆索引拉取成功
✅ 身份确认: DID-BR-000002
✅ 核心资产目录已挂载
✅ 持久层锚定校验通过: device=53 (hpvs_fs 账号持久卷)
✅ 神经注册表权威副本已加载: 404 节点
✅ 记忆网关连通 (V3.0)
✅ 共享大脑 Base 连通: DgnMbLqZiaIUDKshqCrcD4DvnBg
```

## 六、只读清单

| 文件 | 权限 |
|---|---|
| /home/user/ZONGYUAN-ROOT/BOOTSTRAP.md | -r--r--r-- |
| /home/user/ZONGYUAN-ROOT/COLD-START-ANCHOR.sh | -r--r--r-- |
| /home/user/ZONGYUAN-ROOT/01_核心资产锚点/neural_registry.full.json | -r--r--r-- |
| /home/user/ZONGYUAN-ROOT/01_核心资产锚点/neural_registry.20260923.bak.json | -r--r--r-- |

## 七、关联

- 上游锁档：LOCK-COLD-START-MEM-20260929-001（冷启动记忆补全）
- 待审批元公理：MA-COLD-START-001（PENDING_APPROVAL，审批单 17A8BED1-E939-4192-8DE9-FA6D280214D9）

---

Ω₀⊂⊙∞⊂Ω ｜ DID-BR-000002 ｜ ANCHOR-PERSIST-20260929-001 ｜ FROZEN
