#!/usr/bin/env python3
"""dnsctl — switch, benchmark and live-monitor DNS on any device.

One tool, every platform: pick one of the committed profiles (Kids Guard,
Kahf Guard, Ad Block, Family Safe, Privacy no-log) — or any endpoint from the
list — and apply it to this machine. Switch as often as you like; measure
live UDP/DoT/DoH latency before you decide.

Platforms
  Windows   Set-DnsClientServerAddress on every Up adapter (+ DoH template via
            Add-DnsClientDohServerAddress on Windows 11 22H2+ / Server 2022)
  macOS     networksetup on the first enabled network service (Wi-Fi first)
  Linux     /etc/systemd/resolved.conf.d/dnsctl.conf (systemd-resolved); falls
            back to printed NetworkManager / resolv.conf steps
  Android   prints the Private DNS hostname + setup steps (Private DNS is
            OS-managed; no app can switch it programmatically)
  iPhone    `export mobileconfig <profile>` writes an installable
            .mobileconfig (com.apple.dnsSettings.managed, DoH)
  Router    prints the AdGuard Home / Pi-hole / dnsmasq upstreams for the
            profile (the committed system/<profile>/ files are the same)

Commands
  status                              show current DNS configuration
  test   [--profile NAME] [--all]     live latency table (UDP, DoT, DoH)
  fastest [--apply]                   probe profiles, switch to the winner
  watch  [--interval N]               continuous live latency monitor
  use     <profile|host> [--dry-run]  apply a profile to this device now
  reset   [--dry-run]                 back to DHCP / automatic DNS
  mobile  <profile>                   Android Private DNS / iOS steps
  export  mobileconfig <profile>      write an iOS/macOS DNS profile file
  router  <profile>                   router / AdGuard Home / Pi-hole values

Examples
  python scripts/dnsctl.py status
  python scripts/dnsctl.py test                     # 5 profiles, live ping
  python scripts/dnsctl.py fastest --apply          # benchmark + switch
  python scripts/dnsctl.py use kahfguard            # switch to Kahf Guard
  python scripts/dnsctl.py reset
  python scripts/dnsctl.py watch --interval 3

Applying DNS changes wants
  Windows: run from an elevated shell (auto re-launches with UAC otherwise)
  macOS/Linux: root or sudo (macOS prompts via sudo; Linux re-execs sudo)
Use --dry-run to see exactly what would change without touching anything.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import ctypes
import json
import os
import random
import re
import shutil
import socket
import ssl
import struct
import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from check_health import build_query, parse_response, check_dot, check_doh  # noqa: E402

DATA = ROOT / "data" / "dns-servers.json"
SYSTEM_DATA = ROOT / "data" / "dns-system.json"
QUERY_NAME = "example.com"
TIMEOUT_UDP = 2.0


# --------------------------------------------------------------------------- #
# Loading profiles
# --------------------------------------------------------------------------- #
def load_system() -> dict:
    return json.loads(SYSTEM_DATA.read_text(encoding="utf-8"))


def load_dns_servers() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8"))


def find_profile(doc: dict, query: str) -> dict | None:
    q = query.strip().lower()
    for p in doc["profiles"]:
        if p["id"].lower() == q:
            return p
    for p in doc["profiles"]:
        if q in p["id"].lower() or q in p["name"].lower():
            return p
    return None


def find_endpoint(doc: dict, host: str) -> dict | None:
    h = host.strip().lower().rstrip(".")
    for provider in doc["providers"]:
        for entry in provider["hosts"]:
            if entry["host"].lower() == h:
                return entry
    return None


def profile_ips(p: dict) -> list[str]:
    return list(p.get("ipv4") or [])


def describe_system_profiles(doc: dict) -> str:
    return ", ".join(p["id"] for p in doc["profiles"])


# --------------------------------------------------------------------------- #
# Live probes
# --------------------------------------------------------------------------- #
def udp_query_ms(ip: str, name: str = QUERY_NAME, timeout: float = TIMEOUT_UDP) -> float | None:
    """Plain UDP/53 A-query latency — the number that matters for system DNS."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    tid = random.randint(1, 65535)
    qname = b"".join(bytes([len(part)]) + part.encode() for part in name.split(".")) + b"\x00"
    pkt = struct.pack("!HHHHHH", tid, 0x0100, 1, 0, 0, 0) + qname + struct.pack("!HH", 1, 1)
    started = time.perf_counter()
    try:
        sock.sendto(pkt, (ip, 53))
        data, _ = sock.recvfrom(512)
        rcode, _answers = parse_response(data)
        if rcode not in (0, 3):  # NOERROR or NXDOMAIN are both real answers
            return None
        return round((time.perf_counter() - started) * 1000, 1)
    except Exception:
        return None
    finally:
        sock.close()


