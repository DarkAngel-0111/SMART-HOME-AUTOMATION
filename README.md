# ⚡ SmartHome Pro: IoT Automation System
### Arduino Uno • Sensors & Actuators • Mosquitto MQTT • Modern Glassmorphic PWA App

A complete, high-performance Smart Home IoT system powered by an **Arduino Uno**, an intelligent **Python Gateway**, a local **Mosquitto MQTT Broker**, and a stylish **SmartHome Pro Progressive Web App (PWA)** designed to replace MIT App Inventor with high-end dark glassmorphism UI/UX.

---

## 🏛️ System Architecture

```
┌────────────────────────────────────────────────────────┐
│              📱 Android / iPhone / Laptop              │
│               (SmartHome Pro PWA & UI)                 │
│   • Cyberpunk / Glassmorphism Dark Theme               │
│   • Real-Time SVG Radial Gauges (Temp, Humidity, Gas)  │
│   • Dynamic Sun / Moon LDR Sky Visualization           │
│   • Radar Ripple (PIR Motion & IR Obstacle)            │
│   • Ultrasonic Garage Distance Progress Bar            │
│   • Interactive Servo Door Lock Slider & Controls      │
│   • Emergency Flashing Strobe Banner & Web Audio Alarm │
└───────────────────────────┬────────────────────────────┘
                            │  HTTP REST / SSE Stream (Port 5000)
                            ▼
┌────────────────────────────────────────────────────────┐
│        💻 Linux Laptop / Raspberry Pi (Gateway)        │
│                                                        │
│   ┌───────────────────────────┐    MQTT     ┌────────┐ │
│   │   Python Gateway (app.py) │◄───────────►│Mosquit-│ │
│   │   • Serial Command Engine │  Port 1883  │to      │ │
│   │   • REST & SSE Web Server │  or 1884    │Broker  │ │
│   │   • MQTT Pub/Sub Dispatch │             └────────┘ │
│   │   • Built-in Simulator    │                        │
│   └─────────────┬─────────────┘                        │
└─────────────────┼──────────────────────────────────────┘
                  │  USB Serial Cable (9600 baud)
                  │  JSON Telemetry & Command Line Protocol
                  ▼
┌────────────────────────────────────────────────────────┐
│               ⚡ Arduino Uno (ATmega328P)              │
│                (arduino/smart_home.ino)                │
│                                                        │
│   INPUT SENSORS:               OUTPUT ACTUATORS:       │
│   • D2:  PIR Motion Sensor     • D4:  Main Room Light  │
│   • D3:  DHT11/22 Temp & Hum   • D6:  Active Buzzer    │
│   • D5:  Flame Sensor (Fire)   • D10: Servo Motor      │
│   • D7:  IR Entrance Sensor    • D11: Warning Red LED  │
│   • D8/9:Ultrasonic (Distance) • D12: Ventilation Fan  │
│   • A0:  LDR (Ambient Light)   • D13: Activity LED     │
│   • A1:  MQ-6 (LPG/Gas Sensor)                         │
└────────────────────────────────────────────────────────┘
```

---

## 🔌 Hardware Connections & Complete Pinout Table

All 7 sensors and 5 actuators connect simultaneously to the Arduino Uno without any pin conflicts:

