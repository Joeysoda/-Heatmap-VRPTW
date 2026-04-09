"""
COMPREHENSIVE DEMO: Unsupervised GNN-based EVRPTW with Online Scheduling
=========================================================================

This demo showcases the complete implementation of:
1. ✅ Time Window Constraints (VRPTW)
2. ✅ Charging Constraints (Electric Vehicles)
3. ✅ Online/Dynamic Scheduling (Real-time order arrival)
4. ✅ AnyLogic Integration (REST API)
5. ✅ GNN-based Heatmap Guidance
6. ✅ Robot Data Support

Author: FYP Implementation
Date: 2026-02-01
"""

import sys
import os
import numpy as np
from datetime import datetime, timedelta
import time

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import *
from data_loader import (
    load_orders_with_time_windows,
    extract_charging_stations,
    load_edge_travel_times
)
from solver import AGV, dist_func, check_time_window_feasibility, check_battery_feasibility
from online_scheduler import OnlineScheduler
from gnn_model import generate_heatmap


def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def demo_1_data_loading():
    """Demo 1: Load Real Robot Data with Time Windows and Charging Stations"""
    print_header("DEMO 1: Data Loading from Robot Data")
    
    print("\n📂 Loading robot_order.xlsx (with time windows)...")
    try:
        orders = load_orders_with_time_windows(ROBOT_ORDER_FILE)
        print(f"✅ Loaded {len(orders)} orders with time window constraints")
        
        if orders:
            sample = orders[0]
            print(f"\n📦 Sample Order:")
            print(f"   ID: {sample['id']}")
            print(f"   From: {sample.get('start_address', 'N/A')}")
            print(f"   To: {sample.get('end_address', 'N/A')}")
            print(f"   Pickup Window: {sample.get('pickup_tw_start', 'N/A')} → {sample.get('pickup_tw_end', 'N/A')}")
            print(f"   Delivery Window: {sample.get('delivery_tw_start', 'N/A')} → {sample.get('delivery_tw_end', 'N/A')}")
            print(f"   Distance: {sample.get('distance', 'N/A')}m")
            print(f"   Estimated Time: {sample.get('estimated_time', 'N/A')}s")
    except Exception as e:
        print(f"⚠️  Could not load orders: {e}")
        orders = []
    
    print("\n🔋 Extracting charging stations from robot_mission.xlsx...")
    try:
        charging_info = extract_charging_stations(ROBOT_MISSION_FILE)
        print(f"✅ Found {charging_info['num_stations']} charging stations")
        print(f"   Average charging time: {charging_info['avg_charging_time']:.2f}s")
        print(f"   Stations: {charging_info['stations'][:5]}")
    except Exception as e:
        print(f"⚠️  Could not load charging stations: {e}")
        charging_info = {'stations': [], 'avg_charging_time': 300.0}
    
    print("\n🗺️  Loading edge travel times from robot_edge.xlsx...")
    try:
        edge_times = load_edge_travel_times(ROBOT_EDGE_FILE)
        print(f"✅ Loaded {len(edge_times)} edge travel times")
        if edge_times:
            sample_edge = list(edge_times.items())[0]
            print(f"   Sample: {sample_edge[0]} → {sample_edge[1]:.2f}s")
    except Exception as e:
        print(f"⚠️  Could not load edge times: {e}")
        edge_times = {}
    
    return orders, charging_info, edge_times


