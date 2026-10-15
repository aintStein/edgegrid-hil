#define ARDUINO_USB_CDC_ON_BOOT 1
#define ARDUINO_USB_MODE 1

#include <ArduinoJson.h>
#include <DHT.h>
#include <esp_heap_caps.h> // For heap monitoring

#define DHTPIN 10
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

// --- PIN DEFINITIONS ---
#define RELAY_PIN 4

// --- THERMAL MODEL CONSTANTS (ME Verified) ---
const float COOLING_RATE = 0.05178;
const float HEATING_RATE = 0.00822;
const float TEMP_UPPER_LIMIT = 26.0;
const float TEMP_LOWER_LIMIT = 23.0;

// --- CALIBRATION ---
const float TEMP_CALIBRATION_OFFSET = 2.8; 

// --- WATCHDOG & FAILSAFE ---
unsigned long lastPacketTime = 0;
const unsigned long WATCHDOG_TIMEOUT = 1500; 
bool failsafeActive = false;

// --- STATE VARIABLES ---
float roomTemp = 25.0;
bool relayState = true; 
int userPreference = 1; 
float minSafeSlack = 15.0; 
bool useExternalTemp = false;

// --- TIMING ---
unsigned long lastLogicCheck = 0;
unsigned long lastHeapCheck = 0; // For periodic heap stats
const unsigned long LOGIC_INTERVAL = 1000; 
const unsigned long HEAP_CHECK_INTERVAL = 10000; // Print heap every 10s

// --- SERIAL BUFFER ---
String serialBuffer = "";
const int MAX_BUFFER_SIZE = 1024; // Safety limit to prevent memory bloat

void setup() {
  while (!Serial && millis() < 5000);
  delay(500);
  Serial.begin(115200);
  
  if(psramInit()) {
    Serial.println("[PSRAM] 8MB Octal PSRAM initialized");
  } else {
    Serial.println("[PSRAM] WARNING: PSRAM init failed");
  }
  
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, HIGH); 
  lastPacketTime = millis(); 
  
  dht.begin(); 
  
  Serial.println("=========================================");
  Serial.println("[BOOT] EdgeGrid HIL Controller Initialized.");
  Serial.println("=========================================");
}

void loop() {
  unsigned long currentMillis = millis();

  // 1. NON-BLOCKING SERIAL PARSING
  while (Serial.available()) {
    char c = Serial.read();
    if (c == 0) continue; 

    if (c == '\n') {
      if (serialBuffer.length() > 0) { 
        StaticJsonDocument<512> doc;
        DeserializationError error = deserializeJson(doc, serialBuffer);
        
        if (!error) {
          lastPacketTime = currentMillis; 
          
          if (failsafeActive) {
            failsafeActive = false;
            Serial.println("[WATCHDOG] Comms Restored. Returning to Edge Control.");
          }
          
          // ROBUST EDGE CASE HANDLING FOR 'ta'
          if (doc.containsKey("ta")) {
            if (!doc["ta"].isNull() && doc["ta"].is<float>()) {
              float ta = doc["ta"].as<float>();
              if (ta > -40.0 && ta < 85.0) {
                roomTemp = ta;
                useExternalTemp = true;
              }
            }
          }

          // ROBUST EDGE CASE HANDLING FOR 'pref'
          if (doc.containsKey("pref")) {
             if (!doc["pref"].isNull() && doc["pref"].is<int>()) {
              int pref = doc["pref"].as<int>();
              if (pref >= 0 && pref <= 2) {
                userPreference = pref;
                switch(pref) {
                  case 0: minSafeSlack = 30.0; break;
                  case 1: minSafeSlack = 15.0; break;
                  case 2: minSafeSlack = 0.0; break;
                }
              }
            }
          }
          Serial.printf("[RX] Ta=%.1fC, Pref=%d (Slack Threshold: %.1f)\n", 
                        roomTemp, userPreference, minSafeSlack);
        } else {
          // Silently ignore parse errors to keep logs clean during spam tests
          // Serial.printf("[PARSE ERROR] %s\n", error.c_str());
        }
      }
      serialBuffer = ""; 
    } else {
      // Buffer safety: only append if we haven't hit the limit
      if (serialBuffer.length() < MAX_BUFFER_SIZE) {
        serialBuffer += c;
      } else {
        // If buffer is full, discard the rest of this "line" until newline
        continue; 
      }
    }
  }

  // 2. WATCHDOG CHECK
  if (currentMillis - lastPacketTime >= WATCHDOG_TIMEOUT && !failsafeActive) {
    failsafeActive = true;
    relayState = true;
    digitalWrite(RELAY_PIN, HIGH);
    Serial.println("[WATCHDOG] CRITICAL: Comms Lost! Defaulting to SAFE STATE (Relay ON).");
  }

  // 3. THERMAL LOGIC (1Hz)
  if (currentMillis - lastLogicCheck >= LOGIC_INTERVAL) {
    lastLogicCheck = currentMillis;
    
    if (!useExternalTemp) {
        float raw_temp = dht.readTemperature();
        if (!isnan(raw_temp)) {
            roomTemp = raw_temp + TEMP_CALIBRATION_OFFSET;
        } else {
            // Serial.println("[DEBUG] Failed to read from DHT sensor!");
        }
    }
    useExternalTemp = false; 
    
    // --- SLACK CALCULATION ---
    float thermalSlack = 0.0;
    if (roomTemp < TEMP_UPPER_LIMIT) {
      thermalSlack = (TEMP_UPPER_LIMIT - roomTemp) / HEATING_RATE;
    } else {
      thermalSlack = 0.0; 
    }
    
    bool shouldShed = (thermalSlack > minSafeSlack) && (userPreference != 2);
    
    if (shouldShed && relayState) {
      relayState = false;
      // Serial.printf("[ACTUATION] RELAY OFF - Shedding Load (Slack: %.1fmin > %.1fmin)\n", thermalSlack, minSafeSlack);
    } 
    else if (!shouldShed && !relayState) {
      relayState = true;
      // Serial.printf("[ACTUATION] RELAY ON - Restoring Load (Slack: %.1fmin <= %.1fmin)\n", thermalSlack, minSafeSlack);
    }
    
    digitalWrite(RELAY_PIN, relayState);

    // --- API CONTRACT V1.0 TX PAYLOAD ---
    String statusStr = "IDLE";
    if (failsafeActive) statusStr = "FAULT";
    else if (relayState) statusStr = "COOLING";
    else statusStr = "HEATING";

    float target = (userPreference == 2) ? TEMP_LOWER_LIMIT : TEMP_UPPER_LIMIT;

    Serial.printf("[TX] {\"status\":\"%s\",\"relay_state\":%s,\"temp_target\":%.1f,\"slack\":%.1f,\"uptime_ms\":%lu}\n", 
                  statusStr.c_str(), 
                  relayState ? "true" : "false", 
                  target, 
                  thermalSlack, 
                  currentMillis);
    
    delay(5); 
  }
  
  // 4. PERIODIC HEAP MONITORING (Every 10 seconds)
  if (currentMillis - lastHeapCheck >= HEAP_CHECK_INTERVAL) {
    lastHeapCheck = currentMillis;
    Serial.printf("[HEAP] Free: %u | MinFree: %u\n", 
                  esp_get_free_heap_size(), 
                  esp_get_minimum_free_heap_size());
  }

  delay(1); 
}