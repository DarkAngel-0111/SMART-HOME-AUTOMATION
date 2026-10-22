/*
  ==============================================================================
  Smart Home IoT System - Arduino Uno C++ Firmware
  ==============================================================================
  Hardware:
    - Arduino Uno R3 (ATmega328P)
    - MQ-6 Gas Sensor (A1)
    - Flame Sensor (D5)
    - PIR Motion Sensor (D2)
    - LDR Light Sensor (A0)
    - DHT11 / DHT22 Humidity & Temp Sensor (D3)
    - IR Proximity / Obstacle Sensor (D7)
    - Ultrasonic Sensor HC-SR04 (Trig: D8, Echo: D9)
    - Servo Motor (Door / Gate Lock) (D10)
    - Main Room Light Relay / LED (D4)
    - Active Alarm Buzzer (D6)
    - Warning Red LED (D11)
    - Ventilation Fan / Aux Relay (D12)
    - Status / Comm Activity LED (D13)
  ==============================================================================
*/

#include <Servo.h>
#include <DHT.h>

// -----------------------------------------------------------------------------
// Pin Definitions
// -----------------------------------------------------------------------------
const byte PIN_PIR        = 2;   // Digital IN
const byte PIN_DHT        = 3;   // Digital I/O
const byte PIN_LIGHT1     = 4;   // Digital OUT (Light 1: Living Room Relay)
const byte PIN_LIGHT2     = A2;  // Digital OUT (Light 2: Bedroom Relay)
const byte PIN_LIGHT3     = A3;  // Digital OUT (Light 3: Kitchen Relay)
const byte PIN_LIGHT4     = A4;  // Digital OUT (Light 4: Balcony/Outdoor Relay)
const byte PIN_LIGHT      = PIN_LIGHT1; // Alias
const byte PIN_FLAME      = 5;   // Digital IN  (Flame Detector)
const byte PIN_BUZZER     = 6;   // Digital OUT (Active Buzzer)
const byte PIN_IR         = 7;   // Digital IN  (IR Obstacle / Entrance)
const byte PIN_US_TRIG    = 8;   // Digital OUT (Ultrasonic Trig)
const byte PIN_US_ECHO    = 9;   // Digital IN  (Ultrasonic Echo)
const byte PIN_SERVO      = 10;  // PWM OUT     (Servo Motor)
const byte PIN_ALARM_LED  = 11;  // Digital OUT (Warning Red Flashing LED)
const byte PIN_FAN        = 12;  // Digital OUT (Ventilation Fan / Aux)
const byte PIN_STATUS_LED = 13;  // Digital OUT (Built-in Activity LED)

const byte PIN_LDR        = A0;  // Analog IN   (LDR Photoresistor)
const byte PIN_MQ6        = A1;  // Analog IN   (MQ-6 Gas Sensor)

// -----------------------------------------------------------------------------
// Sensor Types and Thresholds
// -----------------------------------------------------------------------------
#define DHT_TYPE DHT11           // Change to DHT22 if using DHT22
DHT dht(PIN_DHT, DHT_TYPE);
Servo doorServo;

// Thresholds (Adjustable via Serial or calibration)
int LDR_DARK_THRESHOLD   = 450;  // Below this value = Night / Dark
int MQ6_GAS_THRESHOLD    = 400;  // Above this value = Gas Leak Detected
const bool FLAME_ACTIVE_LOW = true; // Most flame sensors pull LOW when flame is detected
const bool IR_ACTIVE_LOW    = true; // Most IR obstacle sensors pull LOW when obstructed

// -----------------------------------------------------------------------------
// System State Variables
// -----------------------------------------------------------------------------
bool modeAuto = true;            // AUTO or MANUAL mode
bool light1State = false;        // Light 1 state
bool light2State = false;        // Light 2 state
bool light3State = false;        // Light 3 state
bool light4State = false;        // Light 4 state
bool lightState = false;         // Mirrors light1State for backward compatibility
bool fanState = false;           // false = OFF, true = ON
int  doorAngle = 0;              // 0 = Locked/Closed, 90 = Unlocked/Open
bool buzzerMuted = false;        // Temporary alarm mute

// Sensor Readings
float temperature = 24.0;
float humidity = 50.0;
int   rawGas = 0;
int   rawLdr = 0;
bool  flameDetected = false;
bool  gasAlert = false;
bool  motionDetected = false;
bool  irDetected = false;
int   distanceCm = 0;

