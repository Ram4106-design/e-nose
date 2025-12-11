"""
Configuration and constants for E-NOSE Dashboard
"""

# Backend connection settings
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8082
RECONNECT_DELAY = 2

# Graph settings
MAX_DATA_POINTS = 300

# Sensor configuration with colors (Blue/Cyan theme)
SENSORS = {
    "NO2": "#00d9ff",    # Bright cyan
    "ETH": "#0096c7",    # Medium blue
    "VOC": "#00b4d8",    # Sky blue
    "CO": "#48cae4",     # Light cyan
    "COM": "#0077b6",    # Deep blue
    "ETHM": "#90e0ef",   # Pale cyan
    "VOCM": "#023e8a"    # Dark blue
}

# FSM State configuration
# States: IDLE(0), PRE_COND(1), RAMP_UP(2), HOLD(3), PURGE(4), RECOVERY(5), DONE(6)
# Timing: HOLD = 60s (1min), PURGE = 120s (2min) (as per Arduino firmware)
STATES = {
    "IDLE": {"color": "#888888", "desc": "Idle"},
    "PRE_COND": {"color": "#ffbe0b", "desc": "Pre-Conditioning (5s)"},
    "RAMP_UP": {"color": "#fb5607", "desc": "Ramping Up (3s)"},
    "HOLD": {"color": "#00d9ff", "desc": "Hold (60s / 1min)"},
    "PURGE": {"color": "#8338ec", "desc": "Purge (120s / 2min)"},
    "RECOVERY": {"color": "#39ff14", "desc": "Recovery (5s)"},
    "DONE": {"color": "#00ff00", "desc": "Complete"}
}

# FSM Timing Configuration (matches Arduino firmware)
# Arduino timing: T_HOLD = 20000ms (0s), T_PURGE = 40000ms (40s)
TIMING = {
    "PRE_COND": 5,      # 5 seconds
    "RAMP_UP": 3,       # 3 seconds
    "HOLD": 20,         # 20 seconds 
    "PURGE": 40,       # 40 seconds 
    "RECOVERY": 5       # 5 seconds
}

# Total cycle time per level: ~193 seconds (~3.2 minutes)
# Total for 5 levels: ~16 minutes


# Edge Impulse model settings
DEFAULT_MODEL_PATH = "modelfile.eim"

# Edge Impulse API settings for data ingestion
EDGE_IMPULSE_API_URL = "https://ingestion.edgeimpulse.com/api/training/data"
EDGE_IMPULSE_UPLOAD_TIMEOUT = 30  # seconds

