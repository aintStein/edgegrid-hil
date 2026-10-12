## Serial Transport
- Port: `/dev/ttyACM0` @ 115200 8N1, both ends.
- Physical layer: ESP32-S3 native USB-CDC (VID:PID 1a86:55d3).
- Firmware: `Serial.begin(115200)` after `while(!Serial)` wait. Boot signature: `[BOOT] EdgeGrid HIL Controller Initialized.`
- Streamlit: Reads `SERIAL_PORT` env var (default `/dev/ttyACM0`), baud hardcoded 115200.
