#!/usr/bin/env python3
"""Export plain lists from data/dns-servers.json.

Android Private DNS, routers and many firewall UIs accept a plain hostname
list, one per line.

Usage
  python scripts/export_hosts.py                     # DoT hostnames -> hostnames.txt
  python scripts/export_hosts.py --doh               # DoH URLs -> hostnames-doh.txt
  python scripts/export_hosts.py --all               # every hostname -> hostnames-all.txt
  python scripts/export_hosts.py --filter ads        # only ad-blocking endpoints
  python scripts/export_hosts.py --filter ads --filter malware
  python scripts/export_hosts.py --region germany
  python scripts/export_hosts.py --out my-list.txt

Filters are ANDed. `--filter none` selects unfiltered resolvers.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "dns-servers.json"
FILTERS = ("none", "ads", "malware", "adult", "social")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--doh", action="store_true", help="write DoH URLs instead of DoT hostnames")
    parser.add_argument("--all", action="store_true", help="include every endpoint regardless of protocol")
    parser.add_argument("--filter", action="append", choices=FILTERS, default=[], help="require this filter (repeatable)")
    parser.add_argument("--region", help="only endpoints in this region")
    parser.add_argument("--out", type=Path, help="output file (default depends on the mode)")
    args = parser.parse_args()

    doc = json.loads(DATA.read_text(encoding="utf-8"))
    lines: list[str] = []
    for provider in doc["providers"]:
        for entry in provider["hosts"]:
            proto = entry["protocol"]
            if not args.all:
                if args.doh:
                    if proto not in ("doh", "dot+doh"):
                        continue
                else:  # default: DoT (Android Private DNS)
                    if proto not in ("dot", "dot+doh"):
                        continue
            if args.filter and not all(f in entry["filters"] for f in args.filter):
                continue
            if args.region and entry.get("region") != args.region:
                continue

            if args.doh:
                if not entry.get("doh"):
                    continue
                lines.append(entry["doh"])
            else:
                lines.append(entry["host"])

    if args.out:
        out = args.out
    elif args.doh:
        out = ROOT / "hostnames-doh.txt"
    elif args.all:
        out = ROOT / "hostnames-all.txt"
    else:
        out = ROOT / "hostnames.txt"

    what = "DoH URLs" if args.doh else "hostnames"
    header = (
        f"# Private DNS {what} — generated from data/dns-servers.json\n"
        "# Pick ONE line and paste it into your Private DNS / DoT / DoH settings.\n"
        "# Do not paste the whole list.\n"
    )
    out.write_text(header + "\n".join(lines) + ("\n" if lines else ""), encoding="utf-8", newline="\n")
    print(f"Wrote {len(lines)} {what} to {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}")


if __name__ == "__main__":
    main()