// Alarm and Strobe State
bool alarmActive = false;
unsigned long lastAlarmStrobe = 0;
bool strobeLedState = false;

// Auto Lighting Timer
unsigned long lastMotionTime = 0;
const unsigned long LIGHT_OFF_DELAY_MS = 20000; // 20s light stay-on after motion

// Timers for Non-Blocking Loop
unsigned long lastDHTRead = 0;
unsigned long lastUltrasonicRead = 0;
unsigned long lastTelemetryReport = 0;

// Serial Buffer
const int SERIAL_BUF_SIZE = 64;
char serialBuffer[SERIAL_BUF_SIZE];
byte bufIndex = 0;

// -----------------------------------------------------------------------------
// Setup Routine
// -----------------------------------------------------------------------------
void setup() {
  // Configure Pins
  pinMode(PIN_PIR, INPUT);
  pinMode(PIN_FLAME, INPUT_PULLUP);
  pinMode(PIN_IR, INPUT_PULLUP);
  pinMode(PIN_US_ECHO, INPUT);
  
  pinMode(PIN_LIGHT1, OUTPUT);
  pinMode(PIN_LIGHT2, OUTPUT);
  pinMode(PIN_LIGHT3, OUTPUT);
  pinMode(PIN_LIGHT4, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_ALARM_LED, OUTPUT);
  pinMode(PIN_FAN, OUTPUT);
  pinMode(PIN_STATUS_LED, OUTPUT);
  pinMode(PIN_US_TRIG, OUTPUT);

  // Initial Pin States
  digitalWrite(PIN_LIGHT1, LOW);
  digitalWrite(PIN_LIGHT2, LOW);
  digitalWrite(PIN_LIGHT3, LOW);
  digitalWrite(PIN_LIGHT4, LOW);
  digitalWrite(PIN_BUZZER, LOW);
  digitalWrite(PIN_ALARM_LED, LOW);
  digitalWrite(PIN_FAN, LOW);
  digitalWrite(PIN_STATUS_LED, LOW);
  digitalWrite(PIN_US_TRIG, LOW);

  // Initialize Servo
  doorServo.attach(PIN_SERVO);
  doorServo.write(0); // Start locked
  doorAngle = 0;

  // Initialize Serial & DHT
  Serial.begin(9600);
  dht.begin();

  // Indicate Ready
  digitalWrite(PIN_STATUS_LED, HIGH);
  delay(300);
  digitalWrite(PIN_STATUS_LED, LOW);

  Serial.println(F("{\"system\":\"SMART_HOME_READY\",\"version\":\"2.0\"}"));
}

// -----------------------------------------------------------------------------
// Non-Blocking Ultrasonic Distance Measurement
// -----------------------------------------------------------------------------
void measureUltrasonic() {
  if (millis() - lastUltrasonicRead < 200) return;
  lastUltrasonicRead = millis();

  digitalWrite(PIN_US_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PIN_US_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_US_TRIG, LOW);

  // 25ms timeout corresponds to approx 4.3 meters
  long duration = pulseIn(PIN_US_ECHO, HIGH, 25000);
  if (duration > 0) {
    distanceCm = duration * 0.034 / 2;
  } else {
    distanceCm = 400; // Out of range or no echo
  }
}

// -----------------------------------------------------------------------------
// Non-Blocking DHT Reading
// -----------------------------------------------------------------------------
void readDHT() {
  if (millis() - lastDHTRead < 2000) return;
  lastDHTRead = millis();

  float t = dht.readTemperature();
  float h = dht.readHumidity();

  if (!isnan(t) && !isnan(h)) {
    temperature = t;
    humidity = h;
  }
}

