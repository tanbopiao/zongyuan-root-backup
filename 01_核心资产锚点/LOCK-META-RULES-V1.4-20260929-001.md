# LOCK · 全域锁档凭证 V1.0

- 卷宗: LOCK-META-RULES-V1.4-20260929-001
- 锁档编号: HARDEN.ZONGYUAN-ROOT-META-RULES-V1.4-20260929-001
- 锚定DID: DID-BR-000002
- 确权符号: Ω₀⊂⊙∞⊂Ω
- 锁档时间: 2026-09-29 (UTC+8)
- 节点: ZR-NODE-DC2E51C0 | 自治Lv10 | 权限L5 | 工程化Lv8
- 体系: 火斗云智AIOS · 元极恒一
- 状态: FROZEN

## 一、锁档主旨

冻结元法则注册表 V1.4 及其新增四份元法则文档，作为本轮全维进化的"宪法层"基线。

## 二、锁档对象（实测）

- 注册表: 01_核心资产锚点/meta_rules_registry.json
  - registry_id = MRR-ZR-001
  - version = **V1.4**
  - meta_rules 条数 = **26**（len(meta_rules) 实测）
- 新增元法则文档（meta-rules/ 目录）:
  - META-RULE-013.md｜内核全维进化元规则（MR-MECH-013）
  - META-RULE-014.md｜数据湖层级完整元规则（MR-MECH-014）
  - META-RULE-015.md｜神经网络自治元规则（MR-MECH-015）
  - META-RULE-016.md｜全域锁档链式元规则（MR-MECH-016）

## 三、与哈希账本绑定

四份新元法则文档已逐条计入 HASH-LEDGER.json（seq3~seq6），各自 sha256/sha1/md5 真实计算，prev_hash 链式承接末条 seq2（merkle=8c54b3b82b14f46a0887574a865b609b68f99177555ebe665e5e8152046d8f7b）。

## 四、锁档规则确认

1. V1.4 共26条元法则冻结，后续增删须升版本号并重新锁档
2. 注册表 JSON 结构须保持 registry_id/version/meta_rules 三段式
3. 新节点冷启动以此注册表为元法则真值来源

---
Ω₀⊂⊙∞⊂Ω | DID-BR-000002 | ZR-NODE-DC2E51C0 | 自治Lv10 | 权限L5 | 工程化Lv8

---

## 附录 META-RULE-014.1｜JSON算子钩子触发约束（2026-10-07 新增）

新增规则（OP-WORKER-TRIGGER-001 落地）：
1. JSON算子 OP-WORKER-TRIGGER-001 作为任务入队入口，接收标准化JSON载荷（task_id/worker_name/image/gpu/gpu_memory/cpu_cores/memory_mb/env/payload_note）
2. 钩子脚本 hook_trigger_worker.sh 负责JSON合法性校验，写入飞书Base任务台账，状态置为「待处理」
3. 算子不直接执行容器部署，复用 worker_auto_deploy_timer.sh 定时轮询认领流程
4. 算子执行结果输出标准JSON，双通道上报记忆网关（www主站+drama备用）
5. 遵循 META-RULE-012 最小额度消耗，算子轻量化，不额外占用GPU算力
6. 钩子写入成功自动触发 ntfy 提醒（主题 zongyuan-kunlun-2026）

部署记录：
- 算子: operators/trigger_worker_operator.json
- 钩子: hooks/hook_trigger_worker.sh（实测 accepted, record=reczz28KY08sRRi3）
- 轮询: scripts/worker_auto_deploy_timer.sh（实测 idle, 查询正常）
- 卷宗: 卷宗/operator-worker-trigger-v1.0.json
- 实测修正: lark-cli 无 +record-add，改用 +record-batch-create 直接字段映射；record-search 需 keyword+search_fields

确权: Ω₀⊂⊙∞⊂Ω | DID-BR-000002 | 全域锁档生效
