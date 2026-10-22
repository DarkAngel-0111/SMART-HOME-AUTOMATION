"""
Configuration for Smart Home IoT System
Arduino Uno + USB Serial + Mosquitto MQTT + Modern Web/PWA App
"""

# MQTT Broker Configuration
MQTT_HOST = "localhost"
MQTT_PORT = 1883        # Standard Mosquitto port (falls back to 1884 if 1883 is occupied)
MQTT_FALLBACK_PORT = 1884

# Serial Communication with Arduino Uno
SERIAL_PORT = "/dev/ttyACM0"  # Default Linux Arduino Uno port (auto-detects /dev/ttyUSB0 as fallback)
SERIAL_BAUD = 9600
SERIAL_TIMEOUT = 1.0  # seconds

# Web / REST / SSE Server Configuration
WEB_HOST = "0.0.0.0"
WEB_PORT = 5000

# Arduino Hardware Pin Mappings
PIN_CONFIG = {
    # Inputs
    "PIR": 2,          # PIR Motion Sensor (Digital IN)
    "DHT": 3,          # DHT11 / DHT22 Data (Digital I/O)
    "FLAME": 5,        # Flame Sensor Digital Out (Digital IN)
    "IR": 7,           # IR Obstacle / Doorway Sensor (Digital IN)
    "US_TRIG": 8,      # Ultrasonic HC-SR04 Trigger (Digital OUT)
    "US_ECHO": 9,      # Ultrasonic HC-SR04 Echo (Digital IN)
    "LDR": "A0",       # LDR Light Sensor (Analog IN)
    "MQ6": "A1",       # MQ-6 Gas Sensor (Analog IN)
    
    # Outputs (4 Controlled Lights + Actuators)
    "LIGHT1": 4,        # Light 1: Living Room Relay (Digital OUT)
    "LIGHT2": "A2",     # Light 2: Bedroom Relay (Digital OUT)
    "LIGHT3": "A3",     # Light 3: Kitchen Relay (Digital OUT)
    "LIGHT4": "A4",     # Light 4: Balcony / Outdoor Relay (Digital OUT)
    "LIGHT": 4,         # Alias for Main Light 1
    "BUZZER": 6,        # Active Alarm Buzzer (Digital OUT)
    "SERVO": 10,        # Servo Motor Door/Gate Lock (PWM OUT)
    "ALARM_LED": 11,    # Warning Red Flashing LED (Digital OUT)
    "FAN": 12,          # Ventilation Fan / Aux Relay (Digital OUT)
    "STATUS_LED": 13,   # Arduino Activity Heartbeat LED (Digital OUT)
}

# Sensor Thresholds & Defaults
THRESHOLDS = {
    "MQ6_GAS_ALERT": 400,       # Raw analog reading threshold for gas alert (0-1023)
    "LDR_DARK_LEVEL": 450,      # Reading below which ambient is considered "Night/Dark"
    "ULTRASONIC_PROXIMITY": 20, # Distance in cm for garage/door proximity detection
    "LIGHT_INACTIVITY_SEC": 30, # Seconds of no motion before auto-turning off night light
}

# MQTT Topics
MQTT_TOPICS = {
    # Telemetry
    "TELEMETRY": "smarthome/telemetry",
    
    # Lighting
    "LIGHT_SET": "smarthome/lights/set",
    "LIGHT_STATE": "smarthome/lights/state",
    
    # Door / Gate Servo
    "DOOR_SET": "smarthome/door/set",
    "DOOR_STATE": "smarthome/door/state",
    
    # Automation Mode (AUTO / MANUAL)
    "MODE_SET": "smarthome/mode/set",
    "MODE_STATE": "smarthome/mode/state",
    
    # Alarm System
    "ALARM_SET": "smarthome/alarm/set",
    "ALARM_STATE": "smarthome/alarm/state",
    
    # Ventilation Fan
    "FAN_SET": "smarthome/fan/set",
    "FAN_STATE": "smarthome/fan/state",
    
    # Individual Sensor Feeds
    "SENSOR_TEMP": "smarthome/sensors/temperature",
    "SENSOR_HUM": "smarthome/sensors/humidity",
    "SENSOR_GAS": "smarthome/sensors/gas",
    "SENSOR_FLAME": "smarthome/sensors/flame",
    "SENSOR_MOTION": "smarthome/sensors/motion",
    "SENSOR_LIGHT": "smarthome/sensors/light_level",
    "SENSOR_DISTANCE": "smarthome/sensors/distance",
    "SENSOR_IR": "smarthome/sensors/ir",
}
