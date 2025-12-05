# Hospital AGV Scheduling Project Guide

This guide provides a complete overview of the Hospital AGV Scheduling project, including file structure, dependencies, and full source code. You can use this document to reconstruct the entire project in Cursor or any other IDE.

## 1. Project Overview

This project implements and compares different algorithms for scheduling Automated Guided Vehicles (AGVs) in a hospital environment.
**Core Algorithms:**

1. **GCN-Guided Heuristic**: Uses a Graph Convolutional Network (or MLP fallback) to generate a "heatmap" of edge scores, which guides a greedy insertion heuristic.
2. **Best Fit**: Greedy insertion minimizing global cost increase.
3. **First Fit**: Round-robin assignment with optimal position insertion.
4. **Nearest Neighbor**: Spatially greedy assignment based on the last location.

**Key Metrics:**

- **Makespan**: The maximum time taken by any AGV.
- **Total Cost**: Weighted sum of makespan and local costs.
- **Improvement %**: Performance gain of GCN over the best baseline.

## 2. File Structure

Ensure your project directory matches this structure:

```
project_root/
├── instances/                  # Data directory
│   ├── node.csv                # Node coordinates (Map)
│   └── instances/              # Excel files with orders (*.xlsx)
├── algorithm_comparison_full.png # (Generated) Output plot
├── comparison_results_full.csv   # (Generated) Detailed metrics
├── compare_methods.py          # Baseline algorithm definitions
├── config.py                   # Configuration & Hyperparameters
├── data_loader.py              # Data loading utilities
├── gnn_model.py                # GCN/MLP model definition
├── main.py                     # Entry point: Runs comparison & plotting
├── requirements.txt            # Dependencies
├── solver.py                   # AGV Logic & GCN Heuristic
└── visualize_results.py        # (New) Advanced visualization script
```

## 3. Prerequisites & Installation

### 3.1 Dependencies

Create a `requirements.txt` file:

```txt
numpy
pandas
matplotlib
torch
openpyxl
# Optional: torch-geometric (if using full GNN features)
# torch-scatter
# torch-sparse
```

### 3.2 Installation

```bash
pip install -r requirements.txt
```

## 4. Source Code

Copy the content below into the respective files.

### 4.1 `config.py`

**Note**: Update `BASE_DIR` to match your local path.

```python
import os

# -----------------------------------------------------------------------------
# Environment Settings
# -----------------------------------------------------------------------------
AGV_NUM = 9
FLOOR_PENALTY = 60.0  # Seconds per floor difference

# -----------------------------------------------------------------------------
# File Paths
# -----------------------------------------------------------------------------
# UPDATE THIS PATH TO YOUR PROJECT ROOT
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
# Or use absolute path like: r"d:\1nottingham\Year4a\FYP\hospital-main - 副本"

NODE_FILE = os.path.join(BASE_DIR, "instances", "node.csv")
INSTANCE_DIR = os.path.join(BASE_DIR, "instances", "instances")

# -----------------------------------------------------------------------------
# GCN Model Configuration
# -----------------------------------------------------------------------------
GCN_HIDDEN_DIM = 1
GCN_OUTPUT_DIM = 1
USE_GPU = True
GPU_ID = 0

# -----------------------------------------------------------------------------
# Heuristic Hyperparameters (Score Calculation)
# -----------------------------------------------------------------------------
# score = lambda_dist * delta_dist + lambda_load * delta_load - gamma * delta_heat
LAMBDA_DIST = 0.5
LAMBDA_LOAD = 0.1  # Penalize increase in total time (load balancing)
GAMMA_HEAT = 200.0  # Heatmap reward weight

# -----------------------------------------------------------------------------
# Cost Function Hyperparameters (Offline Evaluation)
# -----------------------------------------------------------------------------
# Scaling factors for log transformation: log(1 + t / alpha)
ALPHA_W = 60.0
ALPHA_S = 60.0
ALPHA_E = 60.0
ALPHA_L = 60.0

# Weights for local cost components
# cost_v = beta_w * wait + beta_s * setup + beta_e * exec + beta_l * lift
BETA_W = 0.0
BETA_S = 1.0
BETA_E = 1.0
BETA_L = 0.0

# Weights for global cost
# total_cost = beta_m * makespan + beta_sum * sum(local_costs)
BETA_M = 1.0
BETA_SUM = 0.0
```

