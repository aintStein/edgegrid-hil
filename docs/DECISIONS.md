## Day 4 Hardware Decisions
- **Silicon**: ESP32-S3-N16R8 (8MB Octal PSRAM). 
- **Transport**: Native USB-CDC via `/dev/ttyACM0`. Forced via `ARDUINO_USB_CDC_ON_BOOT=1` define due to board definition override.
- **Pins**: DHT22 DATA = GPIO10. Relay IN1 = GPIO4 (moved from GPIO12 due to N16R8 PSRAM reservation on GPIO26-32). Added 10k pulldown on GPIO4 for boot safety.
- **Boot Safety**: Relay defaults HIGH (ON/comfort). `pinMode` set AFTER `digitalWrite` to prevent chatter.
- **PSRAM**: Manually initialized via `psramInit()` in setup due to generic FQBN usage.
