#!/usr/bin/env bash
# Family Safe — macOS system DNS
set -euo pipefail
SERVICE="${1:-Wi-Fi}"
PRIMARY='1.1.1.3'
SECONDARY='1.0.0.3'
sudo networksetup -setdnsservers "$SERVICE" "$PRIMARY" "$SECONDARY"
sudo dscacheutil -flushcache
echo "DNS set on $SERVICE: $PRIMARY $SECONDARY"
echo 'macOS has no native DoH. Install a DoH profile with: https://family.cloudflare-dns.com/dns-query'