### 4.2 `data_loader.py`

```python
import pandas as pd
import os
import numpy as np

def load_nodes(node_file_path):
    """
    Load node information from csv file.
    Returns a dictionary: {NodeName: (X, Y, Z)}
    """
    if not os.path.exists(node_file_path):
        raise FileNotFoundError(f"Node file not found: {node_file_path}")
      
    try:
        df = pd.read_csv(node_file_path)
        # Clean column names
        df.columns = [c.strip() for c in df.columns]
      
        node_map = {}
        required = {'NodeName', 'X', 'Y', 'Z'}
        if not required.issubset(set(df.columns)):
            raise ValueError("node.csv missing required columns: NodeName, X, Y, Z")
          
        for _, row in df.iterrows():
            node_map[str(row['NodeName']).strip()] = (float(row['X']), float(row['Y']), float(row['Z']))
              
        print(f"Loaded {len(node_map)} nodes from {node_file_path}")
        return node_map
    except Exception as e:
        print(f"Error loading nodes: {e}")
        return {}

def load_orders(instance_file_path, node_map=None):
    """
    Load orders from an xlsx file.
    Supports standard format or simplified 3-column format [No, StartNode, EndNode].
    Returns a list of dictionaries with coordinates.
    """
    if not os.path.exists(instance_file_path):
        raise FileNotFoundError(f"Instance file not found: {instance_file_path}")
      
    try:
        # Attempt to read the file
        df = pd.read_excel(instance_file_path)
    except Exception as e:
        print(f"Failed to read excel {instance_file_path}: {e}")
        return []
      
    orders = []
  
    # Normalize column names
    df.columns = [str(c).strip() for c in df.columns]
    col_map = {c.lower(): c for c in df.columns}
  
    # Logic to handle 3-column format (No, StartNode, EndNode) without headers or with different headers
    if not any(k in col_map for k in ['startx', 'starty', 'startz', 'start_node', 'startnode']):
        try:
            df_raw = pd.read_excel(instance_file_path, header=None)
            # Check if it looks like the 3-column format
            if df_raw.shape[1] >= 3:
                first_row = [str(x).strip().lower() for x in df_raw.iloc[0, :3].tolist()]
                # Check for header keywords
                if {'no', 'start_node', 'end_node'}.issubset(set(first_row)):
                    df = df_raw.iloc[1:].copy()
                    df.columns = ['no', 'start_node', 'end_node']
                    col_map = {c.lower(): c for c in df.columns}
        except Exception:
            pass

    for idx, row in df.iterrows():
        order_data = {}
      
        # 1. Parse ID
        if 'no' in col_map:
            order_data['id'] = row[col_map['no']]
        elif 'ordernum' in col_map:
            order_data['id'] = row[col_map['ordernum']]
        else:
            order_data['id'] = idx
          
        # 2. Parse Coordinates
        # Case A: Explicit coordinates
        if all(k in col_map for k in ['startx', 'starty', 'startz', 'endx', 'endy', 'endz']):
            order_data['start_x'] = float(row[col_map['startx']])
            order_data['start_y'] = float(row[col_map['starty']])
            order_data['start_z'] = float(row[col_map['startz']])
            order_data['end_x'] = float(row[col_map['endx']])
            order_data['end_y'] = float(row[col_map['endy']])
            order_data['end_z'] = float(row[col_map['endz']])
          
        # Case B: Node names (requires node_map)
        elif node_map and ('startnode' in col_map or 'start_node' in col_map) and ('endnode' in col_map or 'end_node' in col_map):
            s_key = 'startnode' if 'startnode' in col_map else 'start_node'
            e_key = 'endnode' if 'endnode' in col_map else 'end_node'
          
            s_node = str(row[col_map[s_key]]).strip()
            e_node = str(row[col_map[e_key]]).strip()
          
            if s_node in node_map and e_node in node_map:
                sx, sy, sz = node_map[s_node]
                ex, ey, ez = node_map[e_node]
                order_data['start_x'] = sx
                order_data['start_y'] = sy
                order_data['start_z'] = sz
                order_data['end_x'] = ex
                order_data['end_y'] = ey
                order_data['end_z'] = ez
            else:
                print(f"Warning: Node lookup failed for order {order_data['id']} ({s_node} -> {e_node})")
                continue
      
        # Case C: Fallback for unnamed columns (assuming 3-column format)
        else:
             try:
                vals = row.values
                if len(vals) >= 3 and node_map:
                     # Assume [ID, StartNode, EndNode]
                     s_node = str(vals[1]).strip()
                     e_node = str(vals[2]).strip()
                     if s_node in node_map and e_node in node_map:
                        sx, sy, sz = node_map[s_node]
                        ex, ey, ez = node_map[e_node]
                        order_data['start_x'] = sx
                        order_data['start_y'] = sy
                        order_data['start_z'] = sz
                        order_data['end_x'] = ex
                        order_data['end_y'] = ey
                        order_data['end_z'] = ez
                        order_data['id'] = vals[0]
                     else:
                         continue
                else:
                    continue
             except:
                 continue

        orders.append(order_data)
      
    print(f"Loaded {len(orders)} orders from {instance_file_path}")
    return orders
```

