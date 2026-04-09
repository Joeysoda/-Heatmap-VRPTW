"""
AnyLogic File Bridge - 完整的GCN引导在线调度系统
使用论文方法：GCN热力图 + 插入启发式 + 充电约束 + 在线调度

集成模块：
- GCN热力图生成（无监督学习）
- 热力图引导的插入启发式
- 充电站约束管理
- 在线动态订单调度
- 与AnyLogic的文件交换接口
"""

import sys
import os
import json
import time
from datetime import datetime

# 添加当前目录到路径（用于导入core模块）
sys.path.insert(0, os.path.dirname(__file__))

# 导入核心模块 - 直接导入避免__init__.py的循环依赖
from core import config
from core.data_loader import load_all_data
from core.gnn_model import generate_heatmap
from core.online_scheduler import OnlineScheduler

# 导入配置变量
AGV_NUM = config.AGV_NUM
ENABLE_CHARGING = config.ENABLE_CHARGING
ENABLE_TIME_WINDOWS = config.ENABLE_TIME_WINDOWS

# 创建必要的目录
BRIDGE_DIR = os.path.join(os.path.dirname(__file__), 'anylogic_bridge')
INPUT_DIR = os.path.join(BRIDGE_DIR, 'input')
OUTPUT_DIR = os.path.join(BRIDGE_DIR, 'output')
STATUS_DIR = os.path.join(BRIDGE_DIR, 'status')

for dir_path in [BRIDGE_DIR, INPUT_DIR, OUTPUT_DIR, STATUS_DIR]:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"Created directory: {dir_path}")


