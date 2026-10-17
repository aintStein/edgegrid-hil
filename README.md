# EdgeGrid HIL (Hardware-in-the-Loop) Controller

## 🛠️ Engineering Highlights (EE Track)
- **Sensor Calibration:** Implemented a software calibration offset (+2.8°C) for the DHT22 sensor, validated against a physical reference thermometer.
- **Power Profiling & Runtime Validation:** Measured baseline idle draw at 8.3mA. Estimated peak operational load at 103.3mA (including relay coil). Validates a **4.84-hour worst-case runtime** on a 500mAh LiPo battery, meeting the 15mm thin form-factor constraint.
- **Memory Stability:** Firmware survived a high-load 2-minute serial buffer spam test with <1.5KB heap fragmentation. Implemented `MAX_BUFFER_SIZE` limits and robust `isNull()` JSON parsing to prevent crashes on malformed data.
- **Cross-Platform Toolchain:** Successfully validated and documented a seamless build/flash workflow across both Fedora Linux and Windows environments.
- **Live System Integration:** Developed `live_serial_bridge.py` to translate ESP32 v1.0 JSON telemetry into real-time CSV updates, enabling seamless live data visualization in the Streamlit CS Dashboard.

## 🚀 Quick Start
1. Flash firmware: `arduino-cli compile --fqbn esp32:esp32:esp32s3 --output-dir ./build ./edgegrid-hil.ino && arduino-cli upload --fqbn esp32:esp32:esp32s3 --port /dev/ttyACM0 --input-dir ./build ./edgegrid-hil.ino`
2. Run bridge: `python3 live_serial_bridge.py`
3. Run dashboard: `python3 -m streamlit run dashboard.py`
