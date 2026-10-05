# Duratech Link Mini → Home Assistant (ESPHome BLE)

ESPHome firmware that bridges a **Duratech LINK-MINI-60** (Vision Spectra pool lights) to Home Assistant over Bluetooth LE.

The official **DuraCloud** app talks MQTT-over-BLE to the Link Mini. This project reverse-engineers those GATT writes so you can control the lights from HA — without the cloud app for day-to-day use.

> Hardware note: Spectra / Link Mini do **not** expose a colour picker over BLE. The controller pulses 12 V AC so the lamp advances to the next built-in program (1–11). This bridge tracks that counter in software and can memorize the last program after you leave the lights off long enough.

## Features

- Lights on / off via Home Assistant
- “Next program” (+ optional direct program number 1–11 by stepping)
- **Memorize** last program after intentional HA off ≥ 30 s (re-applies on next on)
- Ignores short BLE power glitches so the counter does not jump while lights are off
- Optional RS485 YAML experiments (DuraCloud itself appears BLE-only)

## Requirements

- ESP32 (classic; ESP-IDF framework for the BLE bridge)
- Duratech Link Mini within BLE range of the ESP32
- [ESPHome](https://esphome.io/) + Home Assistant
- Your Link Mini Bluetooth MAC (advertising address)

## Quick start

1. Clone this repo.
2. Copy secrets and fill them in:

   ```bash
   cp secrets.yaml.example secrets.yaml
   ```

   Set at least `wifi_ssid`, `wifi_password`, `api_encryption_key`, `ota_password`, `ap_password`, and **`link_mini_mac`**.

3. Compile and flash:

   ```bash
   esphome run zwembad-link-mini.yaml
   ```

4. Add the device in Home Assistant (ESPHome integration). Useful entities:
   - `switch.*_lamps` — on/off
   - `button.*_next_program` — advance Spectra program
   - `number.*_program` — target program 1–11 (steps via “next”)
   - `binary_sensor.*_ble` — connection status

## Finding your MAC

1. Open nRF Connect (phone) or an nRF Sniffer + Wireshark.
2. Look for the Link Mini advertising name / manufacturer data.
3. Use that **advertising** address in `link_mini_mac`. DuraCloud may display a slightly different last octet — prefer the address you actually see advertising.

Sniffing workflow and known command bytes: see [`SNIFFEN.md`](SNIFFEN.md) and [`SNIFF_LOG.md`](SNIFF_LOG.md).

Analyse captures:

```bash
python tools/analyze_pcap.py captures/your.pcapng --writes
```

## Protocol (short)

GATT service / characteristics (DuraCloud family, same style as H17i-class devices):

| Role | UUID |
|------|------|
| Service | `682B3401-2EF9-4BB9-AD9B-28E228D41C1F` |
| Write | `682B3402-2EF9-4BB9-AD9B-28E228D41C1F` |
| Notify | `682B3403-2EF9-4BB9-AD9B-28E228D41C1F` |

Decoded writes used by the firmware:

| Action | Hex payload |
|--------|-------------|
| On | `041a08080210051a02080100` |
| Off | `041a08080210041a02080100` |
| Next program | `041a08080610051a02320100` |

Parser helpers live in `link_mini_parser.h`.

## Repo layout

| File | Purpose |
|------|---------|
| `zwembad-link-mini.yaml` | **Main** BLE bridge firmware |
| `link_mini_parser.h` | Notify / MQTT-over-BLE parsing |
| `zwembad-rs485.yaml` | Experimental RS485 TX |
| `zwembad-rs485-sniffer.yaml` | Experimental RS485 RX |
| `tools/analyze_pcap.py` | Wireshark capture helper |
| `secrets.yaml.example` | Template (never commit real `secrets.yaml`) |

## Disclaimer

Unofficial community project. Not affiliated with Duratech / Fluidra. Use at your own risk. BLE behaviour can vary by firmware revision of the Link Mini.

## License

MIT — see [LICENSE](LICENSE).