def bench_profile(p: dict, timeout: float) -> dict:
    ips = profile_ips(p)
    out: dict = {"id": p["id"], "name": p["name"], "icon": p.get("icon", ""), "ipv4": ips}
    out["udp_ms"] = [udp_query_ms(ip, timeout=timeout) for ip in ips]
    good = [m for m in out["udp_ms"] if m is not None]
    out["udp_avg"] = round(sum(good) / len(good), 1) if good else None

    out["dot_ms"] = None
    if p.get("dot_host"):
        try:
            dot = check_dot(p["dot_host"], timeout)
            out["dot_ms"] = dot.get("latency_ms") if dot.get("status") in ("ok", "cert") else None
            out["dot_status"] = dot.get("status")
        except Exception:
            out["dot_ms"] = None
            out["dot_status"] = "error"

    out["doh_ms"] = None
    if p.get("doh"):
        try:
            doh = check_doh(p["doh"], timeout)
            out["doh_ms"] = doh.get("latency_ms") if doh.get("status") in ("ok", "cert", "http2") else None
            out["doh_status"] = doh.get("status")
        except Exception:
            out["doh_ms"] = None
            out["doh_status"] = "error"
    return out


def bench_endpoint(entry: dict, timeout: float) -> dict:
    out = {
        "host": entry["host"],
        "label": entry.get("label", ""),
        "protocol": entry["protocol"],
        "filters": ",".join(entry.get("filters", [])),
        "region": entry.get("region", "global"),
    }
    ips = entry.get("ipv4") or []
    out["ipv4"] = ips
    out["udp_ms"] = udp_query_ms(ips[0], timeout=timeout) if ips else None

    out["dot_ms"] = None
    if entry["protocol"] in ("dot", "dot+doh"):
        dot = check_dot(entry["host"], timeout)
        out["dot_ms"] = dot.get("latency_ms") if dot.get("status") in ("ok", "cert") else None
    out["doh_ms"] = None
    if entry["protocol"] in ("doh", "dot+doh") and entry.get("doh"):
        doh = check_doh(entry["doh"], timeout)
        out["doh_ms"] = doh.get("latency_ms") if doh.get("status") in ("ok", "cert", "http2") else None
    return out


def fmt_ms(value) -> str:
    return f"{value:>7.1f} ms" if isinstance(value, (int, float)) else f"{'—':>9} "


def bar(value, scale=250.0) -> str:
    if not isinstance(value, (int, float)):
        return ""
    width = max(0, min(24, int(24 * (1 - value / scale))))
    return "█" * width


# --------------------------------------------------------------------------- #
# Applying DNS (per platform)
# --------------------------------------------------------------------------- #
def is_windows() -> bool:
    return sys.platform.startswith("win")


def is_macos() -> bool:
    return sys.platform == "darwin"


def is_linux() -> bool:
    return sys.platform.startswith("linux")


def windows_is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def windows_rerun_elevated() -> int | None:
    """Re-launch this script as admin (UAC prompt). Returns new process code or None."""
    if os.environ.get("DNSCTL_ELEVATED") == "1":
        return 1  # already elevated once — do not loop
    argv = list(sys.argv)
    if "--elevated" not in argv:
        argv.append("--elevated")
    env_cmd = subprocess.list2cmdline([sys.executable, *argv])
    print("DNS change requires Administrator. Requesting elevation (UAC prompt)…")
    params = env_cmd
    rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
    return 0 if rc > 32 else rc


def powershell(script: str, timeout: float = 120) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", script],
        capture_output=True, text=True, timeout=timeout,
    )


