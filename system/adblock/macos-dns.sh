#!/usr/bin/env bash
# Ad Block — macOS system DNS
set -euo pipefail
SERVICE="${1:-Wi-Fi}"
PRIMARY='94.140.14.14'
SECONDARY='94.140.15.15'
sudo networksetup -setdnsservers "$SERVICE" "$PRIMARY" "$SECONDARY"
sudo dscacheutil -flushcache
echo "DNS set on $SERVICE: $PRIMARY $SECONDARY"
echo 'macOS has no native DoH. Install a DoH profile with: https://dns.adguard-dns.com/dns-query'
