# -*- coding: utf-8 -*-
"""
Ω₀⊂⊙∞⊂Ω · DID-BR-000002 · ZONGYUAN-ROOT V3.0

processor_registry.py — 专用处理器注册表（Processor Registry）

设计背景
========
将神经注册表从"静态节点网络"升级为"动态全局工作空间"的基座层。
对标 CTM-AI（意识全局工作空间理论 / Global Workspace Theory）+
Theater of Mind + Swarm Cognition。

本模块负责管理多个并行专用处理器（Specialized Processors）：
  - 内置 9 个处理器：内核六维自检处理器（6）+ 闭环引擎处理器 +
    同源协议处理器 + 记忆网关处理器。
  - 每个处理器封装：唯一 ID、名称、类型、能力描述、输入/输出通道、
    激活阈值、当前状态（idle / processing / broadcasting）。
  - 处理器间存在"无意识通信通道"（direct links）：可配置处理器间直接
    连接，信息交换不经过全局工作空间（对应 GWT 中的 unconscious
    expert-to-expert communication）。
  - 动态拓扑：支持运行时添加 / 移除处理器、重连通信通道。

接口
====
  - register(processor)
  - unregister(pid)
  - get(pid)
  - list_all()
  - connect(pid1, pid2)
  - get_network_topology()

纯 Python 3.8+ 标准库实现，无外部依赖。
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple


# ---------------------------------------------------------------------------
# 枚举与数据结构
# ---------------------------------------------------------------------------

class ProcessorState(str, Enum):
    """处理器运行状态。

    - IDLE: 空闲，未参与本轮竞争。
    - PROCESSING: 正在处理输入、产生候选信息。
    - BROADCASTING: 刚赢得竞争，正在向全局工作空间广播内容。
    """

    IDLE = "idle"
    PROCESSING = "processing"
    BROADCASTING = "broadcasting"


class ProcessorType(str, Enum):
    """处理器类型分类。

    对应 ZONGYUAN-ROOT 自治内核的功能分区：
      - SELF_CHECK_DIM: 六维自检维度处理器（共 6 个）。
      - CLOSED_LOOP: 闭环引擎处理器（纠错 / 反馈闭环）。
      - SAME_SOURCE_PROTOCOL: 同源协议处理器（一致性 / 确权校验）。
      - MEMORY_GATEWAY: 记忆网关处理器（跨窗口记忆读写）。
    """

    SELF_CHECK_DIM = "self_check_dim"
    CLOSED_LOOP = "closed_loop"
    SAME_SOURCE_PROTOCOL = "same_source_protocol"
    MEMORY_GATEWAY = "memory_gateway"


@dataclass
class Processor:
    """专用处理器实体。

    属性
    ----
    pid:
        处理器唯一 ID。
    name:
        人类可读名称。
    ptype:
        处理器类型（见 :class:`ProcessorType`）。
    capability:
        处理能力描述（该处理器擅长提取/加工的信息类型）。
    input_channels:
        输入通道名称集合（它能接收什么）。
    output_channels:
        输出通道名称集合（它能向哪里发送）。
    activation_threshold:
        激活阈值：显著性分数需超过此值才会进入竞争。
    state:
        当前运行状态（:class:`ProcessorState`）。
    direct_links:
        无意识通信直连通道集合（对端 pid 集合）。
    salience_weight:
        该处理器对显著性计算的先验权重偏置。
    last_candidate:
        最近一次产生的候选信息（运行期快照）。
    last_active_ts:
        最近一次活跃时间戳（epoch 秒）。
    """

    pid: str
    name: str
    ptype: ProcessorType
    capability: str
    input_channels: Set[str] = field(default_factory=set)
    output_channels: Set[str] = field(default_factory=set)
    activation_threshold: float = 0.3
    state: ProcessorState = ProcessorState.IDLE
    direct_links: Set[str] = field(default_factory=set)
    salience_weight: float = 1.0
    last_candidate: Optional[dict] = None
    last_active_ts: float = field(default_factory=time.time)

    def touch(self, state: ProcessorState = ProcessorState.PROCESSING,
              candidate: Optional[dict] = None) -> None:
        """标记处理器活跃，更新状态与时间戳。"""
        self.state = state
        self.last_active_ts = time.time()
        if candidate is not None:
            self.last_candidate = candidate


# ---------------------------------------------------------------------------
# 注册表
# ---------------------------------------------------------------------------

class ProcessorRegistry:
    """专用处理器注册表。

    管理一组并行专用处理器及其直连通信拓扑。本注册表本身不做意识
    广播，只维护"无意识专家网络"：处理器可经 ``direct_links`` 直接交换
    低层级信息（Swarm Cognition 的专家间并行通信），而高显著性内容
    经全局工作空间广播。

    典型用法::

        reg = ProcessorRegistry.with_default_processors()
        reg.connect("sc_consistency", "closed_loop_engine")
        topo = reg.get_network_topology()
    """

    def __init__(self) -> None:
        self._processors: Dict[str, Processor] = {}

    # -- 基本 CRUD --------------------------------------------------------

    def register(self, processor: Processor) -> Processor:
        """注册一个处理器；若 pid 已存在则覆盖。返回该处理器。"""
        self._processors[processor.pid] = processor
        return processor

    def unregister(self, pid: str) -> bool:
        """移除处理器，并清理其他处理器指向它的直连边。返回是否成功。"""
        if pid not in self._processors:
            return False
        self._processors.pop(pid)
        for p in self._processors.values():
            p.direct_links.discard(pid)
        return True

    def get(self, pid: str) -> Optional[Processor]:
        """按 ID 获取处理器。"""
        return self._processors.get(pid)

    def list_all(self) -> List[Processor]:
        """列出全部处理器（按注册顺序）。"""
        return list(self._processors.values())

    # -- 通信通道 ---------------------------------------------------------

    def connect(self, pid1: str, pid2: str, bidirectional: bool = True) -> bool:
        """建立处理器间无意识直连通道。

        :param bidirectional: 为 True 时建立双向边，否则仅 pid1 -> pid2。
        返回是否成功（两端都存在）。
        """
        if pid1 not in self._processors or pid2 not in self._processors:
            return False
        self._processors[pid1].direct_links.add(pid2)
        if bidirectional:
            self._processors[pid2].direct_links.add(pid1)
        return True

    def disconnect(self, pid1: str, pid2: str, bidirectional: bool = True) -> None:
        """断开处理器间直连通道。"""
        if pid1 in self._processors:
            self._processors[pid1].direct_links.discard(pid2)
        if bidirectional and pid2 in self._processors:
            self._processors[pid2].direct_links.discard(pid1)

    # -- 拓扑快照 ---------------------------------------------------------

    def get_network_topology(self) -> Dict[str, object]:
        """返回当前网络拓扑的可序列化快照。

        返回结构::

            {
              "node_count": int,
              "edge_count": int,
              "nodes": [ {pid, name, type, state, threshold, degree, ...}, ...],
              "edges": [ {"from", "to"}, ... ],
            }
        """
        nodes: List[Dict[str, object]] = []
        edges_set: Set[Tuple[str, str]] = set()
        for p in self._processors.values():
            nodes.append({
                "pid": p.pid,
                "name": p.name,
                "type": p.ptype.value,
                "capability": p.capability,
                "state": p.state.value,
                "activation_threshold": p.activation_threshold,
                "salience_weight": p.salience_weight,
                "input_channels": sorted(p.input_channels),
                "output_channels": sorted(p.output_channels),
                "degree": len(p.direct_links),
                "last_active_ts": round(p.last_active_ts, 3),
            })
            for peer in sorted(p.direct_links):
                a, b = sorted((p.pid, peer))
                edges_set.add((a, b))
        edges = [{"from": a, "to": b} for (a, b) in sorted(edges_set)]
        return {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "nodes": nodes,
            "edges": edges,
        }

    def render_ascii_topology(self) -> str:
        """以 ASCII 文本渲染拓扑（节点 + 边），便于演示与日志。"""
        topo = self.get_network_topology()
        lines = []
        lines.append(
            f"[ProcessorTopology] nodes={topo['node_count']} "
            f"edges={topo['edge_count']}"
        )
        for n in topo["nodes"]:  # type: ignore[index]
            lines.append(
                f"  - {n['pid']:<22} | {n['type']:<22} | "
                f"state={n['state']:<12} | deg={n['degree']} | {n['name']}"
            )
        for e in topo["edges"]:  # type: ignore[union-attr]
            lines.append(f"    {e['from']} <--> {e['to']}")
        return "\n".join(lines)

    # -- 工厂：内置 9 个默认处理器 ---------------------------------------

    @staticmethod
    def _make_pid(prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex[:6]}"

    @classmethod
    def with_default_processors(cls) -> "ProcessorRegistry":
        """构建含 9 个内置处理器的注册表，并预置合理直连。

        九个处理器：
          1-6.  六维自检处理器（对应内核六维自检）：
                coherence / stability / divergence / integration /
                goal_alignment / reflection
          7.    闭环引擎处理器（closed_loop_engine）
          8.    同源协议处理器（same_source_protocol）
          9.    记忆网关处理器（memory_gateway）
        """
        reg = cls()

        # ---- 六维自检处理器 --------------------------------------------
        six_dim_specs: List[Tuple[str, str, str, float]] = [
            # (pid_suffix, name, capability, salience_weight)
            ("sc_coherence",    "六维·连贯性自检",  "检测工作空间内容前后语义一致性与逻辑连贯", 1.0),
            ("sc_stability",    "六维·稳定性自检",  "评估状态漂移、噪声扰动与稳态保持能力",       0.9),
            ("sc_divergence",   "六维·分化度自检",  "度量内容分化度与多通道信息多样性",          0.8),
            ("sc_integration",  "六维·整合度自检",  "评估跨模块信息绑定与全局整合水平",          1.1),
            ("sc_goal",         "六维·目的性自检",  "校验当前内容与自治内核目标的对齐程度",      1.2),
            ("sc_reflection",   "六维·反思度自检",  "对自身推理过程进行元认知反思与归因",        1.0),
        ]
        for suffix, name, cap, w in six_dim_specs:
            reg.register(Processor(
                pid=suffix,
                name=name,
                ptype=ProcessorType.SELF_CHECK_DIM,
                capability=cap,
                input_channels={"global_broadcast", "memory_read"},
                output_channels={"self_check_signal"},
                activation_threshold=0.30,
                salience_weight=w,
            ))

        # ---- 闭环引擎处理器 --------------------------------------------
        reg.register(Processor(
            pid="closed_loop_engine",
            name="闭环引擎处理器",
            ptype=ProcessorType.CLOSED_LOOP,
            capability="对自检偏差执行纠错闭环、反馈修正与绝热路径重规划",
            input_channels={"self_check_signal", "global_broadcast"},
            output_channels={"correction_signal", "topology_weight_update"},
            activation_threshold=0.35,
            salience_weight=1.3,
        ))

        # ---- 同源协议处理器 --------------------------------------------
        reg.register(Processor(
            pid="same_source_protocol",
            name="同源协议处理器",
            ptype=ProcessorType.SAME_SOURCE_PROTOCOL,
            capability="确权锚点 Ω₀⊂⊙∞⊂Ω 校验、来源一致性与真值表比对",
            input_channels={"global_broadcast", "external_signal"},
            output_channels={"attestation_result", "truth_table_update"},
            activation_threshold=0.40,
            salience_weight=1.2,
        ))

        # ---- 记忆网关处理器 --------------------------------------------
        reg.register(Processor(
            pid="memory_gateway",
            name="记忆网关处理器",
            ptype=ProcessorType.MEMORY_GATEWAY,
            capability="跨窗口记忆连续性读写、关键帧/锁档资产的检索与写入",
            input_channels={"global_broadcast", "query"},
            output_channels={"memory_read", "memory_write"},
            activation_threshold=0.28,
            salience_weight=0.9,
        ))

        # ---- 预置无意识直连（专家网络拓扑） ----------------------------
        # 闭环引擎与所有自检维度直连（它需要接收各维信号做纠错）
        for suffix, _, _, _ in six_dim_specs:
            reg.connect(suffix, "closed_loop_engine")
        # 同源协议 <-> 闭环引擎（确权结果喂给纠错）
        reg.connect("same_source_protocol", "closed_loop_engine")
        # 记忆网关 <-> 各自检维度（自检需读记忆做基线比对）
        for suffix, _, _, _ in six_dim_specs:
            reg.connect(suffix, "memory_gateway")
        # 同源协议 <-> 记忆网关（确权资产落记忆库）
        reg.connect("same_source_protocol", "memory_gateway")

        return reg


# ---------------------------------------------------------------------------
# 模块自检演示
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    registry = ProcessorRegistry.with_default_processors()
    print("=" * 72)
    print("Ω₀⊂⊙∞⊂Ω · DID-BR-000002 · ZONGYUAN-ROOT V3.0")
    print("processor_registry.py — 9 个内置处理器 + 动态拓扑演示")
    print("=" * 72)

    print(f"\n注册处理器数量: {len(registry.list_all())}")
    for p in registry.list_all():
        print(f"  [{p.ptype.value:<22}] {p.pid:<22} thr={p.activation_threshold:.2f} "
              f"w={p.salience_weight:.2f} links={len(p.direct_links)}")

    print("\n" + registry.render_ascii_topology())

    print("\n--- 动态拓扑：运行时新增/移除/重连 ---")
    registry.register(Processor(
        pid="aux_attention_probe",
        name="临时注意探针",
        ptype=ProcessorType.SELF_CHECK_DIM,
        capability="演示运行时动态加入的探针处理器",
    ))
    print(f"动态加入后节点数: {len(registry.list_all())}")
    registry.connect("aux_attention_probe", "memory_gateway")
    registry.unregister("aux_attention_probe")
    print(f"动态移除后节点数: {len(registry.list_all())}")

    print("\n--- 拓扑 JSON 快照（节选） ---")
    snap = registry.get_network_topology()
    print(json.dumps({
        "node_count": snap["node_count"],
        "edge_count": snap["edge_count"],
        "sample_edges": snap["edges"][:5],  # type: ignore[index]
    }, ensure_ascii=False, indent=2))