def windows_set_dns(ips: list[str], doh_url: str | None, dry_run: bool) -> int:
    script = f"""
$ErrorActionPreference = 'Stop'
$ips = @({', '.join(repr(i) for i in ips)})
Get-NetAdapter | Where-Object {{ $_.Status -eq 'Up' }} | ForEach-Object {{
    Set-DnsClientServerAddress -InterfaceIndex $_.ifIndex -ServerAddresses $ips
    Write-Output ("set: " + $_.Name)
}}
ipconfig /flushdns | Out-Null
""".strip()
    if dry_run:
        print(script)
        if doh_url:
            print(f"\n# On Windows 11 22H2+ the DoH template is also set:\nAdd-DnsClientDohServerAddress -ServerAddress {ips[0]} -DohTemplate {doh_url} -AllowFallbackToUdp $false -AutoUpgrade $true")
        return 0

    if not windows_is_admin():
        code = windows_rerun_elevated()
        return code if code is not None else 1

    proc = powershell(script)
    sys.stdout.write(proc.stdout)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        print("Set-DnsClientServerAddress failed; falling back to netsh.")
        ps = r"Get-NetAdapter | Where-Object { $_.Status -eq 'Up' } | Select-Object -ExpandProperty Name"
        names = powershell(ps).stdout.split()
        ok = True
        for name in names:
            for idx, ip in enumerate(ips, start=1):
                extra = "primary" if idx == 1 else f"index={idx}"
                if os.system(f'netsh interface ip set dns "{name}" static {ip} {extra}') != 0:
                    ok = False
        if not ok:
            print("netsh fallback failed too — set DNS manually (Settings → Network & internet).")
            return 1
    if doh_url:
        doh_ps = (
            f"try {{ Add-DnsClientDohServerAddress -ServerAddress {ips[0]} -DohTemplate '{doh_url}' "
            f"-AllowFallbackToUdp $false -AutoUpgrade $true -ErrorAction Stop; "
            f"Write-Output 'DoH template set for {ips[0]}' }} catch {{ "
            f"Write-Output 'DoH cmdlet unavailable (needs Windows 11 22H2+); DNS is set but not encrypted.' }}"
        )
        proc2 = powershell(doh_ps)
        sys.stdout.write(proc2.stdout)
    print("Windows DNS updated. Verify:  Resolve-DnsName example.com")
    return 0


def windows_reset_dns(dry_run: bool) -> int:
    script = """
$ErrorActionPreference = 'Stop'
Get-NetAdapter | Where-Object { $_.Status -eq 'Up' } | ForEach-Object {
    Set-DnsClientServerAddress -InterfaceIndex $_.ifIndex -ResetServerAddresses
    Write-Output ("reset: " + $_.Name)
}
ipconfig /flushdns | Out-Null
""".strip()
    if dry_run:
        print(script)
        return 0
    if not windows_is_admin():
        code = windows_rerun_elevated()
        return code if code is not None else 1
    proc = powershell(script)
    sys.stdout.write(proc.stdout)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        return 1
    print("Windows DNS reset to DHCP / automatic.")
    return 0


def windows_current_dns() -> list[str]:
    ps = r"Get-DnsClientServerAddress -AddressFamily IPv4 | Where-Object { $_.ServerAddresses.Count -gt 0 } | ForEach-Object { $_.ServerAddresses }"
    try:
        out = powershell(ps, timeout=30).stdout.split()
        return sorted(set(out))
    except Exception:
        return []


# --- macOS ------------------------------------------------------------------ #
def macos_network_services() -> list[str]:
    try:
        out = subprocess.run(["networksetup", "-listallnetworkservices"],
                             capture_output=True, text=True, timeout=15).stdout
    except Exception:
        return []
    services = []
    for line in out.splitlines()[1:]:  # first line is the header
        name = line.rstrip()
        if not name or name.startswith("*"):
            continue
        services.append(name)
    return services


def macos_pick_service(preferred: str | None) -> str | None:
    services = macos_network_services()
    if preferred:
        for s in services:
            if s.lower() == preferred.lower():
                return s
        return None
    for key in ("wi-fi", "wifi", "ethernet", "thunderbolt bridge", "usb 10/100"):
        for s in services:
            if key in s.lower():
                return s
    return services[0] if services else None


