import serial
import time
import csv
import json
from datetime import datetime

# --- CONFIGURATION ---
PORT = '/dev/ttyACM0'  # Change to COM3/COM4 if on Windows later
BAUD = 115200
LOG_FILE = 'evidence/integration_tests/mock_dashboard_log.csv'

def main():
    try:
        s = serial.Serial(PORT, BAUD, timeout=1)
        time.sleep(2)  # Wait for ESP32-S3 CDC initialization
    except serial.SerialException as e:
        print(f"[ERROR] Could not open port {PORT}: {e}")
        return
    
    print(f"[DASHBOARD v1.0] Connected to {PORT}. Logging to {LOG_FILE}")
    
    # Ensure directory exists (optional but good practice)
    import os
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    with open(LOG_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        # Headers matching the v1.0 TX Payload fields
        writer.writerow(['Timestamp', 'TX_Ta', 'TX_Pref', 'RX_Status', 'RX_Relay', 'RX_Target', 'RX_Slack', 'RX_Uptime'])
        
        base_temp = 25.0
        
        print("[DASHBOARD] Starting 60-second integration simulation...")
        
        for i in range(60): 
            # 1. Simulate rising ambient temp (Day 7 Calibration Context)
            current_ta = base_temp + (i * 0.1)
            
            # 2. Send Command (API v1.0 RX)
            cmd = {"grid_mode": "DEFICIT", "ta": round(current_ta, 1), "pref": 1}
            command_str = json.dumps(cmd) + '\n'
            s.write(command_str.encode('utf-8'))
            s.flush()
            
            # 3. Read Response (API v1.0 TX)
            # We read a line and look for the [TX] marker
            if s.in_waiting:
                line = s.readline().decode('utf-8', errors='replace').strip()
                
                if "[TX]" in line:
                    try:
                        # Extract JSON from the format: [TX] {"key":"value"}
                        json_str = line.split('[TX] ')[1]
                        data = json.loads(json_str)
                        
                        # Map v1.0 keys to CSV columns
                        row = [
                            datetime.now().strftime("%H:%M:%S"),
                            cmd['ta'],
                            cmd['pref'],
                            data.get('status', 'N/A'),
                            data.get('relay_state', 'N/A'),
                            data.get('temp_target', 'N/A'),
                            data.get('slack', 'N/A'),
                            data.get('uptime_ms', 'N/A')
                        ]
                        writer.writerow(row)
                        print(f"[LOG] Ta={cmd['ta']}C | Status={data.get('status')} | Slack={data.get('slack')}min")
                    
                    except Exception as e:
                        print(f"[PARSE FAIL] {e}: {line}")
                elif "[DEBUG]" in line:
                    pass # Ignore debug lines for CSV cleanliness
                else:
                    print(f"[UNKNOWN] {line}")
            
            time.sleep(1)
            
    s.close()
    print("[DASHBOARD] Test complete. Check CSV for evidence.")

if __name__ == "__main__":
    main()
