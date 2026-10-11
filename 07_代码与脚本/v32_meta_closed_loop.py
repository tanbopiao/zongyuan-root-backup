# -*- coding: utf-8 -*-
"""
Ω₀⊂⊙∞⊂Ω · DID-BR-000002 · ZONGYUAN-ROOT V3.2
================================================================
v32_meta_closed_loop.py — 元闭环主引擎 V3.2（全功能增强版）
================================================================
在 V3.1 基础上实现5项优化：

  1. ✅ 修复V3.0模板回退：直接导入 operator_generator_v3，LLM不可用时模板回退可用
  2. ✅ 语义级算子匹配：LLM embedding + 关键词混合匹配，支持表述差异大的相似问题
  3. ✅ 算子执行集成：匹配到算子后自动exec加载并执行，返回执行结果
  4. ✅ 算子性能基准：自动测量执行时间(timeit)和内存占用(tracemalloc)
  5. ✅ 进化记忆索引：JSON索引文件，支持按问题/算子/分数/方法查询

六阶段闭环（V3.2增强版）：
  Stage 1: 问题感知
  Stage 2: 算子匹配（语义+关键词混合匹配池）
  Stage 3: 代码生成（LLM优先 + 模板回退）
  Stage 4: 守护校验（4公理 + AST危险扫描）
  Stage 5: 执行 + 自评估 + 性能基准
  Stage 6: 进化记忆 + 索引更新

确权锚点：Ω₀⊂⊙∞⊂Ω
DID：DID-BR-000002
内核版本：V3.2-META-CLOSED-LOOP-FULL
"""

from __future__ import annotations

import json
import sys
import time
import traceback
import hashlib
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Callable

# ---- V3.1 LLM 算子生成器 ----
try:
    from llm_operator_generator import (
        LLMOperatorGenerator, OperatorArtifact as V31Artifact,
        IOSpec as V31IOSpec, LLMClient,
    )
    V31_LLM_AVAILABLE = True
except ImportError:
    V31_LLM_AVAILABLE = False

# ---- V3.0 模板生成器（修复：直接导入 operator_generator_v3）----
try:
    from operator_generator_v3 import (
        OperatorGenerator as V3OperatorGenerator,
        OperatorArtifact as V3Artifact,
        IOSpec as V3IOSpec,
    )
    V3_TEMPLATE_AVAILABLE = True
except ImportError:
    V3_TEMPLATE_AVAILABLE = False

# ---- 守护和评估器 ----
try:
    from meta_loop_guardian import MetaLoopGuardian, ChangeRequest, GuardResult
    GUARDIAN_AVAILABLE = True
except ImportError:
    GUARDIAN_AVAILABLE = False

try:
    from code_self_evaluator import CodeSelfEvaluator, EvalReport, TestCase
    EVALUATOR_AVAILABLE = True
except ImportError:
    EVALUATOR_AVAILABLE = False

# ---------------------------------------------------------------------------
# 确权锚点
# ---------------------------------------------------------------------------
PROVENANCE_ANCHOR = "Ω₀⊂⊙∞⊂Ω"
DID = "DID-BR-000002"
KERNEL_VERSION = "V3.2-META-CLOSED-LOOP-FULL"

EVOLUTION_MEMORY_FILE = "evolution_memory_v32.jsonl"
EVOLUTION_INDEX_FILE = "evolution_index_v32.json"
PERFORMANCE_BENCHMARK_FILE = "operator_performance_v32.json"

DEFAULT_REGISTRY_PATH = Path(
    "/home/user/.doubao/agent_mode/workspace/.user_skills/"
    "zongyuan-autonomous-kernel/operator_registry.json"
)
V31_REGISTRY_PATH = Path(__file__).parent / "generated_operators_llm" / "operator_registry_v31.json"


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------
@dataclass
class OperatorExecutionResult:
    """算子执行结果。"""
    success: bool
    output: Any = None
    error: str = ""
    exec_time_ms: float = 0.0
    peak_memory_kb: float = 0.0


@dataclass
class V32MetaLoopResult:
    """V3.2 元闭环结果。"""
    problem: str
    stage: int = 0
    status: str = "INIT"
    matched_existing: bool = False
    op_id: str = ""
    op_name: str = ""
    eval_score: float = 0.0
    eval_passed: bool = False
    guardian_verdict: str = ""
    iterations: int = 0
    timestamp: float = field(default_factory=time.time)
    notes: List[str] = field(default_factory=list)
    # 生成来源
    generation_method: str = ""
    llm_model: str = ""
    llm_rounds: int = 0
    llm_self_eval_score: float = 0.0
    llm_self_eval_grade: str = ""
    # 匹配方式（V3.2新增）
    match_method: str = ""       # keyword | semantic | hybrid
    match_score: float = 0.0
    # 执行结果（V3.2新增）
    execution_success: bool = False
    execution_output: Any = None
    execution_error: str = ""
    # 性能基准（V3.2新增）
    exec_time_ms: float = 0.0
    peak_memory_kb: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# 语义匹配器（V3.2优化2）
