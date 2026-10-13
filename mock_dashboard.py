import serial, time, csv, json
from datetime import datetime

PORT = '/dev/ttyACM0'
BAUD = 115200
LOG_FILE = 'evidence/integration_tests/mock_dashboard_log.csv'

def main():
    s = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2) # Wait for CDC init
    
    print(f"[DASHBOARD] Connected to {PORT}. Logging to {LOG_FILE}")
    
    with open(LOG_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        # Updated headers for API v1.0
        writer.writerow(['Timestamp', 'TX_Ta', 'TX_Pref', 'RX_Status', 'RX_Relay', 'RX_Target', 'RX_Slack', 'RX_Uptime'])
        
        base_temp = 25.0
        for i in range(60): # Run for 60 seconds
            # Simulate rising ambient temp
            current_ta = base_temp + (i * 0.1)
            
            # Send Command (API v1.0 RX)
            cmd = {"grid_mode": "DEFICIT", "ta": round(current_ta, 1), "pref": 1}
            s.write((json.dumps(cmd) + '\n').encode())
            s.flush()
            
            # Read Response (API v1.0 TX)
            if s.in_waiting:
                line = s.readline().decode(errors='replace').strip()
                if "[TX]" in line:
                    try:
                        # Extract JSON from [TX] {...}
                        json_str = line.split('[TX] ')[1]
                        data = json.loads(json_str)
                        
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
            
            time.sleep(1)
            
    s.close()
    print("[DASHBOARD] Test complete. Check CSV for evidence.")

if __name__ == "__main__":
    main()
