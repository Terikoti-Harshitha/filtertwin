/*
 * ==============================================================================
 * FILTERTWIN - ESP32 VIRTUAL PURIFIER TELEMETRY NODE
 * Team: CoreCraft - Lendi Institute of Engineering & Technology
 * ==============================================================================
 * 
 * REQUIRED WOKWI LIBRARIES (To fix "Adafruit_GFX.h: No such file or directory"):
 * In Wokwi (wokwi.com/projects/new/esp32):
 * 1. Click the down arrow (v) next to the "sketch.ino" tab at the top.
 * 2. Click "New File" and name it "libraries.txt".
 * 3. Add these exact 3 lines inside libraries.txt:
 *      Adafruit SSD1306
 *      Adafruit GFX Library
 *      ArduinoJson
 * (Alternatively: open the "Library Manager" icon in the left sidebar and search them).
 * 
 * Pin Connections:
 * - OLED SDA -> GPIO 21
 * - OLED SCL -> GPIO 22
 * - Potentiometer 1 (Inlet TDS Probe)  -> GPIO 34 (ADC1_CH6)
 * - Potentiometer 2 (Outlet TDS Probe) -> GPIO 35 (ADC1_CH7)
 * - Potentiometer 3 (Flow Turbine)    -> GPIO 32 (ADC1_CH4)
 * - Fault Injection Pushbutton        -> GPIO 4 (Pullup)
 * - Normal Status LED (Green)         -> GPIO 18
 * - Wear Warning LED (Yellow)         -> GPIO 19
 * - Anomaly Alert LED (Red)           -> GPIO 23
 * ==============================================================================
 */

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <ArduinoJson.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// Pin Definitions
const int PIN_INLET_TDS = 34;
const int PIN_OUTLET_TDS = 35;
const int PIN_FLOW = 32;
const int PIN_FAULT_BTN = 4;
const int PIN_LED_NORMAL = 18;
const int PIN_LED_WEAR = 19;
const int PIN_LED_ALERT = 23;

// Network Config (Wokwi default open guest network)
const char* ssid = "Wokwi-GUEST";
const char* password = "";

// FilterTwin Ingestion Endpoint
// Set this to your deployed Render backend URL: https://<your-render-app>.onrender.com/api/v1/telemetry/ingest
// Or for local testing via ngrok: https://<your-ngrok-id>.ngrok-free.app/api/v1/telemetry/ingest
const char* backendUrl = "https://filtertwin-backend.onrender.com/api/v1/telemetry/ingest";

// Cumulative tracking
float cumulativeVolumeL = 450.0;
unsigned long lastTelemetryMillis = 0;
const unsigned long telemetryInterval = 3000; // 3 seconds

void setup() {
  Serial.begin(115200);
  Serial.println("\n[FilterTwin] Starting Virtual ESP32 Node...");

  // Initialize GPIOs
  pinMode(PIN_FAULT_BTN, INPUT_PULLUP);
  pinMode(PIN_LED_NORMAL, OUTPUT);
  pinMode(PIN_LED_WEAR, OUTPUT);
  pinMode(PIN_LED_ALERT, OUTPUT);

  // Initialize OLED Display
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println(F("[Error] SSD1306 allocation failed"));
  } else {
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);
    display.setTextSize(1);
    display.setCursor(10, 20);
    display.println("FilterTwin IoT");
    display.setCursor(10, 35);
    display.println("Connecting WiFi...");
    display.display();
  }

  // Connect to WiFi (Channel 6 skips scanning in Wokwi and connects in 1-2 seconds)
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password, 6);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 25) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WiFi] Connected successfully!");
    Serial.print("[WiFi] IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n[WiFi] Handshake taking time, continuing in background...");
  }
}

