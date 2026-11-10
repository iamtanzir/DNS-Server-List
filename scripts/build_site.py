#!/usr/bin/env python3
"""Build the self-contained index.html from site/template.html + data/dns-servers.json.

The JSON is inlined into a <script type="application/json"> block so the site
works offline (file://) and on GitHub Pages without a backend.

Run:  python scripts/build_site.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "site" / "template.html"
DATA = ROOT / "data" / "dns-servers.json"
OUT = ROOT / "index.html"
PLACEHOLDER = "__DNS_DATA__"


def main() -> None:
    template = TEMPLATE.read_text(encoding="utf-8")
    data = json.loads(DATA.read_text(encoding="utf-8"))
    # Compact JSON; escape "</" so the block cannot terminate early.
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    if PLACEHOLDER not in template:
        raise SystemExit(f"Placeholder {PLACEHOLDER} not found in {TEMPLATE}")

    OUT.write_text(template.replace(PLACEHOLDER, payload), encoding="utf-8")
    print(f"Wrote {OUT} ({OUT.stat().st_size:,} bytes, {len(data['providers'])} providers)")


if __name__ == "__main__":
    main()