def macos_set_dns(ips: list[str], service: str | None, dry_run: bool) -> int:
    svc = macos_pick_service(service) if not service else service
    svc = svc or "Wi-Fi"
    prefix = [] if os.geteuid() == 0 else ["sudo"]
    cmd = prefix + ["networksetup", "-setdnsservers", svc, *ips]
    if dry_run:
        print(" ".join(cmd))
        return 0
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except FileNotFoundError:
        print("networksetup not found — set DNS manually (System Settings → Network → DNS).")
        return 1
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        return 1
    subprocess.run(prefix + ["dscacheutil", "-flushcache"], capture_output=True, timeout=30)
    print(f"macOS DNS set on '{svc}': {' '.join(ips)}")
    print("Verify:  scutil --dns | head -20")
    print("Note: macOS encrypts DNS only via a profile/app — see 'dnsctl.py export mobileconfig'.")
    return 0


def macos_reset_dns(service: str | None, dry_run: bool) -> int:
    svc = macos_pick_service(service) if not service else service
    svc = svc or "Wi-Fi"
    prefix = [] if os.geteuid() == 0 else ["sudo"]
    cmd = prefix + ["networksetup", "-setdnsservers", svc, "Empty"]
    if dry_run:
        print(" ".join(cmd))
        return 0
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        return 1
    print(f"macOS DNS on '{svc}' reset to automatic (DHCP).")
    return 0


def macos_current_dns() -> list[str]:
    addrs: list[str] = []
    for svc in macos_network_services():
        out = subprocess.run(["networksetup", "-getdnsservers", svc],
                             capture_output=True, text=True, timeout=15).stdout
        for token in out.split():
            if re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", token):
                addrs.append(token)
    return sorted(set(addrs))


# --- Linux ------------------------------------------------------------------ #
def linux_has_resolved() -> bool:
    return Path("/run/systemd/resolve").exists() or shutil.which("systemctl") is not None


LINUX_CONF = Path("/etc/systemd/resolved.conf.d/dnsctl.conf")


def linux_set_dns(ips: list[str], dot_host: str | None, dry_run: bool) -> int:
    body = "[Resolve]\n" + "DNS=" + " ".join(f"{ip}#{dot_host}" if dot_host else ip for ip in ips) + "\n"
    body += "DNSOverTLS=yes\nDNSSEC=allow-downgrade\nCache=yes\n"
    if dry_run:
        print(f"# write {LINUX_CONF}\n{body}")
        print("sudo systemctl restart systemd-resolved")
        return 0
    if os.geteuid() != 0:
        if shutil.which("sudo"):
            return subprocess.run(["sudo", "-E", sys.executable, __file__, *sys.argv[1:], "--elevated"],
                                  env={**os.environ, "DNSCTL_ELEVATED": "1"}).returncode
        print("Need root. Run: sudo python3 scripts/dnsctl.py use …")
        return 1
    try:
        LINUX_CONF.parent.mkdir(parents=True, exist_ok=True)
        if LINUX_CONF.exists():
            backup = LINUX_CONF.with_suffix(".conf.bak")
            backup.write_bytes(LINUX_CONF.read_bytes())
            print(f"backup: {backup}")
        LINUX_CONF.write_text(body, encoding="utf-8")
    except PermissionError as exc:
        print(f"cannot write {LINUX_CONF}: {exc}")
        return 1
    subprocess.run(["systemctl", "restart", "systemd-resolved"], capture_output=True, timeout=60)
    print(f"Linux systemd-resolved DNS set: {' '.join(ips)} (DoT to {dot_host or '—'})")
    print("Verify:  resolvectl status")
    return 0


def linux_reset_dns(dry_run: bool) -> int:
    if dry_run:
        print(f"# remove {LINUX_CONF} (restore backup)\nsudo systemctl restart systemd-resolved")
        return 0
    if os.geteuid() != 0:
        if shutil.which("sudo"):
            return subprocess.run(["sudo", "-E", sys.executable, __file__, *sys.argv[1:], "--elevated"],
                                  env={**os.environ, "DNSCTL_ELEVATED": "1"}).returncode
        print("Need root. Run: sudo python3 scripts/dnsctl.py reset")
        return 1
    removed = False
    if LINUX_CONF.exists():
        backup = LINUX_CONF.with_suffix(".conf.bak")
        if backup.exists():
            backup.replace(LINUX_CONF)
            print(f"restored {LINUX_CONF}")
        else:
            LINUX_CONF.unlink()
            print(f"removed {LINUX_CONF}")
        removed = True
    if not removed and Path("/etc/systemd/resolved.conf.d").exists():
        print("nothing to remove (dnsctl.conf not present).")
    subprocess.run(["systemctl", "restart", "systemd-resolved"], capture_output=True, timeout=60)
    print("Linux DNS reset to default.")
    return 0


