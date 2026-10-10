# EdgeGrid HIL: Serial Communication Protocol

This document defines the UART communication contract between the Python Dashboard (Laptop) and the ESP32 Edge Controller.

## 1. Physical Layer Specifications
- **Baud Rate:** 115200
- **Data Bits:** 8
- **Stop Bits:** 1
- **Parity:** None
- **Line Ending:** Newline (`\n`) is REQUIRED at the end of every JSON string.

## 2. Data Schemas (JSON)

### A. RX: Laptop (Python) ➔ ESP32
The dashboard sends raw environmental and grid data. The ESP32 makes the local decision.
```json
{"s": 1.5, "ta": 31.0}
