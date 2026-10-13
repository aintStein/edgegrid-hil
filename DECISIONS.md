## Day 6: Integration Preparation
- **API Contract Finalized:** Moved from simple debug prints to structured JSON TX/RX for Streamlit integration.
- **Watchdog Tuning:** Increased timeout to 1500ms to prevent false-positive faults during Python polling intervals.
- **Headless Operation:** Confirmed system stability without a physical screen, relying entirely on serial telemetry.

## Day 5: Fault Injection & Stress Testing
- **Buffer Spam Test (T-P07):** Verified non-blocking parser handles 50 packets in 2s without resets.
- **Relay Chatter Fix:** Implemented consistent slack calculation based on `TEMP_UPPER_LIMIT` to prevent rapid switching.
- **File Sync Protocol:** Established strict `nano` overwrite + cache clear workflow to prevent stale firmware flashes.