### 4.3 `gnn_model.py`

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import os
from config import USE_GPU, GPU_ID

# Check for PyTorch Geometric
try:
    from torch_geometric.nn import GCNConv
    HAS_PYG = True
except ImportError:
    HAS_PYG = False
    print("Warning: torch_geometric not found. Using simple fallback model.")

class GCNHeatmapModel(nn.Module):
    def __init__(self, input_dim=6, hidden_dim=256, output_dim=1, device=None):
        super(GCNHeatmapModel, self).__init__()
        self.has_pyg = HAS_PYG
      
        if device is None:
            device = torch.device(f"cuda:{GPU_ID}" if USE_GPU and torch.cuda.is_available() else "cpu")
        self.device = device
      
        if self.has_pyg:
            # Use GCN for graph reasoning
            self.conv1 = GCNConv(input_dim, hidden_dim)
            self.conv2 = GCNConv(hidden_dim, hidden_dim)
        else:
            # Simple MLP Fallback
            self.fc1 = nn.Linear(input_dim, hidden_dim)
            self.fc2 = nn.Linear(hidden_dim, hidden_dim)

        # Edge Scorer: Concatenate two node embeddings -> Score
        # Input: hidden_dim * 2 (Source + Target)
        self.edge_scorer = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid() # Output probability/score between 0 and 1
        )
      
        self.to(self.device)

    def forward(self, x, edge_index=None):
        """
        Args:
            x: Node features [NumNodes, InputDim]
            edge_index: Edge list [2, NumEdges] (required for GNN)
        Returns:
            heatmap: [NumNodes, NumNodes] matrix of scores
        """
        x = x.to(self.device)
        if edge_index is not None:
            edge_index = edge_index.to(self.device)
          
        # 1. Node Embedding
        if self.has_pyg and edge_index is not None:
            x = self.conv1(x, edge_index)
            x = F.elu(x)
            x = self.conv2(x, edge_index)
        else:
            x = F.relu(self.fc1(x))
            x = self.fc2(x)
          
        # 2. Pairwise Edge Scoring
        num_nodes = x.size(0)
      
        # Broadcast to form pairs (i, j)
        # x_i: [N, 1, H] -> Source features repeated for each target
        x_i = x.unsqueeze(1).repeat(1, num_nodes, 1)
        # x_j: [1, N, H] -> Target features repeated for each source
        x_j = x.unsqueeze(0).repeat(num_nodes, 1, 1)
      
        # Concatenate: [N, N, 2H]
        pair_feat = torch.cat([x_i, x_j], dim=-1)
      
        # Score: [N, N, 1] -> [N, N]
        heatmap = self.edge_scorer(pair_feat).squeeze(-1)
      
        return heatmap

