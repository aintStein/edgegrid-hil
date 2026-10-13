# EdgeGrid HIL Serial Protocol (v1.0)

**Transport:** USB-CDC (Virtual COM Port)  
**Baud Rate:** 115200  
**Line Ending:** `\n` (Newline)  
**Encoding:** UTF-8  

## 1. Host-to-MCU (RX)
The MCU expects a single-line JSON object followed by a newline character.

| Field | Type | Required | Description | Constraints |
| :--- | :--- | :--- | :--- | :--- |
| `ta` | float | Yes | Ambient Temperature (°C) | Range: -40.0 to 85.0 |
| `pref` | int | Yes | User Preference | 0=Eco, 1=Balanced, 2=Comfort |

**Example Payload:**
```json
{"ta": 25.0, "pref": 1}
