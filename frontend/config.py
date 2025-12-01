"""
Configuration and constants for E-NOSE Dashboard
"""

# Backend connection settings
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8082
RECONNECT_DELAY = 2

# Graph settings
MAX_DATA_POINTS = 300

# Sensor configuration with colors
SENSORS = {
    "NO2": "#FF6B6B",
    "ETH": "#4ECDC4",
    "VOC": "#45B7D1",
    "CO": "#FFA07A",
    "COM": "#98D8C8",
    "ETHM": "#F7DC6F",
    "VOCM": "#BB8FCE"
}

# FSM State configuration
# States: IDLE(0), PRE_COND(1), RAMP_UP(2), HOLD(3), PURGE(4), RECOVERY(5), DONE(6)
# Timing: HOLD = 2 min, PURGE = 4 min
STATES = {
    "IDLE": {"color": "#888888", "desc": "Idle"},
    "PRE_COND": {"color": "#ffbe0b", "desc": "Pre-Conditioning"},
    "RAMP_UP": {"color": "#fb5607", "desc": "Ramping Up"},
    "HOLD": {"color": "#00d9ff", "desc": "Hold (2 min)"},
    "PURGE": {"color": "#8338ec", "desc": "Purge (4 min)"},
    "RECOVERY": {"color": "#39ff14", "desc": "Recovery"},
    "DONE": {"color": "#00ff00", "desc": "Complete"}
}

# Edge Impulse model settings
DEFAULT_MODEL_PATH = "modelfile.eim"

# Edge Impulse API settings for data ingestion
EDGE_IMPULSE_API_URL = "https://ingestion.edgeimpulse.com/api/training/data"
EDGE_IMPULSE_UPLOAD_TIMEOUT = 30  # seconds

