#!/usr/bin/env python3
"""
Smart Home IoT System - Central Gateway Backend
Arduino Uno + USB Serial + Mosquitto MQTT + Modern Web / PWA Server
Zero external dependency fallback (pure Python standard library support).
"""

import os
import sys
import re
import time
import glob
import json
import math
import socket
import logging
import threading
import subprocess
from typing import Dict, Any, Optional

import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(threadName)s) %(message)s"
)
logger = logging.getLogger("SmartHomeGateway")

# Optional PySerial
try:
    import serial
    HAS_PYSERIAL = True
except ImportError:
    HAS_PYSERIAL = False
    logger.warning("pyserial is not installed. Running in simulation mode.")

# Optional Paho-MQTT
try:
    import paho.mqtt.client as mqtt
    HAS_PAHO = True
except ImportError:
    HAS_PAHO = False
    logger.info("paho-mqtt is not installed. Mosquitto CLI will be used as fallback.")

# Optional Flask
try:
    from flask import Flask, jsonify, request, Response, send_from_directory, render_template
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False
    logger.info("Flask not found. Using Python standard library ThreadedHTTPServer.")


# ==============================================================================
# Helper Functions
# ==============================================================================

def get_lan_ip() -> str:
    """Attempts to determine the host machine's LAN IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            ip = "127.0.0.1"
    finally:
        s.close()
    return ip


# ==============================================================================
# Smart Home Gateway Core
# ==============================================================================

class SmartHomeGateway:
    def __init__(self):
        self.lock = threading.Lock()
        self.running = True

        # Comprehensive Telemetry State (Accurate Sensor Data from Hardware)
        self.telemetry: Dict[str, Any] = {
            "temp": 0.0,
            "hum": 0.0,
            "gas": 0,
            "flame": 0,
            "pir": 0,
            "ldr": 0,
            "ir": 0,
            "dist": 0,
            "light1": 0,
            "light2": 0,
            "light3": 0,
            "light4": 0,
            "light": 0,
            "door": 0,
            "fan": 0,
            "alarm": 0,
            "mode": "AUTO",
            "mqtt": "Disconnected",
            "arduino": "Disconnected",
            "active_port": "None",
            "is_simulation": False,
            "has_real_data": False,
            "server_ip": get_lan_ip(),
            "server_port": config.WEB_PORT,
            "timestamp": int(time.time())
        }

        # Serial Connection
        self.ser: Optional[Any] = None
        self.active_serial_port: Optional[str] = None
        self.arduino_connected = False
        self.simulated_serial = False

        # MQTT Connection
        self.mqtt_connected = False
        self.mqtt_client = None
        self.mqtt_port = config.MQTT_PORT

        # SSE Listeners
        self.sse_listeners = []
        self.sse_lock = threading.Lock()

        # Simulation Variables
        self.sim_tick = 0
        self.sim_motion_until = 0
        self.sim_gas_override = None
        self.sim_flame_override = None
        self.sim_night_mode = False

    # --------------------------------------------------------------------------
    # Serial Port Management
    # --------------------------------------------------------------------------

    def find_arduino_port(self) -> Optional[str]:
        """Auto-detects Arduino Uno serial port (/dev/ttyACM* or /dev/ttyUSB*)."""
        if os.path.exists(config.SERIAL_PORT):
            return config.SERIAL_PORT

        candidates = sorted(glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*"))
        if candidates:
            return candidates[0]

        return None

    def connect_serial(self) -> bool:
        """Attempts to open the serial port to Arduino Uno."""
        if not HAS_PYSERIAL:
            self.simulated_serial = True
            self.arduino_connected = False
            self.active_serial_port = "SIMULATOR"
            with self.lock:
                self.telemetry["arduino"] = "Simulated"
                self.telemetry["is_simulation"] = True
            return True

        port = self.find_arduino_port()
        if not port:
            self.simulated_serial = False
            self.arduino_connected = False
            self.active_serial_port = "None"
            with self.lock:
                self.telemetry["arduino"] = "Disconnected"
                self.telemetry["is_simulation"] = False
            return False

        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=config.SERIAL_BAUD,
                timeout=config.SERIAL_TIMEOUT
            )
            time.sleep(2.0)  # Wait for Arduino Uno bootloader reset
            self.active_serial_port = port
            self.arduino_connected = True
            self.simulated_serial = False
            with self.lock:
                self.telemetry["arduino"] = "Connected"
                self.telemetry["active_port"] = port
                self.telemetry["is_simulation"] = False
            logger.info(f"Connected to Arduino Uno on {port} at {config.SERIAL_BAUD} baud.")
            return True
        except Exception as e:
            logger.warning(f"Failed to open serial port {port}: {e}. Running in simulation mode.")
            self.simulated_serial = True
            self.arduino_connected = False
            with self.lock:
                self.telemetry["arduino"] = "Disconnected"
                self.telemetry["is_simulation"] = True
            return False

    def send_serial_command(self, cmd: str) -> bool:
        """Sends an ASCII command line to Arduino Uno or updates simulator."""
        cmd = cmd.strip()
        logger.info(f"Dispatching Command: '{cmd}'")

        if self.arduino_connected and self.ser and self.ser.is_open:
            try:
                msg = f"{cmd}\n".encode('utf-8')
                self.ser.write(msg)
                self.ser.flush()
                return True
            except Exception as e:
                logger.error(f"Error writing to serial: {e}")
                self.arduino_connected = False
                return False
        else:
            # Handle in software simulator
            self.process_simulated_command(cmd)
            return True

    def process_simulated_command(self, cmd: str):
        """Processes command inside the software simulator."""
        cmd_upper = cmd.upper()
        with self.lock:
            # 4 Light Controls
            if cmd_upper in ("LIGHT 1 ON", "LIGHT1 ON", "LIGHT ON"):
                self.telemetry["light1"] = 1
                self.telemetry["light"] = 1
                self.telemetry["mode"] = "MANUAL"
            elif cmd_upper in ("LIGHT 1 OFF", "LIGHT1 OFF", "LIGHT OFF"):
                self.telemetry["light1"] = 0
                self.telemetry["light"] = 0
                self.telemetry["mode"] = "MANUAL"
            elif cmd_upper in ("LIGHT 1 TOGGLE", "LIGHT1 TOGGLE", "LIGHT TOGGLE"):
                val = 0 if self.telemetry.get("light1", 0) else 1
                self.telemetry["light1"] = val
                self.telemetry["light"] = val
                self.telemetry["mode"] = "MANUAL"
            elif cmd_upper in ("LIGHT 2 ON", "LIGHT2 ON"):
                self.telemetry["light2"] = 1
                self.telemetry["mode"] = "MANUAL"
            elif cmd_upper in ("LIGHT 2 OFF", "LIGHT2 OFF"):
                self.telemetry["light2"] = 0
                self.telemetry["mode"] = "MANUAL"
            elif cmd_upper in ("LIGHT 2 TOGGLE", "LIGHT2 TOGGLE"):
                self.telemetry["light2"] = 0 if self.telemetry.get("light2", 0) else 1
                self.telemetry["mode"] = "MANUAL"
            elif cmd_upper in ("LIGHT 3 ON", "LIGHT3 ON"):
                self.telemetry["light3"] = 1
                self.telemetry["mode"] = "MANUAL"
            elif cmd_upper in ("LIGHT 3 OFF", "LIGHT3 OFF"):
                self.telemetry["light3"] = 0
                self.telemetry["mode"] = "MANUAL"
            elif cmd_upper in ("LIGHT 3 TOGGLE", "LIGHT3 TOGGLE"):
                self.telemetry["light3"] = 0 if self.telemetry.get("light3", 0) else 1
                self.telemetry["mode"] = "MANUAL"
            elif cmd_upper in ("LIGHT 4 ON", "LIGHT4 ON"):
                self.telemetry["light4"] = 1
                self.telemetry["mode"] = "MANUAL"
            elif cmd_upper in ("LIGHT 4 OFF", "LIGHT4 OFF"):
                self.telemetry["light4"] = 0
                self.telemetry["mode"] = "MANUAL"
            elif cmd_upper in ("LIGHT 4 TOGGLE", "LIGHT4 TOGGLE"):
                self.telemetry["light4"] = 0 if self.telemetry.get("light4", 0) else 1
                self.telemetry["mode"] = "MANUAL"
            elif cmd_upper in ("LIGHTS ALL ON", "LIGHT ALL ON"):
                self.telemetry["light1"] = 1
                self.telemetry["light2"] = 1
                self.telemetry["light3"] = 1
                self.telemetry["light4"] = 1
                self.telemetry["light"] = 1
                self.telemetry["mode"] = "MANUAL"
            elif cmd_upper in ("LIGHTS ALL OFF", "LIGHT ALL OFF"):
                self.telemetry["light1"] = 0
                self.telemetry["light2"] = 0
                self.telemetry["light3"] = 0
                self.telemetry["light4"] = 0
                self.telemetry["light"] = 0
                self.telemetry["mode"] = "MANUAL"
            elif cmd_upper == "DOOR OPEN":
                self.telemetry["door"] = 90
            elif cmd_upper == "DOOR CLOSE":
                self.telemetry["door"] = 0
            elif cmd_upper.startswith("DOOR "):
                try:
                    angle = int(cmd_upper.split()[1])
                    self.telemetry["door"] = max(0, min(180, angle))
                except Exception:
                    pass
            elif cmd_upper == "MODE AUTO":
                self.telemetry["mode"] = "AUTO"
            elif cmd_upper == "MODE MANUAL":
                self.telemetry["mode"] = "MANUAL"
            elif cmd_upper == "FAN ON":
                self.telemetry["fan"] = 1
            elif cmd_upper == "FAN OFF":
                self.telemetry["fan"] = 0
            elif cmd_upper in ("BUZZER MUTE", "ALARM SILENCE"):
                self.telemetry["alarm"] = 0
            elif cmd_upper == "ALARM TEST":
                self.telemetry["alarm"] = 1
        self.notify_sse()
        self.publish_all_mqtt()

    def handle_arduino_line(self, line: str):
        """Parses a line received from the physical Arduino Uno."""
        line = line.strip()
        if not line:
            return

        # Check if line is JSON telemetry
        if line.startswith("{") and line.endswith("}"):
            try:
                data = json.loads(line)
                with self.lock:
                    for k, v in data.items():
                        if k in self.telemetry:
                            self.telemetry[k] = v
                    # Synchronize light alias
                    if "light1" in data and "light" not in data:
                        self.telemetry["light"] = data["light1"]
                    elif "light" in data and "light1" not in data:
                        self.telemetry["light1"] = data["light"]
                    self.telemetry["has_real_data"] = True
                    self.telemetry["arduino"] = "Connected"
                    self.telemetry["is_simulation"] = False
                    self.telemetry["timestamp"] = int(time.time())
                self.notify_sse()
                self.publish_all_mqtt()
                return
            except json.JSONDecodeError:
                pass

        # Text responses
        logger.info(f"Arduino Echo: {line}")
        with self.lock:
            if "OK LIGHT1 ON" in line or "OK LIGHT ON" in line:
                self.telemetry["light1"] = 1
                self.telemetry["light"] = 1
            elif "OK LIGHT1 OFF" in line or "OK LIGHT OFF" in line:
                self.telemetry["light1"] = 0
                self.telemetry["light"] = 0
            elif "OK LIGHT2 ON" in line:
                self.telemetry["light2"] = 1
            elif "OK LIGHT2 OFF" in line:
                self.telemetry["light2"] = 0
            elif "OK LIGHT3 ON" in line:
                self.telemetry["light3"] = 1
            elif "OK LIGHT3 OFF" in line:
                self.telemetry["light3"] = 0
            elif "OK LIGHT4 ON" in line:
                self.telemetry["light4"] = 1
            elif "OK LIGHT4 OFF" in line:
                self.telemetry["light4"] = 0
            elif "OK LIGHTS ALL ON" in line:
                self.telemetry["light1"] = 1
                self.telemetry["light2"] = 1
                self.telemetry["light3"] = 1
                self.telemetry["light4"] = 1
                self.telemetry["light"] = 1
            elif "OK LIGHTS ALL OFF" in line:
                self.telemetry["light1"] = 0
                self.telemetry["light2"] = 0
                self.telemetry["light3"] = 0
                self.telemetry["light4"] = 0
                self.telemetry["light"] = 0
            elif "OK DOOR OPEN" in line:
                self.telemetry["door"] = 90
            elif "OK DOOR CLOSE" in line:
                self.telemetry["door"] = 0
            elif "OK MODE AUTO" in line:
                self.telemetry["mode"] = "AUTO"
            elif "OK MODE MANUAL" in line:
                self.telemetry["mode"] = "MANUAL"
            elif "OK FAN ON" in line:
                self.telemetry["fan"] = 1
            elif "OK FAN OFF" in line:
                self.telemetry["fan"] = 0
        self.notify_sse()

    def serial_worker(self):
        """Background thread to read Arduino serial lines and maintain connection."""
        while self.running:
            if not self.arduino_connected or not self.ser:
                time.sleep(3.0)
                if not self.arduino_connected:
                    self.connect_serial()
                continue

            try:
                if self.ser.in_waiting > 0:
                    raw = self.ser.readline()
                    line = raw.decode('utf-8', errors='replace').strip()
                    if line:
                        self.handle_arduino_line(line)
                else:
                    time.sleep(0.05)
            except Exception as e:
                logger.warning(f"Serial communication interrupted: {e}")
                self.arduino_connected = False
                if self.ser:
                    try:
                        self.ser.close()
                    except Exception:
                        pass
                    self.ser = None

    # --------------------------------------------------------------------------
    # Telemetry Monitor & Manual Test Worker
    # --------------------------------------------------------------------------

    def simulation_worker(self):
        """Monitors system status without fabricating sensor data."""
        while self.running:
            time.sleep(1.0)
            if self.arduino_connected:
                continue

            with self.lock:
                # Do NOT synthesize fake sensor data. Telemetry is sourced directly from hardware.
                # Only apply explicit manual test triggers (e.g., automated test suites or developer overrides)
                if self.sim_gas_override is not None:
                    self.telemetry["gas"] = self.sim_gas_override
                if self.sim_flame_override is not None:
                    self.telemetry["flame"] = self.sim_flame_override
                if self.sim_motion_until > 0:
                    self.telemetry["pir"] = 1 if time.time() < self.sim_motion_until else 0

                # Emergency Alarm Trigger for explicit hazard overrides
                is_hazard = (self.telemetry["gas"] >= config.THRESHOLDS["MQ6_GAS_ALERT"]) or (self.telemetry["flame"] == 1)
                if is_hazard:
                    self.telemetry["alarm"] = 1
                    self.telemetry["fan"] = 1

                self.telemetry["timestamp"] = int(time.time())

            self.notify_sse()
            self.publish_all_mqtt()

    # --------------------------------------------------------------------------
    # MQTT Broker Integration
    # --------------------------------------------------------------------------

    def start_mqtt(self):
        """Initializes and connects to the Mosquitto MQTT broker."""
        # Try port 1883 first, or fallback 1884
        for port in (config.MQTT_PORT, config.MQTT_FALLBACK_PORT):
            if self._try_connect_mqtt(port):
                self.mqtt_port = port
                break

    def _try_connect_mqtt(self, port: int) -> bool:
        if not HAS_PAHO:
            # Check if mosquitto CLI is responsive on this port
            try:
                res = subprocess.run(
                    ["mosquitto_pub", "-h", config.MQTT_HOST, "-p", str(port),
                     "-t", "smarthome/init", "-m", "ONLINE"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2
                )
                if res.returncode == 0:
                    self.mqtt_connected = True
                    with self.lock:
                        self.telemetry["mqtt"] = "Connected"
                    logger.info(f"Mosquitto CLI operational on port {port}. Starting CLI subscriber worker.")
                    t_sub = threading.Thread(target=self._cli_mqtt_sub_worker, args=(port,), daemon=True)
                    t_sub.start()
                    return True
            except Exception:
                pass
            return False

        try:
            try:
                self.mqtt_client = mqtt.Client(client_id="SmartHome_Gateway")
            except TypeError:
                self.mqtt_client = mqtt.Client(
                    mqtt.CallbackAPIVersion.VERSION1,
                    client_id="SmartHome_Gateway"
                )

            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_message = self.on_mqtt_message
            self.mqtt_client.on_disconnect = self.on_mqtt_disconnect

            self.mqtt_client.connect(config.MQTT_HOST, port, keepalive=60)
            self.mqtt_client.loop_start()
            return True
        except Exception as e:
            logger.debug(f"MQTT connect on port {port} failed: {e}")
            return False

    def _cli_mqtt_sub_worker(self, port: int):
        """Background worker that uses mosquitto_sub CLI to receive MQTT messages."""
        while self.running:
            try:
                proc = subprocess.Popen(
                    ["mosquitto_sub", "-h", config.MQTT_HOST, "-p", str(port),
                     "-t", "smarthome/+/set", "-F", "%t %p"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True
                )
                for line in proc.stdout:
                    if not self.running:
                        break
                    line = line.strip()
                    if line and " " in line:
                        topic, payload = line.split(" ", 1)
                        self.process_mqtt_command(topic, payload)
            except Exception as e:
                logger.warning(f"mosquitto_sub CLI error: {e}")
                time.sleep(3)

    def on_mqtt_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.mqtt_connected = True
            with self.lock:
                self.telemetry["mqtt"] = "Connected"
            logger.info("Connected to Mosquitto MQTT broker.")

            # Subscribe to command topics
            client.subscribe([
                (config.MQTT_TOPICS["LIGHT_SET"], 0),
                (config.MQTT_TOPICS["DOOR_SET"], 0),
                (config.MQTT_TOPICS["MODE_SET"], 0),
                (config.MQTT_TOPICS["FAN_SET"], 0),
                (config.MQTT_TOPICS["ALARM_SET"], 0),
            ])
            logger.info("Subscribed to SmartHome control MQTT topics.")
            self.publish_all_mqtt()
        else:
            self.mqtt_connected = False
            with self.lock:
                self.telemetry["mqtt"] = "Disconnected"

    def on_mqtt_disconnect(self, client, userdata, rc):
        self.mqtt_connected = False
        with self.lock:
            self.telemetry["mqtt"] = "Disconnected"
        logger.warning(f"Disconnected from MQTT broker (rc={rc})")

    def on_mqtt_message(self, client, userdata, msg):
        """Processes incoming MQTT command messages from Paho."""
        topic = msg.topic
        payload = msg.payload.decode('utf-8', errors='replace').strip()
        self.process_mqtt_command(topic, payload)

    def process_mqtt_command(self, topic: str, payload: str):
        """Processes incoming MQTT command messages from either Paho or CLI subscriber."""
        logger.info(f"MQTT Command [{topic}]: '{payload}'")

        if topic == config.MQTT_TOPICS["LIGHT_SET"]:
            p = payload.upper()
            if p in ("ON", "OFF", "TOGGLE"):
                self.send_serial_command(f"LIGHT {p}")
        elif topic == config.MQTT_TOPICS["DOOR_SET"]:
            p = payload.upper()
            if p in ("OPEN", "CLOSE"):
                self.send_serial_command(f"DOOR {p}")
            elif p.isdigit():
                self.send_serial_command(f"DOOR {p}")
        elif topic == config.MQTT_TOPICS["MODE_SET"]:
            p = payload.upper()
            if p in ("AUTO", "MANUAL"):
                self.send_serial_command(f"MODE {p}")
        elif topic == config.MQTT_TOPICS["FAN_SET"]:
            p = payload.upper()
            if p in ("ON", "OFF"):
                self.send_serial_command(f"FAN {p}")
        elif topic == config.MQTT_TOPICS["ALARM_SET"]:
            p = payload.upper()
            if p in ("MUTE", "SILENCE"):
                self.send_serial_command("BUZZER MUTE")
            elif p == "TEST":
                self.send_serial_command("ALARM TEST")

    def publish_mqtt(self, topic: str, message: str, retain: bool = False):
        """Publishes message using Paho or Mosquitto CLI."""
        if HAS_PAHO and self.mqtt_client and self.mqtt_connected:
            try:
                self.mqtt_client.publish(topic, message, qos=0, retain=retain)
                return
            except Exception:
                pass

        # Fallback Mosquitto CLI
        try:
            cmd = ["mosquitto_pub", "-h", config.MQTT_HOST, "-p", str(self.mqtt_port),
                   "-t", topic, "-m", message]
            if retain:
                cmd.append("-r")
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            self.mqtt_connected = True
            with self.lock:
                self.telemetry["mqtt"] = "Connected"
        except Exception:
            pass

    def publish_all_mqtt(self):
        """Publishes all current telemetry to MQTT broker."""
        with self.lock:
            payload = json.dumps(self.telemetry)
            light_state = "ON" if self.telemetry["light"] else "OFF"
            door_state = "OPEN" if self.telemetry["door"] >= 45 else "CLOSED"
            alarm_state = "EMERGENCY" if self.telemetry["alarm"] else "NORMAL"
            mode_state = self.telemetry["mode"]
            temp_val = str(self.telemetry["temp"])
            hum_val = str(self.telemetry["hum"])
            gas_val = str(self.telemetry["gas"])

        self.publish_mqtt(config.MQTT_TOPICS["TELEMETRY"], payload)
        self.publish_mqtt(config.MQTT_TOPICS["LIGHT_STATE"], light_state, retain=True)
        self.publish_mqtt(config.MQTT_TOPICS["DOOR_STATE"], door_state, retain=True)
        self.publish_mqtt(config.MQTT_TOPICS["MODE_STATE"], mode_state, retain=True)
        self.publish_mqtt(config.MQTT_TOPICS["ALARM_STATE"], alarm_state, retain=True)
        self.publish_mqtt(config.MQTT_TOPICS["SENSOR_TEMP"], temp_val)
        self.publish_mqtt(config.MQTT_TOPICS["SENSOR_HUM"], hum_val)
        self.publish_mqtt(config.MQTT_TOPICS["SENSOR_GAS"], gas_val)

    # --------------------------------------------------------------------------
    # Server-Sent Events (SSE) Stream
    # --------------------------------------------------------------------------

    def register_sse(self, queue):
        with self.sse_lock:
            self.sse_listeners.append(queue)

    def unregister_sse(self, queue):
        with self.sse_lock:
            if queue in self.sse_listeners:
                self.sse_listeners.remove(queue)

    def notify_sse(self):
        with self.lock:
            data = json.dumps(self.telemetry)
        with self.sse_lock:
            for q in list(self.sse_listeners):
                try:
                    q.put_nowait(data)
                except Exception:
                    pass

    # --------------------------------------------------------------------------
    # Lifecycle
    # --------------------------------------------------------------------------

    def start(self):
        # 1. Connect serial (or fallback to simulator)
        self.connect_serial()

        # 2. Start serial monitor thread
        t_serial = threading.Thread(target=self.serial_worker, name="SerialWorker", daemon=True)
        t_serial.start()

        # 3. Start simulator background thread
        t_sim = threading.Thread(target=self.simulation_worker, name="SimWorker", daemon=True)
        t_sim.start()

        # 4. Start MQTT connection
        self.start_mqtt()


# Instantiate Global Gateway
gateway = SmartHomeGateway()


# ==============================================================================
# REST API Handlers
# ==============================================================================

def handle_api_request(method: str, path: str, body_bytes: bytes = b"") -> tuple:
    """Dispatches HTTP REST calls to the gateway."""
    method = method.upper()

    if method == "OPTIONS":
        return 204, {}

    if method == "GET":
        if path == "/api/status":
            with gateway.lock:
                return 200, dict(gateway.telemetry)

    if method == "POST":
        # Multi-Light Controls
        match_light = re.match(r"^/api/light/([1-4]|all)/(on|off|toggle)$", path)
        if match_light:
            target, action = match_light.groups()
            cmd = f"LIGHTS ALL {action.upper()}" if target == "all" else f"LIGHT {target} {action.upper()}"
            gateway.send_serial_command(cmd)
            with gateway.lock:
                telemetry_copy = dict(gateway.telemetry)
            return 200, {"status": "ok", "target": target, "action": action, **telemetry_copy}

        # Legacy / Single Light Controls
        if path == "/api/light/on":
            gateway.send_serial_command("LIGHT 1 ON")
            with gateway.lock:
                telemetry_copy = dict(gateway.telemetry)
            return 200, {"status": "ok", "action": "light_on", **telemetry_copy}
        elif path == "/api/light/off":
            gateway.send_serial_command("LIGHT 1 OFF")
            with gateway.lock:
                telemetry_copy = dict(gateway.telemetry)
            return 200, {"status": "ok", "action": "light_off", **telemetry_copy}
        elif path == "/api/light/toggle":
            gateway.send_serial_command("LIGHT 1 TOGGLE")
            with gateway.lock:
                telemetry_copy = dict(gateway.telemetry)
            return 200, {"status": "ok", "action": "light_toggle", **telemetry_copy}
        elif path == "/api/lights/all/on":
            gateway.send_serial_command("LIGHTS ALL ON")
            with gateway.lock:
                telemetry_copy = dict(gateway.telemetry)
            return 200, {"status": "ok", "action": "lights_all_on", **telemetry_copy}
        elif path == "/api/lights/all/off":
            gateway.send_serial_command("LIGHTS ALL OFF")
            with gateway.lock:
                telemetry_copy = dict(gateway.telemetry)
            return 200, {"status": "ok", "action": "lights_all_off", **telemetry_copy}

        # Door / Gate Servo
        elif path == "/api/door/open":
            gateway.send_serial_command("DOOR OPEN")
            return 200, {"status": "ok", "action": "door_open"}
        elif path == "/api/door/close":
            gateway.send_serial_command("DOOR CLOSE")
            return 200, {"status": "ok", "action": "door_close"}
        elif path == "/api/door/set":
            try:
                payload = json.loads(body_bytes.decode('utf-8')) if body_bytes else {}
                angle = int(payload.get("angle", 0))
                gateway.send_serial_command(f"DOOR {angle}")
                return 200, {"status": "ok", "angle": angle}
            except Exception as e:
                return 400, {"error": str(e)}

        # Ventilation Fan
        elif path == "/api/fan/on":
            gateway.send_serial_command("FAN ON")
            return 200, {"status": "ok", "action": "fan_on"}
        elif path == "/api/fan/off":
            gateway.send_serial_command("FAN OFF")
            return 200, {"status": "ok", "action": "fan_off"}
        elif path == "/api/fan/toggle":
            with gateway.lock:
                target = "OFF" if gateway.telemetry["fan"] else "ON"
            gateway.send_serial_command(f"FAN {target}")
            return 200, {"status": "ok", "fan": target}

        # Automation Mode
        elif path == "/api/mode/auto":
            gateway.send_serial_command("MODE AUTO")
            return 200, {"status": "ok", "mode": "AUTO"}
        elif path == "/api/mode/manual":
            gateway.send_serial_command("MODE MANUAL")
            return 200, {"status": "ok", "mode": "MANUAL"}

        # Alarm Controls
        elif path in ("/api/alarm/silence", "/api/alarm/mute"):
            gateway.send_serial_command("BUZZER MUTE")
            gateway.sim_gas_override = 120
            gateway.sim_flame_override = 0
            return 200, {"status": "ok", "action": "alarm_silenced"}
        elif path == "/api/alarm/test":
            gateway.send_serial_command("ALARM TEST")
            return 200, {"status": "ok", "action": "alarm_test"}

        # Test Bench Simulator Controls
        elif path == "/api/simulate/motion":
            gateway.sim_motion_until = time.time() + 10
            return 200, {"status": "ok", "simulated": "motion"}
        elif path == "/api/simulate/gas":
            gateway.sim_gas_override = 650
            return 200, {"status": "ok", "simulated": "gas_alert"}
        elif path == "/api/simulate/flame":
            gateway.sim_flame_override = 1
            return 200, {"status": "ok", "simulated": "flame_alert"}
        elif path == "/api/simulate/night":
            gateway.sim_night_mode = not gateway.sim_night_mode
            return 200, {"status": "ok", "night_mode": gateway.sim_night_mode}
        elif path == "/api/simulate/clear":
            gateway.sim_gas_override = None
            gateway.sim_flame_override = None
            gateway.sim_motion_until = 0
            return 200, {"status": "ok", "simulated": "cleared"}

    return 404, {"error": "Endpoint not found"}


# ==============================================================================
# Standard Library Multi-Threaded HTTP & SSE Server
# ==============================================================================

from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import queue

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

class SmartHomeHTTPHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress excessive polling access logs
        if "/api/status" not in self.path and "/api/stream" not in self.path:
            super().log_message(format, *args)

    def do_HEAD(self):
        self._serve_get(send_body=False)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        self._serve_get(send_body=True)

    def _serve_get(self, send_body=True):
        clean_path = self.path.split('?')[0]

        # 1. Root Dashboard HTML
        if clean_path == "/" or clean_path == "/index.html":
            template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
            if os.path.exists(template_path):
                with open(template_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                if send_body:
                    self.wfile.write(content)
                return

        # 2. Static Assets (CSS, JS, Manifest, APK)
        if clean_path.startswith("/static/"):
            rel_file = clean_path[8:]
            file_path = os.path.join(os.path.dirname(__file__), "static", rel_file)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                mime = "text/plain"
                if rel_file.endswith(".css"):
                    mime = "text/css"
                elif rel_file.endswith(".js"):
                    mime = "application/javascript"
                elif rel_file.endswith(".json"):
                    mime = "application/json"
                elif rel_file.endswith(".png"):
                    mime = "image/png"
                elif rel_file.endswith(".apk"):
                    mime = "application/vnd.android.package-archive"

                with open(file_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', mime)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(content)))
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                if send_body:
                    self.wfile.write(content)
                return

        # 3. Server-Sent Events (SSE) Live Stream
        if clean_path == "/api/stream":
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            q = queue.Queue(maxsize=10)
            gateway.register_sse(q)

            # Send initial state immediately
            with gateway.lock:
                initial_data = json.dumps(gateway.telemetry)
            self.wfile.write(f"data: {initial_data}\n\n".encode('utf-8'))
            self.wfile.flush()

            try:
                while gateway.running:
                    try:
                        msg = q.get(timeout=1.0)
                        self.wfile.write(f"data: {msg}\n\n".encode('utf-8'))
                        self.wfile.flush()
                    except queue.Empty:
                        # Keep-alive heartbeat
                        self.wfile.write(b": keepalive\n\n")
                        self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                gateway.unregister_sse(q)
            return

        # 4. REST API Endpoint
        code, resp = handle_api_request("GET", clean_path)
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(resp).encode('utf-8'))

    def do_POST(self):
        clean_path = self.path.split('?')[0]
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""

        code, resp = handle_api_request("POST", clean_path, body)
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(resp).encode('utf-8'))


# ==============================================================================
# Server Runner
# ==============================================================================

def run_server():
    gateway.start()
    lan_ip = get_lan_ip()
    server_address = (config.WEB_HOST, config.WEB_PORT)
    httpd = ThreadedHTTPServer(server_address, SmartHomeHTTPHandler)

    logger.info("=" * 60)
    logger.info("⚡ SMART HOME IOT GATEWAY & PRO DASHBOARD ACTIVE")
    logger.info(f"📱 Access Mobile Web App:  http://{lan_ip}:{config.WEB_PORT}")
    logger.info(f"💻 Access Localhost:       http://localhost:{config.WEB_PORT}")
    logger.info(f"📡 Mosquitto MQTT Broker:  {config.MQTT_HOST}:{gateway.mqtt_port}")
    logger.info("=" * 60)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down SmartHome Gateway...")
        gateway.running = False
        httpd.server_close()


if __name__ == "__main__":
    run_server()