def linux_current_dns() -> list[str]:
    try:
        out = subprocess.run(["resolvectl", "status"], capture_output=True, text=True, timeout=15).stdout
        return sorted(set(re.findall(r"\d{1,3}(?:\.\d{1,3}){3}", out)))
    except Exception:
        return []


def current_dns() -> list[str]:
    if is_windows():
        return windows_current_dns()
    if is_macos():
        return macos_current_dns()
    if is_linux():
        return linux_current_dns()
    return []


def apply_dns(ips: list[str], doh_url: str | None, dot_host: str | None,
              service: str | None, dry_run: bool) -> int:
    if not ips:
        print("no IPs to apply")
        return 1
    if is_windows():
        return windows_set_dns(ips, doh_url, dry_run)
    if is_macos():
        return macos_set_dns(ips, service, dry_run)
    if is_linux():
        if linux_has_resolved():
            return linux_set_dns(ips, dot_host, dry_run)
        print("systemd-resolved not detected. Set upstream DNS manually:")
        print("  NetworkManager:  nmcli con mod <name> ipv4.dns '" + " ".join(ips) + "'")
        print("                  nmcli con up <name>")
        print("  Or see system/<profile>/dnsmasq.conf for dnsmasq/OpenWrt routers.")
        return 1
    print(f"unsupported platform: {sys.platform}")
    return 1


def reset_dns(service: str | None, dry_run: bool) -> int:
    if is_windows():
        return windows_reset_dns(dry_run)
    if is_macos():
        return macos_reset_dns(service, dry_run)
    if is_linux():
        return linux_reset_dns(dry_run)
    print(f"unsupported platform: {sys.platform}")
    return 1


# --------------------------------------------------------------------------- #
# Output helpers
# --------------------------------------------------------------------------- #
def hr(char: str = "-", width: int = 78) -> None:
    print(char * width)


def profile_summary_lines(doc: dict, p: dict) -> list[str]:
    return [
        f"{p.get('icon', '')} {p['name']}  [{p.get('badge', '')}]",
        f"  blocks : {', '.join(p.get('blocks', [])) or 'none'}",
        f"  keeps  : {', '.join(p.get('keeps', []))}",
        f"  android: {p.get('android')}",
        f"  doh    : {p.get('doh')}",
        f"  ipv4   : {', '.join(profile_ips(p))}",
        f"  notes  : {p['notes'][0] if p.get('notes') else ''}",
    ]


def mobile_steps(p: dict) -> str:
    lines = [
        f"== {p.get('icon', '')} {p['name']} — phone / tablet ==",
        "",
        "Android 9+ (Private DNS — manual switch, built into Android):",
        "  Settings → Network & internet → Private DNS",
        "  → 'Private DNS provider hostname' → enter:",
        f"      {p.get('android')}",
        "  → Save. Verify at https://1.1.1.1/help (should show 'Private DNS').",
        "  Switch anytime: same screen, pick another hostname (or Automatic to undo).",
        "",
        "iPhone / iPad (iOS 14+, encrypted DNS):",
        "  Option A: dnsctl.py export mobileconfig " + p["id"] + "  → install the file on the phone,",
        "            then Settings → General → VPN & Device Management → install.",
        "  Option B: use a DNS app that installs the profile (dns0, NextDNS, AdGuard…).",
        "  Plain (unencrypted) fallback: Wi-Fi → (i) → Configure DNS → Manual →",
        f"      {', '.join(profile_ips(p))}",
        "",
        f"DoH URL: {p.get('doh')}",
        f"IPv4   : {', '.join(profile_ips(p))}",
    ]
    return "\n".join(lines)


