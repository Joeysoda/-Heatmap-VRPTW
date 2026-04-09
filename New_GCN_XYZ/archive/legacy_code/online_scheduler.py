"""
Online Scheduler for Dynamic Order Arrival
Implements rolling horizon optimization with time windows and charging constraints
"""

import numpy as np
from datetime import datetime, timedelta
from config import *
from solver import AGV, dist_func, check_time_window_feasibility, check_battery_feasibility, create_charging_task
import heapq


class OnlineScheduler:
    """
    Online scheduler for dynamic AGV routing with:
    - Dynamic order arrival
    - Time window constraints
    - Battery/charging constraints
    - Real-time AGV status updates
    """
    
    def __init__(self, gcn_model, heatmap, node_to_idx, charging_stations, num_agvs=9, start_time=0):
        """
        Initialize online scheduler.
        
        Args:
            gcn_model: Trained GCN model for heatmap generation
            heatmap: Pre-computed heatmap [N, N]
            node_to_idx: Mapping from (x,y,z) to heatmap index
            charging_stations: List of charging station coordinates
            num_agvs: Number of AGVs
            start_time: Simulation start time (seconds or datetime)
        """
        self.gcn_model = gcn_model
        self.heatmap = heatmap
        self.node_to_idx = node_to_idx
        self.charging_stations = charging_stations
        
        # Initialize AGVs
        self.agvs = [AGV(i, start_time=start_time) for i in range(num_agvs)]
        for agv in self.agvs:
            agv.charging_stations = charging_stations
        
        # Order management
        self.pending_orders = []  # Orders waiting to be assigned
        self.assigned_orders = []  # Orders already assigned
        self.completed_orders = []  # Orders completed
        
        # Event queue (priority queue of events)
        self.event_queue = []  # (time, event_type, agv_id, data)
        
        # Current simulation time
        self.current_time = start_time
        
        # Statistics
        self.stats = {
            'total_orders': 0,
            'completed_orders': 0,
            'late_orders': 0,
            'charging_events': 0,
            'total_distance': 0.0
        }
    
    def add_order(self, order, arrival_time=None):
        """
        Add a dynamically arriving order.
        
        Args:
            order: Order dictionary with coordinates and time windows
            arrival_time: Time when order arrives (None = current time)
        """
        if arrival_time is None:
            arrival_time = self.current_time
        
        order['arrival_time'] = arrival_time
        self.pending_orders.append(order)
        self.stats['total_orders'] += 1
        
        # Trigger immediate assignment if order is urgent
        if self._is_urgent(order):
            self._assign_pending_orders()
    
    def _is_urgent(self, order):
        """Check if order is urgent (tight time window)."""
        if 'pickup_tw_end' not in order:
            return False
        
        if isinstance(order['pickup_tw_end'], datetime):
            time_until_deadline = (order['pickup_tw_end'] - datetime.now()).total_seconds()
            return time_until_deadline < 300  # Less than 5 minutes
        return False
    
    def _assign_pending_orders(self):
        """Assign all pending orders to AGVs using GCN-guided heuristic."""
        if not self.pending_orders:
            return
        
        # Helper to get heatmap value
        def get_heat(p1, p2):
            try:
                idx1 = self.node_to_idx[p1]
                idx2 = self.node_to_idx[p2]
                return self.heatmap[idx1, idx2]
            except KeyError:
                return 0.0
        
        # Sort orders by urgency (earliest deadline first)
        self.pending_orders.sort(key=lambda o: o.get('pickup_tw_end', float('inf')))
        
        assigned_count = 0
        for order in list(self.pending_orders):
            order_s = (order['start_x'], order['start_y'], order['start_z'])
            order_e = (order['end_x'], order['end_y'], order['end_z'])
            
            best_score = float('inf')
            best_agv = None
            best_pos = None
            needs_charging = False
            charging_station = None
            
            # Try to assign to each AGV
            for agv in self.agvs:
                # Skip if AGV is currently executing a task
                if self._is_agv_busy(agv):
                    continue
                
                num_positions = len(agv.route) + 1
                
                for pos in range(num_positions):
                    # Check time window feasibility
                    tw_feasible, _, _ = check_time_window_feasibility(agv, order, pos)
                    if not tw_feasible:
                        continue
                    
                    # Check battery feasibility
                    battery_feasible, needs_charge, charge_station = check_battery_feasibility(
                        agv, order, pos, self.charging_stations
                    )
                    if not battery_feasible:
                        continue
                    
                    # Calculate score
                    delta_dist = 0.0
                    delta_heat = 0.0
                    
                    # Order internal distance
                    internal_dist = dist_func(order_s, order_e)
                    delta_dist += internal_dist
                    delta_heat += get_heat(order_s, order_e)
                    
                    # Connection costs
                    if agv.route:
                        prev_node = None
                        next_node = None
                        
                        if pos > 0:
                            prev_order = agv.route[pos-1]
                            prev_node = (prev_order.get('end_x', prev_order['start_x']), 
                                       prev_order.get('end_y', prev_order['start_y']), 
                                       prev_order.get('end_z', prev_order['start_z']))
                        
                        if pos < len(agv.route):
                            next_order = agv.route[pos]
                            next_node = (next_order['start_x'], next_order['start_y'], next_order['start_z'])
                        
                        if prev_node:
                            delta_dist += dist_func(prev_node, order_s)
                            delta_heat += get_heat(prev_node, order_s)
                        
                        if next_node:
                            delta_dist += dist_func(order_e, next_node)
                            delta_heat += get_heat(order_e, next_node)
                        
                        if prev_node and next_node:
                            delta_dist -= dist_func(prev_node, next_node)
                            delta_heat -= get_heat(prev_node, next_node)
                    
                    # Score calculation
                    current_time = agv.total_time
                    new_total_time = current_time + delta_dist
                    score = (LAMBDA_DIST * delta_dist) + (LAMBDA_LOAD * new_total_time) - (GAMMA_HEAT * delta_heat)
                    
                    # Penalty for needing charging
                    if needs_charge:
                        score += 500  # Charging penalty
                    
                    if score < best_score:
                        best_score = score
                        best_agv = agv
                        best_pos = pos
                        needs_charging = needs_charge
                        charging_station = charge_station
            
            # Assign order to best AGV
            if best_agv is not None:
                # Insert charging task if needed
                if needs_charging and charging_station:
                    charging_task = create_charging_task(charging_station)
                    best_agv.route.insert(best_pos, charging_task)
                    best_agv.update_total_time()
                    best_pos += 1  # Adjust position after charging
                    self.stats['charging_events'] += 1
                
                # Insert order
                best_agv.route.insert(best_pos, order)
                best_agv.update_total_time()
                
                self.pending_orders.remove(order)
                self.assigned_orders.append(order)
                assigned_count += 1
                
                print(f"[{self.current_time:.1f}s] Assigned order {order['id']} to AGV {best_agv.id} at position {best_pos}")
            else:
                print(f"[{self.current_time:.1f}s] Warning: Could not assign order {order['id']}")
        
        return assigned_count
    
    def _is_agv_busy(self, agv):
        """Check if AGV is currently executing a task."""
        # In online mode, AGV is busy if it has started but not completed current task
        return False  # Simplified for now
    
    def step(self, time_delta=1.0):
        """
        Advance simulation by time_delta seconds.
        
        Args:
            time_delta: Time step in seconds
        """
        self.current_time += time_delta
        
        # Process events in event queue
        while self.event_queue and self.event_queue[0][0] <= self.current_time:
            event_time, event_type, agv_id, data = heapq.heappop(self.event_queue)
            self._handle_event(event_type, agv_id, data)
        
        # Update AGV states
        for agv in self.agvs:
            agv.current_time = self.current_time
        
        # Try to assign pending orders
        if self.pending_orders:
            self._assign_pending_orders()
    
    def _handle_event(self, event_type, agv_id, data):
        """Handle simulation events."""
        agv = self.agvs[agv_id]
        
        if event_type == 'task_complete':
            # Task completed
            completed_task = data
            if completed_task.get('type') != 'charge':
                self.completed_orders.append(completed_task)
                self.stats['completed_orders'] += 1
                
                # Check if late
                if 'delivery_tw_end' in completed_task:
                    if self.current_time > completed_task['delivery_tw_end']:
                        self.stats['late_orders'] += 1
            
            # Remove from route
            if completed_task in agv.route:
                agv.route.remove(completed_task)
                agv.update_total_time()
        
        elif event_type == 'battery_low':
            # Battery low - insert charging task
            if self.charging_stations:
                nearest_station = min(self.charging_stations, 
                                    key=lambda s: dist_func(agv.current_location, s))
                charging_task = create_charging_task(nearest_station)
                agv.route.insert(0, charging_task)
                agv.update_total_time()
                self.stats['charging_events'] += 1
    
    def run_until(self, end_time):
        """Run simulation until end_time."""
        while self.current_time < end_time:
            self.step(1.0)
            
            # Check if all orders are completed
            if not self.pending_orders and not self.assigned_orders:
                break
    
    def get_statistics(self):
        """Get current statistics."""
        return {
            **self.stats,
            'current_time': self.current_time,
            'pending_orders': len(self.pending_orders),
            'assigned_orders': len(self.assigned_orders),
            'completion_rate': self.stats['completed_orders'] / max(1, self.stats['total_orders']),
            'late_rate': self.stats['late_orders'] / max(1, self.stats['completed_orders'])
        }
    
    def print_status(self):
        """Print current scheduler status."""
        print(f"\n=== Online Scheduler Status (t={self.current_time:.1f}s) ===")
        print(f"Total orders: {self.stats['total_orders']}")
        print(f"Pending: {len(self.pending_orders)}")
        print(f"Assigned: {len(self.assigned_orders)}")
        print(f"Completed: {self.stats['completed_orders']}")
        print(f"Late orders: {self.stats['late_orders']}")
        print(f"Charging events: {self.stats['charging_events']}")
        
        print(f"\nAGV Status:")
        for agv in self.agvs:
            print(f"  AGV {agv.id}: {len(agv.route)} tasks, Battery: {agv.battery_level:.0f}/{agv.battery_capacity:.0f}")
