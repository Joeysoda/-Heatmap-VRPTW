"""
从已有的实验结果生成图表
Generate charts from existing experiment results
"""

import json
import os
import sys

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
    matplotlib.rcParams['axes.unicode_minus'] = False
    HAS_MATPLOTLIB = True
except ImportError:
    print("错误: matplotlib未安装")
    print("请运行: pip install matplotlib")
    sys.exit(1)

def load_results(result_dir):
    """加载实验结果"""
    json_file = os.path.join(result_dir, 'raw_results.json')
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['results']

def generate_charts(results, output_dir):
    """生成所有图表"""
    
    order_counts = [r['order_count'] for r in results]
    
    # Chart 1: Total Travel Time
    plt.figure(figsize=(12, 6))
    for algo_name in ['GCN-Guided', 'Best Fit', 'First Fit', 'Nearest Neighbor']:
        values = [r['algorithms'][algo_name]['total_travel'] for r in results]
        plt.plot(order_counts, values, marker='o', label=algo_name, linewidth=2)
    
    plt.xlabel('订单数量 / Number of Orders', fontsize=12)
    plt.ylabel('总行驶时间 / Total Travel Time', fontsize=12)
    plt.title('总行驶时间对比 / Total Travel Time Comparison', fontsize=14, fontweight='bold')
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'chart_total_travel.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ 生成: chart_total_travel.png")
    
    # Chart 2: Makespan
    plt.figure(figsize=(12, 6))
    for algo_name in ['GCN-Guided', 'Best Fit', 'First Fit', 'Nearest Neighbor']:
        values = [r['algorithms'][algo_name]['makespan'] for r in results]
        plt.plot(order_counts, values, marker='s', label=algo_name, linewidth=2)
    
    plt.xlabel('订单数量 / Number of Orders', fontsize=12)
    plt.ylabel('Makespan', fontsize=12)
    plt.title('Makespan对比 / Makespan Comparison', fontsize=14, fontweight='bold')
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'chart_makespan.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ 生成: chart_makespan.png")
    
    # Chart 3: Improvement
    plt.figure(figsize=(12, 6))
    improvements = [r['improvement_pct'] for r in results]
    plt.plot(order_counts, improvements, marker='D', color='green', 
            linewidth=2.5, markersize=8, label='GCN vs Best Baseline')
    plt.axhline(y=0, color='red', linestyle='--', alpha=0.5, label='No Improvement')
    
    plt.xlabel('订单数量 / Number of Orders', fontsize=12)
    plt.ylabel('改进百分比 / Improvement %', fontsize=12)
    plt.title('GCN相对于最佳基线的改进 / GCN Improvement over Best Baseline', 
             fontsize=14, fontweight='bold')
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'chart_improvement.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ 生成: chart_improvement.png")
    
    # Chart 4: Combined
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # Subplot 1: Total Travel
    ax1 = axes[0, 0]
    for algo_name in ['GCN-Guided', 'Best Fit', 'First Fit', 'Nearest Neighbor']:
        values = [r['algorithms'][algo_name]['total_travel'] for r in results]
        ax1.plot(order_counts, values, marker='o', label=algo_name, linewidth=2)
    ax1.set_xlabel('订单数量', fontsize=11)
    ax1.set_ylabel('总行驶时间', fontsize=11)
    ax1.set_title('(a) 总行驶时间对比', fontsize=12, fontweight='bold')
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)
    
    # Subplot 2: Makespan
    ax2 = axes[0, 1]
    for algo_name in ['GCN-Guided', 'Best Fit', 'First Fit', 'Nearest Neighbor']:
        values = [r['algorithms'][algo_name]['makespan'] for r in results]
        ax2.plot(order_counts, values, marker='s', label=algo_name, linewidth=2)
    ax2.set_xlabel('订单数量', fontsize=11)
    ax2.set_ylabel('Makespan', fontsize=11)
    ax2.set_title('(b) Makespan对比', fontsize=12, fontweight='bold')
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)
    
    # Subplot 3: Improvement
    ax3 = axes[1, 0]
    improvements = [r['improvement_pct'] for r in results]
    ax3.plot(order_counts, improvements, marker='D', color='green', 
            linewidth=2.5, markersize=8)
    ax3.axhline(y=0, color='red', linestyle='--', alpha=0.5)
    ax3.set_xlabel('订单数量', fontsize=11)
    ax3.set_ylabel('改进百分比 (%)', fontsize=11)
    ax3.set_title('(c) GCN改进百分比', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    
    # Subplot 4: Bar chart
    ax4 = axes[1, 1]
    last_result = results[-1]
    algos = last_result['algorithms']
    algo_names = ['GCN', 'BestFit', 'FirstFit', 'Nearest']
    full_names = ['GCN-Guided', 'Best Fit', 'First Fit', 'Nearest Neighbor']
    costs = [algos[name]['total_cost'] for name in full_names]
    
    bars = ax4.bar(algo_names, costs, color=['#2ecc71', '#3498db', '#e74c3c', '#f39c12'])
    ax4.set_ylabel('总成本', fontsize=11)
    ax4.set_title(f'(d) 总成本对比 ({last_result["order_count"]} 订单)', 
                 fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3, axis='y')
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.0f}', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'chart_combined.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ 生成: chart_combined.png")

def main():
    # 找到最新的结果目录
    results_dir = 'results'
    comparison_dirs = [d for d in os.listdir(results_dir) if d.startswith('comparison_')]
    
    if not comparison_dirs:
        print("错误: 没有找到对比实验结果")
        print("请先运行: 运行_对比实验.bat")
        return
    
    # 使用最新的结果
    latest_dir = sorted(comparison_dirs)[-1]
    result_path = os.path.join(results_dir, latest_dir)
    
    print(f"\n正在从以下目录生成图表:")
    print(f"  {result_path}\n")
    
    # 加载结果
    results = load_results(result_path)
    print(f"加载了 {len(results)} 个实验结果\n")
    
    # 生成图表
    print("生成图表...")
    generate_charts(results, result_path)
    
    print(f"\n✅ 完成！所有图表已保存到:")
    print(f"  {result_path}\n")
    print("生成的图表:")
    print("  - chart_total_travel.png")
    print("  - chart_makespan.png")
    print("  - chart_improvement.png")
    print("  - chart_combined.png")

if __name__ == '__main__':
    main()