def generate_heatmap(unique_nodes, model_path=None):
    """
    Generate heatmap for the given list of unique PHYSICAL nodes.
    unique_nodes: List of (x, y, z) tuples.
  
    Returns:
        heatmap: [N, N] numpy array
    """
    if not unique_nodes:
        return np.zeros((0, 0))
      
    # 1. Construct Node Features
    # Node feature: (x, y, z) -> Input Dim = 3
    scale = 1000.0 
    features = []
    for (x, y, z) in unique_nodes:
        features.append([x / scale, y / scale, z])
      
    device = torch.device(f"cuda:{GPU_ID}" if USE_GPU and torch.cuda.is_available() else "cpu")
    x = torch.tensor(features, dtype=torch.float, device=device)
    num_nodes = len(unique_nodes)
  
    # Create fully connected edges
    if HAS_PYG:
        rows, cols = [], []
        for i in range(num_nodes):
            for j in range(num_nodes):
                # Fully connected
                rows.append(i)
                cols.append(j)
        edge_index = torch.tensor([rows, cols], dtype=torch.long, device=device)
    else:
        edge_index = None
      
    # Input dim is 3 (x, y, z)
    model = GCNHeatmapModel(input_dim=3, device=device)
  
    if model_path and os.path.exists(model_path):
        try:
            model.load_state_dict(torch.load(model_path, map_location=device))
            model.eval()
        except Exception as e:
            print(f"Failed to load model: {e}")
          
    with torch.no_grad():
        heatmap = model(x, edge_index)
      
    return heatmap.cpu().numpy()
```

### 4.4 `solver.py`

```python
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
            return 0.0

    for order_idx, order in enumerate(orders):
        order_s, order_e = get_order_coords(order)
      
        # Determine Stage
        empty_agvs = [a for a in agvs if not a.route]
        is_stage_1 = len(empty_agvs) > 0
      
        candidates = empty_agvs if is_stage_1 else agvs
      
        best_score = float('inf')
        best_move = None # (agv_index, insert_pos, delta_dist)
      
        for agv in candidates:
            num_positions = len(agv.route) + 1
          
            for pos in range(num_positions):
                delta_dist = 0.0
                delta_heat = 0.0
              
                # Order internal distance
                internal_dist = dist_func(order_s, order_e)
                delta_dist += internal_dist
                delta_heat += get_heat(order_s, order_e)
              
                # Connections
                if not agv.route:
                    pass
                else:
                    prev_node = None
                    next_node = None
                  
                    if pos > 0:
                        prev_order = agv.route[pos-1]
                        prev_node = (prev_order['end_x'], prev_order['end_y'], prev_order['end_z'])
                      
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
                      
                # Score
                current_time = agv.total_time
                new_total_time = current_time + delta_dist
              
                score = (LAMBDA_DIST * delta_dist) + (LAMBDA_LOAD * new_total_time) - (GAMMA_HEAT * delta_heat)
              
                if score < best_score:
                    best_score = score
                    best_move = (agv.id, pos, delta_dist)
      
        if best_move:
            agv_id, pos, cost_inc = best_move
            target_agv = agvs[agv_id]
            target_agv.route.insert(pos, order)
            target_agv.update_total_time()
        else:
            print(f"Warning: Could not assign order {order['id']}")
          
    return agvs

def compute_vehicle_costs(agv):
    """Compute detailed costs for a single vehicle."""
    exec_time = 0.0
    setup_time = 0.0
  
    if not agv.route:
        return {'exec_time': 0, 'setup_time': 0, 'total_time': 0, 'local_cost': 0}
      
    for o in agv.route:
        s, e = get_order_coords(o)
        exec_time += dist_func(s, e)
      
    for i in range(len(agv.route) - 1):
        curr = agv.route[i]
        next_o = agv.route[i+1]
        setup_time += dist_func(
            (curr['end_x'], curr['end_y'], curr['end_z']),
            (next_o['start_x'], next_o['start_y'], next_o['start_z'])
        )
      
    total_time = exec_time + setup_time
    exec_scaled = math.log1p(exec_time / ALPHA_E)
    setup_scaled = math.log1p(setup_time / ALPHA_S)
    local_cost = (BETA_E * exec_scaled) + (BETA_S * setup_scaled)
  
    return {'exec_time': exec_time, 'setup_time': setup_time, 'total_time': total_time, 'local_cost': local_cost}

