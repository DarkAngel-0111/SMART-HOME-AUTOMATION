/*
  IoT Device Control System - Arduino Uno Firmware
  Product Requirements Document (PRD) compliant.
  
  Receives serial commands over USB at 9600 baud:
    - "D2 ON"  / "D2 OFF"
    - "D3 ON"  / "D3 OFF"
    - "D4 ON"  / "D4 OFF"
    - "D5 ON"  / "D5 OFF"
    - "STATUS" -> replies with pin states
    - "PING"   -> replies "PONG"
    
  Responds with confirmations:
    - "OK D2 ON"
    - "OK D2 OFF"
    etc.
*/

// Set to 1 if using an Active-LOW relay module (relay turns on when pin is LOW).
// Set to 0 if using regular LEDs or Active-HIGH relay modules.
#define RELAY_ACTIVE_LOW 0

// Pin Definitions
const int PIN_DEV1 = 2; // Device 1 -> Pin D2
const int PIN_DEV2 = 3; // Device 2 -> Pin D3
const int PIN_DEV3 = 4; // Device 3 -> Pin D4
const int PIN_DEV4 = 5; // Device 4 -> Pin D5
const int PIN_STATUS_LED = 13; // Built-in LED for serial activity

// Current logical state (0 = OFF, 1 = ON)
int stateDev1 = 0;
int stateDev2 = 0;
int stateDev3 = 0;
int stateDev4 = 0;

// Serial reception buffer
const int BUFFER_SIZE = 64;
char serialBuffer[BUFFER_SIZE];
int bufferIndex = 0;

void applyPinState(int pin, int logicalState) {
  if (RELAY_ACTIVE_LOW) {
    digitalWrite(pin, (logicalState == 1) ? LOW : HIGH);
  } else {
    digitalWrite(pin, (logicalState == 1) ? HIGH : LOW);
  }
}

void processCommand(char* cmd) {
  // Trim leading/trailing whitespace
  char* p = cmd;
  while (*p == ' ' || *p == '\r' || *p == '\t') p++;
  
  int len = strlen(p);
  while (len > 0 && (p[len - 1] == ' ' || p[len - 1] == '\r' || p[len - 1] == '\n')) {
    p[--len] = '\0';
  }
  
  if (len == 0) return;

  // Flash LED on activity
  digitalWrite(PIN_STATUS_LED, HIGH);

  // Parse Commands
  if (strcasecmp(p, "D2 ON") == 0) {
    stateDev1 = 1;
    applyPinState(PIN_DEV1, stateDev1);
    Serial.println("OK D2 ON");
  } 
  else if (strcasecmp(p, "D2 OFF") == 0) {
    stateDev1 = 0;
    applyPinState(PIN_DEV1, stateDev1);
    Serial.println("OK D2 OFF");
  }
  else if (strcasecmp(p, "D3 ON") == 0) {
    stateDev2 = 1;
    applyPinState(PIN_DEV2, stateDev2);
    Serial.println("OK D3 ON");
  } 
  else if (strcasecmp(p, "D3 OFF") == 0) {
    stateDev2 = 0;
    applyPinState(PIN_DEV2, stateDev2);
    Serial.println("OK D3 OFF");
  }
  else if (strcasecmp(p, "D4 ON") == 0) {
    stateDev3 = 1;
    applyPinState(PIN_DEV3, stateDev3);
    Serial.println("OK D4 ON");
  } 
  else if (strcasecmp(p, "D4 OFF") == 0) {
    stateDev3 = 0;
    applyPinState(PIN_DEV3, stateDev3);
    Serial.println("OK D4 OFF");
  }
  else if (strcasecmp(p, "D5 ON") == 0) {
    stateDev4 = 1;
    applyPinState(PIN_DEV4, stateDev4);
    Serial.println("OK D5 ON");
  } 
  else if (strcasecmp(p, "D5 OFF") == 0) {
    stateDev4 = 0;
    applyPinState(PIN_DEV4, stateDev4);
    Serial.println("OK D5 OFF");
  }
  else if (strcasecmp(p, "STATUS") == 0) {
    Serial.print("STATUS D2:");
    Serial.print(stateDev1);
    Serial.print(" D3:");
    Serial.print(stateDev2);
    Serial.print(" D4:");
    Serial.print(stateDev3);
    Serial.print(" D5:");
    Serial.println(stateDev4);
  }
  else if (strcasecmp(p, "PING") == 0) {
    Serial.println("PONG");
  }
  else {
    Serial.print("ERR UNKNOWN COMMAND: ");
    Serial.println(p);
  }

  digitalWrite(PIN_STATUS_LED, LOW);
}

void setup() {
  // Initialize Serial at 9600 baud
  Serial.begin(9600);
  
  // Configure pins as OUTPUT
  pinMode(PIN_DEV1, OUTPUT);
  pinMode(PIN_DEV2, OUTPUT);
  pinMode(PIN_DEV3, OUTPUT);
  pinMode(PIN_DEV4, OUTPUT);
  pinMode(PIN_STATUS_LED, OUTPUT);
  
  // Initialize all devices to OFF
  applyPinState(PIN_DEV1, stateDev1);
  applyPinState(PIN_DEV2, stateDev2);
  applyPinState(PIN_DEV3, stateDev3);
  applyPinState(PIN_DEV4, stateDev4);
  digitalWrite(PIN_STATUS_LED, LOW);
  
  // Announce ready
  Serial.println("ARDUINO_READY");
}

void loop() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    
    if (c == '\n') {
      serialBuffer[bufferIndex] = '\0';
      processCommand(serialBuffer);
      bufferIndex = 0;
    } else if (c != '\r') {
      if (bufferIndex < BUFFER_SIZE - 1) {
        serialBuffer[bufferIndex++] = c;
      } else {
        // Overflow protection
        bufferIndex = 0;
      }
    }
  }
}
