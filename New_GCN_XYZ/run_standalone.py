"""
独立运行模式 - 直接用Python处理所有订单
不需要AnyLogic，直接输出调度结果
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import json
from datetime import datetime
from core.data_loader import load_all_data
from core.gnn_model import generate_heatmap
from core.solver import solve_allocation, compute_global_costs, print_solution

def main():
    print("\n" + "="*70)
    print("  独立运行模式 - GCN引导的AGV调度")
    print("  直接处理所有订单，无需AnyLogic")
    print("="*70)
    
    # 1. 加载数据
    print("\n[1/4] 加载医院数据...")
    nodes, edges, orders, charging_stations = load_all_data(order_limit=None)
    print(f"  ✓ 加载了 {len(orders)} 个订单")
    
    # 2. 生成热力图
    print("\n[2/4] 生成GCN热力图...")
    unique_nodes = list(set([(o['start_x'], o['start_y'], o['start_z']) for o in orders] +
                           [(o['end_x'], o['end_y'], o['end_z']) for o in orders]))
    node_to_idx = {node: i for i, node in enumerate(unique_nodes)}
    
    model_path = os.path.join(os.path.dirname(__file__), 'models', 'gcn_model.pth')
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    
    heatmap = generate_heatmap(unique_nodes, model_path=model_path, temperature=1.0, train=True)
    print(f"  ✓ 热力图大小: {heatmap.shape}")
    
    # 3. 执行调度
    print("\n[3/4] 执行调度算法...")
    agvs = solve_allocation(orders, heatmap, node_to_idx)
    print(f"  ✓ 调度完成")
    
    # 4. 输出结果
    print("\n[4/4] 输出结果...")
    
    # 打印解决方案
    print_solution(agvs)
    
    # 计算成本
    costs = compute_global_costs(agvs)
    print(f"\n全局指标:")
    print(f"  Makespan: {costs['makespan']:.2f} 秒")
    print(f"  总行驶时间: {costs['total_travel']:.2f} 秒")
    print(f"  总成本: {costs['total_cost']:.4f}")
    
    # 保存到JSON
    output_dir = os.path.join(os.path.dirname(__file__), 'results')
    os.makedirs(output_dir, exist_ok=True)
    
    result = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_orders': len(orders),
        'num_agvs': len(agvs),
        'makespan': costs['makespan'],
        'total_travel_time': costs['total_travel'],
        'total_cost': costs['total_cost'],
        'agvs': []
    }
    
    for agv in agvs:
        if agv.route:
            agv_data = {
                'agv_id': agv.id,
                'num_orders': len(agv.route),
                'total_time': agv.total_time,
                'orders': [o['id'] for o in agv.route]
            }
            result['agvs'].append(agv_data)
    
    output_file = os.path.join(output_dir, f'result_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ 结果已保存到: {output_file}")
    print("="*70)

if __name__ == '__main__':
    main()
