#!/usr/bin/env python3
"""Build the self-contained index.html from site/template.html + the data files.

Three JSON blobs are inlined so the site works offline (file://) and on GitHub
Pages without a backend:

  data/dns-servers.json    -> __DNS_DATA__
  data/guard-profiles.json -> __GUARD_DATA__
  data/health.json         -> __HEALTH_DATA__   (optional; {} when absent)

Run:  python scripts/build_site.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "site" / "template.html"
OUT = ROOT / "index.html"

SOURCES = {
    "__DNS_DATA__": ROOT / "data" / "dns-servers.json",
    "__GUARD_DATA__": ROOT / "data" / "guard-profiles.json",
    "__HEALTH_DATA__": ROOT / "data" / "health.json",
}
OPTIONAL = {"__HEALTH_DATA__"}


def main() -> None:
    template = TEMPLATE.read_text(encoding="utf-8")

    for placeholder, path in SOURCES.items():
        if placeholder not in template:
            raise SystemExit(f"Placeholder {placeholder} not found in {TEMPLATE}")

        if not path.exists():
            if placeholder in OPTIONAL:
                obj = {}
            else:
                raise SystemExit(f"Missing data file: {path}")
        else:
            obj = json.loads(path.read_text(encoding="utf-8"))

        # Compact JSON; escape "</" so the block cannot terminate early.
        payload = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        template = template.replace(placeholder, payload)

    OUT.write_text(template, encoding="utf-8", newline="\n")

    data = json.loads(SOURCES["__DNS_DATA__"].read_text(encoding="utf-8"))
    guard = json.loads(SOURCES["__GUARD_DATA__"].read_text(encoding="utf-8"))
    endpoints = sum(len(p["hosts"]) for p in data["providers"])
    print(
        f"Wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size:,} bytes, "
        f"{len(data['providers'])} providers, {endpoints} endpoints, "
        f"{len(guard['profiles'])} guard profiles)"
    )


if __name__ == "__main__":
    main()
