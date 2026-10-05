# Link Mini BLE sniff log

Notes from reverse-engineering DuraCloud → Link Mini GATT traffic.

App control is **Next program** only (no direct colour picker). The Link Mini pulses 12 V AC so the lamp advances to the next hardware program (see Spectra manual).

Example advertising MAC in docs: **`AA:BB:CC:DD:EE:FF`** (replace with yours in `secrets.yaml`). DuraCloud may show a nearby address; prefer the advertising MAC.

---

## sniffer1.pcapng — 2026-08-06

**File:** `captures/sniffer1.pcapng`  
**Size:** 323592 bytes | **Duration:** ~103.6 s | **Frames:** 3693  
**Procedure (expected):** connect → on → colours → off

### Verdict: **not usable**

| Check | Result |
|-------|--------|
| btatt / GATT writes | **0** — no commands |
| CONNECT followed by sniffer | **No** — advertising only |
| App MAC (nearby address) | **0** frames |
| Advertising MAC | Adv frames visible, connection not followed |
| CONNECT_IND to Link Mini | **No** |

**Conclusion:** Wrong MAC selected, or sniffer did not follow the connection. Resniff with the advertising device selected **before** opening DuraCloud.

---

## sniffer2.pcapng — 2026-08-06

**File:** `captures/sniffer2.pcapng`  
**Size:** 457280 bytes | **Duration:** ~79.2 s | **Frames:** 5466  
**GATT write handle:** `0x0013` | **Notify handle:** `0x0010`

### Verdict: **partially usable** (on/off OK)

| t (s) | Action (inferred) | Write hex |
|------:|-------------------|-----------|
| 12.01 | CONNECT ×2 | `020a0100` |
| 12.13 | Subscribe **Lights** group 1 | `042202080100` |
| 14.02 | **Lights ON** | `041a08080210051a02080100` |
| 16.60 | Mislabelled as OFF (actually next-style) | `041a08080610051a02320100` |

### Notify schema (Lights group)

Fields: **Power**, **White Color**, **Color**, **Brightness**, **Scene Switcher**

Scene names in notify metadata (not direct app picks):

| # | Name |
|---|------|
| 1 | Deep Blue Sea |
| 2 | Daylight Blue |
| 3 | Sunset |
| 4 | Love Is In The Air |
| 5 | Forest Spring |
| 6 | Think Pink |
| 7 | Sunshine |
| 8 | Jungle Beach |
| 9 | Voodoo |
| 10 | Disco |
| 11 | Party |
| 12 | Warm White |
| 13 | Neutral White |
| 14 | Sun White |

---

## sniffer3.pcapng — 2026-08-06

**File:** `captures/sniffer3.pcapng`  
**Size:** 611480 bytes | **Duration:** ~135.8 s | **Frames:** 9091  
**GATT write handle:** `0x0013`

### Verdict: **usable** — “Next program” decoded

| t (s) | Count | Action (inferred) | Write hex |
|------:|------:|-------------------|-----------|
| 16.58 | ×2 | CONNECT | `020a0100` |
| 16.70 | ×2 | Subscribe **Lights** group 1 | `042202080100` |
| 18.38 | ×1 | **Lights ON** | `041a08080210051a02080100` |
| 43.04–120.06 | **×39** | **Next program** | `041a08080610051a02320100` |

---

## sniffer4.pcapng — 2026-08-06

**File:** `captures/sniffer4.pcapng`  
**Duration:** ~24.8 s | **Writes:** 7 (4 unique payloads)

| t (s) | Action | Write hex |
|------:|--------|-----------|
| 16.12 | CONNECT ×2 | `020a0100` |
| 16.24 | Subscribe Lights | `042202080100` |
| 18.76 | App action (1×) | `041a08080210041a02080100` |

After connect, a single command: group 2 **field 4** bool true (`10 04` instead of `10 05`). Notify then shows power on (`120412020801`).

### Derived power model

| Action | Field | Hex |
|--------|-------|-----|
| **ON** | 5 bool true | `041a08080210051a02080100` |
| **OFF** | 4 bool **true** | `041a08080210041a02080100` |
| **Next** | 6 + `3201` | `041a08080610051a02320100` |

Notify schema names this **Switch Next Color Program**. The 14 scene names are metadata, not direct selection.

### Firmware

`zwembad-link-mini.yaml` — **Next program** button uses the sniffer3 bytes. No preset-select (not supported by the app over BLE).