| Component | Arduino Uno Pin | Type | Wiring Details & Function |
|---|---|---|---|
| **PIR Motion Sensor** | `Pin D2` | Digital IN | `VCC` &rarr; 5V, `GND` &rarr; GND, `OUT` &rarr; D2. Auto-triggers lighting. |
| **DHT11 / DHT22 Sensor** | `Pin D3` | Digital I/O | `VCC` &rarr; 5V, `GND` &rarr; GND, `DATA` &rarr; D3 (with 10kΩ pull-up). Climate tracking. |
| **Main Room Light** | `Pin D4` | Digital OUT | Connects to Relay Module `IN1` or LED with 220Ω resistor. Auto/Manual lighting. |
| **Flame Sensor** | `Pin D5` | Digital IN | `VCC` &rarr; 5V, `GND` &rarr; GND, `D0` &rarr; D5. Detects fire radiation. |
| **Active Buzzer** | `Pin D6` | Digital OUT | Positive `+` &rarr; D6, Negative `-` &rarr; GND. Audible hazard siren. |
| **IR Obstacle Sensor** | `Pin D7` | Digital IN | `VCC` &rarr; 5V, `GND` &rarr; GND, `OUT` &rarr; D7. Doorway tripwire/entrance sensor. |
| **Ultrasonic HC-SR04 TRIG** | `Pin D8` | Digital OUT | `TRIG` &rarr; D8. 10µs ultrasonic pulse emitter. |
| **Ultrasonic HC-SR04 ECHO** | `Pin D9` | Digital IN | `ECHO` &rarr; D9. Measures sound reflection time for distance (2–400 cm). |
| **Servo Motor (Door Lock)** | `Pin D10` | PWM OUT | Orange/Yellow &rarr; D10, Red &rarr; 5V, Brown/Black &rarr; GND. 0° Closed, 90° Open. |
| **Warning Red LED** | `Pin D11` | Digital OUT | Anode `+` &rarr; D11 (via 220Ω), Cathode `-` &rarr; GND. Strobe flasher for fire/gas. |
| **Ventilation Fan / Aux** | `Pin D12` | Digital OUT | Connects to Relay Module `IN2` or 5V DC fan. Auto-turns on during gas leak. |
| **Activity Indicator** | `Pin D13` | Digital OUT | Built-in Arduino LED. Flashes on command execution and heartbeat. |
| **LDR Light Sensor** | `Pin A0` | Analog IN | One leg &rarr; 5V, other leg &rarr; A0 & 10kΩ resistor to GND. Day/Night detection. |
| **MQ-6 Gas Sensor** | `Pin A1` | Analog IN | `VCC` &rarr; 5V, `GND` &rarr; GND, `A0` &rarr; A1. LPG & combustible gas concentration. |

---

## ⚡ Smart Automation Rules

1. **🚨 Gas Leak & Fire Emergency**:
   - When **MQ-6 Gas Sensor** detects gas > 400 ADC or **Flame Sensor** detects fire:
     - **Active Buzzer (D6)** sounds continuous emergency siren.
     - **Warning Red LED (D11)** strobes rapidly (every 150ms).
     - **Ventilation Fan (D12)** turns ON to disperse dangerous vapors.
     - **Emergency Banner** flashes on the Mobile App with Web Audio siren chime.
2. **💡 Intelligent Ambient Lighting (LDR + PIR)**:
   - **Daytime (LDR Bright)**: Room light remains OFF to save electricity.
   - **Nighttime (LDR Dark)**: When **PIR Motion Sensor** detects human presence, Room Light turns ON automatically and remains active for 20 seconds after motion ceases.
   - **App Manual Override**: You can switch to `MANUAL` mode at any time to toggle lights directly.
3. **🚪 Smart Door Lock & Garage Proximity (Ultrasonic + Servo + IR)**:
   - **Ultrasonic Sensor (HC-SR04)** measures vehicle or doorway distance in centimeters.
   - **Servo Motor (D10)** functions as a digital deadbolt or garage gate (0° Locked, 90° Unlocked, with smooth slider control up to 180°).

---

## 🚀 Step-by-Step Setup Guide

### Step 1: Flash Arduino Uno
1. Open the **Arduino IDE**.
2. Open [`arduino/smart_home.ino`](arduino/smart_home.ino).
3. If not already installed, install the **DHT sensor library by Adafruit** via **Tools &rarr; Manage Libraries**. (The `<Servo.h>` library is included standard with the Arduino IDE).
4. Connect your Arduino Uno with the USB cable.
5. Select **Tools &rarr; Board &rarr; Arduino Uno** and select your port (e.g. `/dev/ttyACM0` or `/dev/ttyUSB0`).
6. Click **Upload** (Ctrl + U).

### Step 2: Start Mosquitto MQTT Broker
In your Linux terminal:
```bash
mosquitto -p 1884 -d
```
*(If port 1883 is already running on your machine, the gateway automatically connects to port 1883 or falls back to port 1884).*

### Step 3: Run the Python Gateway
```bash
python3 app.py
```
You will see output similar to:
```
⚡ SMART HOME IOT GATEWAY & PRO DASHBOARD ACTIVE
📱 Access Mobile Web App:  http://192.168.1.100:5000
💻 Access Localhost:       http://localhost:5000
📡 Mosquitto MQTT Broker:  localhost:1884
```