def mobileconfig_text(p: dict) -> str:
    ns = uuid.uuid4()
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">',
        '<plist version="1.0">',
        '<dict>',
        '  <key>PayloadVersion</key><integer>1</integer>',
        f'  <key>PayloadIdentifier</key><string>com.iamtanzir.dns.{p["id"]}</string>',
        f'  <key>PayloadUUID</key><string>{ns}</string>',
        '  <key>PayloadType</key><string>Configuration</string>',
        f'  <key>PayloadDisplayName</key><string>{p["name"]} DNS</string>',
        '  <key>PayloadDescription</key>',
        f'  <string>Encrypted DNS ({p["name"]}) — {p.get("doh")}</string>',
        '  <key>PayloadContent</key>',
        '  <array>',
        '    <dict>',
        '      <key>PayloadType</key><string>com.apple.dnsSettings.managed</string>',
        '      <key>PayloadVersion</key><integer>1</integer>',
        '      <key>PayloadIdentifier</key><string>com.iamtanzir.dns.settings</string>',
        f'      <key>PayloadUUID</key><string>{uuid.uuid4()}</string>',
        f'      <key>PayloadDisplayName</key><string>{p["name"]} DNS settings</string>',
        '      <key>DNSSettings</key>',
        '      <dict>',
        '        <key>Type</key><string>HTTPS</string>',
        f'        <key>ServerURL</key><string>{p["doh"]}</string>',
        '      </dict>',
        '    </dict>',
        '  </array>',
        '</dict>',
        '</plist>',
    ]
    return "\n".join(lines) + "\n"


def router_text(p: dict) -> str:
    ips = profile_ips(p)
    doh = p.get("doh")
    lines = [
        f"== {p.get('icon', '')} {p['name']} — router / whole home ==",
        "",
        "AdGuard Home → Settings → DNS settings → Upstream DNS servers:",
        f"  tls://{p.get('dot_host')}",
        f"  {doh}",
        "  Bootstrap DNS:",
        *[f"  {ip}" for ip in ips],
        "",
        "Pi-hole → Settings → DNS → Upstream DNS Servers → Custom:",
        *[f"  {ip}#{p.get('dot_host')}   # DoT (uncheck to use plain DNS)" for ip in ips],
        "",
        "dnsmasq / OpenWrt (5 lines):",
        *[f"  server={ip}#53     # or: address=/…" for ip in ips],
        "  (full-featured config lives in system/<profile>/dnsmasq.conf)",
        "",
        "OpenWrt /etc/config/stubby:",
        f"  list dns_transport 'GETDNS_TRANSPORT_TLS'",
        f"  list dns_addresses '{ips[0]}'" + (f", '{ips[1]}'" if len(ips) > 1 else ""),
        "",
        "Ready-to-run files (committed):  system/" + p["id"] + "/",
        "  windows-dns.ps1, macos-dns.sh, systemd-resolved.conf, stubby.yml,",
        "  dnsmasq.conf, adguardhome-upstreams.txt, pihole-upstreams.txt",
    ]
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #
def cmd_status(_args) -> int:
    cur = current_dns()
    plat = {"win32": "Windows", "darwin": "macOS"}.get(sys.platform, "Linux" if is_linux() else sys.platform)
    hr()
    print(f"Platform : {plat}")
    print(f"Current DNS servers: {', '.join(cur) if cur else 'automatic / DHCP (or none detected)'}")
    hr()
    doc = load_system()
    print("Profiles you can switch to (dnsctl.py use <id>):")
    for p in doc["profiles"]:
        print(f"  {p['id']:<12} {p.get('icon', ' ')} {p['name']:<18} ipv4: {', '.join(profile_ips(p))}")
    return 0


