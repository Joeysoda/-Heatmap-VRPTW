
import math
import numpy as np
from config import *

def dist_func(p1, p2):
    """
    Calculate distance between two points (x,y,z).
    Cost/Time = Manhattan(xy) + abs(diff_z) * FLOOR_PENALTY
    """
    d = abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])
    floor_diff = abs(p1[2] - p2[2])
    return d + floor_diff * FLOOR_PENALTY

class AGV:
    def __init__(self, agv_id):
        self.id = agv_id
        self.route = [] # List of orders
        # Cache for total time to avoid recomputing constantly
        self._total_time = 0.0
        
    def update_total_time(self):
        """Recompute total time based on current route."""
        if not self.route:
            self._total_time = 0.0
            return
            
        t = 0.0
        # 1. First order (no setup cost from depot)
        t += dist_func(
            (self.route[0]['start_x'], self.route[0]['start_y'], self.route[0]['start_z']),
            (self.route[0]['end_x'], self.route[0]['end_y'], self.route[0]['end_z'])
        )
        
        # 2. Subsequent orders
        for i in range(1, len(self.route)):
            prev = self.route[i-1]
            curr = self.route[i]
            
            # Setup: Prev End -> Curr Start
            t += dist_func(
                (prev['end_x'], prev['end_y'], prev['end_z']),
                (curr['start_x'], curr['start_y'], curr['start_z'])
            )
            
            # Execution: Curr Start -> Curr End
            t += dist_func(
                (curr['start_x'], curr['start_y'], curr['start_z']),
                (curr['end_x'], curr['end_y'], curr['end_z'])
            )
        self._total_time = t

    @property
    def total_time(self):
        return self._total_time

def get_order_coords(order):
    return (order['start_x'], order['start_y'], order['start_z']), \
           (order['end_x'], order['end_y'], order['end_z'])

def solve_allocation(orders, heatmap, node_to_idx):
    """
    Allocate orders to AGVs using the specified 2-stage GCN-guided heuristic.
    heatmap: [N, N] score matrix for physical nodes
    node_to_idx: Dict mapping (x, y, z) -> index in heatmap
    """
    agvs = [AGV(i) for i in range(AGV_NUM)]
    
    # Helper to safely get heat
    def get_heat(p1, p2):
        try:
            idx1 = node_to_idx[p1]
            idx2 = node_to_idx[p2]
            return heatmap[idx1, idx2]
        except KeyError:
            # Fallback if node not in map (should not happen if built correctly)
            return 0.0

    for order_idx, order in enumerate(orders):
        order_s, order_e = get_order_coords(order)
        
        # Determine Stage
        # Stage 1: Exists at least one empty vehicle
        empty_agvs = [a for a in agvs if not a.route]
        is_stage_1 = len(empty_agvs) > 0
        
        candidates = empty_agvs if is_stage_1 else agvs
        
        best_score = float('inf')
        best_move = None # (agv_index, insert_pos, delta_dist)
        
        # Iterate over candidate vehicles
        for agv in candidates:
            num_positions = len(agv.route) + 1
            
            for pos in range(num_positions):
                delta_dist = 0.0
                delta_heat = 0.0
                
                # Order internal distance (always added)
                internal_dist = dist_func(order_s, order_e)
                delta_dist += internal_dist
                
                # Heatmap: Internal heat (s -> e)
                delta_heat += get_heat(order_s, order_e)
                
                # --- Calculate Connections ---
                
                # Case 1: Empty Route (Stage 1)
                if not agv.route:
                    # No setup cost.
                    pass
                    
                # Case 2: Non-Empty Route
                else:
                    prev_node = None
                    next_node = None
                    
                    # Predecessor
                    if pos > 0:
                        prev_order = agv.route[pos-1]
                        prev_node = (prev_order['end_x'], prev_order['end_y'], prev_order['end_z'])
                        
                    # Successor
                    if pos < len(agv.route):
                        next_order = agv.route[pos]
                        next_node = (next_order['start_x'], next_order['start_y'], next_order['start_z'])
                    
                    # Add: Prev -> New
                    if prev_node:
                        delta_dist += dist_func(prev_node, order_s)
                        delta_heat += get_heat(prev_node, order_s)
                    
                    # Add: New -> Next
                    if next_node:
                        delta_dist += dist_func(order_e, next_node)
                        delta_heat += get_heat(order_e, next_node)
                        
                    # Remove: Prev -> Next (if existing link broken)
                    if prev_node and next_node:
                        delta_dist -= dist_func(prev_node, next_node)
                        delta_heat -= get_heat(prev_node, next_node)
                        
                # --- Score Calculation ---
                current_time = agv.total_time
                new_total_time = current_time + delta_dist
                
                score = (LAMBDA_DIST * delta_dist) + (LAMBDA_LOAD * new_total_time) - (GAMMA_HEAT * delta_heat)
                
                if score < best_score:
                    best_score = score
                    best_move = (agv.id, pos, delta_dist)
        
        # Execute Best Move
        if best_move:
            agv_id, pos, cost_inc = best_move
            target_agv = agvs[agv_id] # ID matches index 0-8
            target_agv.route.insert(pos, order)
            target_agv.update_total_time()
        else:
            print(f"Warning: Could not assign order {order['id']}")
            
    return agvs