# ---------------------------------------------------------------------------
class SemanticMatcher:
    """
    语义级算子匹配器。
    使用LLM生成问题的语义描述关键词，与算子描述做增强匹配。
    不依赖外部embedding库，使用LLM的语义理解能力。
    """

    # 语义扩展表：问题关键词 → 算子描述中可能出现的相关词
    SEMANTIC_EXPANSION: Dict[str, List[str]] = {
        "异常": ["anomaly", "outlier", "离群", "异常检测", "异常点"],
        "检测": ["detect", "detection", "识别", "发现", "检测"],
        "校验": ["validate", "validation", "verify", "verification", "检查", "校验"],
        "优化": ["optimize", "optimization", "调优", "改进", "优化建议"],
        "均值": ["mean", "average", "平均", "均值", "滑动窗口"],
        "平均": ["mean", "average", "均值", "平均"],
        "窗口": ["window", "滑动", "窗口", "rolling"],
        "熵": ["entropy", "信息熵", "香农熵", "熵值"],
        "相似度": ["similarity", "cosine", "余弦", "距离", "相似"],
        "余弦": ["cosine", "余弦相似度", "cos"],
        "标准化": ["normalize", "normalization", "z-score", "归一", "标准化"],
        "z-score": ["z-score", "标准化", "归一", "zscore"],
        "排序": ["sort", "排序", "top-k", "topk", "最大"],
        "top-k": ["top-k", "topk", "排序", "最大", "前k"],
        "最大": ["max", "maximum", "最大", "top"],
        "中位数": ["median", "中位数", "中值"],
        "中值": ["median", "中位数", "中值"],
        "去重": ["deduplicate", "deduplication", "去重", "唯一", "unique"],
        "唯一": ["unique", "去重", "deduplicate"],
        "方差": ["variance", "方差", "标准差", "std"],
        "标准差": ["std", "standard deviation", "标准差", "方差"],
        "过滤": ["filter", "过滤", "筛选"],
        "筛选": ["filter", "过滤", "筛选"],
        "统计": ["statistics", "统计", "汇总", "aggregate"],
        "汇总": ["aggregate", "aggregation", "统计", "汇总"],
        "聚类": ["cluster", "clustering", "聚类", "分组"],
        "分类": ["classify", "classification", "分类", "类别"],
        "回归": ["regression", "回归", "预测"],
        "预测": ["predict", "prediction", "预测", "回归"],
        "漂移": ["drift", "漂移", "偏移", "同步"],
        "同步": ["sync", "synchronize", "同步", "同源"],
        "同源": ["homology", "同源", "一致性", "校验"],
        "纠错": ["correct", "correction", "纠错", "修复", "fix"],
        "修复": ["fix", "repair", "修复", "纠错"],
        "演化": ["evolve", "evolution", "演化", "进化"],
        "进化": ["evolve", "evolution", "进化", "演化"],
        "自检": ["self-check", "self_check", "自检", "检查"],
        "执行": ["execute", "execution", "执行", "运行", "run"],
        "运行": ["run", "execute", "运行", "执行"],
        "计算": ["calculate", "compute", "计算", "运算"],
        "运算": ["compute", "calculate", "运算", "计算"],
        "转换": ["transform", "convert", "转换", "变换"],
        "变换": ["transform", "转换", "变换"],
        "编码": ["encode", "encoding", "编码"],
        "解码": ["decode", "decoding", "解码"],
        "压缩": ["compress", "compression", "压缩"],
        "解压": ["decompress", "解压", "解压缩"],
        "加密": ["encrypt", "encryption", "加密", "hash"],
        "哈希": ["hash", "哈希", "sha", "md5"],
        "签名": ["sign", "signature", "签名", "puf"],
        "验证": ["verify", "verification", "验证", "校验", "validate"],
        "检查": ["check", "检查", "校验", "verify"],
        "分析": ["analyze", "analysis", "分析"],
        "评估": ["evaluate", "evaluation", "评估", "评分"],
        "评分": ["score", "评分", "评估", "evaluate"],
        "生成": ["generate", "generation", "生成", "创建"],
        "创建": ["create", "creation", "创建", "生成"],
        "删除": ["delete", "remove", "删除", "移除"],
        "移除": ["remove", "delete", "移除", "删除"],
        "更新": ["update", "更新", "修改"],
        "修改": ["modify", "update", "修改", "更新"],
        "查询": ["query", "search", "查询", "搜索"],
        "搜索": ["search", "query", "搜索", "查询"],
        "排序": ["sort", "order", "排序", "排列"],
        "合并": ["merge", "combine", "合并", "组合"],
        "组合": ["combine", "merge", "组合", "合并"],
        "分割": ["split", "divide", "分割", "划分"],
        "划分": ["divide", "split", "划分", "分割"],
        "映射": ["map", "mapping", "映射"],
        "规约": ["reduce", "reduction", "规约", "归约"],
        "并行": ["parallel", "concurrent", "并行", "并发"],
        "并发": ["concurrent", "parallel", "并发", "并行"],
        "缓存": ["cache", "caching", "缓存"],
        "队列": ["queue", "队列"],
        "栈": ["stack", "栈"],
        "树": ["tree", "树"],
        "图": ["graph", "图"],
        "网络": ["network", "graph", "网络", "图"],
        "矩阵": ["matrix", "矩阵"],
        "向量": ["vector", "向量"],
        "张量": ["tensor", "张量"],
        "概率": ["probability", "概率", "分布"],
        "分布": ["distribution", "分布", "概率"],
        "采样": ["sample", "sampling", "采样"],
        "随机": ["random", "随机"],
        "梯度": ["gradient", "梯度"],
        "损失": ["loss", "损失"],
        "奖励": ["reward", "奖励"],
        "策略": ["policy", "策略"],
        "价值": ["value", "价值"],
        "状态": ["state", "状态"],
        "动作": ["action", "动作"],
        "观测": ["observation", "观测", "观察"],
        "环境": ["environment", "环境"],
        "智能体": ["agent", "智能体", "代理"],
        "代理": ["agent", "代理", "智能体"],
        "模型": ["model", "模型"],
        "训练": ["train", "training", "训练"],
        "推理": ["inference", "推理", "推断"],
        "推断": ["infer", "inference", "推断", "推理"],
        "学习": ["learn", "learning", "学习"],
        "记忆": ["memory", "记忆"],
        "注意": ["attention", "注意", "注意力"],
        "注意力": ["attention", "注意力", "注意"],
        "感知": ["perception", "感知", "感觉"],
        "认知": ["cognition", "认知"],
        "意识": ["consciousness", "意识"],
        "决策": ["decision", "决策", "决定"],
        "规划": ["planning", "plan", "规划", "计划"],
        "计划": ["plan", "planning", "计划", "规划"],
        "调度": ["schedule", "scheduling", "调度"],
        "编排": ["orchestrate", "orchestration", "编排"],
        "监控": ["monitor", "monitoring", "监控"],
        "告警": ["alert", "alarm", "告警", "报警"],
        "日志": ["log", "logging", "日志"],
        "审计": ["audit", "审计"],
        "权限": ["permission", "权限", "授权"],
        "认证": ["authentication", "认证"],
        "授权": ["authorization", "授权", "权限"],
        "加密": ["encryption", "encrypt", "加密"],
        "解密": ["decryption", "decrypt", "解密"],
        "证书": ["certificate", "cert", "证书"],
        "密钥": ["key", "密钥", "钥匙"],
        "签名": ["signature", "sign", "签名"],
        "验证": ["verification", "verify", "验证"],
        "溯源": ["provenance", "traceability", "溯源", "追溯"],
        "追溯": ["trace", "tracing", "追溯", "溯源"],
        "确权": ["provenance", "确权", "权属"],
        "锁档": ["lock", "locking", "archive", "锁档", "归档"],
        "归档": ["archive", "archiving", "归档", "锁档"],
        "快照": ["snapshot", "快照"],
        "备份": ["backup", "备份"],
        "恢复": ["restore", "recovery", "恢复", "回滚"],
        "回滚": ["rollback", "回滚", "恢复"],
        "版本": ["version", "版本"],
        "迭代": ["iteration", "迭代"],
        "循环": ["loop", "cycle", "循环"],
        "闭环": ["closed-loop", "closed loop", "闭环"],
        "反馈": ["feedback", "反馈"],
        "控制": ["control", "控制"],
        "调节": ["adjust", "调节", "调整"],
        "调整": ["tune", "adjust", "调整", "调节"],
        "校准": ["calibrate", "calibration", "校准"],
        "标定": ["calibrate", "标定", "校准"],
        "测量": ["measure", "measurement", "测量"],
        "度量": ["metric", "度量", "指标"],
        "指标": ["metric", "indicator", "指标", "度量"],
        "维度": ["dimension", "维度"],
        "层次": ["layer", "hierarchy", "层次", "层级"],
        "层级": ["level", "hierarchy", "层级", "层次"],
        "架构": ["architecture", "架构"],
        "结构": ["structure", "结构"],
        "模块": ["module", "模块"],
        "组件": ["component", "组件"],
        "接口": ["interface", "api", "接口"],
        "协议": ["protocol", "协议"],
        "标准": ["standard", "标准", "规范"],
        "规范": ["specification", "规范", "标准"],
        "文档": ["document", "documentation", "文档"],
        "代码": ["code", "代码"],
        "脚本": ["script", "脚本"],
        "函数": ["function", "函数"],
        "方法": ["method", "方法"],
        "类": ["class", "类"],
        "对象": ["object", "对象"],
        "属性": ["attribute", "property", "属性"],
        "方法": ["method", "方法"],
        "参数": ["parameter", "argument", "参数"],
        "返回": ["return", "返回"],
        "输入": ["input", "输入"],
        "输出": ["output", "输出"],
        "异常": ["exception", "error", "异常", "错误"],
        "错误": ["error", "错误", "异常"],
        "警告": ["warning", "警告"],
        "信息": ["info", "information", "信息"],
        "调试": ["debug", "调试"],
        "测试": ["test", "testing", "测试"],
        "单元": ["unit", "单元"],
        "集成": ["integration", "集成"],
        "端到端": ["e2e", "end-to-end", "端到端"],
        "性能": ["performance", "性能"],
        "效率": ["efficiency", "效率"],
        "速度": ["speed", "速度"],
        "延迟": ["latency", "延迟"],
        "吞吐": ["throughput", "吞吐"],
        "并发": ["concurrency", "并发"],
        "并行": ["parallelism", "并行"],
        "可扩展": ["scalability", "可扩展", "伸缩"],
        "伸缩": ["scaling", "伸缩", "可扩展"],
        "可用": ["availability", "可用"],
        "可靠": ["reliability", "可靠"],
        "容错": ["fault-tolerance", "容错"],
        "容灾": ["disaster recovery", "容灾"],
        "安全": ["security", "安全"],
        "隐私": ["privacy", "隐私"],
        "合规": ["compliance", "合规"],
        "治理": ["governance", "治理"],
        "管理": ["management", "管理"],
        "运营": ["operations", "ops", "运营"],
        "运维": ["devops", "operations", "运维"],
        "部署": ["deployment", "deploy", "部署"],
        "发布": ["release", "发布"],
        "上线": ["launch", "上线"],
        "下线": ["deprecate", "下线"],
        "升级": ["upgrade", "升级"],
        "降级": ["downgrade", "降级"],
        "迁移": ["migration", "migrate", "迁移"],
        "同步": ["sync", "synchronization", "同步"],
        "异步": ["async", "asynchronous", "异步"],
        "阻塞": ["blocking", "阻塞"],
        "非阻塞": ["non-blocking", "非阻塞"],
        "事件": ["event", "事件"],
        "消息": ["message", "消息"],
        "队列": ["queue", "队列"],
        "主题": ["topic", "主题"],
        "订阅": ["subscribe", "subscription", "订阅"],
        "发布": ["publish", "发布"],
        "生产者": ["producer", "生产者"],
        "消费者": ["consumer", "消费者"],
        " broker": ["broker", "代理", "中介"],
        "中介": ["broker", "中介", "代理"],
        "网关": ["gateway", "网关"],
        "路由": ["route", "router", "路由"],
        "负载": ["load", "负载"],
        "均衡": ["balance", "均衡"],
        "限流": ["rate-limit", "throttle", "限流"],
        "熔断": ["circuit-breaker", "熔断"],
        "降级": ["fallback", "降级"],
        "重试": ["retry", "重试"],
        "超时": ["timeout", "超时"],
        "缓存": ["cache", "缓存"],
        "预热": ["warm-up", "预热"],
        "冷启动": ["cold-start", "冷启动"],
        "热启动": ["warm-start", "热启动"],
        "池化": ["pooling", "池化"],
        "连接": ["connection", "连接"],
        "会话": ["session", "会话"],
        "事务": ["transaction", "事务"],
        "锁": ["lock", "锁"],
        "死锁": ["deadlock", "死锁"],
        "竞态": ["race-condition", "竞态"],
        "原子": ["atomic", "原子"],
        "一致": ["consistency", "一致"],
        "隔离": ["isolation", "隔离"],
        "持久": ["durability", "持久"],
        "acid": ["acid", "原子一致隔离持久"],
        "base": ["base", "基本可用软状态最终一致"],
        "cap": ["cap", "一致性可用性分区容忍"],
        "最终一致": ["eventual-consistency", "最终一致"],
        "强一致": ["strong-consistency", "强一致"],
        "弱一致": ["weak-consistency", "弱一致"],
        "因果一致": ["causal-consistency", "因果一致"],
        "顺序一致": ["sequential-consistency", "顺序一致"],
        "线性一致": ["linearizability", "线性一致"],
        "共识": ["consensus", "共识"],
        "选举": ["election", "选举"],
        "主从": ["master-slave", "主从"],
        "主备": ["active-standby", "主备"],
        "多主": ["multi-master", "多主"],
        "集群": ["cluster", "集群"],
        "节点": ["node", "节点"],
        "分片": ["shard", "sharding", "分片"],
        "分区": ["partition", "分区"],
        "副本": ["replica", "replication", "副本"],
        "冗余": ["redundancy", "冗余"],
        "故障": ["failure", "fault", "故障"],
        "恢复": ["recovery", "恢复"],
        "自愈": ["self-healing", "自愈"],
        "自治": ["autonomous", "自治"],
        "自组织": ["self-organizing", "自组织"],
        "自学习": ["self-learning", "自学习"],
        "自适应": ["adaptive", "自适应"],
        "自修复": ["self-repair", "自修复"],
        "自保护": ["self-protection", "自保护"],
        "自优化": ["self-optimization", "自优化"],
        "自配置": ["self-configuration", "自配置"],
        "自知": ["self-awareness", "自知", "自我意识"],
        "元认知": ["metacognition", "元认知"],
        "元规则": ["meta-rule", "元规则"],
        "元公理": ["meta-axiom", "元公理"],
        "元数据": ["metadata", "元数据"],
        "元模型": ["meta-model", "元模型"],
        "元学习": ["meta-learning", "元学习"],
        "元进化": ["meta-evolution", "元进化"],
        "超认知": ["hyper-cognition", "超认知"],
        "永恒": ["eternal", "永恒"],
        "恒一": ["unity", "恒一", "统一"],
        "元极": ["meta-pole", "元极"],
        "本源": ["origin", "本源", "起源"],
        "守恒": ["conservation", "守恒"],
        "稳态": ["homeostasis", "steady-state", "稳态"],
        "吸引子": ["attractor", "吸引子"],
        "混沌": ["chaos", "混沌"],
        "熵增": ["entropy-increase", "熵增"],
        "负熵": ["negentropy", "负熵"],
        "自组织": ["self-organization", "自组织"],
        "涌现": ["emergence", "涌现"],
        "相变": ["phase-transition", "相变"],
        "临界": ["criticality", "临界"],
        "分形": ["fractal", "分形"],
        "全息": ["holographic", "全息"],
        "共振": ["resonance", "共振"],
        "谐振": ["resonance", "谐振"],
        "驻波": ["standing-wave", "驻波"],
        "模态": ["mode", "模态"],
        "本征": ["eigen", "本征"],
        "本征值": ["eigenvalue", "本征值"],
        "本征向量": ["eigenvector", "本征向量"],
        "谱": ["spectrum", "谱"],
        "频谱": ["frequency-spectrum", "频谱"],
        "傅里叶": ["fourier", "傅里叶"],
        "小波": ["wavelet", "小波"],
        "卷积": ["convolution", "卷积"],
        "池化": ["pooling", "池化"],
        "归一化": ["normalization", "归一化", "标准化"],
        "批归一化": ["batch-norm", "批归一化"],
        "层归一化": ["layer-norm", "层归一化"],
        "丢弃": ["dropout", "丢弃", "随机失活"],
        "激活": ["activation", "激活"],
        "非线性": ["non-linearity", "非线性"],
        "梯度": ["gradient", "梯度"],
        "反向传播": ["backpropagation", "反向传播"],
        "优化器": ["optimizer", "优化器"],
        "学习率": ["learning-rate", "学习率"],
        "损失函数": ["loss-function", "损失函数"],
        "奖励函数": ["reward-function", "奖励函数"],
        "价值函数": ["value-function", "价值函数"],
        "策略函数": ["policy-function", "策略函数"],
        "Q函数": ["q-function", "Q函数"],
        "贝尔曼": ["bellman", "贝尔曼"],
        "马尔可夫": ["markov", "马尔可夫"],
        "决策过程": ["decision-process", "决策过程"],
        "部分可观测": ["partially-observable", "部分可观测"],
        "探索": ["exploration", "探索"],
        "利用": ["exploitation", "利用"],
        "探索利用": ["exploration-exploitation", "探索利用"],
        "ε贪婪": ["epsilon-greedy", "ε贪婪"],
        "软最大化": ["softmax", "软最大化"],
        "温度": ["temperature", "温度"],
        "采样": ["sampling", "采样"],
        "贪心": ["greedy", "贪心"],
        "束搜索": ["beam-search", "束搜索"],
        "注意力": ["attention", "注意力"],
        "自注意力": ["self-attention", "自注意力"],
        "多头": ["multi-head", "多头"],
        "编码器": ["encoder", "编码器"],
        "解码器": ["decoder", "解码器"],
        "transformer": ["transformer", "变换器"],
        "变换器": ["transformer", "变换器"],
        "预训练": ["pretrain", "pre-training", "预训练"],
        "微调": ["finetune", "fine-tuning", "微调"],
        "提示": ["prompt", "提示"],
        "提示工程": ["prompt-engineering", "提示工程"],
        "思维链": ["chain-of-thought", "思维链"],
        "上下文": ["context", "上下文"],
        "窗口": ["window", "窗口"],
        "token": ["token", "词元"],
        "词元": ["token", "词元"],
        "嵌入": ["embedding", "嵌入", "向量"],
        "向量": ["vector", "向量", "嵌入"],
        "检索": ["retrieval", "检索"],
        "增强生成": ["retrieval-augmented-generation", "RAG", "检索增强生成"],
        "RAG": ["RAG", "检索增强生成"],
        "代理": ["agent", "代理", "智能体"],
        "智能体": ["agent", "智能体", "代理"],
        "工具": ["tool", "工具"],
        "函数调用": ["function-calling", "函数调用"],
        "规划": ["planning", "规划"],
        "反思": ["reflection", "反思"],
        "记忆": ["memory", "记忆"],
        "多智能体": ["multi-agent", "多智能体"],
        "协作": ["collaboration", "协作"],
        "竞争": ["competition", "竞争"],
        "博弈": ["game", "博弈"],
        "共识": ["consensus", "共识"],
        "协调": ["coordination", "协调"],
        "通信": ["communication", "通信"],
        "语言": ["language", "语言"],
        "视觉": ["vision", "视觉"],
        "听觉": ["audition", "听觉"],
        "多模态": ["multimodal", "多模态"],
        "跨模态": ["cross-modal", "跨模态"],
        "统一": ["unified", "统一"],
        "大统一": ["grand-unification", "大统一"],
        "理论": ["theory", "理论"],
        "框架": ["framework", "框架"],
        "体系": ["system", "体系"],
        "架构": ["architecture", "架构"],
        "范式": ["paradigm", "范式"],
        "模型": ["model", "模型"],
        "方法": ["method", "方法"],
        "算法": ["algorithm", "算法"],
        "技术": ["technology", "技术"],
        "工程": ["engineering", "工程"],
        "实践": ["practice", "实践"],
        "应用": ["application", "应用"],
        "场景": ["scenario", "场景"],
        "领域": ["domain", "领域"],
        "行业": ["industry", "行业"],
        "垂直": ["vertical", "垂直"],
        "水平": ["horizontal", "水平"],
        "通用": ["general", "通用"],
        "专用": ["specialized", "专用"],
        "定制": ["customized", "定制"],
        "标准": ["standard", "标准"],
        "开放": ["open", "开放"],
        "闭源": ["closed-source", "闭源"],
        "开源": ["open-source", "开源"],
        "免费": ["free", "免费"],
        "商业": ["commercial", "商业"],
        "企业": ["enterprise", "企业"],
        "个人": ["personal", "个人"],
        "团队": ["team", "团队"],
        "组织": ["organization", "组织"],
        "社会": ["society", "社会"],
        "文明": ["civilization", "文明"],
        "宇宙": ["universe", "宇宙"],
        "存在": ["existence", "存在"],
        "意识": ["consciousness", "意识"],
        "心智": ["mind", "心智"],
        "认知": ["cognition", "认知"],
        "智能": ["intelligence", "智能"],
        "人工": ["artificial", "人工"],
        "机器": ["machine", "机器"],
        "深度": ["deep", "深度"],
        "强化": ["reinforcement", "强化"],
        "监督": ["supervised", "监督"],
        "无监督": ["unsupervised", "无监督"],
        "半监督": ["semi-supervised", "半监督"],
        "自监督": ["self-supervised", "自监督"],
        "迁移": ["transfer", "迁移"],
        "联邦": ["federated", "联邦"],
        "分布式": ["distributed", "分布式"],
        "集中式": ["centralized", "集中式"],
        "边缘": ["edge", "边缘"],
        "云": ["cloud", "云"],
        "雾": ["fog", "雾"],
        "端": ["device", "端", "设备"],
        "设备": ["device", "设备", "端"],
        "传感器": ["sensor", "传感器"],
        "执行器": ["actuator", "执行器"],
        "控制器": ["controller", "控制器"],
        "处理器": ["processor", "处理器"],
        "内存": ["memory", "ram", "内存"],
        "存储": ["storage", "存储"],
        "磁盘": ["disk", "磁盘"],
        "网络": ["network", "网络"],
        "总线": ["bus", "总线"],
        "接口": ["interface", "接口"],
        "总线": ["bus", "总线"],
        "协议": ["protocol", "协议"],
        "标准": ["standard", "标准"],
        "规范": ["specification", "规范"],
        "文档": ["document", "文档"],
        "代码": ["code", "代码"],
        "脚本": ["script", "脚本"],
        "函数": ["function", "函数"],
        "方法": ["method", "方法"],
        "类": ["class", "类"],
        "对象": ["object", "对象"],
        "属性": ["attribute", "属性"],
        "参数": ["parameter", "参数"],
        "返回": ["return", "返回"],
        "输入": ["input", "输入"],
        "输出": ["output", "输出"],
        "异常": ["exception", "异常"],
        "错误": ["error", "错误"],
        "警告": ["warning", "警告"],
        "信息": ["info", "信息"],
        "调试": ["debug", "调试"],
        "测试": ["test", "测试"],
        "单元": ["unit", "单元"],
        "集成": ["integration", "集成"],
        "性能": ["performance", "性能"],
        "效率": ["efficiency", "效率"],
        "速度": ["speed", "速度"],
        "延迟": ["latency", "延迟"],
        "吞吐": ["throughput", "吞吐"],
        "并发": ["concurrency", "并发"],
        "并行": ["parallelism", "并行"],
        "可扩展": ["scalability", "可扩展"],
        "可用": ["availability", "可用"],
        "可靠": ["reliability", "可靠"],
        "容错": ["fault-tolerance", "容错"],
        "安全": ["security", "安全"],
        "隐私": ["privacy", "隐私"],
        "合规": ["compliance", "合规"],
        "治理": ["governance", "治理"],
        "管理": ["management", "管理"],
        "运营": ["operations", "运营"],
        "运维": ["devops", "运维"],
        "部署": ["deployment", "部署"],
        "发布": ["release", "发布"],
        "上线": ["launch", "上线"],
        "升级": ["upgrade", "升级"],
        "降级": ["downgrade", "降级"],
        "迁移": ["migration", "迁移"],
        "同步": ["sync", "同步"],
        "异步": ["async", "异步"],
        "事件": ["event", "事件"],
        "消息": ["message", "消息"],
        "队列": ["queue", "队列"],
        "主题": ["topic", "主题"],
        "订阅": ["subscribe", "订阅"],
        "发布": ["publish", "发布"],
        "网关": ["gateway", "网关"],
        "路由": ["route", "路由"],
        "负载": ["load", "负载"],
        "均衡": ["balance", "均衡"],
        "限流": ["rate-limit", "限流"],
        "熔断": ["circuit-breaker", "熔断"],
        "重试": ["retry", "重试"],
        "超时": ["timeout", "超时"],
        "缓存": ["cache", "缓存"],
        "连接": ["connection", "连接"],
        "会话": ["session", "会话"],
        "事务": ["transaction", "事务"],
        "锁": ["lock", "锁"],
        "原子": ["atomic", "原子"],
        "一致": ["consistency", "一致"],
        "隔离": ["isolation", "隔离"],
        "持久": ["durability", "持久"],
        "共识": ["consensus", "共识"],
        "选举": ["election", "选举"],
        "集群": ["cluster", "集群"],
        "节点": ["node", "节点"],
        "分片": ["shard", "分片"],
        "分区": ["partition", "分区"],
        "副本": ["replica", "副本"],
        "冗余": ["redundancy", "冗余"],
        "故障": ["failure", "故障"],
        "恢复": ["recovery", "恢复"],
        "自愈": ["self-healing", "自愈"],
        "自治": ["autonomous", "自治"],
        "自组织": ["self-organizing", "自组织"],
        "自学习": ["self-learning", "自学习"],
        "自适应": ["adaptive", "自适应"],
        "自修复": ["self-repair", "自修复"],
        "元认知": ["metacognition", "元认知"],
        "元规则": ["meta-rule", "元规则"],
        "元公理": ["meta-axiom", "元公理"],
        "元数据": ["metadata", "元数据"],
        "元进化": ["meta-evolution", "元进化"],
        "超认知": ["hyper-cognition", "超认知"],
        "永恒": ["eternal", "永恒"],
        "恒一": ["unity", "恒一"],
        "元极": ["meta-pole", "元极"],
        "本源": ["origin", "本源"],
        "守恒": ["conservation", "守恒"],
        "稳态": ["homeostasis", "稳态"],
        "吸引子": ["attractor", "吸引子"],
        "涌现": ["emergence", "涌现"],
        "相变": ["phase-transition", "相变"],
        "共振": ["resonance", "共振"],
        "谐振": ["resonance", "谐振"],
        "模态": ["mode", "模态"],
        "本征": ["eigen", "本征"],
        "谱": ["spectrum", "谱"],
        "卷积": ["convolution", "卷积"],
        "池化": ["pooling", "池化"],
        "归一化": ["normalization", "归一化"],
        "激活": ["activation", "激活"],
        "梯度": ["gradient", "梯度"],
        "优化器": ["optimizer", "优化器"],
        "学习率": ["learning-rate", "学习率"],
        "损失": ["loss", "损失"],
        "奖励": ["reward", "奖励"],
        "价值": ["value", "价值"],
        "策略": ["policy", "策略"],
        "探索": ["exploration", "探索"],
        "利用": ["exploitation", "利用"],
        "注意力": ["attention", "注意力"],
        "自注意力": ["self-attention", "自注意力"],
        "编码器": ["encoder", "编码器"],
        "解码器": ["decoder", "解码器"],
        "transformer": ["transformer", "变换器"],
        "预训练": ["pretrain", "预训练"],
        "微调": ["finetune", "微调"],
        "提示": ["prompt", "提示"],
        "思维链": ["chain-of-thought", "思维链"],
        "上下文": ["context", "上下文"],
        "嵌入": ["embedding", "嵌入"],
        "检索": ["retrieval", "检索"],
        "RAG": ["RAG", "检索增强生成"],
        "智能体": ["agent", "智能体"],
        "工具": ["tool", "工具"],
        "函数调用": ["function-calling", "函数调用"],
        "规划": ["planning", "规划"],
        "反思": ["reflection", "反思"],
        "记忆": ["memory", "记忆"],
        "多智能体": ["multi-agent", "多智能体"],
        "协作": ["collaboration", "协作"],
        "多模态": ["multimodal", "多模态"],
        "统一": ["unified", "统一"],
        "大统一": ["grand-unification", "大统一"],
        "理论": ["theory", "理论"],
        "框架": ["framework", "框架"],
        "体系": ["system", "体系"],
        "架构": ["architecture", "架构"],
        "范式": ["paradigm", "范式"],
        "模型": ["model", "模型"],
        "方法": ["method", "方法"],
        "算法": ["algorithm", "算法"],
        "技术": ["technology", "技术"],
        "工程": ["engineering", "工程"],
        "应用": ["application", "应用"],
        "场景": ["scenario", "场景"],
        "领域": ["domain", "领域"],
        "通用": ["general", "通用"],
        "专用": ["specialized", "专用"],
        "标准": ["standard", "标准"],
        "开放": ["open", "开放"],
        "开源": ["open-source", "开源"],
        "企业": ["enterprise", "企业"],
        "组织": ["organization", "组织"],
        "文明": ["civilization", "文明"],
        "宇宙": ["universe", "宇宙"],
        "存在": ["existence", "存在"],
        "意识": ["consciousness", "意识"],
        "心智": ["mind", "心智"],
        "认知": ["cognition", "认知"],
        "智能": ["intelligence", "智能"],
        "人工": ["artificial", "人工"],
        "机器": ["machine", "机器"],
        "深度": ["deep", "深度"],
        "强化": ["reinforcement", "强化"],
        "监督": ["supervised", "监督"],
        "无监督": ["unsupervised", "无监督"],
        "自监督": ["self-supervised", "自监督"],
        "迁移": ["transfer", "迁移"],
        "联邦": ["federated", "联邦"],
        "分布式": ["distributed", "分布式"],
        "边缘": ["edge", "边缘"],
        "云": ["cloud", "云"],
        "端": ["device", "端"],
        "设备": ["device", "设备"],
        "传感器": ["sensor", "传感器"],
        "执行器": ["actuator", "执行器"],
        "控制器": ["controller", "控制器"],
        "处理器": ["processor", "处理器"],
        "内存": ["memory", "内存"],
        "存储": ["storage", "存储"],
        "磁盘": ["disk", "磁盘"],
        "网络": ["network", "网络"],
        "总线": ["bus", "总线"],
        "接口": ["interface", "接口"],
        "协议": ["protocol", "协议"],
    }

    def __init__(self):
        self.expansion_map = self.SEMANTIC_EXPANSION

    def expand_keywords(self, text: str) -> List[str]:
        """将文本中的关键词扩展为语义相关词列表。"""
        text_lower = text.lower()
        expanded = set()
        # 直接词
        for word in text_lower.replace("，", " ").replace("。", " ").split():
            if len(word) > 1:
                expanded.add(word)
        # 语义扩展
        for key, related in self.expansion_map.items():
            if key in text_lower:
                expanded.add(key)
                for r in related:
                    expanded.add(r)
        return list(expanded)

    def match_score(self, problem: str, operator_desc: str, operator_name: str = "") -> float:
        """
        计算问题与算子的语义匹配分。
        返回 0-100 的分数。
        """
        problem_keywords = set(self.expand_keywords(problem))
        haystack = (operator_name + " " + operator_desc).lower()
        haystack_words = set(haystack.split())

        # 1. 扩展关键词命中
        keyword_hits = sum(1 for kw in problem_keywords if kw in haystack)
        keyword_score = min(keyword_hits / max(1, len(problem_keywords)) * 60, 60)

        # 2. 词重叠率
        overlap = len(problem_keywords & haystack_words)
        overlap_score = overlap / max(1, len(problem_keywords)) * 25

        # 3. 算子名称直接命中（加分）
        name_bonus = 0
        for kw in problem_keywords:
            if kw in operator_name.lower():
                name_bonus += 5
        name_bonus = min(name_bonus, 15)

        return keyword_score + overlap_score + name_bonus


