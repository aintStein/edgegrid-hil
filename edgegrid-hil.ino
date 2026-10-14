#define ARDUINO_USB_CDC_ON_BOOT 1
#define ARDUINO_USB_MODE 1

#include <ArduinoJson.h>
#include <DHT.h> // Ensure you have the DHT library installed via arduino-cli lib install DHT sensor library

#define DHTPIN 10
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

// --- PIN DEFINITIONS ---
#define RELAY_PIN 4  // N16R8 safe pin with 10k pulldown to GND

// --- THERMAL MODEL CONSTANTS (ME Verified) ---
const float COOLING_RATE = 0.05178;   // °C/min when AC ON
const float HEATING_RATE = 0.00822;   // °C/min when AC OFF
const float TEMP_UPPER_LIMIT = 26.0;  // MS 1525 upper bound
const float TEMP_LOWER_LIMIT = 23.0;  // MS 1525 lower bound

// --- CALIBRATION ---
// Calculate: Offset = Reference_Temp - Raw_ESP32_Temp
const float TEMP_CALIBRATION_OFFSET = 2.8; // REPLACE WITH YOUR CALCULATED VALUE

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
const unsigned long LOGIC_INTERVAL = 1000; 

// --- SERIAL BUFFER ---
String serialBuffer = "";

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
  digitalWrite(RELAY_PIN, HIGH); // Safe boot state
  lastPacketTime = millis(); 
  
  dht.begin(); // Initialize DHT sensor
  
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
          
          if (doc.containsKey("ta")) {
            float ta = doc["ta"].as<float>();
            if (ta > -40.0 && ta < 85.0) {
              roomTemp = ta;
              useExternalTemp = true;
            }
          }
          if (doc.containsKey("pref")) {
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
          Serial.printf("[RX] Ta=%.1fC, Pref=%d (Slack Threshold: %.1f)\n", 
                        roomTemp, userPreference, minSafeSlack);
        } else {
          Serial.printf("[PARSE ERROR] %s\n", error.c_str());
        }
      }
      serialBuffer = ""; 
    } else {
      serialBuffer += c;
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
    
    // Read from DHT22 if no external temp provided recently
    if (!useExternalTemp) {
        float raw_temp = dht.readTemperature();
        if (!isnan(raw_temp)) {
            roomTemp = raw_temp + TEMP_CALIBRATION_OFFSET;
            // Debug print for calibration evidence
            Serial.printf("[DEBUG] Raw Temp: %.1f | Calibrated: %.1f\n", raw_temp, roomTemp);
        } else {
            Serial.println("[DEBUG] Failed to read from DHT sensor!");
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
      Serial.printf("[ACTUATION] RELAY OFF - Shedding Load (Slack: %.1fmin > %.1fmin)\n", 
                    thermalSlack, minSafeSlack);
    } 
    else if (!shouldShed && !relayState) {
      relayState = true;
      Serial.printf("[ACTUATION] RELAY ON - Restoring Load (Slack: %.1fmin <= %.1fmin)\n", 
                    thermalSlack, minSafeSlack);
    }
    
    digitalWrite(RELAY_PIN, relayState);

    // --- API CONTRACT V1.0 TX PAYLOAD ---
    String statusStr = "IDLE";
    if (failsafeActive) statusStr = "FAULT";
    else if (relayState) statusStr = "COOLING";
    else statusStr = "HEATING";

    float target = (userPreference == 2) ? TEMP_LOWER_LIMIT : TEMP_UPPER_LIMIT;

    // 1. Send ONLY the JSON on this line for easy parsing
    Serial.printf("[TX] {\"status\":\"%s\",\"relay_state\":%s,\"temp_target\":%.1f,\"slack\":%.1f,\"uptime_ms\":%lu}\n", 
                  statusStr.c_str(), 
                  relayState ? "true" : "false", 
                  target, 
                  thermalSlack, 
                  currentMillis);
    
    delay(5); // Yield to USB stack

    // 2. Send debug info on a SEPARATE line
    Serial.printf("[DEBUG] TimeDelta: %lu ms | Failsafe: %s\n", 
                  currentMillis - lastPacketTime, failsafeActive ? "ACTIVE" : "OK");
  }
  
  delay(1); // Yield to USB stack
}