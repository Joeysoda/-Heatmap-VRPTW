"""
Core module for GCN-guided AGV scheduling system
包含GNN模型、求解器、在线调度器和数据加载器
"""

# 只导入config，其他模块延迟导入避免torch路径冲突
from .config import *

# 延迟导入函数
def _lazy_import():
    """延迟导入避免torch路径问题"""
    global load_all_data, extract_charging_stations
    global GCNHeatmapModel, generate_heatmap
    global AGV, solve_allocation, compute_global_costs
    global OnlineScheduler
    
    from .data_loader import load_all_data, extract_charging_stations
    from .gnn_model import GCNHeatmapModel, generate_heatmap
    from .solver import AGV, solve_allocation, compute_global_costs
    from .online_scheduler import OnlineScheduler

__all__ = [
    'load_all_data',
    'extract_charging_stations',
    'GCNHeatmapModel',
    'generate_heatmap',
    'AGV',
    'solve_allocation',
    'compute_global_costs',
    'OnlineScheduler',
]
