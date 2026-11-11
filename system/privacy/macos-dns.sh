#!/usr/bin/env bash
# Privacy (no-log) — macOS system DNS
set -euo pipefail
SERVICE="${1:-Wi-Fi}"
PRIMARY='9.9.9.9'
SECONDARY='149.112.112.112'
sudo networksetup -setdnsservers "$SERVICE" "$PRIMARY" "$SECONDARY"
sudo dscacheutil -flushcache
echo "DNS set on $SERVICE: $PRIMARY $SECONDARY"
echo 'macOS has no native DoH. Install a DoH profile with: https://dns.quad9.net/dns-query'
