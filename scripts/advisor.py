#!/usr/bin/env python3
"""Offline Smart Advisor — pick the best free encrypted resolver for your device.

The same deterministic scoring model that powers the website's advisor, usable
from a terminal. It reads data/dns-servers.json and (if present) the live
snapshot in data/health.json. Nothing leaves your machine.

Examples
  python scripts/advisor.py
  python scripts/advisor.py --device android --region bangladesh --block ads --block malware
  python scripts/advisor.py --device browser --region europe --privacy --top 5
  python scripts/advisor.py --device android --keep facebook --keep messenger --keep youtube --focus
  python scripts/advisor.py --json

Important: no DNS resolver can block Facebook Reels, Instagram Reels or YouTube
Shorts while keeping those apps — those are paths, not domains. Use --focus and
install guard/shorts-guard.user.js for that part.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "dns-servers.json"
HEALTH = ROOT / "data" / "health.json"

DEVICES = {
    "android": ("Android Private DNS", {"dot"}),
    "ios": ("iPhone / iPad", {"doh"}),
    "windows": ("Windows 11", {"doh"}),
    "macos": ("macOS", {"dot", "doh"}),
    "linux": ("Linux", {"dot"}),
    "browser": ("Browser", {"doh"}),
    "router": ("Router / whole network", {"dot", "doh"}),
}

# Nearby regions get partial credit so a Bangladeshi user still sees Singapore
# and India endpoints ranked above a random EU node.
REGION_GROUPS = {
    "bangladesh": {"bangladesh", "india", "singapore", "hong-kong"},
    "india": {"india", "singapore"},
    "singapore": {"singapore", "indonesia", "hong-kong", "india"},
    "indonesia": {"indonesia", "singapore"},
    "japan": {"japan", "taiwan", "hong-kong"},
    "taiwan": {"taiwan", "japan", "hong-kong"},
    "china": {"china", "hong-kong", "taiwan", "japan"},
    "hong-kong": {"hong-kong", "taiwan", "singapore", "japan"},
    "russia": {"russia"},
    "europe": {"germany", "switzerland", "greece", "denmark", "czechia", "sweden"},
    "germany": {"germany", "switzerland", "czechia", "denmark"},
    "switzerland": {"switzerland", "germany"},
    "usa": {"usa", "canada"},
    "canada": {"canada", "usa"},
    "global": set(),
}

BLOCKS = ("ads", "malware", "adult", "social")
KEEPS = ("facebook", "messenger", "youtube", "instagram", "tiktok")
PROTO_LABEL = {"dot": "DoT :853", "doh": "DoH :443", "dot+doh": "DoT + DoH"}


def load() -> tuple[dict, dict]:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    health = {}
    if HEALTH.exists():
        try:
            health = json.loads(HEALTH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            health = {}
    return data, health


def entries(data: dict):
    for provider in data["providers"]:
        for entry in provider["hosts"]:
            yield provider, entry


def score(provider: dict, entry: dict, health: dict, args) -> tuple[float, list[str]]:
    h = (health.get("results") or {}).get(entry["host"]) or {}
    if h.get("overall") == "dead":
        return float("-inf"), ["dead"]

    allowed = DEVICES[args.device][1]
    if not allowed.intersection({"dot"} if entry["protocol"] == "dot" else {"doh"} if entry["protocol"] == "doh" else {"dot", "doh"}):
        return float("-inf"), ["wrong protocol"]

    filters = set(entry["filters"])
    if "social" in args.block and "social" not in filters:
        return float("-inf"), ["no social filter"]
    if "social" not in args.block and "social" in filters and args.keep:
        return float("-inf"), ["blocks the apps you keep"]

    points = 50.0
    why: list[str] = []

    for goal in args.block:
        if goal in filters:
            points += 26
            why.append(f"blocks {goal}")
        else:
            points -= 34

    if not args.block:
        if filters == {"none"}:
            points += 18
            why.append("no filtering")
        else:
            points -= 8

    if "ads" not in args.block and "ads" in filters:
        points -= 6
    if "adult" not in args.block and "adult" in filters:
        points -= 4

    if args.privacy:
        if provider.get("privacy") == "no-log":
            points += 18
            why.append("no-log")
        elif provider.get("privacy") == "minimal-log":
            points += 5
        else:
            points -= 8

    group = REGION_GROUPS.get(args.region, {args.region})
    if entry["region"] == args.region:
        points += 26
        why.append("your region")
    elif entry["region"] in group:
        points += 14
        why.append("nearby region")
    elif entry["region"] == "global":
        points += 9

    if h.get("overall") == "ok":
        points += 16
        why.append("live now")
    elif h.get("overall") == "partial":
        points += 4
        why.append("partly live")
    if entry.get("doh"):
        points += 2

    return points, why


def setup_steps(device: str, entry: dict) -> list[str]:
    host = entry["host"]
    doh = entry.get("doh")
    ipv4 = entry.get("ipv4") or ["1.1.1.1", "1.0.0.1"]
    if device == "android":
        return [
            "Settings -> Network & internet -> Private DNS",
            "Choose 'Private DNS provider hostname'",
            f"Paste {host} and tap Save",
            "Verify at https://1.1.1.1/help (should say DoT)",
        ]
    if device == "ios":
        return [
            "Install a DoH profile app (DNSecure) or a .mobileconfig profile",
            f"Use the DoH URL {doh}" if doh else "This endpoint has no DoH URL - pick another",
        ]
    if device == "windows":
        return [
            "Settings -> Network & internet -> DNS server assignment -> Edit",
            f"Preferred {ipv4[0]}, Alternate {ipv4[1] if len(ipv4) > 1 else '1.0.0.1'}",
            "Preferred DNS encryption: Encrypted only (DNS over HTTPS)",
            f"Paste {doh}" if doh else "No DoH URL - pick a DoT+DoH resolver",
        ]
    if device == "macos":
        return [
            "System Settings -> Network -> Details... -> DNS",
            "Add " + " / ".join(ipv4[:2]),
            f"Encrypted DNS: install a DoH profile with {doh}" if doh else "Use stubby for DoT",
        ]
    if device == "linux":
        return [
            "Create /etc/systemd/resolved.conf.d/dns.conf",
            f"DNS={ipv4[0]}#{host}",
            "DNSOverTLS=yes",
            "sudo systemctl restart systemd-resolved && resolvectl status",
        ]
    if device == "browser":
        return [
            "Chrome/Edge: Settings -> Privacy and security -> Security -> Use secure DNS -> Custom",
            f"Paste {doh}" if doh else "This endpoint is DoT-only; browsers need DoH",
        ]
    return [
        "AdGuard Home -> Settings -> DNS settings -> Upstream DNS servers",
        f"Add tls://{host}",
        "Point your DHCP DNS at the router",
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--device", choices=DEVICES, default="android")
    parser.add_argument("--region", default="global", choices=sorted(REGION_GROUPS))
    parser.add_argument("--block", action="append", choices=BLOCKS, default=[])
    parser.add_argument("--keep", action="append", choices=KEEPS, default=list(KEEPS))
    parser.add_argument("--privacy", action="store_true", help="prefer no-log providers")
    parser.add_argument("--focus", action="store_true", help="also print the Reels/Shorts setup")
    parser.add_argument("--top", type=int, default=3)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    data, health = load()
    ranked = []
    for provider, entry in entries(data):
        points, why = score(provider, entry, health, args)
        if points == float("-inf"):
            continue
        ranked.append((points, provider, entry, why))
    ranked.sort(key=lambda row: (-row[0], row[2]["host"]))

    if not ranked:
        print("No endpoint matches those constraints. Try --block ads only, or a different --device.")
        return 1

    top = ranked[: args.top]
    if args.json:
        print(json.dumps([
            {
                "score": round(points, 1),
                "provider": provider["name"],
                "host": entry["host"],
                "doh": entry.get("doh"),
                "protocol": entry["protocol"],
                "region": entry["region"],
                "why": why,
                "setup": setup_steps(args.device, entry),
            }
            for points, provider, entry, why in top
        ], indent=2))
        return 0

    print(f"Device : {DEVICES[args.device][0]}")
    print(f"Region : {args.region}")
    print(f"Block  : {', '.join(args.block) if args.block else 'nothing'}")
    print(f"Keep   : {', '.join(args.keep) if args.keep else '—'}")
    print()

    if "social" in args.block and args.keep:
        print("WARNING: DNS-level social blocking blocks Facebook/Instagram/TikTok/Messenger")
        print("         as whole domains. If those apps must work, drop --block social and")
        print("         use ShortsGuard (--focus) for the Reels/Shorts surfaces.\n")

    for i, (points, provider, entry, why) in enumerate(top, 1):
        print(f"{i}. {provider['name']} — {entry['host']}  (score {points:.0f})")
        print(f"   {entry['label']} · {PROTO_LABEL[entry['protocol']]} · {entry['region']} · privacy {provider.get('privacy', 'unknown')}")
        print(f"   why: {', '.join(why) if why else 'balanced match'}")
        if entry.get("doh"):
            print(f"   DoH: {entry['doh']}")
        for step in setup_steps(args.device, entry):
            print(f"     - {step}")
        print()

    if args.focus:
        print("Reels / Shorts: DNS cannot block a path. Install the page-level guard:")
        print("  https://github.com/iamtanzir/DNS-Server-List  ->  ShortsGuard")
        print("  guard/shorts-guard.user.js  (Tampermonkey / Violentmonkey)")
        print("  blocklists/shortsguard-ublock.txt  (uBlock Origin -> My filters)")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