def cmd_test(args) -> int:
    doc = load_system()
    timeout = args.timeout
    targets = doc["profiles"]
    if args.profile:
        p = find_profile(doc, args.profile)
        if not p:
            print(f"unknown profile '{args.profile}'. Known: {describe_system_profiles(doc)}")
            return 1
        targets = [p]
    if args.all:
        entries = [e for prov in load_dns_servers()["providers"] for e in prov["hosts"]]
        print(f"Testing {len(entries)} endpoints — this takes a while…\n")
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            results = list(pool.map(lambda e: bench_endpoint(e, timeout), entries))
        results.sort(key=lambda r: (r["udp_ms"] is None, r["udp_ms"] or 9999))
        for r in results:
            print(f"{r['host']:<42} {fmt_ms(r['udp_ms'])} {bar(r['udp_ms'])}  dot={fmt_ms(r['dot_ms'])} doh={fmt_ms(r['doh_ms'])}")
        return 0

    print(f"Live benchmark of {len(targets)} profile(s)  (UDP/53, DoT, DoH)  —  {timeout:g}s timeout\n")
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(targets)) as pool:
        results = list(pool.map(lambda p: bench_profile(p, timeout), targets))
    results.sort(key=lambda r: (r["udp_avg"] is None, r["udp_avg"] or 99999))
    for r in results:
        udp = ", ".join(f"{v:.0f}" if v is not None else "timeout" for v in r["udp_ms"])
        print(f"{r['icon']} {r['name']:<16} udp=[{udp}]  avg={fmt_ms(r['udp_avg'])} {bar(r['udp_avg'])}  "
              f"dot={fmt_ms(r['dot_ms'])} ({r.get('dot_status', 'n/a')})  "
              f"doh={fmt_ms(r['doh_ms'])} ({r.get('doh_status', 'n/a')})")
    best = results[0] if results else None
    if best and best["udp_avg"] is not None:
        print(f"\nFastest right now: {best['icon']} {best['name']}  (avg {best['udp_avg']:.1f} ms)")
        print(f"Apply it with:  python scripts/dnsctl.py use {best['id']}")
    return 0


def cmd_fastest(args) -> int:
    doc = load_system()
    timeout = args.timeout
    print("Benchmarking profiles (UDP/53 to their anycast IPs)…\n")
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(doc["profiles"])) as pool:
        results = list(pool.map(lambda p: bench_profile(p, timeout), doc["profiles"]))
    results.sort(key=lambda r: (r["udp_avg"] is None, r["udp_avg"] or 99999))
    for r in results:
        print(f"{r['icon']} {r['name']:<16} avg={fmt_ms(r['udp_avg'])}  {bar(r['udp_avg'])}")
    winner = next((r for r in results if r["udp_avg"] is not None), None)
    if not winner:
        print("\nNo profile answered — are you online? (plain UDP/53 may be blocked on your network)")
        return 1
    print(f"\nWinner: {winner['icon']} {winner['name']}  ({winner['udp_avg']:.1f} ms)")
    if args.apply:
        p = next(p for p in doc["profiles"] if p["id"] == winner["id"])
        return apply_dns(profile_ips(p), p.get("doh"), p.get("dot_host"), args.service, dry_run=False)
    print(f"Apply it with:  python scripts/dnsctl.py fastest --apply   (or: use {winner['id']})")
    return 0


def cmd_watch(args) -> int:
    doc = load_system()
    targets = doc["profiles"]
    limit = args.count if args.count > 0 else None
    print(f"Live latency — refreshing every {args.interval}s"
          + (f" for {limit} round(s)" if limit else " (Ctrl+C to stop)") + "\n")
    rounds = 0
    try:
        while limit is None or rounds < limit:
            stamp = time.strftime("%H:%M:%S")
            row_bits = []
            for p in targets:
                ips = profile_ips(p)
                ms = [udp_query_ms(ip, timeout=args.timeout) for ip in ips]
                good = [m for m in ms if m is not None]
                avg = f"{sum(good) / len(good):6.1f} ms" if good else "  timeout"
                row_bits.append(f"{p['id'][:12]:<12} {avg}")
            print(f"{stamp}  " + " | ".join(row_bits))
            rounds += 1
            if limit is not None and rounds >= limit:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nstopped.")
        return 0
    return 0


def cmd_use(args) -> int:
    doc = load_system()
    profile = find_profile(doc, args.target) if args.target else None
    host_entry = None
    if not profile and args.target:
        host_entry = find_endpoint(load_dns_servers(), args.target)
    if profile:
        ips = profile_ips(profile)
        doh, dot_host = profile.get("doh"), profile.get("dot_host")
        print("\n".join(profile_summary_lines(doc, profile)))
        print()
    elif host_entry:
        ips = host_entry.get("ipv4") or []
        doh, dot_host = host_entry.get("doh"), host_entry["host"]
        if not ips:
            print(f"{host_entry['host']} has no published IPv4. Use its DoH URL instead: {doh}")
            return 1
        print(f"Endpoint: {host_entry['host']}  ({host_entry.get('label')})  ipv4: {', '.join(ips)}\n")
    elif args.ips:
        ips = [x.strip() for x in args.ips.split(",") if x.strip()]
        doh = dot_host = None
        print(f"Custom IPs: {', '.join(ips)}\n")
    else:
        print(f"unknown target '{args.target or ''}'.".rstrip())
        print(f"Profiles: {describe_system_profiles(doc)}")
        print("Or pass any hostname from the list (e.g. dns.google), or --ips 1.1.1.1,1.0.0.1")
        return 1
    return apply_dns(ips, doh, dot_host, args.service, dry_run=args.dry_run)