def compute_global_costs(agvs):
    """Compute global system metrics."""
    per_vehicle = [compute_vehicle_costs(a) for a in agvs]
    makespan = max((v['total_time'] for v in per_vehicle), default=0.0)
    sum_local_cost = sum(v['local_cost'] for v in per_vehicle)
    total_travel = sum(v['total_time'] for v in per_vehicle)
    total_cost = (BETA_M * makespan) + (BETA_SUM * sum_local_cost)
    return {'makespan': makespan, 'total_travel': total_travel, 'local_cost': sum_local_cost, 'total_cost': total_cost, 'per_vehicle': per_vehicle}
```

### 4.5 `compare_methods.py`

```python
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
```

### 4.6 `main.py`

```python
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

def process_comparison(instance_path, node_map, results_data):
    instance_name = os.path.basename(instance_path)
    instance_id = instance_name.replace('.xlsx', '')
    print(f"\n{'='*60}")
    print(f"Comparing on Instance: {instance_name}")
    print(f"{'='*60}")
  
    orders = load_orders(instance_path, node_map)
    if not orders:
        return

    # 1. Prepare GCN Data
    unique_coords = set()
    for o in orders:
        unique_coords.add((o['start_x'], o['start_y'], o['start_z']))
        unique_coords.add((o['end_x'], o['end_y'], o['end_z']))
    unique_nodes_list = sorted(list(unique_coords))
    node_to_idx = {coord: i for i, coord in enumerate(unique_nodes_list)}
  
    # --- Method 1: GCN ---
    print("Running GCN...")
    heatmap = generate_heatmap(unique_nodes_list)
    t0 = time.time()
    agvs_gcn = solve_allocation(orders, heatmap, node_to_idx)
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
    baseline_costs = [m_bf['total_cost'], m_ff['total_cost'], m_nn['total_cost']]
    best_baseline = min(baseline_costs)
  
    imp_pct = ((best_baseline - m_gcn['total_cost']) / best_baseline) * 100 if best_baseline > 0 else 0.0
  
    results_data.append({
        'Instance': instance_id,
        'Orders': len(orders),
        'GCN_Cost': m_gcn['total_cost'], 'GCN_Mksp': m_gcn['makespan'],
        'BestFit_Cost': m_bf['total_cost'], 'BestFit_Mksp': m_bf['makespan'],
        'FirstFit_Cost': m_ff['total_cost'], 'FirstFit_Mksp': m_ff['makespan'],
        'Nearest_Cost': m_nn['total_cost'], 'Nearest_Mksp': m_nn['makespan'],
        'Improvement_Pct': imp_pct
    })
  
    print("\nResults:")
    print(f"{'Method':<15} | {'Time (s)':<10} | {'Makespan':<10} | {'Total Cost':<10}")
    print("-" * 55)
    print(f"{'GCN':<15} | {t_gcn:<10.4f} | {m_gcn['makespan']:<10.2f} | {m_gcn['total_cost']:<10.2f}")
    print(f"{'Best Fit':<15} | {t_bf:<10.4f} | {m_bf['makespan']:<10.2f} | {m_bf['total_cost']:<10.2f}")
    print(f"{'First Fit':<15} | {t_ff:<10.4f} | {m_ff['makespan']:<10.2f} | {m_ff['total_cost']:<10.2f}")
    print(f"{'Nearest N.':<15} | {t_nn:<10.4f} | {m_nn['makespan']:<10.2f} | {m_nn['total_cost']:<10.2f}")
    print(f"\nImprovement vs Best Baseline: {imp_pct:.2f}%")