> [!NOTE]
> **Built-in Hardware Simulator**: If you launch `app.py` before plugging in your Arduino, the gateway automatically activates its realistic hardware simulator! You can test all gauges, alarms, motion triggers, and door lock controls immediately right from the browser.

---

## 📱 Android App (.apk) & Mobile Web App

You have two options to control your Smart Home from any smartphone:

### Option 1: Native Android App (`.apk`)
A standalone native Android application has been compiled and packaged:
- **APK File Location**: [`SmartHome_Pro.apk`](SmartHome_Pro.apk) (12 MB)
- **Direct Download via Phone**: While your gateway is running, open your phone's browser and go to:
  ```
  http://<YOUR_LAPTOP_IP>:5000/static/SmartHome_Pro.apk
  ```
- **Install via ADB (if connected via USB)**:
  ```bash
  adb install SmartHome_Pro.apk
  ```
- **How to Connect**:
  1. Launch **SmartHome Pro** on your phone.
  2. Enter your laptop/gateway IP address (e.g. `192.168.1.100`) and port `5000`.
  3. Tap **CONNECT TO SMART HOME**.
  4. The app will save the IP address, connect immediately, and load the full Smart Home controls!
  5. Tap the ⚙️ icon in the top right corner at any time to change or re-enter the IP.

### Option 2: Progressive Web App (PWA)
1. Make sure your smartphone and laptop are connected to the same Wi-Fi network.
2. Open **Google Chrome** (on Android) or **Safari** (on iPhone).
3. Type the gateway address displayed in the terminal: `http://<YOUR_LAPTOP_IP>:5000`.
4. Tap the browser menu &rarr; **"Add to Home screen"** or **"Install App"**.

---

## 📡 MQTT Topic Specification

| Topic | Payload | Direction | Description |
|---|---|---|---|
| `smarthome/telemetry` | `{"temp":24.5,"hum":52,"gas":120,"flame":0,"pir":0,"ldr":650,"dist":45,"door":0,"light":0,"fan":0,"alarm":0}` | Publish | Full JSON telemetry frame |
| `smarthome/lights/set` | `ON`, `OFF`, `TOGGLE` | Subscribe | Command to switch main room light |
| `smarthome/lights/state` | `ON`, `OFF` | Publish | Current main light state |
| `smarthome/door/set` | `OPEN`, `CLOSE`, `0-180` | Subscribe | Command to position servo door lock |
| `smarthome/door/state` | `OPEN`, `CLOSED` | Publish | Current door lock status |
| `smarthome/mode/set` | `AUTO`, `MANUAL` | Subscribe | Automation engine mode switch |
| `smarthome/mode/state` | `AUTO`, `MANUAL` | Publish | Current operational mode |
| `smarthome/alarm/set` | `SILENCE`, `TEST` | Subscribe | Mute buzzer or run alarm test |
| `smarthome/alarm/state` | `NORMAL`, `EMERGENCY` | Publish | Hazard alert level |

---

## 🌐 REST API Endpoints

- `GET  /api/status` &mdash; Returns current live telemetry JSON.
- `GET  /api/stream` &mdash; Server-Sent Events (SSE) real-time push stream.
- `POST /api/light/on` &mdash; Turns main room light ON.
- `POST /api/light/off` &mdash; Turns main room light OFF.
- `POST /api/light/toggle` &mdash; Toggles main room light.
- `POST /api/door/open` &mdash; Unlocks / Opens door servo to 90°.
- `POST /api/door/close` &mdash; Locks / Closes door servo to 0°.
- `POST /api/door/set` &mdash; Moves door servo to specific degree (`{"angle": 45}`).
- `POST /api/fan/toggle` &mdash; Toggles ventilation fan.
- `POST /api/mode/auto` &mdash; Sets automation mode to AUTO.
- `POST /api/mode/manual` &mdash; Sets automation mode to MANUAL.
- `POST /api/alarm/silence` &mdash; Mutes active alarm siren.
- `POST /api/simulate/gas` &mdash; Simulates gas leak emergency.
- `POST /api/simulate/flame` &mdash; Simulates fire radiation trigger.
- `POST /api/simulate/motion` &mdash; Simulates PIR motion detection.
