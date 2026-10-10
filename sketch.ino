// --- PIN DEFINITIONS ---
#define RELAY_PIN 5

// --- THERMAL THRESHOLDS (MS 1525 Comfort Bounds) ---
#define TEMP_UPPER_LIMIT 25.5  // Shed load (Turn OFF)
#define TEMP_LOWER_LIMIT 24.0  // Restore load (Turn ON)

// --- WATCHDOG & FAILSAFE VARIABLES ---
unsigned long lastPacketTime = 0;       
const unsigned long WATCHDOG_TIMEOUT = 3000; // 3 seconds timeout
bool failsafeActive = false;            

// --- MOCK SENSOR & STATE VARIABLES ---
// Starting at 25.0 so we can immediately see it cool down, then heat up
float mock_temp = 25.0; 
bool relay_state = true; // true = ON (Cooling), false = OFF (Shedding)

// --- TIMING VARIABLES ---
unsigned long lastLogicCheck = 0;
unsigned long lastMockSend = 0;
const long logic_interval = 1000;  // Check logic every 1 second
const long mock_interval = 1000;   // Simulate dashboard packet every 1 second

void setup() {
  Serial.begin(115200);
  pinMode(RELAY_PIN, OUTPUT);
  
  // Failsafe: Ensure relay is OFF on boot (Assuming Active HIGH relay logic for simulation)
  digitalWrite(RELAY_PIN, LOW); 
  
  lastPacketTime = millis(); // Initialize watchdog timer
  
  Serial.println("=========================================");
  Serial.println("[BOOT] EdgeGrid HIL Controller Initialized.");
  Serial.println("=========================================");
}

void loop() {
  unsigned long currentMillis = millis();

  // ==========================================
  // 1. WATCHDOG CHECK
  // ==========================================
  // If we haven't received a packet in 3 seconds, and we aren't already in failsafe mode:
  if (currentMillis - lastPacketTime >= WATCHDOG_TIMEOUT && !failsafeActive) {
    failsafeActive = true;
    digitalWrite(RELAY_PIN, HIGH); // Force Relay ON to guarantee comfort
    Serial.println("[WATCHDOG] CRITICAL: Comms Lost! Defaulting to SAFE STATE (Relay ON).");
  }

  // ==========================================
  // 2. MOCK DATA GENERATOR (Simulating Python Dashboard)
  // ==========================================
  // *** CHANGE THIS TO 'false' TO SIMULATE A CABLE UNPLUG / CRASH ***
  bool simulateConnection = false; 

  if (simulateConnection && currentMillis - lastMockSend >= mock_interval) {
    lastMockSend = currentMillis;
    lastPacketTime = currentMillis; // <--- RESETS THE WATCHDOG TIMER
    
    if (failsafeActive) {
      failsafeActive = false;
      Serial.println("[WATCHDOG] Comms Restored. Returning to Edge Control.");
    }
    
    Serial.println("[MOCK] Packet received from Dashboard. Watchdog reset.");
  }

  // ==========================================
  // 3 & 4. MOCK THERMAL SIMULATION & CONTROL LOGIC (FIXED TIMING)
  // ==========================================
  // We only want this to run ONCE every 1000ms (1 second)
  if (currentMillis - lastLogicCheck >= logic_interval) {
    lastLogicCheck = currentMillis;

    // --- THE FIX: Temperature only changes once per second now ---
    // If relay is ON (Cooling), temp drops. If OFF (Shedding), temp rises.
    if (relay_state) {
      mock_temp -= 0.3; // Cool down by 0.3 degrees per second
    } else {
      mock_temp += 0.2; // Heat up by 0.2 degrees per second
    }

    // Hysteresis Logic
    if (mock_temp >= TEMP_UPPER_LIMIT && relay_state == true) {
      relay_state = false; 
      Serial.printf("[ACTUATION] RELAY OFF - Shedding Load (Temp: %.1f)\n", mock_temp);
    } 
    else if (mock_temp <= TEMP_LOWER_LIMIT && relay_state == false) {
      relay_state = true; 
      Serial.printf("[ACTUATION] RELAY ON - Restoring Load (Temp: %.1f)\n", mock_temp);
    }

    // Apply state to hardware
    digitalWrite(RELAY_PIN, relay_state);
    
    // Debug print
    Serial.printf("[STATE] Temp: %.1f | Relay: %s | Failsafe: %s\n", 
                  mock_temp, 
                  relay_state ? "ON" : "OFF", 
                  failsafeActive ? "ACTIVE" : "OK");
  }
}