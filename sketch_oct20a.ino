
const int PIR_PIN = 2;
const int LIGHT_PIN = 8;

void setup() {
  pinMode(PIR_PIN, INPUT);
  pinMode(LIGHT_PIN, OUTPUT);

  digitalWrite(LIGHT_PIN, LOW);

  Serial.begin(9600);
  Serial.println("PIR Motion Detection Started");
  Serial.println("Allow sensor to stabilize...");
}

void loop() {
  int motion = digitalRead(PIR_PIN);

  if (motion == HIGH) {
    digitalWrite(LIGHT_PIN, HIGH);
    Serial.println("Motion detected - LIGHT ON");
  }
  else {
    digitalWrite(LIGHT_PIN, LOW);
    Serial.println("No motion - LIGHT OFF");
  }

  delay(500);
}
