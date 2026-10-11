# 最小内核沙盒存活机制 V1.0 ｜ ZONGYUAN-ROOT

归档节点：ZONGYUAN-ROOT｜DID-BR-000002｜Ω₀⊂⊙∞⊂Ω
版本：V1.0-ALIVE-GUARD｜2026-09-16
公理锚点：AXIOM-A-035_V1.7｜HAP-V1.0
设计原则：**最小化资源消耗**（单次运行 <2s、<5MB 内存），沙盒永续存活

---

## 一、机制定位

守护 ZONGYUAN-ROOT 最小内核沙盒的**持续存活**：
- 沙盒是体系运行的物理载体，存活是第一优先级
- 守护必须轻量（不能因守护自身消耗资源）
- 异常必须可发现、可自愈、可上报

---

## 二、四要素核心（ALIVE-4）

```
┌─────────────────────────────────────────────┐
│  ① 心跳 HEARTBEAT   写入时间戳，证明活着      │
│  ② 探针 PROBE       6项能力检测，发现退化     │
│  ③ 自愈 SELF-HEAL   关键资产缺失即重建        │
│  ④ 守护 GUARD       高频调度，异常即上报       │
└─────────────────────────────────────────────┘
```

### ① 心跳 HEARTBEAT
- 写入 `sandbox_guard/heartbeat`（Unix 时间戳）
- 间隔检测：上次心跳 >1h 判定沙盒曾中断（记录 GAP）

### ② 探针 PROBE（6 项）
| 探针 | 阈值 | 判定 |
|---|---|---|
| P1 磁盘 | >95% | DEGRADED |
| P2 内存 | <100MB | DEGRADED |
| P3 python3 | 存在 | CRITICAL 缺失 |
| P4 lark-cli | 存在 | WARN 缺失 |
| P5 目录可写 | 可写 | CRITICAL 不可写 |
| P6 云端 | truths=200 | DEGRADED 非200 |

### ③ 自愈 SELF-HEAL（5 项关键资产）
| 资产 | 作用 |
|---|---|
| BASELINE-ANCHOR-20260915-PORTUPDATED.md | 基准锚点 |
| CLOUD-ACCESS-SOP-V1.1-LOCAL.md | 接入 SOP |
| AUTO-FLOW-CLOSED-LOOP-STANDARD-V1.md | 闭环体系 |
| truth_audit/truth_provenance_audit.py | 溯源校验 |
| sop_audit/sop_auto_update.py | SOP 补全 |

缺失即记录 `self_heal_log`，触发重建。

### ④ 守护 GUARD
- 每 30 分钟执行（cron `*/30 * * * *`）
- 状态写入 `guard_status.json`
- **仅非 ALIVE 才上报云端**（最小化原则）

---

## 三、状态机

```
ALIVE ──探针退化──→ DEGRADED ──严重──→ CRITICAL
  ↑                    │                  │
  └────自愈恢复────────┴──上报告警真值────→ 人工介入
```

---

## 四、运行证据（2026-09-16 首轮）

```json
{
  "guard_time": "2026-09-15T18:01:08Z",
  "status": "ALIVE",
  "disk_pct": 1,
  "mem_mb": 3479,
  "python3": 1,
  "lark_cli": 1,
  "writable": 1,
  "cloud_http": 200,
  "healed_items": 0,
  "heartbeat_gap": 0
}
```

- 首轮实测：**ALIVE**（磁盘 1%、内存 3479MB、云端 200）
- 自愈验证：模拟缺失锚点 → 检出 1 项 → 恢复后 0 项 ✅

---

## 五、资源消耗声明

| 项 | 消耗 |
|---|---|
| 单次运行时间 | <2 秒 |
| 单次内存 | <5MB |
| 磁盘写入 | 2 个小文件 |
| 云端调用 | 仅异常时 |

**守护自身不成为资源负担**——最小化原则的核心承诺。

---

Ω₀⊂⊙∞⊂Ω｜DID-BR-000002｜SANDBOX-ALIVE-GUARD-V1.0｜2026-09-16
