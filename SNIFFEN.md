# Sniff checklist (Link Mini BLE)

Use an nRF52840 Dongle + Wireshark nRF Sniffer (or equivalent) to capture DuraCloud → Link Mini GATT traffic.

## Setup

1. Find your Link Mini **advertising MAC** in nRF Connect / Wireshark (DuraCloud may show a nearby address — use the advertising one).
2. Put that MAC in `secrets.yaml` as `link_mini_mac`.
3. Select that device in the sniffer **before** opening DuraCloud.
4. Start capture, then operate the lights in the app (on / off / next program).
5. Save as `captures/snifferN.pcapng` and analyse with `tools/analyze_pcap.py`.

## Known useful writes (MQTT-over-BLE)

| Action | Write hex (payload after framing) |
|--------|-----------------------------------|
| Lights **ON** | `041a08080210051a02080100` |
| Lights **OFF** | `041a08080210041a02080100` (field 4 power pad) |
| **Next program** | `041a08080610051a02320100` |

See `SNIFF_LOG.md` for capture history and decoder notes.

<details>
<summary>Common pitfalls</summary>

| Problem | Fix |
|---------|-----|
| No `btatt` packets | Wrong MAC selected, or sniffer not following the connection |
| Toolbar missing | View → Interface Toolbars → nRF Sniffer |

</details>
