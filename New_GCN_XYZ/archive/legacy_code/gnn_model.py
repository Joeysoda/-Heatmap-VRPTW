
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
            nn.Linear(hidden_dim, 1)
            # Removed Sigmoid to use Softmax in forward pass
        )
        
        self.to(self.device)

    def forward(self, x, edge_index=None, temperature=1.0):
        """
        Args:
            x: Node features [NumNodes, InputDim]
            edge_index: Edge list [2, NumEdges] (required for GNN)
            temperature: Scaling factor for logits (higher = softer distribution)
        Returns:
            heatmap: [NumNodes, NumNodes] matrix of probabilities (Softmax)
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
        logits = self.edge_scorer(pair_feat).squeeze(-1)
        
        # Apply Temperature Scaling
        logits = logits / temperature
        
        # 3. Apply Softmax with Diagonal Masking
        # We want P(target | source), so softmax over dim=-1 (columns)
        # Mask self-loops (diagonal) to -inf so probability is 0
        mask = torch.eye(num_nodes, dtype=torch.bool, device=self.device)
        logits = logits.masked_fill(mask, float('-inf'))
        
        heatmap = F.softmax(logits, dim=-1)
        
        return heatmap

def generate_heatmap(unique_nodes, model_path=None, temperature=1.0, train=False):
    """
    Generate heatmap for the given list of unique PHYSICAL nodes.
    unique_nodes: List of (x, y, z) tuples.
    temperature: Float, >1.0 makes distribution softer, <1.0 makes it sharper.
    train: Boolean, if True, performs unsupervised training on the instance.
    
    Returns:
        heatmap: [N, N] numpy array
    """
    if not unique_nodes:
        return np.zeros((0, 0))
        
    # 1. Construct Node Features
    # Node feature: (x, y, z) -> Input Dim = 3
    scale = 1000.0 
    features = []
    # Pre-calculate distance matrix for training
    num_nodes = len(unique_nodes)
    dist_matrix = np.zeros((num_nodes, num_nodes))
    
    coords = np.array(unique_nodes)
    
    for i in range(num_nodes):
        features.append([unique_nodes[i][0] / scale, unique_nodes[i][1] / scale, unique_nodes[i][2]])
        for j in range(num_nodes):
            if i != j:
                # Manhattan + Floor Penalty (Same as solver)
                d = abs(coords[i][0] - coords[j][0]) + abs(coords[i][1] - coords[j][1]) + 60.0 * abs(coords[i][2] - coords[j][2])
                dist_matrix[i, j] = d
    
    device = torch.device(f"cuda:{GPU_ID}" if USE_GPU and torch.cuda.is_available() else "cpu")
    x = torch.tensor(features, dtype=torch.float, device=device)
    
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
    
    # Perform Unsupervised Training if requested
    if train:
        print(f"Training GCN on {len(unique_nodes)} nodes...")
        optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
        # Increase epochs for better convergence since we run it once
        train_unsupervised(model, optimizer, x, edge_index, dist_matrix, num_epochs=500)
        
        # Save the trained model
        if model_path:
            torch.save(model.state_dict(), model_path)
            print(f"Model saved to {model_path}")
            
    with torch.no_grad():
        heatmap = model(x, edge_index, temperature=temperature)
        
    return heatmap.cpu().numpy()

def train_unsupervised(model, optimizer, x, edge_index, dist_matrix, num_epochs=100):
    """
    Performs unsupervised learning to minimize the expected tour length.
    Loss = (Heatmap * DistanceMatrix).sum() + EntropyRegularization
    """
    model.train()
    
    # Normalize distance matrix to [0, 1] range for better gradient flow
    # Min-Max Normalization
    d_min = dist_matrix.min()
    d_max = dist_matrix.max()
    dist_norm = (dist_matrix - d_min) / (d_max - d_min + 1e-5)
    
    dist_tensor = torch.tensor(dist_norm, dtype=torch.float, device=model.device)
    
    print(f"Starting Unsupervised Training ({num_epochs} epochs)...")
    for epoch in range(num_epochs):
        optimizer.zero_grad()
        
        # Forward pass (use higher temperature during training for exploration)
        heatmap = model(x, edge_index, temperature=1.0) # Lower temp to encourage decisions
        
        # 1. Distance Loss: Minimize expected distance
        # We want the model to assign high probability to short edges (values close to 0)
        loss_dist = torch.sum(heatmap * dist_tensor)
        
        # 2. Entropy Loss: Encourage deterministic (sharp) predictions
        # Entropy = -sum(p * log(p))
        # We want to minimize entropy -> make p close to 0 or 1
        entropy = -torch.sum(heatmap * torch.log(heatmap + 1e-9))
        
        # Total Loss
        # Increase weight of distance loss
        loss = loss_dist + 0.001 * entropy
        
        loss.backward()
        
        # Clip gradients to prevent explosion
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        
        optimizer.step()
        
        if (epoch + 1) % 50 == 0:
            print(f"  Epoch {epoch+1}/{num_epochs} | Loss: {loss.item():.4f} (Dist: {loss_dist.item():.4f})")
            
    model.eval()