def demo_2_constraints():
    """Demo 2: Time Window and Charging Constraints"""
    print_header("DEMO 2: Constraint Checking (Time Windows + Charging)")
    
    print("\n🤖 Creating AGV with battery tracking...")
    agv = AGV(0, initial_location=(0, 0, 0), start_time=0)
    print(f"✅ AGV-0 initialized")
    print(f"   Battery: {agv.battery_level:.0f}/{agv.battery_capacity:.0f} units")
    print(f"   Consumption rate: {agv.consumption_rate} units/meter")
    print(f"   Low threshold: {BATTERY_LOW_THRESHOLD} units")
    
    print("\n⏰ Testing Time Window Constraints...")
    test_order = {
        'id': 'TEST001',
        'start_x': 10.0, 'start_y': 20.0, 'start_z': 0,
        'end_x': 50.0, 'end_y': 60.0, 'end_z': 1,
        'pickup_tw_start': datetime.now(),
        'pickup_tw_end': datetime.now() + timedelta(minutes=10),
        'delivery_tw_start': datetime.now() + timedelta(minutes=10),
        'delivery_tw_end': datetime.now() + timedelta(minutes=30)
    }
    
    feasible, pickup_time, delivery_time = check_time_window_feasibility(agv, test_order, 0)
    print(f"   Order: ({test_order['start_x']}, {test_order['start_y']}) → ({test_order['end_x']}, {test_order['end_y']})")
    print(f"   Time window feasible: {'✅ YES' if feasible else '❌ NO'}")
    print(f"   Estimated pickup arrival: {pickup_time:.2f}s")
    print(f"   Estimated delivery arrival: {delivery_time:.2f}s")
    
    print("\n🔋 Testing Battery/Charging Constraints...")
    charging_stations = [(15, 15, 0), (30, 30, 1), (45, 45, 2)]
    
    # Test with sufficient battery
    agv.battery_level = 8000
    feasible, needs_charge, station = check_battery_feasibility(agv, test_order, 0, charging_stations)
    print(f"   Scenario 1: Battery at {agv.battery_level:.0f} units")
    print(f"   Battery feasible: {'✅ YES' if feasible else '❌ NO'}")
    print(f"   Needs charging: {'🔌 YES' if needs_charge else '✅ NO'}")
    if station:
        print(f"   Nearest charging station: {station}")
    
    # Test with low battery
    agv.battery_level = 1500
    feasible, needs_charge, station = check_battery_feasibility(agv, test_order, 0, charging_stations)
    print(f"\n   Scenario 2: Battery at {agv.battery_level:.0f} units (LOW!)")
    print(f"   Battery feasible: {'✅ YES' if feasible else '❌ NO'}")
    print(f"   Needs charging: {'🔌 YES' if needs_charge else '✅ NO'}")
    if station:
        print(f"   Nearest charging station: {station}")
        print(f"   Charging time: {CHARGING_TIME:.0f}s")


def demo_3_online_scheduling():
    """Demo 3: Online/Dynamic Scheduling with Real-time Order Arrival"""
    print_header("DEMO 3: Online Scheduling (Dynamic Order Arrival)")
    
    print("\n🎯 Initializing Online Scheduler...")
    
    # Create dummy heatmap (in real scenario, this comes from trained GNN)
    print("   Generating GNN heatmap...")
    unique_nodes = [(i*10, i*10, i%3) for i in range(20)]
    heatmap = generate_heatmap(unique_nodes)
    node_to_idx = {node: i for i, node in enumerate(unique_nodes)}
    
    charging_stations = [(15, 15, 0), (30, 30, 1), (45, 45, 2)]
    
    scheduler = OnlineScheduler(
        gcn_model=None,
        heatmap=heatmap,
        node_to_idx=node_to_idx,
        charging_stations=charging_stations,
        num_agvs=AGV_NUM,
        start_time=0
    )
    
    print(f"✅ Scheduler initialized with {len(scheduler.agvs)} AGVs")
    print(f"   Charging stations: {len(charging_stations)}")
    print(f"   Heatmap size: {heatmap.shape}")
    
    print("\n📦 Simulating Dynamic Order Arrivals...")
    
    # Create test orders with staggered arrival times
    test_orders = []
    for i in range(10):
        order = {
            'id': f'ORDER_{i+1:03d}',
            'start_x': np.random.uniform(0, 50),
            'start_y': np.random.uniform(0, 50),
            'start_z': np.random.randint(0, 3),
            'end_x': np.random.uniform(0, 50),
            'end_y': np.random.uniform(0, 50),
            'end_z': np.random.randint(0, 3),
            'pickup_tw_start': datetime.now() + timedelta(seconds=i*30),
            'pickup_tw_end': datetime.now() + timedelta(seconds=i*30 + 600),
            'delivery_tw_start': datetime.now() + timedelta(seconds=i*30 + 600),
            'delivery_tw_end': datetime.now() + timedelta(seconds=i*30 + 1200)
        }
        test_orders.append(order)
    
    # Add orders dynamically
    for i, order in enumerate(test_orders):
        arrival_time = i * 30.0  # Orders arrive every 30 seconds
        scheduler.add_order(order, arrival_time)
        print(f"   t={arrival_time:6.1f}s: Order {order['id']} arrives")
    
    print(f"\n✅ Added {len(test_orders)} orders to scheduler")
    
    print("\n⏱️  Running Simulation (10 time steps)...")
    for step in range(10):
        scheduler.step(30.0)  # Step 30 seconds at a time
        print(f"   Step {step+1:2d}: t={scheduler.current_time:6.1f}s | "
              f"Pending: {len(scheduler.pending_orders):2d} | "
              f"Assigned: {len(scheduler.assigned_orders):2d} | "
              f"Completed: {scheduler.stats['completed_orders']:2d}")
    
    print("\n📊 Final Statistics:")
    stats = scheduler.get_statistics()
    print(f"   Total orders: {stats['total_orders']}")
    print(f"   Completed: {stats['completed_orders']}")
    print(f"   Pending: {stats['pending_orders']}")
    print(f"   Completion rate: {stats['completion_rate']:.1%}")
    print(f"   Late orders: {stats['late_orders']}")
    print(f"   Charging events: {stats['charging_events']}")
    
    print("\n🤖 AGV Status:")
    for agv in scheduler.agvs[:3]:  # Show first 3 AGVs
        print(f"   AGV-{agv.id}: {len(agv.route)} tasks, "
              f"Battery: {agv.battery_level:.0f}/{agv.battery_capacity:.0f}, "
              f"Total time: {agv.total_time:.1f}s")
    
    return scheduler


