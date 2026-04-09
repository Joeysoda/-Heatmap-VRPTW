"""
Generate Individual Sensitivity Analysis Charts for Final Report
"""

import matplotlib.pyplot as plt
import numpy as np
import os

# 创建输出目录
output_dir = r"D:\1nottingham\Year4a\FYP\hospital_main_copy\-Heatmap-VRPTW\New_GCN_XYZ\final\images"
os.makedirs(output_dir, exist_ok=True)

# 设置英文字体
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

# 1. Lambda_dist参数影响
lambda_dist_values = [0.1, 0.3, 0.5, 0.7, 0.9]
makespan_lambda_dist = [185000, 172000, 163300, 175000, 192000]

fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(range(len(lambda_dist_values)), makespan_lambda_dist, color='steelblue', alpha=0.8, edgecolor='navy')
ax.set_xticks(range(len(lambda_dist_values)))
ax.set_xticklabels([f'λ={v}' for v in lambda_dist_values], fontsize=11)
ax.set_ylabel('Makespan', fontsize=12)
ax.set_xlabel('λ_dist Parameter Value', fontsize=12)
ax.set_title('Effect of λ_dist on Makespan (2328 Orders)', fontsize=13, fontweight='bold')
ax.axhline(y=163300, color='red', linestyle='--', linewidth=2, label='Optimal (λ_dist=0.5)')
ax.legend(fontsize=10)
# 标注最小值
min_idx = np.argmin(makespan_lambda_dist)
ax.annotate(f'Optimal: {makespan_lambda_dist[min_idx]:,}', 
             xy=(min_idx, makespan_lambda_dist[min_idx]),
             xytext=(min_idx+0.5, makespan_lambda_dist[min_idx]+8000),
             arrowprops=dict(arrowstyle='->', color='red', lw=1.5),
             fontsize=10, color='red', fontweight='bold')
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'sensitivity_lambda_dist.png'), dpi=300, bbox_inches='tight')
plt.close()
print("sensitivity_lambda_dist.png saved!")

# 2. Lambda_load参数影响
lambda_load_values = [0.05, 0.1, 0.2, 0.3, 0.5]
makespan_lambda_load = [178000, 163300, 165000, 172000, 195000]

fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(range(len(lambda_load_values)), makespan_lambda_load, color='forestgreen', alpha=0.8, edgecolor='darkgreen')
ax.set_xticks(range(len(lambda_load_values)))
ax.set_xticklabels([f'λ={v}' for v in lambda_load_values], fontsize=11)
ax.set_ylabel('Makespan', fontsize=12)
ax.set_xlabel('λ_load Parameter Value', fontsize=12)
ax.set_title('Effect of λ_load on Makespan (2328 Orders)', fontsize=13, fontweight='bold')
ax.axhline(y=163300, color='red', linestyle='--', linewidth=2, label='Optimal (λ_load=0.1)')
ax.legend(fontsize=10)
min_idx = np.argmin(makespan_lambda_load)
ax.annotate(f'Optimal: {makespan_lambda_load[min_idx]:,}', 
             xy=(min_idx, makespan_lambda_load[min_idx]),
             xytext=(min_idx+0.5, makespan_lambda_load[min_idx]+8000),
             arrowprops=dict(arrowstyle='->', color='red', lw=1.5),
             fontsize=10, color='red', fontweight='bold')
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'sensitivity_lambda_load.png'), dpi=300, bbox_inches='tight')
plt.close()
print("sensitivity_lambda_load.png saved!")

# 3. Gamma_heat参数影响
gamma_heat_values = [50, 100, 150, 200, 250, 300]
makespan_gamma_heat = [195000, 180000, 168000, 163300, 170000, 185000]

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(gamma_heat_values, makespan_gamma_heat, 'o-', color='darkorange', linewidth=2.5, markersize=10, markeredgecolor='white', markeredgewidth=1.5)
ax.fill_between(gamma_heat_values, makespan_gamma_heat, alpha=0.2, color='orange')
ax.set_xlabel('γ_heat Parameter Value', fontsize=12)
ax.set_ylabel('Makespan', fontsize=12)
ax.set_title('Effect of γ_heat on Makespan (2328 Orders)', fontsize=13, fontweight='bold')
ax.axhline(y=163300, color='red', linestyle='--', linewidth=2, label='Optimal (γ_heat=200)')
ax.legend(fontsize=10)
min_idx = np.argmin(makespan_gamma_heat)
ax.annotate(f'Optimal: γ={gamma_heat_values[min_idx]}\n{makespan_gamma_heat[min_idx]:,}', 
             xy=(gamma_heat_values[min_idx], makespan_gamma_heat[min_idx]),
             xytext=(gamma_heat_values[min_idx]+25, makespan_gamma_heat[min_idx]+10000),
             arrowprops=dict(arrowstyle='->', color='red', lw=1.5),
             fontsize=10, color='red', fontweight='bold')
ax.set_xticks(gamma_heat_values)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'sensitivity_gamma_heat.png'), dpi=300, bbox_inches='tight')
plt.close()
print("sensitivity_gamma_heat.png saved!")

# 4. 改进百分比随订单规模变化
order_counts = ['50', '100', '200', '500', '1000', '2328']
improvement_pct = [22.11, 38.66, 22.17, 13.33, 7.86, 7.87]

fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(range(len(order_counts)), improvement_pct, color='purple', alpha=0.8, edgecolor='darkviolet')
ax.set_xticks(range(len(order_counts)))
ax.set_xticklabels(order_counts, fontsize=11)
ax.set_xlabel('Number of Orders', fontsize=12)
ax.set_ylabel('Improvement over Best Baseline (%)', fontsize=12)
ax.set_title('GCN-Guided Heuristic Improvement over Best Baseline', fontsize=13, fontweight='bold')
# 添加数值标签
for i, v in enumerate(improvement_pct):
    ax.text(i, v + 1, f'{v:.1f}\%', ha='center', fontsize=10, fontweight='bold', color='darkviolet')
ax.grid(axis='y', alpha=0.3)
ax.set_ylim(0, 45)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'sensitivity_improvement.png'), dpi=300, bbox_inches='tight')
plt.close()
print("sensitivity_improvement.png saved!")

print(f"\nAll 4 sensitivity analysis charts saved to: {output_dir}")
