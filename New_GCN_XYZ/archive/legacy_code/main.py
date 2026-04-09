import os
import time
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from config import *
from data_loader import load_nodes, load_orders
from gnn_model import generate_heatmap
from solver import AGV, dist_func, get_order_coords, compute_global_costs, solve_allocation
from compare_methods import solve_best_fit, solve_first_fit, solve_nearest_neighbor

def process_comparison(instance_path, node_map, results_data, global_heatmap, global_node_to_idx):
    instance_name = os.path.basename(instance_path)
    instance_id = instance_name.replace('.xlsx', '')
    print(f"\n{'='*60}")
    print(f"Comparing on Instance: {instance_name}")
    print(f"{'='*60}")
    
    orders = load_orders(instance_path, node_map)
    if not orders:
        return

    # Use the Pre-trained Global Heatmap and Global Node Map
    # This assumes all nodes in orders are present in the global map (which they should be)
    
    # --- Method 1: GCN ---
    print("Running GCN (Inference)...")
    t0 = time.time()
    agvs_gcn = solve_allocation(orders, global_heatmap, global_node_to_idx)
    t_gcn = time.time() - t0
    m_gcn = compute_global_costs(agvs_gcn)
    
    # --- Method 2: Best Fit (Greedy) ---
    print("Running Best Fit...")
    t0 = time.time()
    agvs_bf = solve_best_fit(orders, AGV_NUM)
    t_bf = time.time() - t0
    m_bf = compute_global_costs(agvs_bf)
    
    # --- Method 3: First Fit (Round Robin) ---
    print("Running First Fit...")
    t0 = time.time()
    agvs_ff = solve_first_fit(orders, AGV_NUM)
    t_ff = time.time() - t0
    m_ff = compute_global_costs(agvs_ff)
    
    # --- Method 4: Nearest Neighbor ---
    print("Running Nearest Neighbor...")
    t0 = time.time()
    agvs_nn = solve_nearest_neighbor(orders, AGV_NUM)
    t_nn = time.time() - t0
    m_nn = compute_global_costs(agvs_nn)
    
    # --- Calculate Improvement (GCN vs Best of others) ---
    # We want to maximize improvement, so we compare against the best (minimum cost) baseline.
    baseline_costs = [m_bf['total_cost'], m_ff['total_cost'], m_nn['total_cost']]
    best_baseline = min(baseline_costs)
    
    # Improvement % = (Baseline - GCN) / Baseline * 100
    # If GCN is smaller, improvement is positive.
    imp_pct = ((best_baseline - m_gcn['total_cost']) / best_baseline) * 100 if best_baseline > 0 else 0.0
    
    # Store results
    results_data.append({
        'Instance': instance_id,
        'Orders': len(orders),
        'GCN_Cost': m_gcn['total_cost'], 'GCN_Mksp': m_gcn['makespan'], 'GCN_TotalTravel': m_gcn['total_travel'],
        'BestFit_Cost': m_bf['total_cost'], 'BestFit_Mksp': m_bf['makespan'], 'BestFit_TotalTravel': m_bf['total_travel'],
        'FirstFit_Cost': m_ff['total_cost'], 'FirstFit_Mksp': m_ff['makespan'], 'FirstFit_TotalTravel': m_ff['total_travel'],
        'Nearest_Cost': m_nn['total_cost'], 'Nearest_Mksp': m_nn['makespan'], 'Nearest_TotalTravel': m_nn['total_travel'],
        'Improvement_Pct': imp_pct
    })
    
    # --- Print Summary ---
    print("\nResults:")
    print(f"{'Method':<15} | {'Time (s)':<10} | {'Makespan':<10} | {'Total Travel':<12} | {'Objective':<10}")
    print("-" * 70)
    print(f"{'GCN':<15} | {t_gcn:<10.4f} | {m_gcn['makespan']:<10.2f} | {m_gcn['total_travel']:<12.2f} | {m_gcn['total_cost']:<10.2f}")
    print(f"{'Best Fit':<15} | {t_bf:<10.4f} | {m_bf['makespan']:<10.2f} | {m_bf['total_travel']:<12.2f} | {m_bf['total_cost']:<10.2f}")
    print(f"{'First Fit':<15} | {t_ff:<10.4f} | {m_ff['makespan']:<10.2f} | {m_ff['total_travel']:<12.2f} | {m_ff['total_cost']:<10.2f}")
    print(f"{'Nearest N.':<15} | {t_nn:<10.4f} | {m_nn['makespan']:<10.2f} | {m_nn['total_travel']:<12.2f} | {m_nn['total_cost']:<10.2f}")
    print(f"\nImprovement vs Best Baseline: {imp_pct:.2f}%")

