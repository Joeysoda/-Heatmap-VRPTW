import os

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
AGV_NUM = 9
FLOOR_PENALTY = 60.0
DEFAULT_DEPOT = (0.0, 0.0, 0)
RANDOM_SEED = 42

# ---------------------------------------------------------------------------
# Battery / Charging
# ---------------------------------------------------------------------------
BATTERY_CAPACITY = 10000.0
BATTERY_CONSUMPTION_RATE = 1.0
BATTERY_LOW_THRESHOLD = 2000.0
CHARGING_TIME = 300.0
SERVICE_TIME_PICKUP = 30.0
SERVICE_TIME_DELIVERY = 30.0
ENABLE_CHARGING = True

# ---------------------------------------------------------------------------
# Time Window
# ---------------------------------------------------------------------------
ENABLE_TIME_WINDOWS = True
USE_HARD_TIME_WINDOWS = True
TIME_WINDOW_PENALTY = 1000.0

# ---------------------------------------------------------------------------
# File Paths
# ---------------------------------------------------------------------------
BASE_DIR = r"d:\1nottingham\Year4a\FYP\hospital-main"
NODE_FILE = os.path.join(BASE_DIR, "Hospital_Simulator", "test_instances", "d2_150.txt")
INSTANCE_DIR = os.path.join(BASE_DIR, "Hospital_Simulator", "test_instances")

ROBOT_DATA_DIR = r"d:\1nottingham\Year4a\FYP\hospital-main\robot_data"
ROBOT_ORDER_FILE = os.path.join(ROBOT_DATA_DIR, "robot_order.xlsx")
ROBOT_MISSION_FILE = os.path.join(ROBOT_DATA_DIR, "robot_mission.xlsx")
ROBOT_EDGE_FILE = os.path.join(ROBOT_DATA_DIR, "robot_edge.xlsx")
ROBOT_NODE_FILE = os.path.join(ROBOT_DATA_DIR, "robot_node.xlsx")

# ---------------------------------------------------------------------------
# GCN Model
# ---------------------------------------------------------------------------
GCN_HIDDEN_DIM = 1
GCN_OUTPUT_DIM = 1
USE_GPU = True
GPU_ID = 0

# ---------------------------------------------------------------------------
# Heuristic Weights
# score = lambda_dist * delta_dist + lambda_load * projected_makespan
#         - gamma_heat * delta_heat + tw_weight * urgency + battery_weight * risk
# ---------------------------------------------------------------------------
LAMBDA_DIST = 0.50
LAMBDA_LOAD = 0.12
GAMMA_HEAT = 280.0
TW_URGENCY_WEIGHT = 0.22
BATTERY_RISK_WEIGHT = 0.18
CHARGING_INSERTION_PENALTY = 120.0

# ---------------------------------------------------------------------------
# Cost Function (log-scaled components)
# ---------------------------------------------------------------------------
ALPHA_W = 60.0
ALPHA_S = 60.0
ALPHA_E = 60.0
ALPHA_L = 60.0

BETA_W = 0.35
BETA_S = 1.0
BETA_E = 1.0
BETA_L = 0.25

BETA_M = 1.0
BETA_SUM = 0.10

# ---------------------------------------------------------------------------
# Charging Station Defaults
# ---------------------------------------------------------------------------
DEFAULT_CHARGING_STATIONS = [
    (0.0, 0.0, 0),
    (100.0, 100.0, 1),
    (200.0, 200.0, 2),
    (300.0, 300.0, 3),
]

# ---------------------------------------------------------------------------
# Bounded GCN tuning search space
# ---------------------------------------------------------------------------
GCN_TUNING_SPACE = {
    "LAMBDA_DIST": [0.35, 0.50, 0.65],
    "LAMBDA_LOAD": [0.08, 0.12, 0.16],
    "GAMMA_HEAT": [180.0, 280.0, 360.0],
    "TW_URGENCY_WEIGHT": [0.10, 0.22, 0.35],
    "BATTERY_RISK_WEIGHT": [0.10, 0.18, 0.30],
}

