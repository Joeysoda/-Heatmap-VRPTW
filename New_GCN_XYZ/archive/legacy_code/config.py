
import os

# -----------------------------------------------------------------------------
# Environment Settings
# -----------------------------------------------------------------------------
AGV_NUM = 9
FLOOR_PENALTY = 60.0  # Seconds per floor difference

# -----------------------------------------------------------------------------
# Battery and Charging Configuration
# -----------------------------------------------------------------------------
BATTERY_CAPACITY = 10000.0  # Battery capacity in units
BATTERY_CONSUMPTION_RATE = 1.0  # Units per meter
BATTERY_LOW_THRESHOLD = 2000.0  # Threshold to trigger charging
CHARGING_TIME = 300.0  # Seconds to fully charge
SERVICE_TIME_PICKUP = 30.0  # Seconds for pickup service
SERVICE_TIME_DELIVERY = 30.0  # Seconds for delivery service

# -----------------------------------------------------------------------------
# Time Window Configuration
# -----------------------------------------------------------------------------
TIME_WINDOW_PENALTY = 1000.0  # Penalty for violating time windows
ENABLE_TIME_WINDOWS = True  # Enable/disable time window constraints
ENABLE_CHARGING = True  # Enable/disable charging constraints

# -----------------------------------------------------------------------------
# File Paths
# -----------------------------------------------------------------------------
# Using absolute paths based on user input
BASE_DIR = r"d:\1nottingham\Year4a\FYP\hospital-main"
NODE_FILE = os.path.join(BASE_DIR, "Hospital_Simulator", "test_instances", "d2_150.txt")
INSTANCE_DIR = os.path.join(BASE_DIR, "Hospital_Simulator", "test_instances")

# Real robot data paths
ROBOT_DATA_DIR = r"d:\1nottingham\Year4a\FYP\hospital-main\robot_data"
ROBOT_ORDER_FILE = os.path.join(ROBOT_DATA_DIR, "robot_order.xlsx")
ROBOT_MISSION_FILE = os.path.join(ROBOT_DATA_DIR, "robot_mission.xlsx")
ROBOT_EDGE_FILE = os.path.join(ROBOT_DATA_DIR, "robot_edge.xlsx")
ROBOT_NODE_FILE = os.path.join(ROBOT_DATA_DIR, "robot_node.xlsx")

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
