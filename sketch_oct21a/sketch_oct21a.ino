
/*
  SMART HOME IoT PROJECT
  Board: Arduino Uno R3

  LED Light       : D4
  PIR Sensor      : D2
  DHT22 DATA      : D3
  Flame Sensor DO : D5
  Buzzer          : D6
  LDR Module AO   : A0
  MQ-2 Sensor AO  : A1

  Serial commands:
  LIGHT ON
  LIGHT OFF
  ALL ON
  ALL OFF
  AUTO
*/

#include <DHT.h>

// Pin configuration
const byte LED_PIN = 4;
const byte PIR_PIN = 2;
const byte DHT_PIN = 3;
const byte FLAME_PIN = 5;
const byte BUZZER_PIN = 6;

const byte LDR_PIN = A0;
const byte MQ2_PIN = A1;

// DHT22 setup
#define DHT_TYPE DHT22
DHT dht(DHT_PIN, DHT_TYPE);

// Adjust after checking actual readings
const int LDR_DARK_THRESHOLD = 400;
const int MQ2_THRESHOLD = 500;

// Most flame modules output LOW when flame is detected
const byte FLAME_ACTIVE_LEVEL = LOW;

// Set to true if your module detects flame with HIGH
const bool FLAME_ACTIVE_HIGH = false;

// State variables
bool manualOverride = false;
bool manualLight = false;

bool motionDetected = false;
bool flameDetected = false;
bool gasDetected = false;

bool lightOn = false;

unsigned long lastReport = 0;
unsigned long lastDHTRead = 0;

float temperature = NAN;
float humidity = NAN;

void setup() {
  pinMode(LED_PIN, OUTPUT);
  pinMode(PIR_PIN, INPUT);
  pinMode(FLAME_PIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  digitalWrite(LED_PIN, LOW);
  digitalWrite(BUZZER_PIN, LOW);

  Serial.begin(9600);
  Serial.setTimeout(50);

  dht.begin();

  Serial.println("SMART HOME READY");
  Serial.println("Commands:");
  Serial.println("LIGHT ON");
  Serial.println("LIGHT OFF");
  Serial.println("ALL ON");
  Serial.println("ALL OFF");
  Serial.println("AUTO");
}

void readCommands() {
  if (!Serial.available()) {
    return;
  }

  String command = Serial.readStringUntil('\n');
  command.trim();
  command.toUpperCase();

  if (command == "LIGHT ON" || command == "ALL ON") {
    manualOverride = true;
    manualLight = true;
    Serial.println("LIGHT ON");
  }
  else if (command == "LIGHT OFF" ||
           command == "ALL OFF") {
    manualOverride = true;
    manualLight = false;
    Serial.println("LIGHT OFF");
  }
  else if (command == "AUTO") {
    manualOverride = false;
    Serial.println("AUTO MODE");
  }
}

void readDHT22() {
  // DHT22 should not be read more frequently than
  // approximately once every 2 seconds.
  if (millis() - lastDHTRead < 2000) {
    return;
  }

  lastDHTRead = millis();

  float newTemperature = dht.readTemperature();
  float newHumidity = dht.readHumidity();

  if (!isnan(newTemperature) && !isnan(newHumidity)) {
    temperature = newTemperature;
    humidity = newHumidity;
  } else {
    Serial.println("DHT22 read error");
  }
}

void loop() {
  readCommands();

  int ldrValue = analogRead(LDR_PIN);
  int mq2Value = analogRead(MQ2_PIN);

  motionDetected = (digitalRead(PIR_PIN) == HIGH);

  int flameValue = digitalRead(FLAME_PIN);

  if (FLAME_ACTIVE_HIGH) {
    flameDetected = (flameValue == HIGH);
  } else {
    flameDetected = (flameValue == FLAME_ACTIVE_LEVEL);
  }

  // Basic analog threshold; calibrate for your module
  gasDetected = (mq2Value >= MQ2_THRESHOLD);

  bool dark = (ldrValue < LDR_DARK_THRESHOLD);

  // Manual commands override automatic lighting.
  // AUTO mode turns the light on in darkness or on motion.
  if (manualOverride) {
    lightOn = manualLight;
  } else {
    lightOn = dark || motionDetected;
  }

  digitalWrite(LED_PIN, lightOn ? HIGH : LOW);

  // Keep safety alarm active even when ALL OFF is commanded.
  if (gasDetected || flameDetected) {
    digitalWrite(BUZZER_PIN, HIGH);
  } else {
    digitalWrite(BUZZER_PIN, LOW);
  }

  readDHT22();

  // Print sensor status once per second
  if (millis() - lastReport >= 1000) {
    lastReport = millis();

    Serial.print("LDR=");
    Serial.print(ldrValue);

    Serial.print(" MQ2=");
    Serial.print(mq2Value);

    Serial.print(" PIR=");
    Serial.print(motionDetected ? "MOTION" : "CLEAR");

    Serial.print(" FLAME=");
    Serial.print(flameDetected ? "DETECTED" : "CLEAR");

    Serial.print(" GAS=");
    Serial.print(gasDetected ? "ALERT" : "NORMAL");

    Serial.print(" LIGHT=");
    Serial.print(lightOn ? "ON" : "OFF");

    Serial.print(" TEMP_C=");
    if (isnan(temperature)) {
      Serial.print("ERROR");
    } else {
      Serial.print(temperature, 1);
    }

    Serial.print(" HUMIDITY=");
    if (isnan(humidity)) {
      Serial.println("ERROR");
    } else {
      Serial.print(humidity, 1);
      Serial.println("%");
    }
  }
}