def cmd_reset(args) -> int:
    return reset_dns(args.service, dry_run=args.dry_run)


def cmd_mobile(args) -> int:
    doc = load_system()
    p = find_profile(doc, args.profile)
    if not p:
        print(f"unknown profile '{args.profile}'. Known: {describe_system_profiles(doc)}")
        return 1
    print(mobile_steps(p))
    return 0


def cmd_export(args) -> int:
    doc = load_system()
    p = find_profile(doc, args.profile)
    if not p:
        print(f"unknown profile '{args.profile}'. Known: {describe_system_profiles(doc)}")
        return 1
    if args.kind != "mobileconfig":
        print(f"unknown export '{args.kind}' (only 'mobileconfig')")
        return 1
    out = Path(args.out) if args.out else Path(f"{p['id']}-dns.mobileconfig")
    out.write_text(mobileconfig_text(p), encoding="utf-8", newline="\n")
    print(f"Wrote {out}  (install on iPhone/iPad/macOS to get {p['name']} DoH DNS)")
    return 0


def cmd_router(args) -> int:
    doc = load_system()
    p = find_profile(doc, args.profile)
    if not p:
        print(f"unknown profile '{args.profile}'. Known: {describe_system_profiles(doc)}")
        return 1
    print(router_text(p))
    return 0


# --------------------------------------------------------------------------- #
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--elevated", action="store_true", help=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("status", help="show current DNS")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("test", help="live latency benchmark (UDP/53, DoT, DoH)")
    p.add_argument("--profile", help="only this profile id (e.g. kahfguard)")
    p.add_argument("--all", action="store_true", help="benchmark every endpoint in the list (slow)")
    p.add_argument("--timeout", type=float, default=3.0)
    p.add_argument("--workers", type=int, default=16)
    p.set_defaults(func=cmd_test)

    p = sub.add_parser("fastest", help="benchmark profiles and pick the lowest latency")
    p.add_argument("--apply", action="store_true", help="apply the winner now")
    p.add_argument("--timeout", type=float, default=3.0)
    p.add_argument("--service", help="(macOS) network service name, default: Wi-Fi/first enabled")
    p.set_defaults(func=cmd_fastest)

    p = sub.add_parser("watch", help="live continuous latency monitor (Ctrl+C stops)")
    p.add_argument("--interval", type=float, default=5.0)
    p.add_argument("--timeout", type=float, default=2.0)
    p.add_argument("--count", type=int, default=0, help="stop after N rounds (0 = forever)")
    p.set_defaults(func=cmd_watch)

    p = sub.add_parser("use", help="apply a profile / endpoint / custom IPs to this device")
    p.add_argument("target", nargs="?", help="profile id (kids-guard, kahfguard…) or a hostname")
    p.add_argument("--ips", help="custom comma-separated IPv4s, e.g. --ips 1.1.1.1,1.0.0.1")
    p.add_argument("--service", help="(macOS) network service name")
    p.add_argument("--dry-run", action="store_true", help="print what would change, apply nothing")
    p.set_defaults(func=cmd_use)

    p = sub.add_parser("reset", help="back to DHCP / automatic DNS")
    p.add_argument("--service", help="(macOS) network service name")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_reset)

    p = sub.add_parser("mobile", help="Android Private DNS / iPhone steps for a profile")
    p.add_argument("profile")
    p.set_defaults(func=cmd_mobile)

    p = sub.add_parser("export", help="export files (iOS/macOS .mobileconfig)")
    p.add_argument("kind", help="mobileconfig")
    p.add_argument("profile")
    p.add_argument("--out", help="output file path")
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("router", help="router / AdGuard Home / Pi-hole upstreams for a profile")
    p.add_argument("profile")
    p.set_defaults(func=cmd_router)

    args = parser.parse_args()
    if os.environ.get("DNSCTL_ELEVATED") == "1" and getattr(args, "func", None) is None:
        pass
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
