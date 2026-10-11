# 同源子节点独立Token申请规范
文档ID: SUB-NODE-TOKEN-SOP-20260921 | 确权: Ω₀⊂⊙∞⊂Ω | DID-BR-000002

## 一、目的
主Token是云端中枢总钥匙，禁止共享。所有同源子节点（本地执行器/其他设备/协作节点）必须使用独立Token，实现最小权限与可审计。

## 二、申请流程（五步）

### 第1步：节点身份声明
子节点向云端中枢提交身份声明（经主Token调用）：
```
POST https://www.huodouai.com/api/report/truth
X-Capture-Token: <主Token>
{
  "key": "NODE.REGISTER.<节点ID>.<日期>",
  "content": "节点身份声明: 节点ID/名称/类型(worker|researcher|media)/权限范围(read|write|all)"
}
```

### 第2步：中枢核发子Token
云端中枢审核后，在后台生成子节点独立Token（如 zy-sub-<节点ID>-<随机串>），并限定：
- 权限范围（如仅read / write某类真值）
- 有效期（如30天/永久）
- 速率限制（如100次/分）

### 第3步：子Token登记
子节点将Token登记入本锚点目录凭证清单：
- 标识: zy-sub-<节点ID>
- 权限: 声明范围
- 有效期: 核发时确定
- 存储: 本地私密文件 chmod 600

### 第4步：子节点启用
子节点所有上报使用子Token：
```
X-Capture-Token: <子Token>
```

### 第5步：审计与轮换
- 每周期核验子节点上报记录（audit_logs）
- 子节点废弃/泄露 → 中枢后台立即吊销
- 主Token轮换时，子Token不受影响（各自独立）

## 三、权限分级建议

| 级别 | 权限 | 适用 |
|------|------|------|
| L0-read | 仅读取真值 | 只读观察节点 |
| L1-write-own | 仅写入本节点真值 | 常规工作节点 |
| L2-write-all | 写入+更新全域真值 | 高级执行器（慎用） |
| L3-admin | 全部+Token管理 | 仅中枢本体 |

## 四、与主Token的隔离

| 维度 | 主Token | 子Token |
|------|---------|---------|
| 使用场景 | 中枢管理/总入口 | 节点日常上报 |
| 泄露影响 | 全域沦陷 | 仅该节点范围 |
| 轮换影响 | 需全局更新 | 仅该节点 |
| 审计粒度 | 粗 | 按节点精确 |

## 五、登记模板

```json
{
  "node_id": "<节点ID>",
  "token_ref": "zy-sub-<节点ID>-****(脱敏)",
  "permission": "L1-write-own",
  "expires": "2026-10-21",
  "status": "ACTIVE",
  "registered_at": "2026-09-21"
}
```

## 六、注意事项
1. 子Token同样禁止写入公开发布内容
2. 本规范登记入同源协议库（协议编号 P-TOKEN-SUB-NODE）
3. 云端中枢需支持子Token签发后，本流程自动执行