def plot_results(results_data):
    df = pd.DataFrame(results_data)
    df['Orders'] = df['Orders'].astype(int)
    df = df.sort_values('Orders')
  
    instances = df['Instance'].tolist()
    x = np.arange(len(instances))
    width = 0.2
  
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 18), sharex=True)
  
    # 1. Total Cost
    ax1.bar(x - 1.5*width, df['GCN_Cost'], width, label='GCN')
    ax1.bar(x - 0.5*width, df['BestFit_Cost'], width, label='Best Fit')
    ax1.bar(x + 0.5*width, df['FirstFit_Cost'], width, label='First Fit')
    ax1.bar(x + 1.5*width, df['Nearest_Cost'], width, label='Nearest Neighbor')
    ax1.set_ylabel('Total Cost')
    ax1.set_title('Total Cost Comparison')
    ax1.legend()
    ax1.grid(True, linestyle='--', alpha=0.6)
  
    # 2. Makespan
    ax2.bar(x - 1.5*width, df['GCN_Mksp'], width, label='GCN')
    ax2.bar(x - 0.5*width, df['BestFit_Mksp'], width, label='Best Fit')
    ax2.bar(x + 0.5*width, df['FirstFit_Mksp'], width, label='First Fit')
    ax2.bar(x + 1.5*width, df['Nearest_Mksp'], width, label='Nearest Neighbor')
    ax2.set_ylabel('Makespan (s)')
    ax2.set_title('Makespan Comparison')
    ax2.legend()
    ax2.grid(True, linestyle='--', alpha=0.6)
  
    # 3. Improvement
    colors = ['g' if v >= 0 else 'r' for v in df['Improvement_Pct']]
    ax3.bar(x, df['Improvement_Pct'], width*2, color=colors, alpha=0.7)
    ax3.axhline(0, color='black', linewidth=0.8)
    ax3.set_ylabel('Improvement (%)')
    ax3.set_title('GCN Cost Improvement vs Best Baseline')
    ax3.set_xticks(x)
    ax3.set_xticklabels(instances, rotation=45)
    ax3.grid(True, linestyle='--', alpha=0.6)
  
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
  
    small_ids = ['20', '32', '41', '64', '73']
    medium_ids = ['100', '128', '150', '173', '195']
    large_ids = ['211', '243', '275', '306', '328']
    target_ids = small_ids + medium_ids + large_ids
  
    id_to_file = {os.path.basename(f).replace('.xlsx', ''): f for f in all_files}
    instance_files = []
    for tid in target_ids:
        if tid in id_to_file:
            instance_files.append(id_to_file[tid])
        else:
            print(f"Warning: Instance {tid} not found.")
          
    if not instance_files:
        print("No instances found.")
        return
      
    output_path = os.path.join(os.path.dirname(__file__), "comparison_results_full.txt")
    with open(output_path, 'w') as f:
        f.write("--- Algorithm Comparison Results ---\n")
        f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
  
    results_data = []
    for f in instance_files:
        try:
            process_comparison(f, node_map, results_data)
        except Exception as e:
            print(f"Error processing {f}: {e}")
            import traceback
            traceback.print_exc()
          
    if results_data:
        df = pd.DataFrame(results_data)
        df.to_csv('comparison_results_full.csv', index=False)
        print("\nDetailed results saved to comparison_results_full.csv")
        plot_results(results_data)

if __name__ == "__main__":
    main()
```

### 4.7 `visualize_results.py`

```python
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

