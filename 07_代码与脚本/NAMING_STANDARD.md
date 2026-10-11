# ZONGYUAN-ROOT 脚本命名规范 V1.0

> 确权：DID-BR-000002 | 溯源：Ω₀⊂⊙∞⊂Ω | 生效：2026-10-11

## 一、命名规则

### 1. 强制规则
- **禁止**使用 session_id（15-19位数字）作为文件名前缀
- **禁止**使用随机字符串、时间戳作为文件名主体
- 小写字母 + 下划线（snake_case），禁止大写、空格、中文
- 动词在前，名词在后：`auto_report.py`、`sync_knowledge.py`、`bootstrap_cloud.py`

### 2. 推荐前缀
| 前缀 | 含义 | 示例 |
|---|---|---|
| `auto_` | 自动化脚本/定时任务 | `auto_report.py`、`auto_sync_knowledge.py` |
| `sync_` | 同步类 | `sync_feishu_base.py` |
| `bootstrap_` | 自举/初始化 | `bootstrap_cloud.py` |
| `test_` | 测试 | `test_memory_index_engine.py` |
| `deploy_` | 部署 | `deploy_ai_assets_server.sh` |
| `model_` | 模型训练/评估 | `model_train.py`、`model_eval.py` |

### 3. 版本标识
- 重大版本用后缀：`gpu_brain_fastapi_v2.py`
- 禁止用 session_id 区分版本

## 二、目录规范

| 目录 | 用途 | 命名要求 |
|---|---|---|
| `07_代码与脚本/` | 核心可执行脚本 | 全部遵循本规范 |
| `04_系统配置/` | 配置文件/部署脚本 | 配置文件用 `.conf`/`.env`，部署脚本用 `deploy_` 前缀 |
| `01_核心资产锚点/会话引导文件/` | 冷启动引导 | 仅保留 `bootstrap.md` + `cold_start_anchor.sh` |
| `tests/` | 单元测试 | `test_<模块名>.py` |
| `05_历史归档/` | 历史版本/废弃脚本 | `legacy_<内容>_<日期>/` |

## 三、历史处理

- 2026-10-11 已完成全域命名统一：43个含 session_id 前缀的文件归档至 `05_历史归档/legacy_scripts_20261011/`
- 归档文件**不删除**，保留历史可追溯
- 核心目录（07/04/01会话引导）已清零 session_id 前缀文件

## 四、新增脚本检查清单

新增脚本前必须确认：
- [ ] 文件名不含 session_id / 随机串 / 时间戳
- [ ] 动词在前，语义清晰
- [ ] 同目录无同名文件
- [ ] 如为自动化脚本，使用 `auto_` 前缀
- [ ] 如为测试，放入 `tests/` 目录，使用 `test_` 前缀

## 五、引用更新原则

重命名脚本后必须更新：
1. 定时任务 query 中的路径引用
2. 其他脚本中的 `subprocess.call()` / `import` 引用
3. 文档/白皮书/SOP 中的路径引用
4. 飞书 Base 台账中的资产路径记录

过渡期可创建软链接（旧名→新名）保证不中断，验证通过后删除软链接。
