#!/usr/bin/env python3
"""Analyse Duratech Link Mini BLE captures (Wireshark .pcapng) with tshark."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path


def find_tshark() -> str:
    env = os.environ.get("TSHARK")
    if env and Path(env).is_file():
        return env
    found = shutil.which("tshark")
    if found:
        return found
    for candidate in (
        r"C:\Program Files\Wireshark\tshark.exe",
        "/usr/bin/tshark",
        "/usr/local/bin/tshark",
        "/Applications/Wireshark.app/Contents/MacOS/tshark",
    ):
        if Path(candidate).is_file():
            return candidate
    raise FileNotFoundError(
        "tshark not found. Install Wireshark or set TSHARK to the tshark binary path."
    )


def collect_pcaps(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    if path.is_dir():
        return sorted(path.glob("*.pcapng")) + sorted(path.glob("*.pcap"))
    raise FileNotFoundError(path)


def capture_stats(tshark: str, pcap: Path) -> dict:
    size = pcap.stat().st_size
    frame_count = 0
    duration = 0.0
    try:
        cmd = [
            tshark,
            "-r",
            str(pcap),
            "-T",
            "fields",
            "-e",
            "frame.time_relative",
        ]
        times = [
            float(x)
            for x in subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).splitlines()
            if x.strip()
        ]
        frame_count = len(times)
        if times:
            duration = max(times)
    except (subprocess.CalledProcessError, ValueError):
        pass
    return {"size": size, "frames": frame_count, "duration": duration}


def att_opcode_counts(tshark: str, pcap: Path) -> Counter[str]:
    cmd = [tshark, "-r", str(pcap), "-Y", "btatt", "-T", "fields", "-e", "btatt.opcode"]
    out = subprocess.check_output(cmd, text=True, errors="replace")
    return Counter(line.strip() for line in out.splitlines() if line.strip())


def get_write_rows(tshark: str, pcap: Path) -> list[tuple[float, str, str]]:
    cmd = [
        tshark,
        "-r",
        str(pcap),
        "-Y",
        "btatt.opcode == 0x12",
        "-T",
        "fields",
        "-e",
        "frame.time_relative",
        "-e",
        "btatt.handle",
        "-e",
        "btatt.value",
    ]
    out = subprocess.check_output(cmd, text=True, errors="replace")
    rows: list[tuple[float, str, str]] = []
    for line in out.strip().splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        t, handle, hexv = parts
        payload = hexv.replace(":", "")
        if payload:
            rows.append((float(t), handle, payload))
    return rows


def list_write_payloads(tshark: str, pcap: Path) -> None:
    rows = get_write_rows(tshark, pcap)
    print(f"\n=== {pcap.name}: ATT Write Request timeline ===")
    if not rows:
        print("(geen Write Request pakketten — misschien verkeerd device gefilterd?)")
        return

    unique: Counter[str] = Counter()
    for _, handle, payload in rows:
        unique[f"handle={handle} {payload}"] += 1

    print(f"Writes totaal: {len(rows)} | unieke payloads: {len(unique)}")
    print("\n--- Unieke payloads (aantal) ---")
    for key, count in unique.most_common():
        print(f"  {count:3d}x  {key}")

    print("\n--- Chronologisch (alle writes met waarde) ---")
    for t, handle, payload in rows:
        print(f"  {t:8.3f}s  handle={handle}  {payload}")


def sequence_around_handshake(tshark: str, pcap: Path) -> None:
    cmd_w = [
        tshark,
        "-r",
        str(pcap),
        "-Y",
        "btatt.opcode == 0x12",
        "-T",
        "fields",
        "-e",
        "frame.time_relative",
        "-e",
        "btatt.value",
    ]
    cmd_n = [
        tshark,
        "-r",
        str(pcap),
        "-Y",
        "btatt.opcode == 0x1b",
        "-T",
        "fields",
        "-e",
        "frame.time_relative",
        "-e",
        "btatt.value",
    ]
    writes: list[tuple[float, str, str]] = []
    for line in subprocess.check_output(cmd_w, text=True).splitlines():
        if not line.strip():
            continue
        t, v = line.split("\t")
        writes.append((float(t), "W", v.replace(":", "")))
    notifies: list[tuple[float, str, str]] = []
    for line in subprocess.check_output(cmd_n, text=True).splitlines():
        if not line.strip():
            continue
        t, v = line.split("\t")
        raw = bytes.fromhex(v.replace(":", ""))
        notifies.append((float(t), "N", f"len={len(raw)}"))

    start = None
    for t, _, v in writes:
        if v.startswith("020a"):
            start = t
            break
    if start is None:
        print(f"{pcap.name}: geen CONNECT (020a0100)")
        return

    events = [(t, d, p) for t, d, p in writes + notifies if start - 0.1 <= t <= start + 3.0]
    events.sort()
    print(f"\n=== {pcap.name}: +/-3s rond eerste CONNECT @ {start:.3f}s ===")
    for t, direction, payload in events:
        print(f"{t - start:+7.3f}s  {direction}  {payload}")


def generate_report(tshark: str, pcap: Path) -> str:
    stats = capture_stats(tshark, pcap)
    opcodes = att_opcode_counts(tshark, pcap)
    rows = get_write_rows(tshark, pcap)
    unique: Counter[str] = Counter()
    for _, handle, payload in rows:
        unique[f"{handle}|{payload}"] += 1

    opcode_names = {
        "0x12": "Write Request",
        "0x13": "Write Response",
        "0x1b": "Handle Value Notification",
    }

    lines = [
        f"## {pcap.name} -- {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        f"**File:** `captures/{pcap.name}`  ",
        f"**Size:** {stats['size']} bytes | **Duration:** ~{stats['duration']:.1f} s | **Frames:** {stats['frames']}  ",
        "**Procedure (verwacht):** verbinden → aan → rood → groen → blauw → paars → party → uit",
        "",
    ]

    if not opcodes:
        lines.extend(
            [
                "### Verdict",
                "",
                "**Leeg of verkeerd device** — geen btatt-pakketten. Opnieuw sniffen met Link Mini MAC gekozen.",
                "",
            ]
        )
        return "\n".join(lines)

    lines.append("### ATT counts")
    lines.append("")
    lines.append("| Opcode | Name | Count |")
    lines.append("|--------|------|------:|")
    for op, count in sorted(opcodes.items()):
        name = opcode_names.get(op, op)
        if op in ("0x12", "0x13", "0x1b") or count > 5:
            lines.append(f"| {op} | {name} | {count} |")
    lines.append("")

    if rows:
        handle_counts = Counter(h for _, h, _ in rows)
        main_handle = handle_counts.most_common(1)[0][0] if handle_counts else "?"
        lines.append(f"Write handle of interest: **{main_handle}** ({len(rows)} writes with value).")
        lines.append("")

    lines.append("### Unieke write payloads")
    lines.append("")
    lines.append("| Count | Handle | Hex |")
    lines.append("|------:|--------|-----|")
    for key, count in unique.most_common():
        handle, payload = key.split("|", 1)
        lines.append(f"| {count} | {handle} | `{payload}` |")
    lines.append("")

    lines.append("### Chronologische writes (handle 0x000f)")
    lines.append("")
    lines.append("| t (s) | Hex |")
    lines.append("|------:|-----|")
    for t, handle, payload in rows:
        if handle.lower() in ("0x000f", "0xf"):
            lines.append(f"| {t:.3f} | `{payload}` |")
    lines.append("")

    has_connect = any(p.startswith("020a") for _, _, p in rows)
    lines.append("### Verdict")
    lines.append("")
    if has_connect:
        lines.append("- CONNECT (`020a0100`) gevonden")
    else:
        lines.append("- **Geen CONNECT** — capture opnieuw, sniffer starten vóór DuraCloud opent")
    lines.append(f"- {len(unique)} unieke commando-payloads — klaar voor koppeling aan lamp-acties")
    lines.append("")

    return "\n".join(lines)


def summarize_pcap(tshark: str, pcap: Path) -> None:
    stats = capture_stats(tshark, pcap)
    opcodes = att_opcode_counts(tshark, pcap)

    print(f"\n=== {pcap.name} ===")
    print(f"Size: {stats['size']} bytes | Frames: {stats['frames']} | Duration: ~{stats['duration']:.1f}s")

    if not opcodes:
        print("Geen btatt-pakketten (controleer device-filter in nRF Sniffer)")
        return

    names = {
        "0x01": "Error Response",
        "0x02": "Exchange MTU Request",
        "0x12": "Write Request",
        "0x13": "Write Response",
        "0x1b": "Handle Value Notification",
    }
    print("\nATT counts:")
    for op, count in sorted(opcodes.items()):
        label = names.get(op, op)
        print(f"  {op} {label}: {count}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        nargs="?",
        default="captures",
        help="pcapng file or directory (default: captures/)",
    )
    parser.add_argument("--writes", action="store_true", help="show ATT Write Request timeline")
    parser.add_argument(
        "--handshake",
        action="store_true",
        help="show sequence around first CONNECT",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="print SNIFF_LOG.md section (markdown)",
    )
    parser.add_argument(
        "--append-log",
        action="store_true",
        help="append --report output to SNIFF_LOG.md",
    )
    args = parser.parse_args()

    try:
        tshark = find_tshark()
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1

    root = Path(__file__).resolve().parents[1]
    target = Path(args.path)
    if not target.is_absolute():
        target = root / target

    try:
        pcaps = collect_pcaps(target)
    except FileNotFoundError:
        print(f"No captures at {target}", file=sys.stderr)
        print("Place .pcapng in captures/ (see SNIFFEN.md)", file=sys.stderr)
        return 1

    if not pcaps:
        print(f"No .pcapng/.pcap files in {target}", file=sys.stderr)
        return 1

    reports: list[str] = []
    for pcap in pcaps:
        try:
            if args.report or args.append_log:
                reports.append(generate_report(tshark, pcap))
            else:
                summarize_pcap(tshark, pcap)
                if args.writes:
                    list_write_payloads(tshark, pcap)
                if args.handshake:
                    sequence_around_handshake(tshark, pcap)
        except subprocess.CalledProcessError as exc:
            print(f"{pcap.name}: tshark failed ({exc.returncode})", file=sys.stderr)

    if reports:
        combined = "\n\n---\n\n".join(reports)
        if args.append_log:
            log_path = root / "SNIFF_LOG.md"
            marker = f"<!-- auto: {pcaps[-1].name} -->"
            existing = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
            if marker not in existing:
                with log_path.open("a", encoding="utf-8") as fh:
                    if existing and not existing.endswith("\n"):
                        fh.write("\n")
                    fh.write("\n---\n\n")
                    fh.write(combined)
                    fh.write(f"\n\n{marker}\n")
                print(f"Appended to {log_path}", file=sys.stderr)
            else:
                print(f"Already in SNIFF_LOG.md: {pcaps[-1].name}", file=sys.stderr)
        else:
            print(combined)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
