CALIBRATION_MARKDOWN = """**Kalibratie programmanummer**

De lamp stuurt het actieve programma *niet* terug via BLE. Home Assistant houdt een teller bij in het ESP-geheugen.

**Wanneer kalibreren?**  
Kleur op de lamp ≠ **Huidig programma** in HA.

**Snelste methode**
1. Kijk welke kleur de lamp nu toont (1–11)
2. Zet **Huidig programma** op dat nummer

**Via Sync naar blauw** (~30 s)
1. Druk **Sync naar blauw** — lamp uit, pulseert, teller → 5
2. Lamp **blauw** (6)? → **Teller 6 blauw**
3. **Caribisch blauw** (5)? → kleur **6 Blauw** of **Teller 6 blauw**

**Teller-knoppen** — zeker van de kleur? **Teller 6 blauw** / **Teller 7 groen**

*Tip: bedien kleuren via HA óf via de Spectra-app — niet afwisselen.*"""
