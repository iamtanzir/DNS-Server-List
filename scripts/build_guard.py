#!/usr/bin/env python3
"""Generate the ShortsGuard blocklists and keep the browser extension in sync.

Source of truth: data/guard-profiles.json
Outputs:
  blocklists/shortsguard-ublock.txt        uBlock Origin cosmetic rules
  blocklists/shortsguard-adguard.txt       AdGuard browser cosmetic rules
  blocklists/shortsguard-adguardhome.txt   AdGuard Home DNS rules
  blocklists/shortsguard-hosts.txt         hosts format (Pi-hole, Windows, macOS)
  blocklists/shortsguard-dnsmasq.txt       dnsmasq / OpenWrt
  blocklists/shortsguard-domains.txt       plain domain list (NextDNS, pfSense…)
  guard/extension/shorts-guard.js          copy of the userscript for the MV3 build

Run:  python scripts/build_guard.py
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GUARD = ROOT / "data" / "guard-profiles.json"
BLOCKLISTS = ROOT / "blocklists"
USERSCRIPT = ROOT / "guard" / "shorts-guard.user.js"
EXTENSION = ROOT / "guard" / "extension"

# The "nuclear" group is intentionally never exported: it breaks the apps.
EXPORT_GROUPS = {"tiktok", "likee", "kwai", "snackvideo"}

HEADER = (
    "# ShortsGuard — generated from data/guard-profiles.json\n"
    "# Blocks whole short-video apps only. Facebook / Messenger / Instagram / YouTube stay up.\n"
    "# Reels and Shorts cannot be blocked at DNS level: they are paths on the same domains.\n"
)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    doc = json.loads(GUARD.read_text(encoding="utf-8"))

    rules = doc.get("rules") or {}
    required = ("ublock", "adguard", "adguardhome", "hosts", "dnsmasq")
    missing = [k for k in required if not rules.get(k)]
    if missing:
        raise SystemExit(f"guard-profiles.json is missing rule sets: {missing}")

    BLOCKLISTS.mkdir(exist_ok=True)
    outputs = {
        "shortsguard-ublock.txt": rules["ublock"],
        "shortsguard-adguard.txt": rules["adguard"],
        "shortsguard-adguardhome.txt": rules["adguardhome"],
        "shortsguard-hosts.txt": rules["hosts"],
        "shortsguard-dnsmasq.txt": rules["dnsmasq"],
    }
    for name, text in outputs.items():
        write(BLOCKLISTS / name, text)

    # Plain domain list for tools that want one domain per line (NextDNS, pfSense…).
    domains: list[str] = []
    for group in doc.get("domain_groups", []):
        if group["id"] not in EXPORT_GROUPS:
            continue
        for domain in group["domains"]:
            if domain not in domains:
                domains.append(domain)
    write(
        BLOCKLISTS / "shortsguard-domains.txt",
        HEADER + "\n" + "\n".join(domains) + "\n",
    )

    # Keep the MV3 extension's content script byte-identical to the userscript.
    if not USERSCRIPT.exists():
        raise SystemExit(f"Missing userscript: {USERSCRIPT}")
    EXTENSION.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(USERSCRIPT, EXTENSION / "shorts-guard.js")

    print(f"Wrote {len(outputs)} rule files + shortsguard-domains.txt ({len(domains)} domains)")
    print(f"Synced {USERSCRIPT.relative_to(ROOT)} -> {(EXTENSION / 'shorts-guard.js').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
