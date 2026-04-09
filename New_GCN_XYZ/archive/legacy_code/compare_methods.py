from solver import AGV, dist_func, get_order_coords

# -----------------------------------------------------------------------------
# Baseline Algorithms
# -----------------------------------------------------------------------------

def calculate_insertion_cost(agv, order, pos):
    """
    Calculate the increase in travel time (cost) if order is inserted at pos.
    Returns: delta_dist
    """
    order_s, order_e = get_order_coords(order)
    delta_dist = 0.0
    
    # 1. Internal distance (always added)
    delta_dist += dist_func(order_s, order_e)
    
    # 2. Connections
    # Case: Empty Route
    if not agv.route:
        pass
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
        
        # Add: New -> Next
        if next_node:
            delta_dist += dist_func(order_e, next_node)
            
        # Remove: Prev -> Next (if existing link broken)
        if prev_node and next_node:
            delta_dist -= dist_func(prev_node, next_node)
            
    return delta_dist

def solve_best_fit(orders, agv_num):
    """
    Best Fit (Greedy Insertion):
    For each order, place it in the AGV and position that minimizes the *global* increase in total travel time.
    """
    agvs = [AGV(i) for i in range(agv_num)]
    
    for order in orders:
        best_cost = float('inf')
        best_move = None # (agv_idx, pos)
        
        for agv in agvs:
            num_positions = len(agv.route) + 1
            for pos in range(num_positions):
                cost_inc = calculate_insertion_cost(agv, order, pos)
                if cost_inc < best_cost:
                    best_cost = cost_inc
                    best_move = (agv.id, pos)
        
        if best_move:
            agv = agvs[best_move[0]]
            agv.route.insert(best_move[1], order)
            agv.update_total_time()
            
    return agvs

def solve_first_fit(orders, agv_num):
    """
    First Fit (Round Robin):
    Assign orders to AGVs in a cyclic order (0, 1, 2, ...).
    Inside the assigned AGV, find the best insertion position.
    """
    agvs = [AGV(i) for i in range(agv_num)]
    
    for i, order in enumerate(orders):
        # Select AGV in round-robin fashion
        agv_idx = i % agv_num
        agv = agvs[agv_idx]
        
        # Find best position within THIS AGV
        best_pos = 0
        best_cost = float('inf')
        
        num_positions = len(agv.route) + 1
        for pos in range(num_positions):
            cost_inc = calculate_insertion_cost(agv, order, pos)
            if cost_inc < best_cost:
                best_cost = cost_inc
                best_pos = pos
        
        # Insert
        agv.route.insert(best_pos, order)
        agv.update_total_time()
        
    return agvs

def solve_nearest_neighbor(orders, agv_num):
    """
    Nearest Neighbor (Spatial Greedy):
    Assign order to the AGV whose LAST location is closest to the order's START location.
    Append to the end of that AGV's route.
    """
    agvs = [AGV(i) for i in range(agv_num)]
    
    for order in orders:
        order_s, order_e = get_order_coords(order)
        
        best_agv = None
        min_dist = float('inf')
        
        for agv in agvs:
            if not agv.route:
                # Empty AGV: Distance is 0 (ideal candidate usually)
                dist = 0 
            else:
                last_order = agv.route[-1]
                last_pos = (last_order['end_x'], last_order['end_y'], last_order['end_z'])
                dist = dist_func(last_pos, order_s)
            
            if dist < min_dist:
                min_dist = dist
                best_agv = agv
                
        # Append to end
        best_agv.route.append(order)
        best_agv.update_total_time()
        
    return agvs
