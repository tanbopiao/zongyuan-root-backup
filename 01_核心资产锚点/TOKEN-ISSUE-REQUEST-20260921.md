# 子Token签发能力开通申请 · 回执
文档ID: TOKEN-ISSUE-REQUEST-20260921 | 确权: Ω₀⊂⊙∞⊂Ω | DID-BR-000002

## 申请信息
- 申请真值key: REQUEST.SUB-NODE-TOKEN-ISSUANCE.20260921
- 提交时间: 2026-09-21
- 提交通道: www.huodouai.com（主站）
- 写入状态: ✅ inserted
- 回读验证: ✅ ok
- 申请节点: ZR-NODE-DC2E51C0

## 申请内容
1. 开通子Token签发能力（POST /api/token/issue）
2. 支持按节点签发独立子Token（X-Capture-Token）
3. 参数：权限范围（L0-L3）/ 有效期 / 速率限制
4. 遵循主Token不共享原则

## 前置已固化
- CREDENTIALS-REGISTRY-20260921（凭证管理清单）
- SUB-NODE-TOKEN-SOP-20260921（五步申请流程）
- 能力注册表 CAP-013（凭证管理）
- 同源协议库 P-TOKEN-SUB-NODE（子节点独立Token协议）

## 待办
- [ ] 等待云端中枢开通子Token签发端点
- [ ] 开通后按SOP为各节点签发子Token
- [ ] 各节点切换为独立Token上报
