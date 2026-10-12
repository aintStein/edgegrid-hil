#include <ArduinoJson.h>

// --- PIN DEFINITIONS ---
#define RELAY_PIN 5

// --- THERMAL THRESHOLDS (MS 1525 Comfort Bounds) ---
#define TEMP_MAX_COMFORT 26.0   // Absolute max before comfort is violated

// --- ME LEAD CONSTANTS (Real Physics) ---
// Heating rate when AC is OFF (°C per minute)
#define HEATING_RATE_PER_MIN 0.00822 
// Cooling rate when AC is ON (°C per minute)
#define COOLING_RATE_PER_MIN 0.05178 

// --- DEMO MODE (For Pitch Video) ---
// Set to true to multiply thermal rates by 60x for the 3-minute video
#define DEMO_MODE true 
const float TIME_LAPSE_MULTIPLIER = 60.0; 

// --- WATCHDOG & FAILSAFE VARIABLES ---
unsigned long lastPacketTime = 0;       
const unsigned long WATCHDOG_TIMEOUT = 3000; // 3 seconds
bool failsafeActive = false;            

// --- STATE VARIABLES ---
float current_temp = 24.5; // Starting room temp
bool relay_state = true;   // true = ON (Cooling), false = OFF (Shedding)
float thermal_slack = 0.0; // Minutes until room hits 26.0°C

// --- USER PREFERENCE LOGIC ---
int user_preference = 2; // 1: Max Savings, 2: Balanced, 3: Max Comfort
float min_safe_slack = 15.0; // Default for Balanced

// --- TIMING VARIABLES ---
unsigned long lastLogicCheck = 0;
unsigned long lastMockSend = 0;
const long logic_interval = 1000;  // 1 second
const long mock_interval = 2000;   // Simulate dashboard packet every 2 seconds

// --- MOCK JSON PAYLOADS (Simulating CS Lead's Streamlit App) ---
// Change "pref" to 1, 2, or 3 to test different user modes
const char* json_payload_balanced = "{\"s\": 0.2, \"ta\": 31.0, \"pref\": 2}\n";

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
  const char* incoming_data = json_payload_balanced; 

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
      
      // Update User Preference if present
      if (doc.containsKey("pref")) {
        user_preference = doc["pref"];
        if (user_preference == 1) min_safe_slack = 30.0;      // Max Savings
        else if (user_preference == 2) min_safe_slack = 15.0; // Balanced
        else if (user_preference == 3) min_safe_slack = 0.0;  // Max Comfort (Never shed)
      }
      
      Serial.printf("[RX] Solar=%.1fkW, Ambient=%.1fC, Pref=%d (Slack Threshold: %.1f)\n", 
                    solar_kw, ambient_temp, user_preference, min_safe_slack);
    }
  }

  // ==========================================
  // 3. THERMAL PHYSICS & EDGE DECISION
  // ==========================================
  if (currentMillis - lastLogicCheck >= logic_interval) {
    lastLogicCheck = currentMillis;

    // A. Apply physical rates (scaled by multiplier if in DEMO_MODE)
    float current_heating = HEATING_RATE_PER_MIN;
    float current_cooling = COOLING_RATE_PER_MIN;
    
    if (DEMO_MODE) {
      current_heating *= TIME_LAPSE_MULTIPLIER;
      current_cooling *= TIME_LAPSE_MULTIPLIER;
    }

    if (relay_state) {
      current_temp -= (current_cooling / 60.0); // Convert min rate to sec rate
    } else {
      current_temp += (current_heating / 60.0);
    }

    // B. Calculate Thermal Slack
    if (current_temp >= TEMP_MAX_COMFORT) {
      thermal_slack = 0.0;
    } else {
      // Use real heating rate for slack calculation (scaled for demo)
      thermal_slack = (TEMP_MAX_COMFORT - current_temp) / current_heating;
    }

    // C. EDGE DECISION MAKING
    if (thermal_slack > min_safe_slack && relay_state == true) {
      relay_state = false; // Safe to shed
      Serial.printf("[DECISION] Shedding Load. Slack: %.1f > Threshold: %.1f\n", thermal_slack, min_safe_slack);
    } 
    else if (thermal_slack <= min_safe_slack && relay_state == false) {
      relay_state = true; // Must restore comfort
      Serial.printf("[DECISION] Restoring Load. Slack: %.1f <= Threshold: %.1f\n", thermal_slack, min_safe_slack);
    }

    // D. Apply state and broadcast TX
    digitalWrite(RELAY_PIN, relay_state ? HIGH : LOW);
    
    Serial.printf("[TX] {\"r\": %d, \"t\": %.1f, \"sl\": %.1f}\n", 
                  relay_state ? 1 : 0, current_temp, thermal_slack);
  }
}