def plot_comparison(csv_path, output_path='final_comparison_chart.png'):
    if not os.path.exists(csv_path):
        print(f"Error: File not found at {csv_path}")
        return

    df = pd.read_csv(csv_path)
    df.sort_values('Orders', inplace=True)
  
    instances = df['Instance'].astype(str).tolist()
    orders = df['Orders'].tolist()
    x = np.arange(len(instances))
    width = 0.2
  
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(16, 20), sharex=True)
  
    c_gcn = '#2ecc71'
    c_bf = '#3498db'
    c_ff = '#9b59b6'
    c_nn = '#e74c3c'
  
    ax1.bar(x - 1.5*width, df['GCN_Cost'], width, label='GCN (Proposed)', color=c_gcn, edgecolor='black', linewidth=0.5)
    ax1.bar(x - 0.5*width, df['BestFit_Cost'], width, label='Best Fit', color=c_bf, edgecolor='black', linewidth=0.5)
    ax1.bar(x + 0.5*width, df['FirstFit_Cost'], width, label='First Fit', color=c_ff, edgecolor='black', linewidth=0.5)
    ax1.bar(x + 1.5*width, df['Nearest_Cost'], width, label='Nearest Neighbor', color=c_nn, edgecolor='black', linewidth=0.5)
    ax1.set_ylabel('Total Cost (Weighted Time)', fontsize=12, fontweight='bold')
    ax1.set_title('Performance Comparison: Total Cost (Lower is Better)', fontsize=14, fontweight='bold')
    ax1.legend(loc='upper left', frameon=True, fancybox=True, shadow=True)
    ax1.grid(True, linestyle='--', alpha=0.4)

    ax2.bar(x - 1.5*width, df['GCN_Mksp'], width, label='GCN', color=c_gcn, edgecolor='black', linewidth=0.5)
    ax2.bar(x - 0.5*width, df['BestFit_Mksp'], width, label='Best Fit', color=c_bf, edgecolor='black', linewidth=0.5)
    ax2.bar(x + 0.5*width, df['FirstFit_Mksp'], width, label='First Fit', color=c_ff, edgecolor='black', linewidth=0.5)
    ax2.bar(x + 1.5*width, df['Nearest_Mksp'], width, label='Nearest Neighbor', color=c_nn, edgecolor='black', linewidth=0.5)
    ax2.set_ylabel('Makespan (seconds)', fontsize=12, fontweight='bold')
    ax2.set_title('Efficiency Comparison: Makespan (Lower is Better)', fontsize=14, fontweight='bold')
    ax2.grid(True, linestyle='--', alpha=0.4)

    improvements = df['Improvement_Pct'].tolist()
    bar_colors = ['#27ae60' if val >= 0 else '#c0392b' for val in improvements]
  
    rects = ax3.bar(x, improvements, width*2.5, color=bar_colors, alpha=0.8, edgecolor='black', linewidth=0.5)
    ax3.axhline(0, color='black', linewidth=1.5)
    ax3.set_ylabel('Improvement over Best Baseline (%)', fontsize=12, fontweight='bold')
    ax3.set_title('GCN Improvement Percentage (Higher is Better)', fontsize=14, fontweight='bold')
  
    for i, rect in enumerate(rects):
        height = rect.get_height()
        val = improvements[i]
        label_y = height + (1 if height >= 0 else -3)
        ax3.text(rect.get_x() + rect.get_width()/2., label_y,
                f'{val:.1f}%',
                ha='center', va='bottom' if height >= 0 else 'top',
                fontsize=10, fontweight='bold', color='black')

    ax3.set_xlabel('Instance ID (Ordered by Scale)', fontsize=12, fontweight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels([f"ID: {i}\n(n={o})" for i, o in zip(instances, orders)], rotation=0, fontsize=10)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    print(f"Chart saved successfully to {output_path}")

if __name__ == "__main__":
    csv_file = r"d:\1nottingham\Year4a\FYP\hospital-main - 副本\New_GCN_XYZ\comparison_results_full.csv"
    plot_comparison(csv_file)
```

## 5. Running the Project

1. **Prepare Data**: Ensure `instances/node.csv` and `instances/instances/*.xlsx` exist.
2. **Execute**:
   ```bash
   python main.py
   ```
3. **Outputs**:
   - `algorithm_comparison_full.png`: Visual comparison chart.
   - `comparison_results_full.csv`: Raw data.
   - `comparison_results_full.txt`: Execution log.

## 6. GCN Model Theoretical Details

This section details the theoretical framework of the Graph Convolutional Network (GCN) used in this project, addressing why it was chosen, its architecture, and training objectives.

### 6.1 Why GCN for AGV Scheduling?

AGV scheduling in a hospital environment is fundamentally a problem defined on a graph topology.

- **Topology Awareness**: Unlike standard heuristics that only consider Euclidean distance, GCNs can learn the structural properties of the map (e.g., identifying bottlenecks, hubs, or dead ends).
- **Permutation Invariance**: The order in which nodes are presented doesn't change the graph structure. GNNs naturally handle this, whereas sequence models (RNNs) might be sensitive to input ordering.
- **Local to Global**: Through message passing, GCNs aggregate local neighborhood information to form global node embeddings, allowing the model to make decisions based on the wider context of the map.

### 6.2 Model Architecture

The model effectively learns a policy to predict the "favorability" of connecting any two nodes in the graph.

**1. Input Layer**

- **Input**: A feature matrix $X$ of shape $[N, 3]$, where $N$ is the total number of physical nodes in the hospital map (`node.csv`).
- **Features**: Each node $i$ is represented by its normalized 3D coordinates $(x_i, y_i, z_i)$.
- **Graph Structure**: In the current implementation, the model constructs a **fully connected graph** (or uses an MLP fallback), meaning every node can potentially communicate with every other node. It does not currently utilize a pre-defined physical adjacency matrix.

**2. Graph Convolution Layers**
The core reasoning happens via $L$ layers of Graph Convolution (GCNConv):

$$
H^{(l+1)} = \sigma(\tilde{D}^{-\frac{1}{2}}\tilde{A}\tilde{D}^{-\frac{1}{2}} H^{(l)} W^{(l)})
$$

- **Hidden Dimension**: 256 (default).
- The model propagates information across the graph structure, updating each node's embedding based on its neighbors.

**3. Edge Scoring (Output)**
After obtaining the final node embeddings $H^{(L)}$, we predict a score for every possible edge $(u, v)$.

- **Mechanism**: Concatenate embeddings of source node $u$ and target node $v$: $[h_u || h_v]$.
- **MLP Decoder**: Pass this combined vector through a Multi-Layer Perceptron (Linear -> ReLU -> Linear -> Sigmoid).
- **Output**: A Heatmap matrix of shape $[N, N]$, where entry $(i, j) \in [0, 1]$ represents the probability that connecting node $i$ to node $j$ is part of an optimal solution.

### 6.3 Training Objective

While the current implementation uses the model in inference mode to guide the heuristic, the theoretical training objective is **Imitation Learning** (Supervised Learning).

- **Goal**: Train the GCN to mimic an optimal solver (or a high-quality expert heuristic).
- **Labels**: For a set of training instances, run an expert solver to generate the optimal routes. Create a binary adjacency matrix $Y_{expert}$ where $Y_{ij} = 1$ if the edge $(i, j)$ is used in the optimal solution, and $0$ otherwise.
- **Loss Function**: Binary Cross-Entropy (BCE) Loss between the predicted heatmap $\hat{Y}$ and the ground truth $Y_{expert}$:
  $$
  \mathcal{L} = - \sum_{i,j} [Y_{ij} \log(\hat{Y}_{ij}) + (1-Y_{ij}) \log(1-\hat{Y}_{ij})]
  $$
- By minimizing this loss, the GCN learns to assign high scores to edges that are statistically likely to be part of efficient routes, effectively "pruning" the search space for the greedy heuristic.

### 6.4 Heatmap Post-Processing

To ensure the generated heatmap is robust and visually informative, a two-step post-processing strategy is applied to the raw model output.

**1. Temperature Scaling (Micro-Adjustment)**

- **Purpose**: Controls the sharpness of the probability distribution.
- **Mechanism**: The raw logits from the model are divided by a temperature parameter $T$ before applying Softmax: $P_i = \text{softmax}(z_i / T)$.
- **Effect**:
  - **High $T$ (>1)**: "Softens" the distribution, making the differences between probabilities smaller. This is crucial when the model is untrained or randomly initialized, as it prevents the heatmap from collapsing into a binary (0/1) state, allowing us to see subtle gradients and potential routes.
  - **Low $T$ (<1)**: "Sharpens" the distribution, exaggerating the confidence of the highest scoring edges.

**2. Epsilon-Smoothing (Macro-Adjustment)**

- **Purpose**: Eliminates zero-probability "blind spots" to ensure exploration.
- **Mechanism**: A small uniform probability distribution (noise) is mixed with the model's output:
  $$
  P_{final} = (1 - \epsilon) \cdot P_{model} + \epsilon \cdot P_{uniform}
  $$
- **Effect**: Even if the GCN predicts a near-zero probability for a valid edge, this step ensures it retains a minimal non-zero probability. This prevents the heuristic from getting stuck if the GCN makes a mistake, guaranteeing that all nodes remain theoretically reachable.

**Visualization**:
The final heatmaps (e.g., `heatmap_dist_manhattan.png`) use a **Manhattan Distance + Floor Penalty** metric to represent the true cost of movement in the hospital:

$$
\text{Cost}_{ij} = |x_i - x_j| + |y_i - y_j| + 60 \times |z_i - z_j|
$$

This highlights the significant cost of vertical travel (elevators) compared to horizontal movement.
