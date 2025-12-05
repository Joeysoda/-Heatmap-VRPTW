
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
    # This logic was refined in previous iterations to handle specific user files
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
