#!/usr/bin/env python3
"""Validate data/dns-servers.json and report a summary.

Checks:
  * JSON parses and has the expected top-level shape
  * required fields on providers and hosts
  * hostnames look like valid DNS names
  * hostnames are unique across the whole file
  * filter / protocol vocabularies are respected

Exits non-zero if any error is found. Run:  python scripts/validate.py
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "dns-servers.json"

HOST_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[a-z0-9-]{1,63}(?<!-)(\.(?!-)[a-z0-9-]{1,63}(?<!-))*$"
)
VALID_FILTERS = {"none", "ads", "malware", "adult", "social"}
VALID_PROTOCOLS = {"dot", "doh", "dot+doh"}

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def main() -> int:
    try:
        doc = json.loads(DATA.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"ERROR: {DATA} not found")
        return 1
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON in {DATA}: {exc}")
        return 1

    providers = doc.get("providers")
    if not isinstance(providers, list) or not providers:
        err("'providers' must be a non-empty list")
        providers = []

    seen_hosts: dict[str, str] = {}
    host_count = 0

    for i, provider in enumerate(providers):
        where = provider.get("name") or provider.get("id") or f"providers[{i}]"
        for field in ("id", "name", "hosts"):
            if not provider.get(field):
                err(f"{where}: missing required field '{field}'")

        hosts = provider.get("hosts") or []
        if not isinstance(hosts, list) or not hosts:
            err(f"{where}: 'hosts' must be a non-empty list")
            continue

        for j, entry in enumerate(hosts):
            host = (entry or {}).get("host", "")
            tag = f"{where} -> hosts[{j}] ({host or 'no host'})"

            if not host:
                err(f"{tag}: missing 'host'")
                continue
            host = host.strip().lower()
            if not HOST_RE.match(host):
                err(f"{tag}: '{host}' is not a valid DNS hostname")
            if host in seen_hosts:
                err(f"{tag}: duplicate host (already used by {seen_hosts[host]})")
            seen_hosts[host] = where
            host_count += 1

            protocol = entry.get("protocol")
            if protocol not in VALID_PROTOCOLS:
                err(f"{tag}: protocol '{protocol}' not in {sorted(VALID_PROTOCOLS)}")

            filters = entry.get("filters")
            if not isinstance(filters, list) or not filters:
                err(f"{tag}: 'filters' must be a non-empty list")
            else:
                bad = [f for f in filters if f not in VALID_FILTERS]
                if bad:
                    err(f"{tag}: unknown filters {bad}")
                if "none" in filters and len(filters) > 1:
                    warn(f"{tag}: 'none' combined with other filters")

            for field in ("label", "region"):
                if not str(entry.get(field, "")).strip():
                    warn(f"{tag}: empty '{field}'")

    print(f"Providers : {len(providers)}")
    print(f"Endpoints : {host_count}")
    print(f"Warnings  : {len(warnings)}")
    for w in warnings:
        print(f"  warn: {w}")

    if errors:
        print(f"\n{len(errors)} error(s):")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("\nOK — data file is valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