// -----------------------------------------------------------------------------
// Command Dispatcher
// -----------------------------------------------------------------------------
void processCommand(char* cmd) {
  // Trim spaces
  while (*cmd == ' ' || *cmd == '\r' || *cmd == '\t') cmd++;
  int len = strlen(cmd);
  while (len > 0 && (cmd[len - 1] == ' ' || cmd[len - 1] == '\r' || cmd[len - 1] == '\n')) {
    cmd[--len] = '\0';
  }
  if (len == 0) return;

  // Flash status LED on serial command
  digitalWrite(PIN_STATUS_LED, HIGH);

  if (strcasecmp(cmd, "LIGHT 1 ON") == 0 || strcasecmp(cmd, "LIGHT1 ON") == 0 || strcasecmp(cmd, "LIGHT ON") == 0) {
    light1State = true;
    lightState = true;
    digitalWrite(PIN_LIGHT1, HIGH);
    Serial.println(F("OK LIGHT1 ON"));
  }
  else if (strcasecmp(cmd, "LIGHT 1 OFF") == 0 || strcasecmp(cmd, "LIGHT1 OFF") == 0 || strcasecmp(cmd, "LIGHT OFF") == 0) {
    light1State = false;
    lightState = false;
    digitalWrite(PIN_LIGHT1, LOW);
    Serial.println(F("OK LIGHT1 OFF"));
  }
  else if (strcasecmp(cmd, "LIGHT 1 TOGGLE") == 0 || strcasecmp(cmd, "LIGHT1 TOGGLE") == 0 || strcasecmp(cmd, "LIGHT TOGGLE") == 0) {
    light1State = !light1State;
    lightState = light1State;
    digitalWrite(PIN_LIGHT1, light1State ? HIGH : LOW);
    Serial.println(light1State ? F("OK LIGHT1 ON") : F("OK LIGHT1 OFF"));
  }
  else if (strcasecmp(cmd, "LIGHT 2 ON") == 0 || strcasecmp(cmd, "LIGHT2 ON") == 0) {
    light2State = true;
    digitalWrite(PIN_LIGHT2, HIGH);
    Serial.println(F("OK LIGHT2 ON"));
  }
  else if (strcasecmp(cmd, "LIGHT 2 OFF") == 0 || strcasecmp(cmd, "LIGHT2 OFF") == 0) {
    light2State = false;
    digitalWrite(PIN_LIGHT2, LOW);
    Serial.println(F("OK LIGHT2 OFF"));
  }
  else if (strcasecmp(cmd, "LIGHT 2 TOGGLE") == 0 || strcasecmp(cmd, "LIGHT2 TOGGLE") == 0) {
    light2State = !light2State;
    digitalWrite(PIN_LIGHT2, light2State ? HIGH : LOW);
    Serial.println(light2State ? F("OK LIGHT2 ON") : F("OK LIGHT2 OFF"));
  }
  else if (strcasecmp(cmd, "LIGHT 3 ON") == 0 || strcasecmp(cmd, "LIGHT3 ON") == 0) {
    light3State = true;
    digitalWrite(PIN_LIGHT3, HIGH);
    Serial.println(F("OK LIGHT3 ON"));
  }
  else if (strcasecmp(cmd, "LIGHT 3 OFF") == 0 || strcasecmp(cmd, "LIGHT3 OFF") == 0) {
    light3State = false;
    digitalWrite(PIN_LIGHT3, LOW);
    Serial.println(F("OK LIGHT3 OFF"));
  }
  else if (strcasecmp(cmd, "LIGHT 3 TOGGLE") == 0 || strcasecmp(cmd, "LIGHT3 TOGGLE") == 0) {
    light3State = !light3State;
    digitalWrite(PIN_LIGHT3, light3State ? HIGH : LOW);
    Serial.println(light3State ? F("OK LIGHT3 ON") : F("OK LIGHT3 OFF"));
  }
  else if (strcasecmp(cmd, "LIGHT 4 ON") == 0 || strcasecmp(cmd, "LIGHT4 ON") == 0) {
    light4State = true;
    digitalWrite(PIN_LIGHT4, HIGH);
    Serial.println(F("OK LIGHT4 ON"));
  }
  else if (strcasecmp(cmd, "LIGHT 4 OFF") == 0 || strcasecmp(cmd, "LIGHT4 OFF") == 0) {
    light4State = false;
    digitalWrite(PIN_LIGHT4, LOW);
    Serial.println(F("OK LIGHT4 OFF"));
  }
  else if (strcasecmp(cmd, "LIGHT 4 TOGGLE") == 0 || strcasecmp(cmd, "LIGHT4 TOGGLE") == 0) {
    light4State = !light4State;
    digitalWrite(PIN_LIGHT4, light4State ? HIGH : LOW);
    Serial.println(light4State ? F("OK LIGHT4 ON") : F("OK LIGHT4 OFF"));
  }
  else if (strcasecmp(cmd, "LIGHTS ALL ON") == 0 || strcasecmp(cmd, "LIGHT ALL ON") == 0) {
    light1State = light2State = light3State = light4State = lightState = true;
    digitalWrite(PIN_LIGHT1, HIGH);
    digitalWrite(PIN_LIGHT2, HIGH);
    digitalWrite(PIN_LIGHT3, HIGH);
    digitalWrite(PIN_LIGHT4, HIGH);
    Serial.println(F("OK LIGHTS ALL ON"));
  }
  else if (strcasecmp(cmd, "LIGHTS ALL OFF") == 0 || strcasecmp(cmd, "LIGHT ALL OFF") == 0) {
    light1State = light2State = light3State = light4State = lightState = false;
    digitalWrite(PIN_LIGHT1, LOW);
    digitalWrite(PIN_LIGHT2, LOW);
    digitalWrite(PIN_LIGHT3, LOW);
    digitalWrite(PIN_LIGHT4, LOW);
    Serial.println(F("OK LIGHTS ALL OFF"));
  }
  else if (strcasecmp(cmd, "DOOR OPEN") == 0) {
    doorAngle = 90;
    doorServo.write(doorAngle);
    Serial.println(F("OK DOOR OPEN"));
  }
  else if (strcasecmp(cmd, "DOOR CLOSE") == 0) {
    doorAngle = 0;
    doorServo.write(doorAngle);
    Serial.println(F("OK DOOR CLOSE"));
  }
  else if (strncasecmp(cmd, "DOOR ", 5) == 0) {
    int angle = atoi(cmd + 5);
    if (angle >= 0 && angle <= 180) {
      doorAngle = angle;
      doorServo.write(doorAngle);
      Serial.print(F("OK DOOR "));
      Serial.println(doorAngle);
    }
  }
  else if (strcasecmp(cmd, "MODE AUTO") == 0) {
    modeAuto = true;
    Serial.println(F("OK MODE AUTO"));
  }
  else if (strcasecmp(cmd, "MODE MANUAL") == 0) {
    modeAuto = false;
    Serial.println(F("OK MODE MANUAL"));
  }
  else if (strcasecmp(cmd, "FAN ON") == 0) {
    fanState = true;
    digitalWrite(PIN_FAN, HIGH);
    Serial.println(F("OK FAN ON"));
  }
  else if (strcasecmp(cmd, "FAN OFF") == 0) {
    fanState = false;
    digitalWrite(PIN_FAN, LOW);
    Serial.println(F("OK FAN OFF"));
  }
  else if (strcasecmp(cmd, "BUZZER MUTE") == 0 || strcasecmp(cmd, "ALARM SILENCE") == 0) {
    buzzerMuted = true;
    digitalWrite(PIN_BUZZER, LOW);
    Serial.println(F("OK ALARM SILENCED"));
  }
  else if (strcasecmp(cmd, "ALARM TEST") == 0) {
    buzzerMuted = false;
    digitalWrite(PIN_BUZZER, HIGH);
    digitalWrite(PIN_ALARM_LED, HIGH);
    delay(200);
    digitalWrite(PIN_BUZZER, LOW);
    digitalWrite(PIN_ALARM_LED, LOW);
    Serial.println(F("OK ALARM TESTED"));
  }
  else if (strcasecmp(cmd, "STATUS") == 0) {
    sendTelemetryJSON();
  }
  else if (strcasecmp(cmd, "PING") == 0) {
    Serial.println(F("PONG"));
  }
  else {
    Serial.print(F("ERR UNKNOWN_CMD: "));
    Serial.println(cmd);
  }

  digitalWrite(PIN_STATUS_LED, LOW);
}

