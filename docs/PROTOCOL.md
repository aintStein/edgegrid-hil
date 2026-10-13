# EdgeGrid HIL Serial Protocol v1.0

## Transport
- **Physical:** Native USB-CDC (ESP32-S3)
- **Port:** `/dev/ttyACM0` (Linux) or `COMx` (Windows)
- **Baud:** 115200 8N1
- **Encoding:** UTF-8 JSON lines (terminated by `\n`)

## RX: Dashboard → Firmware (Commands)
| Field | Type | Description | Range |
| :--- | :--- | :--- | :--- |
| `grid_mode` | String | Current grid state | "SURPLUS", "DEFICIT" |
| `ta` | Float | Ambient Temperature (°C) | -40.0 to 85.0 |
| `pref` | Int | User Preference Level | 0 (Eco), 1 (Balanced), 2 (Comfort) |

**Example RX:** `{"grid_mode":"DEFICIT","ta":32.5,"pref":1}`

## TX: Firmware → Dashboard (Telemetry)
| Field | Type | Description |
| :--- | :--- | :--- |
| `r` | Int | Relay State (1=ON/Cooling, 0=OFF/Shedding) |
| `t` | Float | Current Room Temperature (°C) |
| `sl` | Float | Thermal Slack (minutes until overheat) |
| `fs` | Bool | Failsafe Active (true if comms lost) |

**Example TX:** `{"r":1,"t":24.5,"sl":15.2,"fs":false}`