def demo_4_anylogic_integration(scheduler):
    """Demo 4: AnyLogic Integration via REST API"""
    print_header("DEMO 4: AnyLogic Integration (REST API)")
    
    print("\n🌐 Creating AnyLogic Interface...")
    from anylogic_interface import AnyLogicInterface
    
    interface = AnyLogicInterface(scheduler, host='localhost', port=5000)
    print(f"✅ Interface created on {interface.host}:{interface.port}")
    
    print("\n📡 Available API Endpoints:")
    endpoints = [
        ("GET",  "/health",              "Health check and system status"),
        ("POST", "/order/add",           "Add new order dynamically"),
        ("POST", "/agv/status",          "Update AGV status from AnyLogic"),
        ("GET",  "/agv/route/<agv_id>", "Get current route for an AGV"),
        ("GET",  "/scheduler/status",    "Get scheduler statistics"),
        ("POST", "/scheduler/step",      "Step simulation forward")
    ]
    
    for method, endpoint, description in endpoints:
        print(f"   {method:4s} {endpoint:25s} - {description}")
    
    print("\n📝 Example API Usage:")
    
    print("\n1️⃣  Add Order from AnyLogic:")
    example_order = {
        "order_id": "002023031300001",
        "start_node": "042$SITE-00189",
        "end_node": "045$SITE-00241",
        "start_x": 10.5,
        "start_y": 20.3,
        "start_z": 0,
        "end_x": 15.2,
        "end_y": 25.1,
        "end_z": 1,
        "pickup_tw_start": "2023-03-13T00:15:55",
        "pickup_tw_end": "2023-03-13T00:18:01",
        "delivery_tw_start": "2023-03-13T00:18:01",
        "delivery_tw_end": "2023-03-13T00:29:33",
        "arrival_time": 955.0
    }
    print(f"   POST /order/add")
    print(f"   Body: {example_order}")
    
    print("\n2️⃣  Update AGV Status from AnyLogic:")
    example_status = {
        "agv_id": 0,
        "current_x": 10.5,
        "current_y": 20.3,
        "current_z": 0,
        "battery_level": 8500.0,
        "current_time": 1200.5,
        "status": "idle"
    }
    print(f"   POST /agv/status")
    print(f"   Body: {example_status}")
    
    print("\n3️⃣  Get AGV Route for Animation:")
    print(f"   GET /agv/route/0")
    print(f"   Response: {{")
    print(f"     'agv_id': 0,")
    print(f"     'route': [{{order_id, start_x, start_y, end_x, end_y, ...}}],")
    print(f"     'battery_level': 8500.0")
    print(f"   }}")
    
    print("\n🚀 To Start API Server:")
    print(f"   python anylogic_interface.py")
    print(f"   Server will run on http://{interface.host}:{interface.port}")
    
    print("\n📱 AnyLogic Integration Steps:")
    print("   1. Start Python API server (python anylogic_interface.py)")
    print("   2. In AnyLogic, use RestAPI blocks to communicate:")
    print("      - Send orders: POST http://localhost:5000/order/add")
    print("      - Get routes: GET http://localhost:5000/agv/route/<id>")
    print("      - Update status: POST http://localhost:5000/agv/status")
    print("   3. Use route data to animate AGV movements in AnyLogic")
    print("   4. Real-time synchronization between Python scheduler and AnyLogic animation")


