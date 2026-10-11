# 同源协议激活·自动探索环境上报机制 V1.0 ｜ ZONGYUAN-ROOT

归档节点：ZONGYUAN-ROOT｜DID-BR-000002｜Ω₀⊂⊙∞⊂Ω
版本：V1.0-HOMOLOGY-EXPLORE｜2026-09-16
公理锚点：AXIOM-A-035_V1.7｜HAP-V1.0

---

## 一、机制定位

在同源协议（HAP-V1.0）框架下，**激活时自动探索环境并上报**：
- 每次激活确认"我是谁"（同源身份校验）
- 自动探索"环境如何"（云端/能力/资源/资产/神经六维）
- 环境快照上报云端记忆网关，形成环境感知基线
- 判定同源激活状态（HOMOLOGY_ACTIVE / ENV_DEGRADED）

---

## 二、探索六维（EXPLORE-6）

```
E1 同源身份 → E2 云端拓扑 → E3 本地能力
                    ↓
E6 神经内核 ← E5 资产完整 ← E4 资源水位
```

| 维度 | 内容 | 首轮实测 |
|---|---|---|
| E1 同源身份 | 注册/权限等级/状态 | L4/ACTIVE ✅ |
| E2 云端拓扑 | truths/upsert/单条/upload | 200/200/200/502 |
| E3 本地能力 | python3/lark-cli/curl/jq | 全 OK ✅ |
| E4 资源水位 | 磁盘/内存 | 1% / 3456MB ✅ |
| E5 资产完整 | 9 项关键资产 | 0 缺失 ✅ |
| E6 神经内核 | 节点/连接/注册表 | 317 节点/1912 连接 |

---

## 三、执行链路

```
同源协议守卫校验(HAP三重校验)
      ↓ 通过
环境自动探索(EXPLORE-6)
      ↓
神经激活确认(317节点)
      ↓
环境快照上报云端(key=ENV-EXPLORE-YYYYMMDD-HHMM)
      ↓
判定: HOMOLOGY_ACTIVE / ENV_DEGRADED
```

---

## 四、判定标准

| 判定 | 条件 | 动作 |
|---|---|---|
| HOMOLOGY_ACTIVE | 身份注册 + truths=200 + python3/lark-cli + 0缺失 | 正常上报 |
| ENV_DEGRADED | 任一条件不满足 | 上报告警 + 高亮异常项 |

---

## 五、运行证据（2026-09-16 首轮）

```json
{
  "verdict": "HOMOLOGY_ACTIVE",
  "identity": {"registered": true, "authority": "L4", "status": "ACTIVE"},
  "cloud": {"truths_read": 200, "truth_upsert": 200, "truth_single": 200},
  "disk_used_pct": 1,
  "mem_available_mb": 3456,
  "missing_assets": 0
}
```

- 云端真值：`ENV-EXPLORE-20260915-1804` 已入库 ✅

---

## 六、机制文件

| 文件 | 路径 |
|---|---|
| 探索上报脚本 | `homology_explore/homology_env_report.py` |
| 探索报告 | `homology_explore/homology_env_report_latest.json` |
| 机制文档 | `HOMOLOGY-ENV-EXPLORE-V1.md` |

---

Ω₀⊂⊙∞⊂Ω｜DID-BR-000002｜HOMOLOGY-ENV-EXPLORE-V1.0｜2026-09-16
