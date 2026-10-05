# Home Assistant Community — draft / status

**Category:** Share your Projects!  
**Title:** Duratech Link Mini (Vision Spectra) BLE bridge for Home Assistant (ESPHome)

**Status (2026-10-05):** Submitted under account `gomblouse-arch`. Discourse flagged the new account (“typed too fast”) and the topic is **pending moderator approval**. Check:
https://community.home-assistant.io/u/gomblouse-arch/activity/pending

---

Hi all,

I reverse-engineered the DuraCloud MQTT-over-BLE protocol used by the **Duratech LINK-MINI-60** (Vision Spectra pool lights) and built an **ESPHome** bridge so the lights can be controlled from Home Assistant.

### What it does
- Lights on/off from HA
- “Next program” (Spectra advances via 12 V AC pulse — no direct colour GATT command)
- Optional program number 1–11 by stepping
- Remembers the last program after an intentional off ≥ 30 s
- Filters short BLE power glitches so the counter does not jump while lights are off

### Hardware
- ESP32 + Link Mini in BLE range
- No RS485 required for day-to-day control (RS485 YAML is experimental only)

### Repo
https://github.com/gomblouse-arch/esphome-duratech-link-mini

MIT licensed. Not affiliated with Duratech/Fluidra. Feedback and improvements welcome — especially if your Link Mini firmware behaves differently.

Happy to answer questions.