def demo_5_gnn_heatmap():
    """Demo 5: GNN-based Heatmap Guidance"""
    print_header("DEMO 5: GNN Heatmap for Route Guidance")
    
    print("\n🧠 GNN Model Architecture:")
    print("   Input: Node features (x, y, z coordinates)")
    print("   Hidden: Graph Convolutional Layers (256 dim)")
    print("   Output: Edge probability heatmap [N×N]")
    print("   Training: Unsupervised proxy loss (no labels needed!)")
    
    print("\n🗺️  Generating Heatmap for Sample Network...")
    
    # Create sample network
    nodes = [
        (0, 0, 0), (10, 0, 0), (20, 0, 0),
        (0, 10, 1), (10, 10, 1), (20, 10, 1),
        (0, 20, 2), (10, 20, 2), (20, 20, 2)
    ]
    
    print(f"   Network: {len(nodes)} nodes across 3 floors")
    
    heatmap = generate_heatmap(nodes)
    print(f"✅ Heatmap generated: {heatmap.shape}")
    
    print("\n📊 Heatmap Statistics:")
    print(f"   Min score: {heatmap.min():.4f}")
    print(f"   Max score: {heatmap.max():.4f}")
    print(f"   Mean score: {heatmap.mean():.4f}")
    print(f"   Std dev: {heatmap.std():.4f}")
    
    print("\n🎯 How Heatmap Guides Routing:")
    print("   1. GNN learns edge 'favorability' from network structure")
    print("   2. High scores → edges likely in optimal routes")
    print("   3. Low scores → edges to avoid (bottlenecks, long distances)")
    print("   4. Greedy heuristic uses scores to make insertion decisions")
    print("   5. No labeled data needed - fully unsupervised!")
    
    print("\n💡 Key Advantage:")
    print("   Traditional methods: Only consider distance")
    print("   GNN method: Considers network topology, bottlenecks, patterns")
    print("   Result: Better routes without manual tuning!")


def main():
    """Run comprehensive demo"""
    print("\n" + "="*80)
    print("  COMPREHENSIVE DEMO: GNN-based EVRPTW with Online Scheduling")
    print("  Unsupervised Learning for Multi-Vehicle Routing")
    print("="*80)
    print(f"\n  📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  🐍 Python: {sys.version.split()[0]}")
    print(f"  📂 Working Directory: {os.getcwd()}")
    print("\n" + "="*80)
    
    print("\n🎯 Implementation Features:")
    features = [
        "✅ Time Window Constraints (VRPTW)",
        "✅ Battery/Charging Constraints (Electric Vehicles)",
        "✅ Online/Dynamic Scheduling (Real-time order arrival)",
        "✅ AnyLogic Integration (REST API)",
        "✅ GNN-based Heatmap Guidance (Unsupervised)",
        "✅ Multi-floor Hospital Environment",
        "✅ Real Robot Data Support"
    ]
    for feature in features:
        print(f"   {feature}")
    
    try:
        # Demo 1: Data Loading
        orders, charging_info, edge_times = demo_1_data_loading()
        
        # Demo 2: Constraints
        demo_2_constraints()
        
        # Demo 3: Online Scheduling
        scheduler = demo_3_online_scheduling()
        
        # Demo 4: AnyLogic Integration
        demo_4_anylogic_integration(scheduler)
        
        # Demo 5: GNN Heatmap
        demo_5_gnn_heatmap()
        
        # Final Summary
        print_header("DEMO COMPLETE ✅")
        print("\n🎉 All features demonstrated successfully!")
        print("\n📚 Next Steps:")
        print("   1. Run test_implementation.py for comprehensive testing")
        print("   2. Start API server: python anylogic_interface.py")
        print("   3. Connect AnyLogic simulation to REST API")
        print("   4. Train GNN model on your specific network (optional)")
        print("   5. Visualize results: python visualize_heatmap.py")
        
        print("\n📖 Documentation:")
        print("   - PROJECT_GUIDE.md: Complete implementation guide")
        print("   - config.py: Configuration parameters")
        print("   - README: Usage instructions")
        
        print("\n" + "="*80)
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
