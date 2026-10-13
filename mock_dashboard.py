import serial
import json
import time
import csv
import os
from datetime import datetime

# --- CONFIGURATION ---
PORT = '/dev/ttyACM0'
BAUD = 115200
LOG_DIR = 'evidence/integration_tests'
CSV_FILE = os.path.join(LOG_DIR, f'day6_mock_dashboard_{datetime.now().strftime("%H%M%S")}.csv')

def setup_serial():
    s = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2) # Wait for ESP32 boot
    return s

def send_command(ser, ta, pref):
    """Send a JSON command to the MCU"""
    payload = json.dumps({"ta": ta, "pref": pref}) + "\n"
    ser.write(payload.encode())

def log_to_csv(timestamp, tx_data, rx_data):
    """Append telemetry to CSV"""
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, mode='a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp", "TX_Ta", "TX_Pref", "RX_Status", "RX_Relay", "RX_Target", "RX_Slack", "RX_Uptime"])
        writer.writerow([
            timestamp, 
            tx_data.get('ta'), 
            tx_data.get('pref'), 
            rx_data.get('status'), 
            rx_data.get('relay_state'), 
            rx_data.get('temp_target'), 
            rx_data.get('slack'), 
            rx_data.get('uptime_ms')
        ])

def main():
    print(f"[DASHBOARD] Starting Mock Dashboard. Logging to {CSV_FILE}")
    os.makedirs(LOG_DIR, exist_ok=True)
    
    ser = setup_serial()
    
    # Simulation parameters
    current_temp = 25.0
    preference = 1 # Balanced
    
    try:
        while True:
            # 1. Simulate Environmental Changes
            # Slowly increase temp to test slack logic
            current_temp += 0.1 
            
            # 2. Send Data to MCU (TX)
            tx_payload = {"ta": round(current_temp, 1), "pref": preference}
            send_command(ser, tx_payload['ta'], tx_payload['pref'])
            
            # 3. Read Response from MCU (RX)
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            
            if "[TX]" in line:
                # Extract JSON part from the debug string
                json_str = line.split("[TX] ")[-1]
                try:
                    rx_data = json.loads(json_str)
                    print(f"[LOG] Ta={tx_payload['ta']}C | Status={rx_data.get('status')} | Slack={rx_data.get('slack')}min")
                    
                    # 4. Log to CSV
                    log_to_csv(datetime.now().isoformat(), tx_payload, rx_data)
                    
                except json.JSONDecodeError:
                    print(f"[ERROR] Failed to parse JSON: {json_str}")
            
            time.sleep(1) # 1Hz update rate
            
    except KeyboardInterrupt:
        print("\n[DASHBOARD] Stopping simulation.")
        ser.close()

if __name__ == "__main__":
    main()
