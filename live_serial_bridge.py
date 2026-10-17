import serial
import json
import csv
import time
from datetime import datetime
from pathlib import Path

PORT = '/dev/ttyACM0'
BAUD = 115200
CSV_FILE = Path(__file__).resolve().parent / "energy_results.csv"

def setup_csv():
    if not CSV_FILE.exists():
        with open(CSV_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Timestamp", "House ID", "Current Room Temperature (°C)", 
                "AC Action", "Relay State", "Thermal Slack (min)"
            ])

def main():
    setup_csv()
    print(f"[BRIDGE] Listening to {PORT}... Press Ctrl+C to stop.")
    
    try:
        s = serial.Serial(PORT, BAUD, timeout=1)
        time.sleep(2) # Wait for ESP32 reset
        
        with open(CSV_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            
            while True:
                if s.in_waiting:
                    line = s.readline().decode('utf-8', errors='replace').strip()
                    
                    if "[TX]" in line:
                        try:
                            json_str = line.split('[TX] ')[1]
                            data = json.loads(json_str)
                            
                            relay_on = data.get('relay_state', False)
                            ac_action = "COOLING" if relay_on else "DEFERRED/OFF"
                            energy_demand = 1.5 if relay_on else 0.0 
                            
                            row = [
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "House_1",
                                data.get('temp_target', 25.0),
                                ac_action,
                                "ON" if relay_on else "OFF",
                                data.get('slack', 0.0)
                            ]
                            writer.writerow(row)
                            f.flush()
                            print(f"[BRIDGE] Logged: {ac_action} | Slack: {row[5]}min")
                            
                        except json.JSONDecodeError:
                            pass
                            
                time.sleep(0.1)
                
    except serial.SerialException as e:
        print(f"[ERROR] Could not open port: {e}")
    except KeyboardInterrupt:
        print("\n[BRIDGE] Stopped.")

if __name__ == "__main__":
    main()