def compute_vehicle_costs(agv):
    """
    Compute detailed costs for a single vehicle.
    """
    exec_time = 0.0
    setup_time = 0.0
    
    if not agv.route:
        return {
            'exec_time': 0, 'setup_time': 0, 'total_time': 0,
            'local_cost': 0
        }
        
    # 1. Execution Time (Sum of all orders)
    for o in agv.route:
        s, e = get_order_coords(o)
        exec_time += dist_func(s, e)
        
    # 2. Setup Time (Transitions)
    for i in range(len(agv.route) - 1):
        curr = agv.route[i]
        next_o = agv.route[i+1]
        setup_time += dist_func(
            (curr['end_x'], curr['end_y'], curr['end_z']),
            (next_o['start_x'], next_o['start_y'], next_o['start_z'])
        )
        
    # Raw Total
    total_time = exec_time + setup_time
    
    # Log Scaling
    # wait/lift are 0
    exec_scaled = math.log1p(exec_time / ALPHA_E)
    setup_scaled = math.log1p(setup_time / ALPHA_S)
    
    # Local Cost
    local_cost = (BETA_E * exec_scaled) + (BETA_S * setup_scaled)
    
    return {
        'exec_time': exec_time,
        'setup_time': setup_time,
        'total_time': total_time,
        'local_cost': local_cost
    }

def compute_global_costs(agvs):
    """
    Compute global system metrics.
    """
    per_vehicle = [compute_vehicle_costs(a) for a in agvs]
    
    makespan = max((v['total_time'] for v in per_vehicle), default=0.0)
    sum_local_cost = sum(v['local_cost'] for v in per_vehicle)
    
    # Total raw travel time (for comparison)
    total_travel = sum(v['total_time'] for v in per_vehicle)
    
    # Global Objective
    total_cost = (BETA_M * makespan) + (BETA_SUM * sum_local_cost)
    
    return {
        'makespan': makespan,
        'total_travel': total_travel,
        'local_cost': sum_local_cost,
        'total_cost': total_cost,
        'per_vehicle': per_vehicle
    }

def print_solution(agvs):
    print("\n--- Final Solution ---")
    for agv in agvs:
        if agv.route:
            costs = compute_vehicle_costs(agv)
            route_ids = [str(o['id']) for o in agv.route]
            print(f"AGV {agv.id}: {len(agv.route)} orders, "
                  f"Time: {costs['total_time']:.1f} (Exec: {costs['exec_time']:.1f}, Setup: {costs['setup_time']:.1f})")
            print(f"  Route: {' -> '.join(route_ids)}")