// -----------------------------------------------------------------------------
// Read Serial Stream Non-Blocking
// -----------------------------------------------------------------------------
void checkSerial() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (bufIndex > 0) {
        serialBuffer[bufIndex] = '\0';
        processCommand(serialBuffer);
        bufIndex = 0;
      }
    } else {
      if (bufIndex < SERIAL_BUF_SIZE - 1) {
        serialBuffer[bufIndex++] = c;
      }
    }
  }
}

// -----------------------------------------------------------------------------
// Format & Broadcast JSON Telemetry
// -----------------------------------------------------------------------------
void sendTelemetryJSON() {
  Serial.print(F("{\"temp\":"));
  Serial.print(temperature, 1);
  Serial.print(F(",\"hum\":"));
  Serial.print(humidity, 1);
  Serial.print(F(",\"gas\":"));
  Serial.print(rawGas);
  Serial.print(F(",\"flame\":"));
  Serial.print(flameDetected ? 1 : 0);
  Serial.print(F(",\"pir\":"));
  Serial.print(motionDetected ? 1 : 0);
  Serial.print(F(",\"ldr\":"));
  Serial.print(rawLdr);
  Serial.print(F(",\"ir\":"));
  Serial.print(irDetected ? 1 : 0);
  Serial.print(F(",\"dist\":"));
  Serial.print(distanceCm);
  Serial.print(F(",\"light1\":"));
  Serial.print(light1State ? 1 : 0);
  Serial.print(F(",\"light2\":"));
  Serial.print(light2State ? 1 : 0);
  Serial.print(F(",\"light3\":"));
  Serial.print(light3State ? 1 : 0);
  Serial.print(F(",\"light4\":"));
  Serial.print(light4State ? 1 : 0);
  Serial.print(F(",\"light\":"));
  Serial.print(light1State ? 1 : 0);
  Serial.print(F(",\"door\":"));
  Serial.print(doorAngle);
  Serial.print(F(",\"fan\":"));
  Serial.print(fanState ? 1 : 0);
  Serial.print(F(",\"alarm\":"));
  Serial.print(alarmActive ? 1 : 0);
  Serial.print(F(",\"mode\":\""));
  Serial.print(modeAuto ? F("AUTO") : F("MANUAL"));
  Serial.println(F("\"}"));
}

