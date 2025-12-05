
import os

# -----------------------------------------------------------------------------
# Environment Settings
# -----------------------------------------------------------------------------
AGV_NUM = 9
FLOOR_PENALTY = 60.0  # Seconds per floor difference

# -----------------------------------------------------------------------------
# File Paths
# -----------------------------------------------------------------------------
# Using absolute paths based on user input
BASE_DIR = r"d:\1nottingham\Year4a\FYP\hospital-main - 副本"
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
