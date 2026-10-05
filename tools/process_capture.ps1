# Verwerk nieuwste capture (agent draait dit — jij niet nodig)
param(
    [string]$File = ""
)

$Root = Split-Path $PSScriptRoot -Parent
$Captures = Join-Path $Root "captures"

if ($File) {
    $Pcap = $File
} else {
    $latest = Get-ChildItem $Captures -Filter "*.pcapng" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if (-not $latest) {
        Write-Error "Geen .pcapng in $Captures"
        exit 1
    }
    $Pcap = $latest.FullName
}

Write-Host "Verwerk: $Pcap"
py (Join-Path $Root "tools\analyze_pcap.py") $Pcap --append-log
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Klaar — zie SNIFF_LOG.md"
