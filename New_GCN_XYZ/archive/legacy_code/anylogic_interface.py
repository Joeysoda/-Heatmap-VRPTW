"""
AnyLogic Integration Interface
Provides API for communication between Python scheduler and AnyLogic simulation
"""

from flask import Flask, request, jsonify
import json
from datetime import datetime
from online_scheduler import OnlineScheduler
from data_loader import extract_charging_stations, load_edge_travel_times
from config import *
import threading
import time


class AnyLogicInterface:
    """
    Interface for AnyLogic simulation integration.
    Provides REST API endpoints for:
    - Receiving orders from AnyLogic
    - Sending AGV assignments back to AnyLogic
    - Updating AGV status
    - Querying scheduler state
    """
    
    def __init__(self, scheduler, host='localhost', port=5000):
        """
        Initialize AnyLogic interface.
        
        Args:
            scheduler: OnlineScheduler instance
            host: API host address
            port: API port number
        """
        self.scheduler = scheduler
        self.app = Flask(__name__)
        self.host = host
        self.port = port
        
        # Setup routes
        self._setup_routes()
        
        # Background thread for scheduler updates
        self.running = False
        self.update_thread = None
    
    def _setup_routes(self):
        """Setup Flask API routes."""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint."""
            return jsonify({
                'status': 'running',
                'current_time': self.scheduler.current_time,
                'num_agvs': len(self.scheduler.agvs)
            })
        
        @self.app.route('/order/add', methods=['POST'])
        def add_order():
            """
            Add a new order from AnyLogic.
            
            Expected JSON format:
            {
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
            """
            try:
                data = request.json
                
                # Parse order
                order = {
                    'id': data['order_id'],
                    'start_node': data['start_node'],
                    'end_node': data['end_node'],
                    'start_x': float(data['start_x']),
                    'start_y': float(data['start_y']),
                    'start_z': float(data['start_z']),
                    'end_x': float(data['end_x']),
                    'end_y': float(data['end_y']),
                    'end_z': float(data['end_z']),
                }
                
                # Parse time windows if provided
                if 'pickup_tw_start' in data:
                    order['pickup_tw_start'] = datetime.fromisoformat(data['pickup_tw_start'])
                if 'pickup_tw_end' in data:
                    order['pickup_tw_end'] = datetime.fromisoformat(data['pickup_tw_end'])
                if 'delivery_tw_start' in data:
                    order['delivery_tw_start'] = datetime.fromisoformat(data['delivery_tw_start'])
                if 'delivery_tw_end' in data:
                    order['delivery_tw_end'] = datetime.fromisoformat(data['delivery_tw_end'])
                
                arrival_time = data.get('arrival_time', self.scheduler.current_time)
                
                # Add order to scheduler
                self.scheduler.add_order(order, arrival_time)
                
                # Get assignment
                assignment = self._get_order_assignment(order['id'])
                
                return jsonify({
                    'status': 'success',
                    'order_id': order['id'],
                    'assignment': assignment
                })
                
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 400
        
        @self.app.route('/agv/status', methods=['POST'])
        def update_agv_status():
            """
            Update AGV status from AnyLogic.
            
            Expected JSON format:
            {
                "agv_id": 0,
                "current_x": 10.5,
                "current_y": 20.3,
                "current_z": 0,
                "battery_level": 8500.0,
                "current_time": 1200.5,
                "status": "idle" | "busy" | "charging"
            }
            """
            try:
                data = request.json
                agv_id = int(data['agv_id'])
                
                if 0 <= agv_id < len(self.scheduler.agvs):
                    agv = self.scheduler.agvs[agv_id]
                    
                    # Update location
                    if all(k in data for k in ['current_x', 'current_y', 'current_z']):
                        agv.current_location = (
                            float(data['current_x']),
                            float(data['current_y']),
                            float(data['current_z'])
                        )
                    
                    # Update battery
                    if 'battery_level' in data:
                        agv.battery_level = float(data['battery_level'])
                    
                    # Update time
                    if 'current_time' in data:
                        agv.current_time = float(data['current_time'])
                    
                    return jsonify({
                        'status': 'success',
                        'agv_id': agv_id
                    })
                else:
                    return jsonify({
                        'status': 'error',
                        'message': f'Invalid AGV ID: {agv_id}'
                    }), 400
                    
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 400
        
        @self.app.route('/agv/route/<int:agv_id>', methods=['GET'])
        def get_agv_route(agv_id):
            """Get current route for an AGV."""
            try:
                if 0 <= agv_id < len(self.scheduler.agvs):
                    agv = self.scheduler.agvs[agv_id]
                    
                    route = []
                    for task in agv.route:
                        route.append({
                            'order_id': task['id'],
                            'type': task.get('type', 'delivery'),
                            'start_node': task.get('start_node', ''),
                            'end_node': task.get('end_node', ''),
                            'start_x': task['start_x'],
                            'start_y': task['start_y'],
                            'start_z': task['start_z'],
                            'end_x': task.get('end_x', task['start_x']),
                            'end_y': task.get('end_y', task['start_y']),
                            'end_z': task.get('end_z', task['start_z'])
                        })
                    
                    return jsonify({
                        'status': 'success',
                        'agv_id': agv_id,
                        'route': route,
                        'num_tasks': len(route),
                        'battery_level': agv.battery_level
                    })
                else:
                    return jsonify({
                        'status': 'error',
                        'message': f'Invalid AGV ID: {agv_id}'
                    }), 400
                    
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 400
        
        @self.app.route('/scheduler/status', methods=['GET'])
        def get_scheduler_status():
            """Get current scheduler status."""
            try:
                stats = self.scheduler.get_statistics()
                
                return jsonify({
                    'status': 'success',
                    'statistics': stats,
                    'agv_status': [
                        {
                            'agv_id': agv.id,
                            'num_tasks': len(agv.route),
                            'battery_level': agv.battery_level,
                            'total_time': agv.total_time
                        }
                        for agv in self.scheduler.agvs
                    ]
                })
                
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 400
        
        @self.app.route('/scheduler/step', methods=['POST'])
        def step_scheduler():
            """Manually step the scheduler forward."""
            try:
                data = request.json
                time_delta = data.get('time_delta', 1.0)
                
                self.scheduler.step(time_delta)
                
                return jsonify({
                    'status': 'success',
                    'current_time': self.scheduler.current_time
                })
                
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 400
    
    def _get_order_assignment(self, order_id):
        """Get AGV assignment for an order."""
        for agv in self.scheduler.agvs:
            for idx, task in enumerate(agv.route):
                if task['id'] == order_id:
                    return {
                        'agv_id': agv.id,
                        'position': idx,
                        'estimated_start_time': agv.current_time  # Simplified
                    }
        return None
    
    def start(self, threaded=True):
        """Start the API server."""
        if threaded:
            self.running = True
            self.update_thread = threading.Thread(target=self._background_update)
            self.update_thread.daemon = True
            self.update_thread.start()
        
        print(f"Starting AnyLogic Interface on {self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, threaded=True)
    
    def _background_update(self):
        """Background thread for periodic scheduler updates."""
        while self.running:
            time.sleep(1.0)  # Update every second
            self.scheduler.step(1.0)
    
    def stop(self):
        """Stop the interface."""
        self.running = False
        if self.update_thread:
            self.update_thread.join()


def create_interface_from_config():
    """
    Create AnyLogic interface with default configuration.
    Loads charging stations and initializes scheduler.
    """
    # Load charging stations
    charging_info = extract_charging_stations(ROBOT_MISSION_FILE)
    charging_stations = [(0, 0, 0)]  # Placeholder - need actual coordinates
    
    # Create dummy scheduler (will be replaced with actual GCN model)
    from online_scheduler import OnlineScheduler
    import numpy as np
    
    # Dummy heatmap and node mapping
    heatmap = np.ones((100, 100)) * 0.5
    node_to_idx = {}
    
    scheduler = OnlineScheduler(
        gcn_model=None,
        heatmap=heatmap,
        node_to_idx=node_to_idx,
        charging_stations=charging_stations,
        num_agvs=AGV_NUM
    )
    
    interface = AnyLogicInterface(scheduler)
    return interface


if __name__ == '__main__':
    # Example usage
    interface = create_interface_from_config()
    interface.start()
