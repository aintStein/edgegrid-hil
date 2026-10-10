#include <ArduinoJson.h>

// --- PIN DEFINITIONS ---
#define RELAY_PIN 5

// --- THERMAL THRESHOLDS (MS 1525 Comfort Bounds) ---
#define TEMP_MAX_COMFORT 26.0   // Absolute max before comfort is violated
#define TEMP_MIN_COMFORT 24.0   // Target to cool back down to

// --- WATCHDOG & FAILSAFE VARIABLES ---
unsigned long lastPacketTime = 0;       
const unsigned long WATCHDOG_TIMEOUT = 3000; // 3 seconds
bool failsafeActive = false;            

// --- STATE VARIABLES ---
// CHANGED TO 18.0 TO DEMONSTRATE HIGH THERMAL SLACK
float current_temp = 18.0; 
bool relay_state = true;   // true = ON (Cooling), false = OFF (Shedding)
float thermal_slack = 0.0; // Minutes until room hits 26.0°C

// --- TIMING VARIABLES ---
unsigned long lastLogicCheck = 0;
unsigned long lastMockSend = 0;
const long logic_interval = 1000;  // 1 second
const long mock_interval = 2000;   // Simulate dashboard packet every 2 seconds

// --- MOCK JSON PAYLOADS (Simulating CS Lead's Python Script) ---
// Scenario A: Plenty of solar, room is cool
const char* json_payload_good = "{\"s\": 2.5, \"ta\": 31.0}\n";
// Scenario B: Solar drops, but room has high thermal slack (safe to shed)
const char* json_payload_shed = "{\"s\": 0.2, \"ta\": 31.0}\n";

void setup() {
  Serial.begin(115200);
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, HIGH); // Default to ON (Comfort) on boot
  
  lastPacketTime = millis(); 
  
  Serial.println("=========================================");
  Serial.println("[BOOT] EdgeGrid HIL Controller Initialized.");
  Serial.println("=========================================");
}

void loop() {
  unsigned long currentMillis = millis();

  // ==========================================
  // 1. WATCHDOG CHECK
  // ==========================================
  if (currentMillis - lastPacketTime >= WATCHDOG_TIMEOUT && !failsafeActive) {
    failsafeActive = true;
    relay_state = true; // Force Relay ON
    digitalWrite(RELAY_PIN, HIGH);
    Serial.println("[WATCHDOG] CRITICAL: Comms Lost! Defaulting to SAFE STATE (Relay ON).");
  }

  // ==========================================
  // 2. SIMULATE INCOMING JSON FROM DASHBOARD
  // ==========================================
  // CHANGE THIS VARIABLE TO TEST DIFFERENT SCENARIOS:
  // Use `json_payload_good` or `json_payload_shed` or set to NULL to test watchdog
  const char* incoming_data = json_payload_shed; 

  if (incoming_data != NULL && currentMillis - lastMockSend >= mock_interval) {
    lastMockSend = currentMillis;
    lastPacketTime = currentMillis; // Reset watchdog
    
    if (failsafeActive) {
      failsafeActive = false;
      Serial.println("[WATCHDOG] Comms Restored. Returning to Edge Control.");
    }

    // --- JSON PARSING LOGIC ---
    StaticJsonDocument<256> doc;
    DeserializationError error = deserializeJson(doc, incoming_data);

    if (error) {
      Serial.print("[JSON ERROR] Failed to parse: ");
      Serial.println(error.c_str());
    } else {
      float solar_kw = doc["s"];
      float ambient_temp = doc["ta"];
      
      // In a real system, ambient_temp would influence the thermal decay model.
      // For now, we log it to prove parsing works.
      Serial.printf("[RX] Parsed: Solar=%.1fkW, Ambient=%.1fC\n", solar_kw, ambient_temp);
    }
  }

  // ==========================================
  // 3. THERMAL SLACK CALCULATION & CONTROL LOGIC
  // ==========================================
  if (currentMillis - lastLogicCheck >= logic_interval) {
    lastLogicCheck = currentMillis;

    // A. Simulate physical temperature change
    if (relay_state) {
      current_temp -= 0.005; // Cool down slowly (0.3 deg per 60 secs)
    } else {
      current_temp += 0.008; // Heat up slowly (0.5 deg per 60 secs)
    }

    // B. Calculate Thermal Slack (Minutes until hitting 26.0°C)
    // If temp is already >= 26.0, slack is 0.
    if (current_temp >= TEMP_MAX_COMFORT) {
      thermal_slack = 0.0;
    } else {
      // Heating rate is approx 0.5 deg per min (defined by ME lead)
      float heating_rate_per_min = 0.5; 
      thermal_slack = (TEMP_MAX_COMFORT - current_temp) / heating_rate_per_min;
    }

    // C. EDGE DECISION MAKING
    // Rule: Only shed load if we have MORE than 15 minutes of thermal slack
    const float MIN_SAFE_SLACK = 15.0; 

    if (thermal_slack > MIN_SAFE_SLACK && relay_state == true) {
      relay_state = false; // Safe to shed
      Serial.printf("[DECISION] Shedding Load. Thermal Slack: %.1f mins (Safe)\n", thermal_slack);
    } 
    else if (thermal_slack <= MIN_SAFE_SLACK && relay_state == false) {
      relay_state = true; // Must restore comfort
      Serial.printf("[DECISION] Restoring Load. Thermal Slack: %.1f mins (Critical)\n", thermal_slack);
    }

    // D. Apply state and report back (TX)
    digitalWrite(RELAY_PIN, relay_state ? HIGH : LOW);
    
    // Simulate the TX payload back to the dashboard
    Serial.printf("[TX] {\"r\": %d, \"t\": %.1f, \"sl\": %.1f}\n", 
                  relay_state ? 1 : 0, current_temp, thermal_slack);
  }
}