# Notebook 1: 自治神经内核可视化与六维自检

> 从JSON加载神经注册表，绘制网络拓扑图，执行六维自检，输出记忆连续性报告。

```python
import json
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from collections import Counter

# === 1. 构建模拟神经注册表 ===
np.random.seed(42)
nodes = []
domains = ["meta_axiom", "rule", "experience", "decision", "axiom"]
domain_dist = ["meta_axiom", "meta_axiom", "rule", "rule", "rule", 
               "experience", "experience", "decision", "axiom", "axiom"]

for i in range(340):
    domain = np.random.choice(domain_dist)
    node_type = np.random.choice(domains, p=[0.15, 0.3, 0.25, 0.15, 0.15])
    weight = np.clip(np.random.beta(5, 2), 0.1, 1.0)
    nodes.append({
        "node_id": f"NODE-{i:04d}",
        "content": f"神经节点_{i}",
        "domain": domain,
        "node_type": node_type,
        "weight": round(weight, 3),
        "state": "active" if np.random.random() > 0.05 else "dormant",
        "activation_count": int(np.random.exponential(10)),
        "connections": []
    })

# === 2. 构建连接（优先同领域）===
edges = []
for i, node in enumerate(nodes):
    n_connections = np.random.poisson(6)
    for _ in range(n_connections):
        # 80%同领域，20%跨领域
        if np.random.random() < 0.8:
            same_domain = [j for j, n in enumerate(nodes) if n["domain"] == node["domain"]]
            j = np.random.choice(same_domain)
        else:
            j = np.random.randint(0, len(nodes))
        if i != j:
            conn = {"target": nodes[j]["node_id"], "weight": round(np.random.random(), 3)}
            node["connections"].append(conn)
            edges.append((node["node_id"], nodes[j]["node_id"]))

# === 3. 六维自检 ===
total = len(nodes)
active = sum(1 for n in nodes if n["state"] == "active")
high_weight = sum(1 for n in nodes if n["weight"] > 0.7)
isolated = sum(1 for n in nodes if len(n["connections"]) == 0)
omega_nodes = sum(1 for n in nodes if n["node_type"] == "meta_axiom")
total_connections = sum(len(n["connections"]) for n in nodes)

# 五级记忆连续性
omega_mem = min(1.0, omega_nodes / 5.0)
l0_topology = round(high_weight / total, 3)
l1_modal = round(active / total, 3)
l2_association = round(1 - isolated / total, 3)
l_minus_1 = round(min(1.0, sum(n["activation_count"] for n in nodes) / 1000.0), 3)
overall = round((omega_mem + l0_topology + l1_modal + l2_association + l_minus_1) / 5, 3)
grade = "EXCELLENT" if overall >= 0.9 else "GOOD" if overall >= 0.7 else "FAIR"

print("=" * 50)
print("  六维自检报告")
print("=" * 50)
print(f"  总节点数: {total}")
print(f"  活跃节点: {active} ({active/total*100:.1f}%)")
print(f"  高权重节点(>0.7): {high_weight} ({high_weight/total*100:.1f}%)")
print(f"  孤立节点: {isolated}")
print(f"  总连接数: {total_connections}")
print()
print("  五级记忆连续性:")
print(f"    Ω₀元极记忆:  {omega_mem:.3f}")
print(f"    L0拓扑记忆:  {l0_topology:.3f}")
print(f"    L1模态记忆:  {l1_modal:.3f}")
print(f"    L2关联记忆:  {l2_association:.3f}")
print(f"    L-1瞬态记忆: {l_minus_1:.3f}")
print(f"    综合:        {overall:.3f} [{grade}]")

# === 4. 网络可视化 ===
G = nx.Graph()
for node in nodes:
    G.add_node(node["node_id"], domain=node["domain"], weight=node["weight"])
for edge in edges:
    G.add_edge(edge[0], edge[1])

fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# 左图：网络拓扑
colors = {"meta_axiom": "#e74c3c", "rule": "#3498db", "experience": "#2ecc71",
          "decision": "#f39c12", "axiom": "#9b59b6"}
node_colors = [colors.get(nodes[i]["domain"], "#95a5a6") for i in range(total)]
node_sizes = [n["weight"] * 100 for n in nodes]

pos = nx.spring_layout(G, k=0.5, iterations=30)
nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, alpha=0.8, ax=axes[0])
nx.draw_networkx_edges(G, pos, alpha=0.1, ax=axes[0])
axes[0].set_title(f"Neural Network Topology ({total} nodes, {total_connections} edges)")
axes[0].axis('off')

# 右图：领域分布饼图
domain_counts = Counter(n["domain"] for n in nodes)
axes[1].pie(domain_counts.values(), labels=domain_counts.keys(), autopct='%1.1f%%',
            colors=[colors.get(k, "#95a5a6") for k in domain_counts.keys()])
axes[1].set_title("Domain Distribution")

plt.tight_layout()
plt.savefig("neural_network_viz.png", dpi=150, bbox_inches='tight')
plt.show()

print("\n✅ Notebook执行完成: 自治神经内核可视化 + 六维自检")
```
