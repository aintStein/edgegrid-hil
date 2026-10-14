# EdgeGrid HIL Serial Protocol v1.0

## Transport
- **Physical:** Native USB-CDC (ESP32-S3)
- **Port:** `/dev/ttyACM0` (Linux) or `COMx` (Windows)
- **Baud:** 115200 8N1
- **Encoding:** UTF-8 JSON lines (terminated by `\n`)

## RX: Dashboard → Firmware (Commands)
| Field | Type | Description | Range |
| :--- | :--- | :--- | :--- |
| `grid_mode` | String | Current grid state | "SURPLUS", "DEFICIT", "NORMAL" |
| `ta` | Float | Ambient Temperature (°C) | -40.0 to 85.0 |
| `pref` | Int | User Preference Level | 0 (Eco), 1 (Balanced), 2 (Comfort) |

**Example RX:** `{"grid_mode":"DEFICIT","ta":32.5,"pref":1}`

## TX: Firmware → Dashboard (Telemetry)
| Field | Type | Description |
| :--- | :--- | :--- |
| `status` | String | System State | "IDLE", "COOLING", "HEATING", "FAULT" |
| `relay_state` | Boolean | Relay Status | true (ON), false (OFF) |
| `temp_target` | Float | Target Temperature (°C) | 23.0 - 26.0 |
| `slack` | Float | Thermal Slack (minutes) | 0.0+ |
| `uptime_ms` | Unsigned Long | Milliseconds since boot | 0+ |

**Example TX:** `{"status":"COOLING","relay_state":true,"temp_target":26.0,"slack":15.2,"uptime_ms":12345}`

## Failsafe Behavior
- **Trigger:** No valid RX packet received within 1500ms.
- **Action:** Relay defaults to ON (Safe State), Status becomes "FAULT".
- **Recovery:** Automatically returns to Edge Control upon receipt of valid JSON.
