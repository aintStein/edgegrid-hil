import serial
import time
import random
import string

PORT = '/dev/ttyACM0'
BAUD = 115200

def spam_serial(duration_seconds=120):
    s = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2)
    print(f"[SPAMMER] Starting 10-minute buffer spam test on {PORT}...")
    
    start_time = time.time()
    count = 0
    
    while time.time() - start_time < duration_seconds:
        choice = random.choice(['valid', 'partial', 'garbage', 'empty'])
        
        if choice == 'valid':
            msg = f'{{"grid_mode":"NORMAL","ta":{25 + random.uniform(-1, 1)},"pref":1}}\n'
        elif choice == 'partial':
            msg = f'{{"grid_mode":"NORM' 
        elif choice == 'garbage':
            msg = ''.join(random.choices(string.printable, k=50)) + '\n'
        else:
            msg = '\n'
            
        s.write(msg.encode())
        count += 1
        time.sleep(random.uniform(0.01, 0.1))
        
    s.close()
    print(f"[SPAMMER] Test complete. Sent {count} messages.")

if __name__ == "__main__":
    spam_serial()
