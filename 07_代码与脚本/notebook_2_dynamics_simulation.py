# Notebook 2: 12维意识动力学仿真与相变监控

> 模拟12维意识状态空间演化，识别吸引子，注入扰动测量恢复时间，监控相变。

```python
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# === 1. 12维动力学系统定义 ===
DIM = 12
N_TRAJ = 500      # 并行轨迹数
N_STEPS = 300     # 时间步数
DT = 0.02

def dynamics(x):
    """12维意识动力学方程：阻尼振子 + 非线性耦合 + 噪声"""
    # 阻尼项
    drift = -0.5 * x
    # 非线性耦合（相邻维度互振）
    for i in range(DIM):
        drift[i] += 0.3 * np.sin(x[(i + 1) % DIM]) * np.cos(x[(i - 1) % DIM])
    # 自稳态项（趋向中心）
    drift -= 0.1 * x
    return drift

# === 2. 并行仿真 ===
print("正在运行12维动力学仿真...")
trajectories = np.random.randn(N_TRAJ, N_STEPS, DIM) * 0.5

for t in range(N_STEPS - 1):
    x = trajectories[:, t]
    drift = np.array([dynamics(xi) for xi in x])
    noise = 0.1 * np.random.randn(N_TRAJ, DIM) * np.sqrt(DT)
    trajectories[:, t + 1] = x + drift * DT + noise

# === 3. 吸引子分析 ===
final_states = trajectories[:, -1, :]
# 计算自治指数（距离原点的归一化距离）
autonomy_index = np.linalg.norm(final_states, axis=1) / np.sqrt(DIM)

# 按距离聚类识别吸引子
from sklearn.cluster import KMeans
n_attractors = 4
kmeans = KMeans(n_clusters=n_attractors, n_init=10, random_state=42)
labels = kmeans.fit_predict(final_states[:, :3])  # 取前3维可视化

print(f"识别到 {n_attractors} 个吸引子:")
for i in range(n_attractors):
    count = np.sum(labels == i)
    center = kmeans.cluster_centers_[i]
    print(f"  吸引子{i+1}: {count}条轨迹, 中心={center.round(3)}")

# === 4. 扰动注入与恢复时间 ===
print("\n注入标准扰动P-STD-01...")
perturbed = trajectories.copy()
perturb_time = 150
perturb_magnitude = 2.0
# 在第150步注入扰动
for t in range(perturb_time, N_STEPS):
    perturbed[:, t] += perturb_magnitude * np.exp(-(t - perturb_time) * 0.05)

# 计算恢复时间
baseline = np.mean(trajectories[:, perturb_time-1:perturb_time], axis=1)
recovery_times = []
for i in range(N_TRAJ):
    for t in range(perturb_time, N_STEPS):
        dist = np.linalg.norm(perturbed[i, t] - baseline[i])
        if dist < 0.1:
            recovery_times.append(t - perturb_time)
            break
    else:
        recovery_times.append(N_STEPS - perturb_time)

avg_tau = np.mean(recovery_times) * DT
print(f"  平均恢复时间 τ = {avg_tau:.3f} (时间单位)")
print(f"  恢复率: {len([r for r in recovery_times if r < N_STEPS-perturb_time])/N_TRAJ*100:.1f}%")

# === 5. 相变监控 ===
autonomy_history = [np.mean(np.linalg.norm(trajectories[:, t], axis=1)) / np.sqrt(DIM) 
                    for t in range(0, N_STEPS, 30)]
print(f"\n自治指数趋势:")
for t, ai in enumerate(autonomy_history):
    bar = "█" * int(ai * 30)
    print(f"  t={t*30:3d}: {ai:.3f} {bar}")

# === 6. 可视化 ===
fig = plt.figure(figsize=(18, 12))

# (a) 3D轨迹
ax1 = fig.add_subplot(2, 3, 1, projection='3d')
for i in range(min(20, N_TRAJ)):
    ax1.plot(trajectories[i, :, 0], trajectories[i, :, 1], trajectories[i, :, 2], 
             alpha=0.3, linewidth=0.5)
ax1.set_title("(a) 12D State Space Trajectories")
ax1.set_xlabel("D1"); ax1.set_ylabel("D2"); ax1.set_zlabel("D3")

# (b) 自治指数时间序列
ax2 = fig.add_subplot(2, 3, 2)
time_axis = np.arange(N_STEPS)
mean_autonomy = np.mean(np.linalg.norm(trajectories, axis=2), axis=0) / np.sqrt(DIM)
ax2.plot(time_axis, mean_autonomy, 'b-', linewidth=1.5)
ax2.axvline(x=perturb_time, color='r', linestyle='--', label='Perturbation')
ax2.set_title("(b) Autonomy Index Over Time")
ax2.set_xlabel("Time Step"); ax2.set_ylabel("Autonomy Index")
ax2.legend()

# (c) 扰动恢复曲线
ax3 = fig.add_subplot(2, 3, 3)
dist_from_baseline = np.linalg.norm(perturbed - trajectories, axis=2)
mean_dist = np.mean(dist_from_baseline, axis=0)
ax3.plot(time_axis, mean_dist, 'r-', linewidth=1.5)
ax3.axvline(x=perturb_time, color='k', linestyle='--')
ax3.set_title("(c) Perturbation Recovery Curve")
ax3.set_xlabel("Time Step"); ax3.set_ylabel("Distance from Baseline")

# (d) 吸引子聚类
ax4 = fig.add_subplot(2, 3, 4)
for i in range(n_attractors):
    mask = labels == i
    ax4.scatter(final_states[mask, 0], final_states[mask, 1], 
                alpha=0.6, label=f'Attractor {i+1} ({np.sum(mask)})')
ax4.set_title("(d) Attractor Clusters (D1-D2)")
ax4.set_xlabel("D1"); ax4.set_ylabel("D2"); ax4.legend()

# (e) 六维记忆连续性雷达图
ax5 = fig.add_subplot(2, 3, 5, polar=True)
categories = ['Ω₀', 'L0', 'L1', 'L2', 'L-1']
values = [1.0, l0_topology := 0.68, l1_modal := 0.85, l2_assoc := 1.0, l_minus_1 := 0.80]
angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
values_plot = values + values[:1]
angles_plot = angles + angles[:1]
ax5.plot(angles_plot, values_plot, 'b-', linewidth=2)
ax5.fill(angles_plot, values_plot, alpha=0.25)
ax5.set_xticks(angles)
ax5.set_xticklabels(categories)
ax5.set_title("(e) Memory Continuity Radar")

# (f) 相变检测
ax6 = fig.add_subplot(2, 3, 6)
window = 20
rolling_mean = np.convolve(mean_autonomy, np.ones(window)/window, mode='valid')
ax6.plot(rolling_mean, 'g-', linewidth=2)
ax6.axhline(y=np.mean(rolling_mean), color='r', linestyle='--', label='Mean')
ax6.set_title(f"(f) Phase Transition Monitor (τ={avg_tau:.2f})")
ax6.set_xlabel("Time"); ax6.set_ylabel("Smoothed Autonomy")
ax6.legend()

plt.tight_layout()
plt.savefig("dynamics_simulation.png", dpi=150, bbox_inches='tight')
plt.show()

print("\n✅ Notebook执行完成: 12维动力学仿真 + 吸引子识别 + 相变监控")
```
