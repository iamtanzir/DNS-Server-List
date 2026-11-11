#!/usr/bin/env bash
# Kahf Guard — macOS system DNS
set -euo pipefail
SERVICE="${1:-Wi-Fi}"
PRIMARY='142.132.207.231'
SECONDARY='157.90.95.113'
sudo networksetup -setdnsservers "$SERVICE" "$PRIMARY" "$SECONDARY"
sudo dscacheutil -flushcache
echo "DNS set on $SERVICE: $PRIMARY $SECONDARY"
echo 'macOS has no native DoH. Install a DoH profile with: https://medium.kahfguard.com/dns-query'