void loop() {
  // 1. Read virtual sensor probes
  int rawInlet = analogRead(PIN_INLET_TDS);
  int rawOutlet = analogRead(PIN_OUTLET_TDS);
  int rawFlow = analogRead(PIN_FLOW);
  bool faultBtnPressed = (digitalRead(PIN_FAULT_BTN) == LOW);

  // Convert ADC values (12-bit: 0 - 4095) to physical engineering units
  // If user hasn't turned dials yet (all at 0), provide nominal operating baseline
  float inletTds, outletTds, flowLpm;
  if (rawInlet == 0 && rawOutlet == 0 && rawFlow == 0) {
    inletTds = 550.0;
    outletTds = 38.0;
    flowLpm = 2.10;
  } else {
    inletTds = map(rawInlet, 0, 4095, 100, 1000);
    outletTds = map(rawOutlet, 0, 4095, 10, 450);
    flowLpm = (rawFlow / 4095.0) * 3.0; // 0.0 to 3.0 LPM
  }

  // If fault button pressed, simulate acute hydraulic clogging & TDS breakthrough
  if (faultBtnPressed) {
    flowLpm = flowLpm * 0.25;      // Sudden 75% drop
    outletTds = inletTds * 0.85;   // Membrane rupture
  }

  // Ensure physically plausible bounds
  if (outletTds > inletTds) outletTds = inletTds;
  float rejectionPct = ((inletTds - outletTds) / inletTds) * 100.0;
  if (rejectionPct < 0) rejectionPct = 0;

  // 2. Local State Classification & LED indicators
  String status = "normal";
  if (faultBtnPressed || flowLpm < 0.6 || rejectionPct < 65.0) {
    status = "abrupt_anomaly";
    digitalWrite(PIN_LED_NORMAL, LOW);
    digitalWrite(PIN_LED_WEAR, LOW);
    digitalWrite(PIN_LED_ALERT, HIGH);
  } else if (rejectionPct < 85.0 || flowLpm < 1.4) {
    status = "gradual_wear";
    digitalWrite(PIN_LED_NORMAL, LOW);
    digitalWrite(PIN_LED_WEAR, HIGH);
    digitalWrite(PIN_LED_ALERT, LOW);
  } else {
    status = "normal";
    digitalWrite(PIN_LED_NORMAL, HIGH);
    digitalWrite(PIN_LED_WEAR, LOW);
    digitalWrite(PIN_LED_ALERT, LOW);
  }

  // 3. Update OLED Screen
  updateOled(inletTds, outletTds, flowLpm, rejectionPct, status);

  // 4. Send Periodic Telemetry JSON via HTTP
  if (millis() - lastTelemetryMillis >= telemetryInterval) {
    lastTelemetryMillis = millis();
    cumulativeVolumeL += (flowLpm * (telemetryInterval / 60000.0));
    sendTelemetryHttp(inletTds, outletTds, flowLpm, rejectionPct, status);
  }

  delay(200);
}

void updateOled(float inlet, float outlet, float flow, float rej, String status) {
  display.clearDisplay();
  
  // Header
  display.setTextSize(1);
  display.setCursor(0, 0);
  display.print("FILTERTWIN ESP32");
  display.setCursor(100, 0);
  display.print(status == "normal" ? "[OK]" : "[!]");

  // Metrics Display
  display.setCursor(0, 16);
  display.print("Flow: ");
  display.print(flow, 2);
  display.print(" LPM");

  display.setCursor(0, 28);
  display.print("In TDS : ");
  display.print((int)inlet);
  display.print(" ppm");

  display.setCursor(0, 40);
  display.print("Out TDS: ");
  display.print((int)outlet);
  display.print(" ppm");

  display.setCursor(0, 52);
  display.print("Rejection: ");
  display.print(rej, 1);
  display.print("%");

  display.display();
}

void sendTelemetryHttp(float inlet, float outlet, float flow, float rej, String status) {
  // Construct JSON document
  StaticJsonDocument<256> doc;
  doc["device_id"] = "wokwi-esp32-01";
  doc["flow_rate_lpm"] = round(flow * 100) / 100.0;
  doc["inlet_tds_ppm"] = round(inlet * 10) / 10.0;
  doc["outlet_tds_ppm"] = round(outlet * 10) / 10.0;
  doc["rejection_percentage"] = round(rej * 10) / 10.0;
  doc["cumulative_volume_l"] = round(cumulativeVolumeL * 10) / 10.0;
  doc["sensor_status"] = status;

  String jsonPayload;
  serializeJson(doc, jsonPayload);

  Serial.print("[Telemetry Output] ");
  Serial.println(jsonPayload);

  // HTTP POST if connected
  if (WiFi.status() == WL_CONNECTED) {
    WiFiClientSecure client;
    client.setInsecure(); // Required for ESP32 HTTPS validation without root CA certificate
    HTTPClient http;
    http.begin(client, backendUrl);
    http.addHeader("Content-Type", "application/json");
    
    int httpResponseCode = http.POST(jsonPayload);
    if (httpResponseCode > 0) {
      Serial.printf("[HTTP] Ingestion response code: %d (Successfully ingested into FilterTwin!)\n", httpResponseCode);
    } else {
      Serial.printf("[HTTP] Error sending telemetry: %s\n", http.errorToString(httpResponseCode).c_str());
    }
    http.end();
  } else {
    Serial.println("[WiFi] Reconnecting to Wokwi-GUEST...");
    WiFi.begin(ssid, password, 6);
  }
}