def plot_results(results_data):
    df = pd.DataFrame(results_data)
    # Sort by number of orders
    df['Orders'] = df['Orders'].astype(int)
    df = df.sort_values('Orders')
    
    instances = df['Instance'].tolist()
    x = np.arange(len(instances))
    width = 0.2
    
    # Create 3 subplots
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 18), sharex=True)
    
    # 1. Total Travel Time Comparison (Sum of all vehicles)
    rects1 = ax1.bar(x - 1.5*width, df['GCN_TotalTravel'], width, label='GCN')
    rects2 = ax1.bar(x - 0.5*width, df['BestFit_TotalTravel'], width, label='Best Fit')
    rects3 = ax1.bar(x + 0.5*width, df['FirstFit_TotalTravel'], width, label='First Fit')
    rects4 = ax1.bar(x + 1.5*width, df['Nearest_TotalTravel'], width, label='Nearest Neighbor')
    
    ax1.set_ylabel('Total Travel Time (s)')
    ax1.set_title('Total Travel Time Comparison (Sum of all vehicles)')
    ax1.legend()
    ax1.grid(True, linestyle='--', alpha=0.6)
    
    # 2. Makespan Comparison
    rects1_m = ax2.bar(x - 1.5*width, df['GCN_Mksp'], width, label='GCN')
    rects2_m = ax2.bar(x - 0.5*width, df['BestFit_Mksp'], width, label='Best Fit')
    rects3_m = ax2.bar(x + 0.5*width, df['FirstFit_Mksp'], width, label='First Fit')
    rects4_m = ax2.bar(x + 1.5*width, df['Nearest_Mksp'], width, label='Nearest Neighbor')
    
    ax2.set_ylabel('Makespan (s)')
    ax2.set_title('Makespan Comparison')
    ax2.legend()
    ax2.grid(True, linestyle='--', alpha=0.6)
    
    # 3. Improvement Percentage
    # Line chart or Bar chart? Bar is clearer for discrete instances.
    colors = ['g' if v >= 0 else 'r' for v in df['Improvement_Pct']]
    ax3.bar(x, df['Improvement_Pct'], width*2, color=colors, alpha=0.7)
    ax3.axhline(0, color='black', linewidth=0.8)
    
    ax3.set_ylabel('Improvement (%)')
    ax3.set_title('GCN Makespan Cost Improvement vs Best Baseline')
    ax3.set_xticks(x)
    ax3.set_xticklabels(instances, rotation=45)
    ax3.grid(True, linestyle='--', alpha=0.6)
    
    # Add value labels on improvement bars
    for i, v in enumerate(df['Improvement_Pct']):
        ax3.text(i, v + (1 if v >= 0 else -2), f"{v:.1f}%", ha='center', va='bottom' if v >= 0 else 'top', fontsize=9, fontweight='bold')

    plt.tight_layout()
    plt.savefig('algorithm_comparison_full.png')
    print("\nPlot saved to algorithm_comparison_full.png")

def main():
    node_map = load_nodes(NODE_FILE)
    if not node_map: return

    # Filter instances
    pattern = os.path.join(INSTANCE_DIR, "*.xlsx")
    all_files = glob.glob(pattern)
    
    # Small (5) + Medium (5) + Large (5)
    small_ids = ['20', '32', '41', '64', '73']
    medium_ids = ['100', '128', '150', '173', '195']
    large_ids = ['211', '243', '275', '306', '328']
    
    target_ids = small_ids + medium_ids + large_ids
    
    instance_files = []
    # Map ID to file path
    id_to_file = {}
    for f in all_files:
        fname = os.path.basename(f).replace('.xlsx', '')
        id_to_file[fname] = f
        
    # Preserve order of target_ids
    for tid in target_ids:
        if tid in id_to_file:
            instance_files.append(id_to_file[tid])
        else:
            print(f"Warning: Instance {tid} not found.")
            
    if not instance_files:
        print("No instances found.")
        return
        
    # --- Pre-train GCN on the Global Graph ---
    print("\n" + "="*60)
    print("PRE-TRAINING GCN MODEL ON GLOBAL GRAPH")
    print("="*60)
    
    # 1. Get all unique nodes from the node map
    # node_map values are (x, y, z) tuples
    all_nodes_list = sorted(list(set(node_map.values())))
    global_node_to_idx = {coord: i for i, coord in enumerate(all_nodes_list)}
    
    print(f"Total nodes in hospital graph: {len(all_nodes_list)}")
    
    model_path = os.path.join(os.path.dirname(__file__), "gcn_model.pth")
    
    # Train (or load) and generate global heatmap
    # We set train=True to ensure it trains if not loaded, or re-trains. 
    # To strictly follow "train once", we could check if file exists.
    # But user said "train for a few more processes", implying we should run training now.
    global_heatmap = generate_heatmap(all_nodes_list, model_path=model_path, train=True, temperature=2.0)
    print("Global Heatmap generated.")

    output_path = os.path.join(os.path.dirname(__file__), "comparison_results_full.txt")
    with open(output_path, 'w') as f:
        f.write("--- Algorithm Comparison Results ---\n")
        f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results_data = []
    for f in instance_files:
        try:
            process_comparison(f, node_map, results_data, global_heatmap, global_node_to_idx)
        except Exception as e:
            print(f"Error processing {f}: {e}")
            import traceback
            traceback.print_exc()
            
    # Save detailed results to CSV
    if results_data:
        df = pd.DataFrame(results_data)
        df.to_csv('comparison_results_full.csv', index=False)
        print("\nDetailed results saved to comparison_results_full.csv")
        plot_results(results_data)

if __name__ == "__main__":
    main()