class AGVSchedulingSystem:
    """
    完整的AGV调度系统
    集成GCN热力图、在线调度和AnyLogic接口
    """
    
    def __init__(self):
        self.scheduler = None
        self.heatmap = None
        self.node_to_idx = None
        self.charging_stations = None
        self.initialized = False
        
    def initialize(self):
        """初始化系统：加载数据、训练GCN、创建调度器"""
        print("\n" + "="*70)
        print("  GCN-Guided Online AGV Scheduling System")
        print("  基于论文方法的完整实现")
        print("="*70)
        
        try:
            # 1. 加载robot_data数据
            print("\n[1/4] Loading hospital robot data...")
            nodes, edges, orders, charging_stations = load_all_data(order_limit=None)  # 加载所有订单
            self.charging_stations = charging_stations
            
            # 2. 构建节点映射和热力图
            print("\n[2/4] Building graph and generating GCN heatmap...")
            unique_nodes = list(set([(o['start_x'], o['start_y'], o['start_z']) for o in orders] +
                                   [(o['end_x'], o['end_y'], o['end_z']) for o in orders]))
            
            if not unique_nodes:
                print("Warning: No unique nodes found, using fallback nodes")
                unique_nodes = [(0, 0, 0), (100, 100, 0), (200, 200, 1)]
            
            self.node_to_idx = {node: i for i, node in enumerate(unique_nodes)}
            
            # 生成热力图（包含无监督训练）
            model_path = os.path.join(os.path.dirname(__file__), 'models', 'gcn_model.pth')
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            
            print(f"  Training GCN on {len(unique_nodes)} nodes...")
            self.heatmap = generate_heatmap(
                unique_nodes, 
                model_path=model_path,
                temperature=1.0,
                train=True  # 启用无监督训练
            )
            print(f"  Heatmap shape: {self.heatmap.shape}")
            
            # 3. 创建在线调度器
            print("\n[3/4] Initializing online scheduler...")
            self.scheduler = OnlineScheduler(
                gcn_model=None,  # 已经有heatmap了
                heatmap=self.heatmap,
                node_to_idx=self.node_to_idx,
                charging_stations=self.charging_stations,
                num_agvs=AGV_NUM,
                start_time=0
            )
            
            # 4. 系统就绪
            print("\n[4/4] System initialization complete!")
            print("="*70)
            print("\n✓ GCN Model: Trained and ready")
            print(f"✓ Heatmap: {self.heatmap.shape[0]}x{self.heatmap.shape[1]} matrix")
            print(f"✓ Charging Stations: {len(self.charging_stations)} locations")
            print(f"✓ AGVs: {AGV_NUM} vehicles")
            print(f"✓ Constraints: Charging={'ON' if ENABLE_CHARGING else 'OFF'}, TimeWindows={'ON' if ENABLE_TIME_WINDOWS else 'OFF'}")
            print("="*70 + "\n")
            
            self.initialized = True
            return True
            
        except Exception as e:
            print(f"\n✗ Initialization failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def process_orders(self):
        """处理AnyLogic发来的订单"""
        if not self.initialized:
            print("System not initialized. Initializing now...")
            if not self.initialize():
                return
        
        # 检查输入目录中的订单文件
        order_files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.json')]
        
        if not order_files:
            return
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Processing {len(order_files)} order(s)...")
        
        # 加载所有订单
        new_orders = []
        for filename in order_files:
            filepath = os.path.join(INPUT_DIR, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    order = json.load(f)
                    new_orders.append(order)
                    print(f"  ✓ Loaded: {order.get('id', 'UNKNOWN')}")
            except Exception as e:
                print(f"  ✗ Error loading {filename}: {e}")
                continue
        
        if not new_orders:
            return
        
        # 添加订单到调度器
        for order in new_orders:
            self.scheduler.add_order(order)
        
        # 执行调度（一步）
        self.scheduler.step(time_delta=1.0)
        
        # 输出结果
        self.output_routes()
        
        # 删除已处理的订单文件
        for filename in order_files:
            try:
                os.remove(os.path.join(INPUT_DIR, filename))
            except:
                pass
        
        # 显示统计信息
        stats = self.scheduler.get_statistics()
        print(f"  Statistics:")
        print(f"    - Total orders: {stats['total_orders']}")
        print(f"    - Pending: {stats['pending_orders']}")
        print(f"    - Completed: {stats['completed_orders']}")
        print(f"    - Charging events: {stats['charging_events']}")
    
    def output_routes(self):
        """输出路由到AnyLogic"""
        result = {
            'timestamp': time.time(),
            'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'num_agvs': len(self.scheduler.agvs),
            'agvs': []
        }
        
        for agv in self.scheduler.agvs:
            if agv.route:
                agv_data = {
                    'agv_id': agv.id,
                    'num_tasks': len(agv.route),
                    'total_time': round(agv.total_time, 2),
                    'battery_level': round(agv.battery_level, 2),
                    'battery_capacity': agv.battery_capacity,
                    'route': []
                }
                
                for idx, task in enumerate(agv.route):
                    task_data = {
                        'sequence': idx,
                        'task_id': task.get('id', f'TASK_{idx}'),
                        'type': task.get('type', 'delivery'),
                        'start_x': task['start_x'],
                        'start_y': task['start_y'],
                        'start_z': task['start_z'],
                        'end_x': task.get('end_x', task['start_x']),
                        'end_y': task.get('end_y', task['start_y']),
                        'end_z': task.get('end_z', task['start_z'])
                    }
                    agv_data['route'].append(task_data)
                
                result['agvs'].append(agv_data)
        
        # 写入输出文件
        output_file = os.path.join(OUTPUT_DIR, 'routes.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        # 写入状态文件
        status_file = os.path.join(STATUS_DIR, 'ready.txt')
        with open(status_file, 'w', encoding='utf-8') as f:
            f.write(f"Ready at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"AGVs with routes: {len(result['agvs'])}\n")
            f.write(f"Total tasks: {sum(len(a['route']) for a in result['agvs'])}\n")


def main():
    """主循环：监控输入目录并处理订单"""
    print("\n" + "="*70)
    print("  AnyLogic File Bridge - GCN-Guided Online Scheduler")
    print("="*70)
    print(f"Input directory:  {INPUT_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Status directory: {STATUS_DIR}")
    print("="*70)
    
    # 创建系统实例
    system = AGVSchedulingSystem()
    
    # 初始化系统
    if not system.initialize():
        print("\n✗ System initialization failed. Exiting...")
        return
    
    print("\n✓ System ready. Waiting for orders from AnyLogic...")
    print("  (Press Ctrl+C to stop)\n")
    
    try:
        while True:
            system.process_orders()
            time.sleep(1.0)  # 每秒检查一次
            
    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        print("  System stopped by user")
        print("="*70)
        
        # 显示最终统计
        if system.scheduler:
            print("\nFinal Statistics:")
            system.scheduler.print_status()
        
    except Exception as e:
        print(f"\n\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
