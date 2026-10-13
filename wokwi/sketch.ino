/*
  WildGuard AI - virtual field sensor node (ESP32 on Wokwi)
  PIR (GPIO27)        -> human/animal motion
  Pot 1 (GPIO34)      -> microphone sound level (dB)
  Pot 2 (GPIO35)      -> tree vibration sensor (0..1)
  LED  (GPIO2)        -> lights when an alert is returned by the backend
*/
#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>

// Paste your ngrok HTTPS URL here (see README step 7)
const char* BACKEND_URL = "https://https://filling-prognosis-slurp.ngrok-free.dev/api/sensors/reading";

const char* NODE_ID = "wokwi-esp32-1";
const float NODE_LAT = 21.9800;
const float NODE_LON = 88.9200;

const int PIR_PIN = 27;
const int SOUND_PIN = 34;
const int VIB_PIN = 35;
const int LED_PIN = 2;

void setup() {
  Serial.begin(115200);
  pinMode(PIR_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  WiFi.begin("Wokwi-GUEST", "", 6);
  Serial.print("Connecting WiFi");
  while (WiFi.status() != WL_CONNECTED) { delay(250); Serial.print("."); }
  Serial.println(" connected");
}

void loop() {
  bool motion = digitalRead(PIR_PIN) == HIGH;
  float soundDb = 30.0 + (analogRead(SOUND_PIN) / 4095.0) * 80.0;   // 30..110 dB
  float vibration = analogRead(VIB_PIN) / 4095.0;                    // 0..1

  char body[256];
  snprintf(body, sizeof(body),
    "{\"node_id\":\"%s\",\"lat\":%.5f,\"lon\":%.5f,\"motion\":%s,"
    "\"sound_db\":%.1f,\"vibration\":%.2f,\"battery\":95}",
    NODE_ID, NODE_LAT, NODE_LON, motion ? "true" : "false", soundDb, vibration);

  WiFiClientSecure client;
  client.setInsecure();
  HTTPClient http;
  http.begin(client, BACKEND_URL);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("ngrok-skip-browser-warning", "1");
  int code = http.POST(body);
  String resp = http.getString();
  http.end();

  bool alert = resp.indexOf("category") > 0;
  digitalWrite(LED_PIN, alert ? HIGH : LOW);
  Serial.printf("sent %s -> HTTP %d %s\n", body, code, alert ? "ALERT" : "ok");
  delay(3000);
}