// -----------------------------------------------------------------------------
// Main Loop
// -----------------------------------------------------------------------------
void loop() {
  // 1. Process Incoming Serial Commands
  checkSerial();

  // 2. Read Sensors
  rawGas = analogRead(PIN_MQ6);
  rawLdr = analogRead(PIN_LDR);
  motionDetected = (digitalRead(PIN_PIR) == HIGH);

  int flameVal = digitalRead(PIN_FLAME);
  flameDetected = FLAME_ACTIVE_LOW ? (flameVal == LOW) : (flameVal == HIGH);

  int irVal = digitalRead(PIN_IR);
  irDetected = IR_ACTIVE_LOW ? (irVal == LOW) : (irVal == HIGH);

  gasAlert = (rawGas >= MQ6_GAS_THRESHOLD);
  alarmActive = (gasAlert || flameDetected);

  measureUltrasonic();
  readDHT();

  // 3. Safety Alarm & Emergency Red LED Strobe
  if (alarmActive) {
    // Strobe Warning Red LED every 150ms
    if (millis() - lastAlarmStrobe >= 150) {
      lastAlarmStrobe = millis();
      strobeLedState = !strobeLedState;
      digitalWrite(PIN_ALARM_LED, strobeLedState ? HIGH : LOW);
    }
    // Sound buzzer unless muted
    if (!buzzerMuted) {
      digitalWrite(PIN_BUZZER, HIGH);
    }
    // Auto-turn on fan for gas dispersal if gas detected
    if (gasAlert && !fanState) {
      fanState = true;
      digitalWrite(PIN_FAN, HIGH);
    }
  } else {
    // Normal state - warning LED and buzzer OFF
    digitalWrite(PIN_ALARM_LED, LOW);
    digitalWrite(PIN_BUZZER, LOW);
    buzzerMuted = false; // Reset mute when threat clears
  }

  // 4. Intelligent Lighting Automation (Auto Mode)
  if (modeAuto) {
    bool isNight = (rawLdr < LDR_DARK_THRESHOLD);

    if (motionDetected) {
      lastMotionTime = millis();
    }

    if (isNight) {
      // At night: turn on when motion is detected, keep on for LIGHT_OFF_DELAY_MS
      if (motionDetected || (millis() - lastMotionTime < LIGHT_OFF_DELAY_MS)) {
        if (!lightState) {
          lightState = true;
          digitalWrite(PIN_LIGHT, HIGH);
        }
      } else {
        if (lightState) {
          lightState = false;
          digitalWrite(PIN_LIGHT, LOW);
        }
      }
    } else {
      // During daytime: keep light OFF to conserve energy
      if (lightState) {
        lightState = false;
        digitalWrite(PIN_LIGHT, LOW);
      }
    }
  }

  // 5. Periodic Telemetry Report (Every 1 second)
  if (millis() - lastTelemetryReport >= 1000) {
    lastTelemetryReport = millis();
    sendTelemetryJSON();
  }
}
