#!/usr/bin/env python3
"""Export a plain newline-separated list of DoT hostnames from data/dns-servers.json.

Android Private DNS, routers and many firewall UIs accept a plain hostname list.
Run:  python scripts/export_hosts.py            # writes hostnames.txt
      python scripts/export_hosts.py --doh      # only DoH-capable hosts
"""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "dns-servers.json"
OUT = ROOT / "hostnames.txt"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--doh", action="store_true", help="only DoH-capable endpoints")
    parser.add_argument("--all", action="store_true", help="include every endpoint regardless of protocol")
    args = parser.parse_args()

    doc = json.loads(DATA.read_text(encoding="utf-8"))
    hosts: list[str] = []
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
            hosts.append(entry["host"])

    OUT.write_text(
        "# Private DNS hostnames — generated from data/dns-servers.json\n"
        "# Pick ONE and paste it into your Private DNS / DoT settings. Do not paste the whole list.\n"
        + "\n".join(hosts)
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(hosts)} hostnames to {OUT}")


if __name__ == "__main__":
    main()