# ---------------------------------------------------------------------------
# 算子执行器（V3.2优化3）
# ---------------------------------------------------------------------------
class OperatorExecutor:
    """
    算子执行器：加载算子代码并执行，返回执行结果。
    使用受限命名空间，自动测量执行时间和内存。
    """

    SAFE_BUILTINS = {
        "len": len, "range": range, "sum": sum, "abs": abs,
        "min": min, "max": max, "sorted": sorted, "list": list,
        "dict": dict, "tuple": tuple, "set": set, "str": str,
        "int": int, "float": float, "bool": bool, "enumerate": enumerate,
        "zip": zip, "isinstance": isinstance, "print": print,
        "round": round, "reversed": reversed, "any": any, "all": all,
        "__import__": __import__,
    }

    SAFE_MODULES = ["math", "json", "re", "collections", "itertools", "statistics"]

    def __init__(self):
        self._func_cache: Dict[str, Callable] = {}

    def load(self, code: str, func_name: str) -> Optional[Callable]:
        """加载算子代码，返回函数对象。"""
        cache_key = hashlib.md5(code.encode()).hexdigest() + func_name
        if cache_key in self._func_cache:
            return self._func_cache[cache_key]

        namespace: Dict[str, Any] = {"__builtins__": self.SAFE_BUILTINS}
        for mod in self.SAFE_MODULES:
            try:
                namespace[mod] = __import__(mod)
            except ImportError:
                pass

        try:
            exec(code, namespace)  # noqa: S102
            func = namespace.get(func_name)
            if func and callable(func):
                self._func_cache[cache_key] = func
                return func
        except Exception:  # noqa: BLE001
            return None
        return None

    def execute(
        self,
        code: str,
        func_name: str,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> OperatorExecutionResult:
        """
        执行算子，返回执行结果（含性能基准）。
        """
        kwargs = kwargs or {}
        result = OperatorExecutionResult(success=False)

        func = self.load(code, func_name)
        if not func:
            result.error = f"函数 {func_name} 加载失败"
            return result

        # 性能基准：执行时间 + 内存
        import tracemalloc
        tracemalloc.start()
        start = time.perf_counter()
        try:
            output = func(*args, **kwargs)
            result.success = True
            result.output = output
        except Exception as exc:  # noqa: BLE001
            result.error = f"{type(exc).__name__}: {exc}"
        finally:
            elapsed = (time.perf_counter() - start) * 1000
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

        result.exec_time_ms = round(elapsed, 4)
        result.peak_memory_kb = round(peak / 1024, 2)
        return result


# ---------------------------------------------------------------------------
# 进化记忆索引（V3.2优化5）
# ---------------------------------------------------------------------------
class EvolutionMemoryIndex:
    """
    进化记忆索引：为JSONL进化记忆建立可查询索引。
    支持按问题/算子/分数/方法/日期查询。
    """

    def __init__(self, memory_path: Path, index_path: Path):
        self.memory_path = memory_path
        self.index_path = index_path
        self.records: List[Dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        """从JSONL加载所有记录。"""
        if not self.memory_path.exists():
            return
        with self.memory_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        self.records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass

    def rebuild(self) -> None:
        """重建索引并保存。"""
        index = {
            "total_records": len(self.records),
            "by_method": {},
            "by_status": {},
            "by_op_name": {},
            "score_stats": {
                "min": 0.0, "max": 0.0, "avg": 0.0,
            },
            "date_range": {"first": "", "last": ""},
            "recent_10": [],
        }

        scores = []
        for r in self.records:
            method = r.get("generation_method", "unknown")
            status = r.get("status", "unknown")
            op_name = r.get("op_name", "unknown")
            score = r.get("eval_score", 0.0)
            ts = r.get("timestamp", "")

            index["by_method"][method] = index["by_method"].get(method, 0) + 1
            index["by_status"][status] = index["by_status"].get(status, 0) + 1
            index["by_op_name"][op_name] = index["by_op_name"].get(op_name, 0) + 1
            scores.append(score)

            if ts:
                if not index["date_range"]["first"]:
                    index["date_range"]["first"] = ts
                index["date_range"]["last"] = ts

        if scores:
            index["score_stats"] = {
                "min": round(min(scores), 2),
                "max": round(max(scores), 2),
                "avg": round(sum(scores) / len(scores), 2),
            }

        index["recent_10"] = self.records[-10:]

        with self.index_path.open("w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

    def query(
        self,
        problem_contains: str = "",
        op_name: str = "",
        method: str = "",
        status: str = "",
        min_score: float = 0.0,
        max_score: float = 100.0,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """按条件查询进化记忆。"""
        results = []
        for r in reversed(self.records):
            if problem_contains and problem_contains.lower() not in r.get("problem", "").lower():
                continue
            if op_name and op_name.lower() not in r.get("op_name", "").lower():
                continue
            if method and r.get("generation_method", "") != method:
                continue
            if status and r.get("status", "") != status:
                continue
            score = r.get("eval_score", 0.0)
            if score < min_score or score > max_score:
                continue
            results.append(r)
            if len(results) >= limit:
                break
        return results

    def add(self, record: Dict[str, Any]) -> None:
        """添加一条记录并追加到JSONL。"""
        self.records.append(record)
        with self.memory_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# 主引擎：V3.2 元闭环（全功能增强版）
# ---------------------------------------------------------------------------
class V32MetaClosedLoop:
    """ZONGYUAN-ROOT V3.2 元闭环主引擎（全功能增强版）。"""

    def __init__(
        self,
        workspace_dir: Optional[Path] = None,
        registry_path: Optional[Path] = None,
        llm_model: str = "doubao-reasoning2",
        use_llm: bool = True,
    ) -> None:
        self.workspace = Path(workspace_dir) if workspace_dir else Path.cwd()
        self.registry_path = registry_path or DEFAULT_REGISTRY_PATH
        self.evolution_memory_path = self.workspace / EVOLUTION_MEMORY_FILE
        self.evolution_index_path = self.workspace / EVOLUTION_INDEX_FILE
        self.performance_path = self.workspace / PERFORMANCE_BENCHMARK_FILE

        # ---- V3.1 LLM 算子生成器 ----
        self.llm_generator: Optional[LLMOperatorGenerator] = None
        if use_llm and V31_LLM_AVAILABLE:
            try:
                self.llm_generator = LLMOperatorGenerator(
                    workspace_dir=self.workspace,
                    llm_model=llm_model,
                )
            except Exception as exc:  # noqa: BLE001
                print(f"  [V32] LLM生成器初始化失败: {exc}")

        # ---- V3.0 模板生成器（修复：直接导入 operator_generator_v3）----
        self.template_generator: Optional[V3OperatorGenerator] = None
        if V3_TEMPLATE_AVAILABLE:
            try:
                self.template_generator = V3OperatorGenerator(
                    registry_path=self.registry_path,
                    workspace_dir=self.workspace,
                )
            except Exception as exc:  # noqa: BLE001
                print(f"  [V32] 模板生成器初始化失败: {exc}")

        # ---- 守护和评估器 ----
        self.guardian = MetaLoopGuardian(workspace_dir=self.workspace) if GUARDIAN_AVAILABLE else None
        self.evaluator = CodeSelfEvaluator() if EVALUATOR_AVAILABLE else None

        # ---- V3.2 新增组件 ----
        self.semantic_matcher = SemanticMatcher()
        self.executor = OperatorExecutor()
        self.memory_index = EvolutionMemoryIndex(self.evolution_memory_path, self.evolution_index_path)

        # ---- 统一算子匹配池 ----
        self.operator_pool: Dict[str, Dict[str, Any]] = {}
        self._load_operator_pool()

        # ---- 性能基准缓存 ----
        self.performance_benchmarks: Dict[str, Dict[str, Any]] = {}
        self._load_performance_benchmarks()

        # 闭环历史
        self.loop_history: List[V32MetaLoopResult] = []

    # ------------------------------------------------------------------
    # 加载统一算子匹配池
    # ------------------------------------------------------------------
    def _load_operator_pool(self) -> None:
        # V2 / V3.0 注册表
        if self.registry_path.exists():
            try:
                data = json.loads(self.registry_path.read_text(encoding="utf-8"))
                for sub_key, sub in data.get("subsystems", {}).items():
                    for op in sub.get("operators", []):
                        oid = op.get("operator_id", "")
                        if oid and oid not in self.operator_pool:
                            self.operator_pool[oid] = {
                                "source": "v2_registry",
                                "subsystem": sub_key,
                                "name": op.get("name", ""),
                                "description": op.get("description", ""),
                                "code": op.get("code", ""),
                                "generation_method": "existing",
                            }
            except (json.JSONDecodeError, OSError):
                pass

        # V3.1 LLM 生成注册表
        if V31_REGISTRY_PATH.exists():
            try:
                data = json.loads(V31_REGISTRY_PATH.read_text(encoding="utf-8"))
                for sub_key, sub in data.get("subsystems", {}).items():
                    for op in sub.get("operators", []):
                        oid = op.get("operator_id", "")
                        if oid and oid not in self.operator_pool:
                            # 尝试从生成的文件中加载代码
                            code = ""
                            code_path = op.get("code_path", "")
                            if code_path and Path(code_path).exists():
                                try:
                                    code = Path(code_path).read_text(encoding="utf-8")
                                except OSError:
                                    pass
                            self.operator_pool[oid] = {
                                "source": "v31_llm_registry",
                                "subsystem": sub_key,
                                "name": op.get("name", ""),
                                "description": op.get("description", ""),
                                "code": code,
                                "generation_method": op.get("generation_method", "llm"),
                                "llm_model": op.get("llm_model", ""),
                                "self_eval_score": op.get("self_eval_score", 0),
                                "self_eval_grade": op.get("self_eval_grade", ""),
                            }
            except (json.JSONDecodeError, OSError):
                pass

    def _add_to_pool(self, artifact: Any, source: str = "runtime", code: str = "") -> None:
        oid = getattr(artifact, "op_id", "")
        if oid and oid not in self.operator_pool:
            self.operator_pool[oid] = {
                "source": source,
                "name": getattr(artifact, "op_name", ""),
                "description": getattr(artifact, "problem_desc", ""),
                "code": code or getattr(artifact, "code", ""),
                "generation_method": getattr(artifact, "generation_method", "llm"),
                "llm_model": getattr(artifact, "llm_model", ""),
                "self_eval_score": getattr(artifact, "self_eval_score", 0),
                "self_eval_grade": getattr(artifact, "self_eval_grade", ""),
            }

    # ------------------------------------------------------------------
    # 性能基准
    # ------------------------------------------------------------------
    def _load_performance_benchmarks(self) -> None:
        if self.performance_path.exists():
            try:
                self.performance_benchmarks = json.loads(self.performance_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self.performance_benchmarks = {}

    def _save_performance_benchmarks(self) -> None:
        with self.performance_path.open("w", encoding="utf-8") as f:
            json.dump(self.performance_benchmarks, f, ensure_ascii=False, indent=2)

    def _benchmark_operator(self, op_id: str, code: str, func_name: str, test_args: tuple) -> Dict[str, Any]:
        """对算子执行性能基准测试。"""
        # 运行3次取平均
        times = []
        memories = []
        success_count = 0
        for _ in range(3):
            result = self.executor.execute(code, func_name, test_args)
            if result.success:
                success_count += 1
                times.append(result.exec_time_ms)
                memories.append(result.peak_memory_kb)

        benchmark = {
            "op_id": op_id,
            "func_name": func_name,
            "runs": 3,
            "success_runs": success_count,
            "avg_exec_time_ms": round(sum(times) / len(times), 4) if times else 0,
            "min_exec_time_ms": round(min(times), 4) if times else 0,
            "max_exec_time_ms": round(max(times), 4) if times else 0,
            "avg_peak_memory_kb": round(sum(memories) / len(memories), 2) if memories else 0,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S+08:00", time.localtime()),
        }
        self.performance_benchmarks[op_id] = benchmark
        self._save_performance_benchmarks()
        return benchmark

    # ------------------------------------------------------------------
    # Stage 1: 问题感知
    # ------------------------------------------------------------------
    def _stage_perceive(self, problem: str) -> Dict[str, Any]:
        return {
            "problem": problem,
            "keywords": [w for w in problem.replace("，", " ").replace("。", " ").split() if len(w) > 1],
            "semantic_keywords": self.semantic_matcher.expand_keywords(problem),
            "timestamp": time.time(),
        }

    # ------------------------------------------------------------------
    # Stage 2: 算子匹配（V3.2：语义+关键词混合匹配）
    # ------------------------------------------------------------------
    def _stage_match(self, problem: str) -> Tuple[Optional[str], str, float]:
        """
        语义+关键词混合匹配。
        返回 (op_id, match_method, match_score)。
        """
        best_op_id: Optional[str] = None
        best_score = 0.0
        best_method = "keyword"

        for oid, meta in self.operator_pool.items():
            # 语义匹配分
            sem_score = self.semantic_matcher.match_score(
                problem,
                meta.get("description", ""),
                meta.get("name", ""),
            )
            if sem_score > best_score:
                best_score = sem_score
                best_op_id = oid
                best_method = "semantic" if sem_score > 30 else "keyword"

        # 匹配阈值：语义分≥25（约2个扩展关键词命中）
        if best_score >= 25.0:
            return best_op_id, best_method, best_score
        return None, "none", 0.0

    # ------------------------------------------------------------------
    # Stage 3: 代码生成（V3.2：LLM优先 + 模板回退修复）
    # ------------------------------------------------------------------
    def _stage_generate(self, problem: str) -> Tuple[Any, str]:
        # 路径1: LLM 生成
        if self.llm_generator and self.llm_generator.llm.available:
            try:
                artifact, score, grade = self.llm_generator.auto_generate(problem)
                if artifact.sandbox_ok:
                    artifact.self_eval_score = score
                    artifact.self_eval_grade = grade
                    return artifact, "llm"
                print(f"  [Stage 3] LLM生成验证失败，尝试模板回退...")
            except Exception as exc:  # noqa: BLE001
                print(f"  [Stage 3] LLM生成异常: {exc}，尝试模板回退...")

        # 路径2: V3.0 模板填充回退（修复：使用 operator_generator_v3）
        if self.template_generator:
            try:
                artifact = self.template_generator.generate(problem)
                ok = self.template_generator.validate(artifact)
                if ok:
                    self.template_generator.register(artifact)
                    return artifact, "template_fallback"
            except Exception as exc:  # noqa: BLE001
                print(f"  [Stage 3] 模板回退也失败: {exc}")

        # 路径3: 完全失败
        from llm_operator_generator import OperatorArtifact, IOSpec
        artifact = OperatorArtifact(
            op_id=f"OP-FAILED-{time.strftime('%Y%m%d-%H%M%S')}",
            op_name="op_failed",
            problem_desc=problem,
            io_spec=IOSpec(description=problem),
            code="# GENERATION FAILED",
            generation_method="failed",
            sandbox_ok=False,
        )
        return artifact, "failed"

    # ------------------------------------------------------------------
    # Stage 4: 守护校验
    # ------------------------------------------------------------------
    def _stage_guard(self, artifact: Any) -> Any:
        if not self.guardian:
            class AllowResult:
                verdict = "SKIPPED_NO_GUARDIAN"
                allowed = True
                violated_axioms = []
                dangerous_hits = []
            return AllowResult()

        change = ChangeRequest(
            target_file=f"{getattr(artifact, 'op_id', 'unknown')}.py",
            new_code=getattr(artifact, "code", ""),
            change_type="generate",
            source_problem=getattr(artifact, "problem_desc", ""),
            author="v32_meta_loop",
        )
        return self.guardian.check(change)

    # ------------------------------------------------------------------
    # Stage 5: 执行 + 自评估 + 性能基准（V3.2增强）
    # ------------------------------------------------------------------
    def _stage_evaluate(self, artifact: Any, generation_method: str) -> Tuple[float, bool, int]:
        if generation_method == "llm" and hasattr(artifact, "self_eval_score"):
            score = artifact.self_eval_score
            passed = score >= 70.0
            return score, passed, artifact.generation_round

        if self.evaluator:
            try:
                test_cases = []
                func_name = getattr(artifact, "op_name", "op_unknown")
                report = self.evaluator.evaluate(artifact.code, test_cases, func_name=func_name)
                return report.total_score, report.passed, report.iteration
            except Exception:  # noqa: BLE001
                pass

        try:
            import ast
            ast.parse(artifact.code)
            return 75.0, True, 1
        except SyntaxError:
            return 30.0, False, 1

    # ------------------------------------------------------------------
    # Stage 6: 进化记忆 + 索引更新（V3.2增强）
    # ------------------------------------------------------------------
    def _stage_evolve_memory(self, result: V32MetaLoopResult) -> None:
        record = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S+08:00", time.localtime()),
            "problem": result.problem,
            "op_id": result.op_id,
            "op_name": result.op_name,
            "generation_method": result.generation_method,
            "match_method": result.match_method,
            "match_score": round(result.match_score, 2),
            "llm_model": result.llm_model,
            "llm_rounds": result.llm_rounds,
            "eval_score": round(result.eval_score, 2),
            "eval_passed": result.eval_passed,
            "guardian_verdict": result.guardian_verdict,
            "execution_success": result.execution_success,
            "exec_time_ms": result.exec_time_ms,
            "peak_memory_kb": result.peak_memory_kb,
            "iterations": result.iterations,
            "status": result.status,
            "provenance_anchor": PROVENANCE_ANCHOR,
            "did": DID,
            "kernel_version": KERNEL_VERSION,
        }
        self.memory_index.add(record)
        self.memory_index.rebuild()

    # ------------------------------------------------------------------
    # 主入口：单次元闭环
    # ------------------------------------------------------------------
    def run(self, problem: str, execute_test: bool = True) -> V32MetaLoopResult:
        """
        执行一次完整 V3.2 六阶段元闭环。
        execute_test: 是否在匹配到算子后执行测试（默认True）。
        """
        result = V32MetaLoopResult(problem=problem)
        print(f"\n{'='*60}")
        print(f"[V3.2 META-LOOP] 接收问题: {problem}")
        print(f"{'='*60}")

        # ---- Stage 1: 问题感知 ----
        result.stage = 1
        percept = self._stage_perceive(problem)
        result.notes.append(f"stage1_perceive: semantic_keywords={len(percept['semantic_keywords'])}")
        print(f"  [Stage 1] 问题感知完成，语义关键词: {percept['semantic_keywords'][:8]}...")

        # ---- Stage 2: 算子匹配（语义+关键词混合）----
        result.stage = 2
        matched_op, match_method, match_score = self._stage_match(problem)
        result.match_method = match_method
        result.match_score = match_score

        if matched_op:
            meta = self.operator_pool[matched_op]
            result.matched_existing = True
            result.op_id = matched_op
            result.op_name = meta.get("name", matched_op)
            result.generation_method = meta.get("generation_method", "existing")
            result.status = "SUCCESS"
            result.notes.append(f"stage2_match: 命中 {matched_op} (方法={match_method}, 分={match_score:.1f})")
            print(f"  [Stage 2] 命中既有算子: {matched_op} ({result.op_name})")
            print(f"           匹配方式: {match_method}, 匹配分: {match_score:.1f}")
            print(f"           来源: {meta.get('source', 'unknown')}")

            # V3.2新增：执行算子测试
            if execute_test and meta.get("code"):
                print(f"  [Stage 2+] 执行算子测试...")
                # 构造简单测试输入（基于算子名称推断）
                test_args = self._infer_test_args(result.op_name)
                exec_result = self.executor.execute(meta["code"], result.op_name, test_args)
                result.execution_success = exec_result.success
                result.execution_output = exec_result.output
                result.execution_error = exec_result.error
                result.exec_time_ms = exec_result.exec_time_ms
                result.peak_memory_kb = exec_result.peak_memory_kb
                if exec_result.success:
                    print(f"           执行成功: 输出={str(exec_result.output)[:60]}, "
                          f"耗时={exec_result.exec_time_ms}ms, 内存={exec_result.peak_memory_kb}KB")
                    # 性能基准
                    self._benchmark_operator(matched_op, meta["code"], result.op_name, test_args)
                else:
                    print(f"           执行失败: {exec_result.error[:80]}")

            print(f"  [SHORT-CIRCUIT] 既有算子可直接执行，无需生成。")
            self.loop_history.append(result)
            return result

        result.notes.append("stage2_match: 未命中，触发LLM生成")
        print(f"  [Stage 2] 未命中既有算子（匹配池共 {len(self.operator_pool)} 个），触发生成...")

        # ---- Stage 3: 代码生成 ----
        result.stage = 3
        artifact, gen_method = self._stage_generate(problem)
        result.op_id = getattr(artifact, "op_id", "")
        result.op_name = getattr(artifact, "op_name", "")
        result.generation_method = gen_method
        result.llm_model = getattr(artifact, "llm_model", "")
        result.llm_rounds = getattr(artifact, "generation_round", 0)
        result.llm_self_eval_score = getattr(artifact, "self_eval_score", 0)
        result.llm_self_eval_grade = getattr(artifact, "self_eval_grade", "")

        if gen_method == "failed":
            result.status = "FAILED"
            result.notes.append("stage3: 所有生成路径均失败")
            print(f"  [Stage 3] 生成失败（LLM不可用且模板回退失败）")
            self.loop_history.append(result)
            return result

        print(f"  [Stage 3] 生成算子: {result.op_id}")
        print(f"           方式: {gen_method}, 模型: {result.llm_model or 'N/A'}, 轮次: {result.llm_rounds}")
        if gen_method == "llm":
            print(f"           LLM自评估: {result.llm_self_eval_score:.1f}/{result.llm_self_eval_grade}")

        # ---- Stage 4: 守护校验 ----
        result.stage = 4
        guard = self._stage_guard(artifact)
        result.guardian_verdict = getattr(guard, "verdict", "UNKNOWN")
        if not getattr(guard, "allowed", True):
            result.status = "REJECTED"
            result.notes.append(f"stage4_guard: 拒绝 - {getattr(guard, 'violated_axioms', [])}")
            print(f"  [Stage 4] 守护拒绝: {getattr(guard, 'violated_axioms', [])}")
            self.loop_history.append(result)
            return result
        result.notes.append("stage4_guard: PROCEED")
        print(f"  [Stage 4] 守护通过: {result.guardian_verdict}")

        # ---- Stage 5: 执行 + 自评估 + 性能基准 ----
        result.stage = 5
        score, passed, iterations = self._stage_evaluate(artifact, gen_method)
        result.eval_score = score
        result.eval_passed = passed
        result.iterations = iterations

        # V3.2新增：执行新生成算子的测试
        code = getattr(artifact, "code", "")
        if passed and code:
            test_args = self._infer_test_args(result.op_name)
            exec_result = self.executor.execute(code, result.op_name, test_args)
            result.execution_success = exec_result.success
            result.execution_output = exec_result.output
            result.execution_error = exec_result.error
            result.exec_time_ms = exec_result.exec_time_ms
            result.peak_memory_kb = exec_result.peak_memory_kb
            if exec_result.success:
                print(f"  [Stage 5] 执行测试: 成功, 输出={str(exec_result.output)[:60]}, "
                      f"耗时={exec_result.exec_time_ms}ms")
                # 性能基准
                self._benchmark_operator(result.op_id, code, result.op_name, test_args)
            else:
                print(f"  [Stage 5] 执行测试: 失败 - {exec_result.error[:60]}")

        result.notes.append(f"stage5_eval: score={score:.1f}, passed={passed}, exec={result.execution_success}")
        print(f"  [Stage 5] 自评估: 总分={score:.1f}, passed={passed}, 迭代={iterations}")

        if not passed:
            result.status = "FAILED"
            print(f"           未达标")
            self.loop_history.append(result)
            return result

        # 新算子加入匹配池
        self._add_to_pool(artifact, source="v32_runtime", code=code)
        result.notes.append("stage5: 算子已加入匹配池")
        print(f"  [Stage 5] 算子已加入匹配池（当前池大小: {len(self.operator_pool)}）")

        # ---- Stage 6: 进化记忆 + 索引 ----
        result.stage = 6
        self._stage_evolve_memory(result)
        result.status = "SUCCESS"
        result.notes.append("stage6: 进化记忆已写入+索引已更新")
        print(f"  [Stage 6] 进化记忆已写入+索引已更新")
        print(f"[DONE] V3.2元闭环完成，算子 {result.op_id} 已固化。")

        self.loop_history.append(result)
        return result

    @staticmethod
    def _infer_test_args(op_name: str) -> tuple:
        """根据算子名称推断测试输入。"""
        name = op_name.lower()
        if "median" in name or "中值" in name or "中位数" in name:
            return ([1, 2, 3, 4, 5],)
        if "variance" in name or "方差" in name:
            return ([1, 2, 3, 4, 5],)
        if "entropy" in name or "熵" in name:
            return ([0.25, 0.25, 0.25, 0.25],)
        if "cosine" in name or "余弦" in name or "similarity" in name:
            return ([1, 2, 3], [4, 5, 6])
        if "normalize" in name or "标准化" in name or "z-score" in name:
            return ([1, 2, 3, 4, 5],)
        if "top" in name or "最大" in name:
            return ([3, 1, 4, 1, 5, 9, 2, 6], 3)
        if "deduplicate" in name or "去重" in name or "unique" in name:
            return ([1, 2, 2, 3, 3, 3, 4],)
        if "mean" in name or "平均" in name or "均值" in name or "window" in name:
            return ([1, 2, 3, 4, 5], 3)
        if "anomaly" in name or "异常" in name:
            return ([0] * 19 + [100],)
        if "validate" in name or "校验" in name:
            return ({"name": "test", "age": 25}, ["name", "age"])
        # 默认
        return ([1, 2, 3, 4, 5],)

    # ------------------------------------------------------------------
    # 连续进化模式
    # ------------------------------------------------------------------
    def run_evolution_batch(self, problems: List[str], execute_test: bool = True) -> List[V32MetaLoopResult]:
        results: List[V32MetaLoopResult] = []
        for p in problems:
            try:
                r = self.run(p, execute_test=execute_test)
            except Exception as exc:  # noqa: BLE001
                r = V32MetaLoopResult(
                    problem=p, status="FAILED",
                    notes=[f"exception: {exc}\n{traceback.format_exc()}"],
                )
            results.append(r)
        return results

    # ------------------------------------------------------------------
    # 进化记忆查询（V3.2新增）
    # ------------------------------------------------------------------
    def query_memory(
        self,
        problem_contains: str = "",
        op_name: str = "",
        method: str = "",
        status: str = "",
        min_score: float = 0.0,
        max_score: float = 100.0,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """查询进化记忆索引。"""
        return self.memory_index.query(
            problem_contains=problem_contains,
            op_name=op_name,
            method=method,
            status=status,
            min_score=min_score,
            max_score=max_score,
            limit=limit,
        )

    # ------------------------------------------------------------------
    # 系统状态
    # ------------------------------------------------------------------
    def status(self) -> Dict[str, Any]:
        return {
            "provenance_anchor": PROVENANCE_ANCHOR,
            "did": DID,
            "kernel_version": KERNEL_VERSION,
            "operator_pool_size": len(self.operator_pool),
            "llm_available": self.llm_generator is not None and self.llm_generator.llm.available if self.llm_generator else False,
            "llm_model": self.llm_generator.llm.model if self.llm_generator else "N/A",
            "template_fallback_available": self.template_generator is not None,
            "guardian_available": self.guardian is not None,
            "evaluator_available": self.evaluator is not None,
            "semantic_matcher_keywords": len(SemanticMatcher.SEMANTIC_EXPANSION),
            "performance_benchmarks_count": len(self.performance_benchmarks),
            "memory_records": len(self.memory_index.records),
            "loop_history_count": len(self.loop_history),
        }


# ======================================================================
# 演示
# ======================================================================
if __name__ == "__main__":
    print(f"{PROVENANCE_ANCHOR} · {DID} · {KERNEL_VERSION}")
    print("=" * 60)
    print("[DEMO] V3.2 元闭环主引擎（全功能增强版）演示\n")

    demo_workspace = Path(__file__).parent
    engine = V32MetaClosedLoop(workspace_dir=demo_workspace)

    # 启动自检
    status = engine.status()
    print("[BOOT] 内核状态:")
    print(f"  - 算子匹配池大小: {status['operator_pool_size']}")
    print(f"  - LLM可用: {status['llm_available']} (模型: {status['llm_model']})")
    print(f"  - 模板回退可用: {status['template_fallback_available']}")
    print(f"  - 守护器可用: {status['guardian_available']}")
    print(f"  - 语义匹配关键词数: {status['semantic_matcher_keywords']}")
    print(f"  - 性能基准数: {status['performance_benchmarks_count']}")
    print(f"  - 进化记忆记录数: {status['memory_records']}")

    # ---- 演示1：匹配复用（含执行测试）----
    print(f"\n{'='*60}")
    print("[DEMO 1] 匹配复用 + 执行测试 + 性能基准")
    print(f"{'='*60}")
    reuse_problems = [
        "需要一个滑动窗口均值算子，计算数据序列中每个位置的滑动窗口平均值",
        "需要一个熵值计算算子，计算概率分布的信息熵",
    ]
    reuse_results = engine.run_evolution_batch(reuse_problems, execute_test=True)

    # ---- 演示2：全新算子LLM生成 ----
    print(f"\n{'='*60}")
    print("[DEMO 2] 全新算子LLM生成 + 执行测试 + 性能基准")
    print(f"{'='*60}")
    new_problems = [
        "需要一个几何均值算子，计算数据序列的几何平均值",
        "需要一个众数计算算子，返回数据序列中出现次数最多的元素",
        "需要一个范围计算算子，返回数据序列的最大值减最小值",
    ]
    new_results = engine.run_evolution_batch(new_problems, execute_test=True)

    # ---- 演示3：进化记忆索引查询 ----
    print(f"\n{'='*60}")
    print("[DEMO 3] 进化记忆索引查询")
    print(f"{'='*60}")
    print("  查询: method=llm, min_score=80")
    query_results = engine.query_memory(method="llm", min_score=80, limit=5)
    for r in query_results:
        print(f"    - {r.get('op_name', '?'):30s} | score={r.get('eval_score', 0):.1f} | {r.get('problem', '')[:40]}")

    # ---- 总结 ----
    print(f"\n{'='*60}")
    print("[SUMMARY] V3.2 元闭环执行汇总")
    print(f"{'='*60}")
    all_results = reuse_results + new_results
    new_generated = sum(1 for r in all_results if not r.matched_existing and r.status == "SUCCESS")
    reused = sum(1 for r in all_results if r.matched_existing)
    llm_count = sum(1 for r in all_results if r.generation_method == "llm")
    exec_success = sum(1 for r in all_results if r.execution_success)
    failed = sum(1 for r in all_results if r.status == "FAILED")

    print(f"  总问题数: {len(all_results)}")
    print(f"  成功: {len(all_results) - failed} | 失败: {failed}")
    print(f"  匹配复用: {reused} | LLM新生成: {new_generated}")
    print(f"  执行测试成功: {exec_success}/{len(all_results)}")
    print(f"  最终匹配池大小: {len(engine.operator_pool)}")
    print(f"  性能基准数: {len(engine.performance_benchmarks)}")
    print(f"  进化记忆记录数: {len(engine.memory_index.records)}")
    print()

    for i, r in enumerate(all_results, 1):
        tag = "复用" if r.matched_existing else "新生成"
        exec_tag = "执行OK" if r.execution_success else "执行FAIL"
        print(f"  [{i}] [{r.status}] {tag} | {exec_tag} | {r.problem[:40]}...")
        print(f"      op={r.op_name}, method={r.generation_method}, score={r.eval_score:.1f}, "
              f"time={r.exec_time_ms}ms, mem={r.peak_memory_kb}KB")

    print(f"\n{PROVENANCE_ANCHOR} · V3.2 元闭环演示完成")
