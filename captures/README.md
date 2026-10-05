# BLE captures

Plaats hier je Wireshark/nRF Sniffer `.pcapng`-bestanden (niet in git — te groot).

Analyseer met:

```powershell
py tools/analyze_pcap.py captures/sniffer1.pcapng --writes
```

Of geef een map:

```powershell
py tools/analyze_pcap.py captures/ --writes --handshake
```

Zie `SNIFF_LOG.md` voor gedocumenteerde bevindingen per capture.
