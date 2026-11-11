# 🛡️ Private DNS Server List + ShortsGuard

**A live-verified collection of free public DNS-over-TLS (DoT) and DNS-over-HTTPS (DoH) resolvers — plus a page-level guard that hides Facebook Reels, Instagram Reels and YouTube Shorts while keeping the normal apps, feeds, DMs and Messenger working.**

[![Validate DNS data](https://github.com/iamtanzir/DNS-Server-List/actions/workflows/validate.yml/badge.svg)](https://github.com/iamtanzir/DNS-Server-List/actions/workflows/validate.yml)
[![Health check](https://github.com/iamtanzir/DNS-Server-List/actions/workflows/health.yml/badge.svg)](https://github.com/iamtanzir/DNS-Server-List/actions/workflows/health.yml)
[![GitHub Pages](https://img.shields.io/badge/demo-interactive%20list-58a6ff)](https://iamtanzir.github.io/DNS-Server-List/)
[![License: MIT](https://img.shields.io/badge/license-MIT-3fb950)](LICENSE)
[![Endpoints](https://img.shields.io/badge/endpoints-67%20%2F%2038%20providers-d2a8ff)](data/dns-servers.json)
[![Health](https://img.shields.io/badge/last%20check-64%20healthy%20%C2%B7%203%20partial%20%C2%B7%200%20dead-3fb950)](data/health.json)

🌐 **Live interactive site:** <https://iamtanzir.github.io/DNS-Server-List/> — search 67 endpoints, filter by capability, copy any hostname, run the **Smart Advisor**, build a **full DNS system** for every device, and install **ShortsGuard** from one page.

> বাংলায় পড়ুন: [দ্রুত শুরু (বাংলা গাইড)](#-বাংলা-গাইড) — Android Private DNS, ShortsGuard এবং Smart Advisor-এর ধাপে ধাপে নির্দেশনা।

---

## 📑 Contents

- [What this repo actually does](#-what-this-repo-actually-does)
- [Why encrypted DNS?](#-why-encrypted-dns)
- [Quick start — Android Private DNS](#-quick-start--android-private-dns)
- [Quick picks](#-quick-picks)
- [The full list (67 endpoints / 38 providers)](#-the-full-list)
- [ShortsGuard — Reels & Shorts blocked, apps kept](#-shortsguard--reels--shorts-blocked-apps-kept)
- [Full DNS System — one profile, every device](#-full-dns-system--one-profile-every-device)
- [dnsctl — switch DNS on any device, with live ping & latency](#️-dnsctl--switch-dns-on-any-device-with-live-ping--latency)
- [Smart Advisor](#-smart-advisor)
- [Live health checks](#-live-health-checks)
- [DoT vs DoH — which one do I need?](#-dot-vs-doh--which-one-do-i-need)
- [Setup on other platforms](#-setup-on-other-platforms)
- [Interactive website](#-interactive-website)
- [Repository structure](#-repository-structure)
- [Contributing](#-contributing)
- [FAQ](#-faq)
- [বাংলা গাইড](#-বাংলা-গাইড)
- [⚠️ Disclaimer](#️-disclaimer)

---

## 🎯 What this repo actually does

There are two layers, and they solve different problems:

| Layer | Technology | What it can do | What it **cannot** do |
|---|---|---|---|
| **DNS resolver** | DoT / DoH | Encrypt lookups; block whole domains (ads, malware, adult, entire apps) for every app on the device | Block a **path** such as `/reel/`, `/reels/` or `/shorts/` |
| **ShortsGuard** | Userscript / MV3 extension / uBlock rules | Hide the Reels & Shorts **surfaces** inside the page and redirect their URLs | Work without a browser extension or content blocker |

That split is the honest answer to the most common request:

> “Facebook should work, but Facebook Reels should be blocked. YouTube should work, but Shorts should be blocked. Instagram should work, but Reels should be blocked. TikTok should work. Messenger should work.”

**DNS alone cannot do that.** `facebook.com/reel/123`, `youtube.com/shorts/abc` and `instagram.com/reels/xyz` live on the **same domains** as the normal feed. Blocking `fbcdn.net`, `cdninstagram.com` or `googlevideo.com` to kill short videos also kills every photo, story, normal video and Messenger attachment. ShortsGuard handles the page-level part; DNS handles device-wide ads / malware / adult filtering and optional whole-app blocks.

A third, packaging layer — the **Full DNS System** — turns one protection profile into exact settings and ready-to-run configs for Android, iPhone, Windows, macOS, Linux, a whole-home router and a browser.

---

## ❓ Why encrypted DNS?

Plain DNS (port 53) is **unencrypted and unauthenticated** — your ISP, Wi-Fi operator or anyone on the network can see and tamper with every domain you look up. Encrypted DNS fixes this:

| Protocol | Port | Analogy | Best for |
|----------|------|---------|----------|
| **DoT** — DNS over TLS | 853 | VPN for DNS | Android *Private DNS*, routers, system-wide DoT |
| **DoH** — DNS over HTTPS | 443 | Normal HTTPS traffic | Browsers, OSes with DoH support, restrictive networks |

Benefits: privacy (the network cannot snoop your lookups), integrity (no DNS spoofing/poisoning), and optional **content filtering** — ads, trackers, malware, phishing or adult sites blocked at the DNS level for *every app*, with no app-by-app setup.

---

## ⚡ Quick start — Android Private DNS

1. Open **Settings → Network & internet → Private DNS**
   *(some phones: Settings → Connections → More connection settings → Private DNS)*
2. Select **Private DNS provider hostname**
3. Paste **ONE** hostname, for example:
   ```
   dns.adguard-dns.com
   ```
4. Tap **Save** — done. All apps now use encrypted DNS.

> ⚠️ **Paste only one hostname.** Do not paste the whole list.
> ⚠️ Hostnames marked **DoH only** do not work in Android Private DNS — use them in browser/OS DoH settings. Everything marked **DoT** or **DoT+DoH** works.

Verify: open <https://1.1.1.1/help> and confirm it says *“Using DNS over TLS (DoT)”*.

---

## 🎯 Quick picks

| You want… | Use this hostname |
|---|---|
| Best all-round speed + privacy | `1dot1dot1dot1.cloudflare-dns.com` |
| Block malware everywhere | `security.cloudflare-dns.com` or `dns.quad9.net` |
| Block **ads** device-wide | `dns.adguard-dns.com` |
| Family-safe (ads + adult) | `family.cloudflare-dns.com` or `dns-family.adguard.com` |
| Family + ads + gambling + SafeSearch | `medium.kahfguard.com` (Kahf Guard) |
| Ad + malware block, Germany | `dnsforge.de` |
| No-log, non-profit | `dns.quad9.net` (`dns10.quad9.net` = unfiltered) |
| No-log, EU, Wikimedia | `wikimedia-dns.org` |
| China users | `dns.alidns.com` (AliDNS) or `dot.pub` (DNSPod) |
| Japan users | `public.dns.iij.jp` |
| Taiwan users | `dns.twnic.tw` |
| Indonesia users | `dns.bebasid.com` |
| Custom blocklists, per device | [NextDNS](https://nextdns.io) — `dns.nextdns.io` |
| Keep Facebook/YouTube/Instagram but hide Reels/Shorts | **DNS cannot do this** — use [ShortsGuard](#-shortsguard--reels--shorts-blocked-apps-kept) |
| Block social media completely (breaks the apps) | `p3.freedns.controld.com` — opt-in only |

---

## 📋 The full list

**Protocol key:** `DoT` = Android Private DNS · `DoH` = browser/OS HTTPS DNS · `DoT+DoH` = both.
**Filters key:** `none` = unfiltered · `ads` = ad/tracker blocking · `malware` = malware/phishing · `adult` = adult content · `social` = social-media domains (blocks whole apps).

Every endpoint below answered a real DNS query when it was added. Dead services are removed instead of being left to fail silently. The machine-readable source of truth is [`data/dns-servers.json`](data/dns-servers.json); the live health snapshot is [`data/health.json`](data/health.json).

| # | Provider | Hostname | Protocol | Filters | Region |
|---|----------|----------|----------|---------|--------|
| 1 | Cloudflare | `1dot1dot1dot1.cloudflare-dns.com` | DoT+DoH | none | global |
| 2 | Cloudflare | `one.one.one.one` | DoT+DoH | none | global |
| 3 | Cloudflare | `family.cloudflare-dns.com` | DoT+DoH | malware, adult | global |
| 4 | Cloudflare | `security.cloudflare-dns.com` | DoT+DoH | malware | global |
| 5 | Google Public DNS | `dns.google` | DoT+DoH | none | global |
| 6 | Quad9 | `dns.quad9.net` | DoT+DoH | malware | global |
| 7 | Quad9 | `dns9.quad9.net` | DoT+DoH | none | global |
| 8 | Quad9 | `dns10.quad9.net` | DoT+DoH | none | global |
| 9 | Quad9 | `dns11.quad9.net` | DoT+DoH | malware | global |
| 10 | AdGuard DNS | `dns.adguard-dns.com` | DoT+DoH | ads | global |
| 11 | AdGuard DNS | `dns-family.adguard.com` | DoT+DoH | ads, adult | global |
| 12 | AdGuard DNS | `dns-unfiltered.adguard.com` | DoT+DoH | none | global |
| 13 | AdGuard DNS | `dns.adguard.com` | DoT+DoH | ads | global |
| 14 | ControlD (Free DNS) | `p0.freedns.controld.com` | DoT+DoH | none | global |
| 15 | ControlD (Free DNS) | `p1.freedns.controld.com` | DoT+DoH | malware | global |
| 16 | ControlD (Free DNS) | `p2.freedns.controld.com` | DoT+DoH | malware, ads | global |
| 17 | ControlD (Free DNS) | `p3.freedns.controld.com` | DoT+DoH | malware, ads, social | global |
| 18 | Mullvad DNS | `doh.mullvad.net` | DoT+DoH | none | global |
| 19 | Mullvad DNS | `adblock.doh.mullvad.net` | DoT+DoH | ads | global |
| 20 | NextDNS | `dns.nextdns.io` | DoT+DoH | none | global |
| 21 | NextDNS | `anycast.dns.nextdns.io` | DoT+DoH | none | global |
| 22 | CleanBrowsing | `family-filter-dns.cleanbrowsing.org` | DoT+DoH | adult, malware | global |
| 23 | CleanBrowsing | `adult-filter-dns.cleanbrowsing.org` | DoT+DoH | adult | global |
| 24 | CleanBrowsing | `security-filter-dns.cleanbrowsing.org` | DoT+DoH | malware | global |
| 25 | OpenDNS (Cisco Umbrella) | `dns.opendns.com` | DoT+DoH | malware | global |
| 26 | OpenDNS (Cisco Umbrella) | `familyshield.opendns.com` | DoT+DoH | malware, adult | global |
| 27 | DNS.SB | `dot.sb` | DoT | none | hong-kong |
| 28 | DNS.SB | `doh.sb` | DoH | none | hong-kong |
| 29 | Wikimedia DNS | `wikimedia-dns.org` | DoT+DoH | none | global |
| 30 | Hurricane Electric | `ordns.he.net` | DoT+DoH | none | global |
| 31 | Yandex DNS | `common.dot.dns.yandex.net` | DoT | none | russia |
| 32 | TWNIC Public DNS | `dns.twnic.tw` | DoT+DoH | none | taiwan |
| 33 | BebasDNS (BebasID) | `dns.bebasid.com` | DoT+DoH | none | indonesia |
| 34 | dismail.de DNS | `fdns1.dismail.de` | DoT+DoH | none | germany |
| 35 | dismail.de DNS | `fdns2.dismail.de` | DoT+DoH | none | germany |
| 36 | CIRA Canadian Shield | `private.canadianshield.cira.ca` | DoT | none | canada |
| 37 | CIRA Canadian Shield | `protected.canadianshield.cira.ca` | DoT | malware | canada |
| 38 | CIRA Canadian Shield | `family.canadianshield.cira.ca` | DoT | malware, adult | canada |
| 39 | SWITCH DNS | `dns.switch.ch` | DoT+DoH | none | switzerland |
| 40 | CZ.NIC ODVR | `odvr.nic.cz` | DoT | none | czechia |
| 41 | IIJ Public DNS | `public.dns.iij.jp` | DoT | none | japan |
| 42 | AliDNS (Alibaba) | `dns.alidns.com` | DoT+DoH | none | china |
| 43 | DNSPod Public DNS+ | `dot.pub` | DoT | none | china |
| 44 | DNSPod Public DNS+ | `doh.pub` | DoH | none | china |
| 45 | 360 Secure DNS | `dot.360.cn` | DoT | malware | china |
| 46 | 360 Secure DNS | `doh.360.cn` | DoH | malware | china |
| 47 | Comss One DNS | `dns.comss.one` | DoT+DoH | none | russia |
| 48 | DNS For Family | `dns-dot.dnsforfamily.com` | DoT | adult | global |
| 49 | BlahDNS | `dot-de.blahdns.com` | DoT | none | germany |
| 50 | BlahDNS | `doh-de.blahdns.com` | DoH | none | germany |
| 51 | DNS Forge | `dnsforge.de` | DoT+DoH | ads, malware | germany |
| 52 | FFMUC DNS | `dot.ffmuc.net` | DoT+DoH | none | germany |
| 53 | Digitale Gesellschaft DNS | `dns.digitale-gesellschaft.ch` | DoT+DoH | none | switzerland |
| 54 | LibreDNS | `dot.libredns.gr` | DoT | none | greece |
| 55 | LibreDNS | `doh.libredns.gr` | DoH | none | greece |
| 56 | DeCloudUs DNS | `dns.decloudus.com` | DoT | none | usa |
| 57 | ibksturm DNS | `ibksturm.synology.me` | DoT | none | germany |
| 58 | DNS Privacy (Stubby / no-log projects) | `getdnsapi.net` | DoT | none | global |
| 59 | DNS Privacy (Stubby / no-log projects) | `dns.cmrg.net` | DoT | none | global |
| 60 | DNS Privacy (Stubby / no-log projects) | `unicast.censurfridns.dk` | DoT | none | denmark |
| 61 | DNS Privacy (Stubby / no-log projects) | `anycast.censurfridns.dk` | DoT | none | denmark |
| 62 | Seby DNS | `dot.seby.io` | DoT | none | global |
| 63 | Rethink DNS | `max.rethinkdns.com` | DoT+DoH | none | global |
| 64 | Privacy-First DNS (tiar.app) | `dot.tiar.app` | DoT | none | singapore |
| 65 | Privacy-First DNS (tiar.app) | `doh.tiar.app` | DoH | none | singapore |
| 66 | Njalla DNS | `dns.njal.la` | DoT+DoH | none | sweden |
| 67 | Kahf Guard (KahfDNS) | `medium.kahfguard.com` | DoT+DoH | ads, malware, adult | global |

A plain copy-paste hostname list is in [`hostnames.txt`](hostnames.txt) (DoT-capable endpoints) and [`hostnames-doh.txt`](hostnames-doh.txt) (DoH URLs).

---

## 🚫 ShortsGuard — Reels & Shorts blocked, apps kept

### What it does

| App | Normal use | Reels / Shorts |
|---|---|---|
| **Facebook** | ✅ Feed, Marketplace, Groups, Pages | ❌ Reels tab, Reels shelf and `/reel/` links hidden + redirected |
| **Messenger** | ✅ Chats, calls, attachments (`messenger.com`, `/messages`) | — |
| **YouTube** | ✅ Home, subscriptions, watch page | ❌ Shorts shelf, Shorts tab, Shorts search results hidden; `/shorts/<id>` redirected to the normal `/watch?v=<id>` player |
| **Instagram** | ✅ Feed, Stories, DMs (`/direct/`) | ❌ Reels tab, Reels shelf and `/reels/` links hidden + redirected |
| **TikTok** | ✅ Works in Focus Mode | TikTok is 100% short video; the **optional** DNS Hard Block can remove it entirely |

### The honest limit (read this first)

> DNS resolves **domain names**, nothing else. `facebook.com/reel/123`, `youtube.com/shorts/abc` and `instagram.com/reels/xyz` all live on the **same domains** as the normal feed. No DNS resolver on earth can block a path — and blocking `fbcdn.net` / `cdninstagram.com` / `googlevideo.com` to kill short videos also kills every photo, video, story and Messenger attachment.
>
> So ShortsGuard blocks the short-video **surfaces inside the page** (userscript, extension or content blocker) and uses DNS only for whole-app blocks and normal ad/malware/adult filtering.

### Profiles

| Profile | Layer | Blocks | Keeps |
|---|---|---|---|
| **Kids Guard** (default) | DNS + browser | Ads, trackers, malware, adult content, Reels/Shorts surfaces | Facebook, Messenger, YouTube, Instagram, TikTok, WhatsApp |
| **Focus Mode** (recommended for adults) | Browser | YouTube Shorts, Facebook Reels, Instagram Reels | Facebook, Messenger, Instagram DMs, YouTube, TikTok, WhatsApp |
| **Focus + Filtered DNS** (best all-round) | DNS + browser | Focus Mode + ads, trackers, malware device-wide | Same as Focus |
| **DNS Hard Block** (opt-in, breaks apps) | DNS | TikTok, Likee, Kwai, SnackVideo **completely** | Facebook, Messenger, Instagram, YouTube |
| **Family Safe** | DNS + browser | Adult + malware + all short-video surfaces | Facebook, Messenger, Instagram DMs, YouTube |

### Install (pick one)

1. **Userscript — fastest, all browsers**
   - Install [Tampermonkey](https://www.tampermonkey.net/) (Chrome/Edge/Brave) or [Violentmonkey](https://violentmonkey.github.io/) (Firefox).
   - Open [`guard/shorts-guard.user.js`](guard/shorts-guard.user.js) and click **Raw** — the manager offers **Install**.
   - Open YouTube, Facebook and Instagram once to confirm the badge appears.
   - Toggle targets from the script menu (**ShortsGuard → settings**).

2. **uBlock Origin / AdGuard — no extra extension if you already use one**
   - uBlock Origin → Dashboard → **My filters** → paste [`blocklists/shortsguard-ublock.txt`](blocklists/shortsguard-ublock.txt) → **Apply changes**.
   - AdGuard → **Filters → Custom** → paste [`blocklists/shortsguard-adguard.txt`](blocklists/shortsguard-adguard.txt).

3. **Bundled MV3 extension (Chrome / Edge / Brave)**
   - Open `chrome://extensions`, enable **Developer mode**.
   - **Load unpacked** → select the [`guard/extension`](guard/extension) folder.
   - Pin ShortsGuard and toggle YouTube / Facebook / Instagram from the popup.

4. **Whole network (apps only) — AdGuard Home / Pi-hole / dnsmasq**
   - AdGuard Home → **Filters → DNS blocklists → Add blocklist** → paste the raw URL of [`blocklists/shortsguard-adguardhome.txt`](blocklists/shortsguard-adguardhome.txt).
   - Pi-hole → **Adlists** → paste the raw URL of [`blocklists/shortsguard-hosts.txt`](blocklists/shortsguard-hosts.txt) → **Update gravity**.
   - dnsmasq / OpenWrt → include [`blocklists/shortsguard-dnsmasq.txt`](blocklists/shortsguard-dnsmasq.txt).
   - This blocks TikTok / Likee / Kwai / SnackVideo on every device. It **cannot** hide Reels/Shorts inside Facebook/Instagram/YouTube — use Focus Mode for that.

The plain domain list for NextDNS / pfSense / other tools is [`blocklists/shortsguard-domains.txt`](blocklists/shortsguard-domains.txt).

> **Safety net:** the DNS blocklists allowlist `messenger.com`, `facebook.com`, `instagram.com` and `youtube.com`, and the guard never touches `/messages`, `/direct/`, `web.whatsapp.com` or any media CDN.

---

## 🧰 Full DNS System — one profile, every device

The **DNS System** tab (and the generated [`system/`](system/) folder) turns one protection profile into exact settings for every platform — Android, iPhone/iPad, Windows, macOS, Linux, a whole-home router and a browser-only setup.

### Profiles

| Profile | Blocks | Android Private DNS | DoH URL | IPv4 |
|---|---|---|---|---|
| 🧸 **Kids Guard** (default) | ads, trackers, malware, adult, SafeSearch | `dns-family.adguard.com` | `https://dns-family.adguard.com/dns-query` | `94.140.14.15`, `94.140.15.16` |
| 🕌 **Kahf Guard** | ads, trackers, malware, adult, gambling, SafeSearch | `medium.kahfguard.com` | `https://medium.kahfguard.com/dns-query` | `142.132.207.231`, `157.90.95.113` |
| 🎯 **Ad Block** | ads, trackers | `dns.adguard-dns.com` | `https://dns.adguard-dns.com/dns-query` | `94.140.14.14`, `94.140.15.15` |
| 👨‍👩‍👧 **Family Safe** | malware, adult, SafeSearch | `family.cloudflare-dns.com` | `https://family.cloudflare-dns.com/dns-query` | `1.1.1.3`, `1.0.0.3` |
| 🕵️ **Privacy (no-log)** | nothing (Quad9 still blocks known malware) | `dns.quad9.net` | `https://dns.quad9.net/dns-query` | `9.9.9.9`, `149.112.112.112` |

All five keep Facebook, Messenger, YouTube, Instagram, TikTok and WhatsApp working. Reels/Shorts remain a page-level job — use ShortsGuard for those.

### Ready-to-run files

`python scripts/build_system.py` renders every profile into [`system/<profile>/`](system/):

| Platform | File |
|---|---|
| Windows 10/11 | `windows-dns.ps1` (run as Administrator) |
| macOS | `macos-dns.sh` (run with `sudo`) |
| Linux (systemd-resolved) | `systemd-resolved.conf` → `/etc/systemd/resolved.conf.d/dns.conf` |
| Stubby | `stubby.yml` → `/etc/stubby/stubby.yml` |
| dnsmasq / OpenWrt | `dnsmasq.conf` |
| AdGuard Home | `adguardhome-upstreams.txt` |
| Pi-hole | `pihole-upstreams.txt` |

[`system/safesearch.conf`](system/safesearch.conf) adds the Google / YouTube / Bing SafeSearch CNAMEs for AdGuard Home, Pi-hole and dnsmasq 2.86+.

The website renders the same templates in your browser, so **Copy** and **Download** work offline and always match the committed files.

### Kahf Guard (KahfDNS) — live-verified

`medium.kahfguard.com` was tested on 2026-11-11 before being added:

- **DoT** on `:853` answered `example.com/A` with a valid `*.kahfguard.com` certificate (Let's Encrypt).
- **DoH** at `https://medium.kahfguard.com/dns-query` works (HTTP/2; browsers and Windows 11 support it).
- **Filtering verified:** `doubleclick.net`, `googleadservices.com`, `pornhub.com`, `xvideos.com`, `bet365.com` and `malware.wicar.org` all return `blocked.kahfguard.com`, while `facebook.com`, `youtube.com` and `tiktok.com` resolve normally.
- **SafeSearch:** `www.google.com` resolves to `forcesafesearch.google.com`.
- **Privacy:** query logs auto-delete within 48 hours (minimal-log), no account needed.

Kahf Guard also advertises DoQ (`quic://medium.kahfguard.com:853`) and DoH3 (`h3://medium.kahfguard.com/dns-query`); this repo verifies and lists DoT + DoH.

---

## 🎛️ dnsctl — switch DNS on any device, with live ping & latency

[`scripts/dnsctl.py`](scripts/dnsctl.py) is the “give me the system” switch: a single cross-platform tool that (1) measures **live** latency of every protection profile, and (2) applies it to this PC / Mac / Linux box. Phone and router covered too. Switch as often as you like — no installer, no account.

```bash
python scripts/dnsctl.py status              # what is my DNS right now?
python scripts/dnsctl.py test                # live UDP/DoT/DoH latency table
python scripts/dnsctl.py fastest             # which profile answers fastest right now
python scripts/dnsctl.py fastest --apply     # benchmark, then switch to the winner
python scripts/dnsctl.py use kahfguard       # apply Kahf Guard now
python scripts/dnsctl.py use family          # …or any other profile
python scripts/dnsctl.py use dns.google      # …or any single endpoint from the list
python scripts/dnsctl.py use --ips 1.1.1.1,1.0.0.1   # …or your own IPs
python scripts/dnsctl.py watch               # continuous live latency (Ctrl+C stops)
python scripts/dnsctl.py reset               # back to DHCP / automatic
```

Live output (example, your network will differ):

```text
Live benchmark of 5 profile(s)  (UDP/53, DoT, DoH)
👨‍👩‍👧 Family Safe      udp=[43, 43]  avg=   43.0 ms  ███████████████████  dot= 700.0 ms (ok) doh= 198.0 ms (ok)
🕵️ Privacy (no-log) udp=[83, 89]  avg=   85.7 ms  ███████████████      dot= 673.0 ms (ok) doh= 177.0 ms (http2)
🕌 Kahf Guard       udp=[224, 231] avg=  227.6 ms  ██                   dot=1726.0 ms (cert) doh= 714.0 ms (http2)
🎯 Ad Block         udp=[321, 306] avg=  313.8 ms                     dot=1653.0 ms (ok) doh= 516.0 ms (ok)
🧸 Kids Guard       udp=[333, 334] avg=  333.5 ms                     dot=1773.0 ms (ok) doh= 392.0 ms (ok)
```

| Platform | What `use` does | Needs |
|---|---|---|
| Windows 10/11 | Sets DNS on every Up adapter + DoH template via `Add-DnsClientDohServerAddress` (22H2+) | Administrator (auto UAC re-launch) |
| macOS | `networksetup -setdnsservers` on Wi-Fi / first enabled service | sudo |
| Linux (systemd-resolved) | writes `/etc/systemd/resolved.conf.d/dnsctl.conf` (+ backup), restarts | root/sudo |
| Android | `dnsctl.py mobile <profile>` prints the Private DNS hostname + steps (Android OS switches it, no app can) | one-time manual step |
| iPhone / iPad | `dnsctl.py export mobileconfig <profile>` writes an installable `.mobileconfig` (encrypted DoH) | one-time install |
| Router | `dnsctl.py router <profile>` prints AdGuard Home / Pi-hole / dnsmasq / OpenWrt upstreams (or use `system/<profile>/`) | router admin |

Everything is local: no cloud, no account, no telemetry. `--dry-run` shows exactly what would change without touching anything. Undo anytime with `reset`.

### dnsctl বাংলা সারাংশ

একটা কমান্ডে সব ডিভাইসে DNS বদলানো: `python scripts/dnsctl.py fastest --apply` — কোন DNS এখনো সবচেয়ে কম ping, তা live মাপবে এবং দ্রুততমটা ইন্সটল করে দেবে। `use kahfguard` / `use family` দিয়ে যেকোনো সময় যেকোনোটায় switch করা যায়। PC/Laptop (Windows/macOS/Linux) সরাসরি বদলায়; Android-এ `mobile` কমান্ড Private DNS hostname দেয় (Android-এ এটা manual step); iPhone-এ `export mobileconfig` ফাইল install করতে হয়; Router-এ `router` কমান্ড AdGuard Home/Pi-hole সেটিং দেয়। `reset` দিয়ে সব আগের মতো ফিরে যায়। সব কমান্ডে `--dry-run` দিলে কিছু বদলায় না, শুধু দেখানো হয়।

---

## 🤖 Smart Advisor

The **Smart Advisor** tab answers seven questions and ranks the best resolver for your device, region and blocking goals, with exact setup steps. It is a **deterministic, offline, explainable rules model** — not a cloud LLM, not an upload, not tracking. Every score is computed from the data in this repo.

It also tells you when your goal is impossible at the DNS layer (Reels/Shorts) and points you to ShortsGuard.

### CLI version

```bash
python scripts/advisor.py --device android --region bangladesh --block malware --keep facebook,messenger,youtube,instagram,tiktok
python scripts/advisor.py --device windows --region global --block ads,malware --privacy
python scripts/advisor.py --device android --region bangladesh --block ads,malware --focus
```

The CLI mirrors the website scoring model so the answer is reproducible outside the browser.

---

## 🩺 Live health checks

[`scripts/check_health.py`](scripts/check_health.py) performs a **real DNS lookup**, not just a TCP connect:

- **DoT** → TLS handshake on port 853 + length-prefixed DNS query for `example.com/A`, then parses `rcode` / answer count.
- **DoH** → `POST application/dns-message` to the endpoint's DoH URL, with a `GET ?name=…&type=A` JSON fallback.

```bash
python scripts/check_health.py                 # all endpoints, writes data/health.json
python scripts/check_health.py --host dns.google
python scripts/check_health.py --only-dot
python scripts/check_health.py --timeout 6 --workers 24
python scripts/check_health.py --no-write      # do not touch health.json
python scripts/check_health.py --strict        # exit 1 if any endpoint is dead
```

Current snapshot (2026-11-11): **64 healthy · 3 partial · 0 dead · 67 checked**.

`partial` means one protocol worked and the other was blocked by the local network or needs HTTP/2. `cert` means DNS answered but the checking machine's root store did not validate the certificate (often an outdated CA bundle, not a broken resolver) — those endpoints still count as alive.

The scheduled [`health.yml`](.github/workflows/health.yml) workflow refreshes `data/health.json` weekly so the site badges stay honest.

---

## 🔐 DoT vs DoH — which one do I need?

| | DoT (`dns.google` style) | DoH (`https://…/dns-query`) |
|---|---|---|
| **Android Private DNS** | ✅ Native support | ❌ Not supported |
| **Windows 11** | ❌ | ✅ Settings → DNS over HTTPS |
| **macOS / Linux** | via stubby / dnsmasq | via systemd-resolved / browser |
| **Chrome / Firefox** | ❌ | ✅ Built-in “Secure DNS” |
| **Speed** | Slightly faster (dedicated port) | Indistinguishable in practice |
| **Censorship resistance** | Easy to block port 853 | Hard to block (looks like HTTPS) |

**Rule of thumb:** Android → use the `DoT` / `DoT+DoH` hostnames. Browsers → use DoH. Both are end-to-end encrypted.

---

## 🖥️ Setup on other platforms

### Windows 10 (21H2+) / Windows 11
Settings → **Network & internet** → your connection → **DNS server assignment** → **Edit** → **Manual** → enable **IPv4**:
- Preferred: `1.1.1.1`, Alternate: `1.0.0.1` (Cloudflare) — or `8.8.8.8` / `8.8.4.4` (Google) — or `9.9.9.9` / `149.112.112.112` (Quad9)
- Under *Preferred DNS encryption* choose **Encrypted only (DNS over HTTPS)** and paste the provider's DoH URL.

### macOS
System Settings → **Network** → select interface → **Details…** → **DNS** → `+` → add e.g. `1.1.1.1`, `1.0.0.1`. For full DoH, install a DoH profile app (for example [DNSecure](https://apps.apple.com/app/dnsecure/id1533413232)) or use `/etc/resolver` + a DoT proxy such as [stubby](https://getdnsapi.net/stubby/).

### Linux (systemd-resolved)
```ini
# /etc/systemd/resolved.conf.d/dns.conf
[Resolve]
DNS=1.1.1.1#security.cloudflare-dns.com 9.9.9.9#dns.quad9.net
DNSOverTLS=yes
```
Then `sudo systemctl restart systemd-resolved` and check with `resolvectl status`.

### Chrome / Brave / Edge
Settings → **Privacy and security** → **Security** → **Use secure DNS** → **Custom**:
`https://dns.google/dns-query` · `https://cloudflare-dns.com/dns-query` · `https://dns.adguard-dns.com/dns-query`

### Firefox
Settings → **Privacy & Security** → **DNS over HTTPS** → *Increased Protection* → provider **Cloudflare** / **NextDNS** / custom `https://dns.google/dns-query`.

### Router (whole network)
Most routers (OpenWrt, pfSense, AsusWRT-Merlin, MikroTik) support DNS-over-TLS forwarding. On OpenWrt:
```sh
opkg update && opkg install stubby
# point /etc/config/stubby at e.g. dns.quad9.net, then set DHCP DNS to the router
```
On stock routers: set the DNS servers to the filtered IPs (e.g. AdGuard `94.140.14.14` / `94.140.15.15`).

---

## 🌐 Interactive website

`index.html` is a **self-contained** interactive version of the list and the guard:

- **Resolvers** — live search, filter chips (All / Working now / Unfiltered / Ad-Blocking / Malware Shield / Family-Safe / Social Block / DoT / DoH), health badges, one-click copy of hostnames, DoH URLs and IPv4 addresses.
- **ShortsGuard** — profiles, a per-surface matrix, the exact uBlock / AdGuard / hosts / dnsmasq rules, and install guides.
- **DNS System** — pick a protection profile and a device, copy the hostname / DoH URL / IPv4, and download ready-to-run Windows, macOS, Linux, Stubby, dnsmasq, AdGuard Home and Pi-hole configs.
- **Smart Advisor** — the offline scoring engine with setup steps.
- **Setup Guide** — Android, iOS, Windows, macOS, Linux, browser and router instructions, plus a Bengali quick-start.

Dark & light themes, keyboard shortcut `/` for search, and no network calls after load.

### Run locally
Double-click `index.html`, or:
```bash
python -m http.server 8000   # then open http://localhost:8000
```

### Publish to GitHub Pages (free)
1. Repo **Settings → Pages → Source: Deploy from a branch → Branch `main` → folder `/ (root)` → Save**
2. Every push to `main` auto-publishes to `https://iamtanzir.github.io/DNS-Server-List/`.

*(Alternative: Source **GitHub Actions** + the [`pages.yml`](.github/workflows/pages.yml) workflow, triggered manually from the Actions tab.)*

### Regenerate after editing data
```bash
python scripts/build_system.py
python scripts/build_guard.py
python scripts/export_hosts.py
python scripts/export_hosts.py --doh
python scripts/build_site.py
python scripts/validate.py --strict
python -m compileall -q scripts             # syntax check for the CLI tools too
```

---

## 📁 Repository structure

```
├── index.html                    # Built, self-contained site (open in any browser)
├── site/template.html            # Site source; data is inlined by build_site.py
├── data/
│   ├── dns-servers.json          # Source of truth: 38 providers / 67 endpoints
│   ├── guard-profiles.json       # ShortsGuard profiles, targets, domains, rules
│   ├── dns-system.json           # Full DNS System: profiles, platforms, config templates
│   └── health.json               # Latest live health snapshot
├── system/                       # Generated per-profile configs (build_system.py)
│   ├── kids-guard/               # Windows, macOS, Linux, Stubby, dnsmasq, AdGuard, Pi-hole
│   ├── kahfguard/
│   ├── adblock/
│   ├── family/
│   ├── privacy/
│   ├── safesearch.conf           # SafeSearch CNAME records
│   └── README.md
├── hostnames.txt                 # Plain DoT-capable hostname list (generated)
├── hostnames-doh.txt             # Plain DoH URL list (generated)
├── blocklists/                   # Generated ShortsGuard lists
│   ├── shortsguard-ublock.txt
│   ├── shortsguard-adguard.txt
│   ├── shortsguard-adguardhome.txt
│   ├── shortsguard-hosts.txt
│   ├── shortsguard-dnsmasq.txt
│   └── shortsguard-domains.txt
├── guard/
│   ├── shorts-guard.user.js      # Userscript (source)
│   └── extension/                # MV3 extension (manifest, popup, synced script)
├── scripts/
│   ├── validate.py               # Data + artifact validator (CI)
│   ├── check_health.py           # Live DoT/DoH verifier
│   ├── build_guard.py            # Blocklist generator + extension sync
│   ├── build_system.py           # dns-system.json → system/<profile>/ configs
│   ├── export_hosts.py           # JSON → hostnames.txt / hostnames-doh.txt
│   ├── build_site.py             # template + JSON → index.html
│   ├── dnsctl.py                 # Cross-platform DNS switch + live latency monitor
│   └── advisor.py                # CLI Smart Advisor
├── .github/workflows/
│   ├── validate.yml              # CI: validate + rebuild + diff
│   ├── health.yml                # Weekly live health refresh
│   └── pages.yml                 # Optional GitHub Actions Pages deploy
├── DNS-Server-List               # Original plain-text list (kept for compatibility)
└── LICENSE                       # MIT
```

---

## 🤝 Contributing

Found a dead resolver or a new one? Adding entries is three steps:

1. **Fork** and edit `data/dns-servers.json` — copy an existing provider block:
   ```json
   {
     "id": "mydns",
     "name": "My DNS",
     "website": "https://example.com",
     "privacy": "no-log",
     "hosts": [
       {
         "host": "dns.example.com",
         "label": "Standard",
         "protocol": "dot+doh",
         "filters": ["none"],
         "region": "global",
         "doh": "https://dns.example.com/dns-query",
         "ipv4": ["192.0.2.1", "192.0.2.2"],
         "notes": ""
       }
     ]
   }
   ```
   Rules: unique lowercase hostnames, `protocol` ∈ `dot | doh | dot+doh`, `filters` ⊆ `none | ads | malware | adult | social`, `privacy` ∈ `no-log | minimal-log | unknown`.
2. **Validate & rebuild:**
   ```bash
   python scripts/build_system.py
   python scripts/build_guard.py
   python scripts/export_hosts.py
   python scripts/export_hosts.py --doh
   python scripts/build_site.py
   python scripts/validate.py --strict
   python scripts/check_health.py --host dns.example.com
   ```
3. **Open a PR** — CI must pass and will show the endpoint count.

Please only submit resolvers you have actually tested. An endpoint that cannot answer a real query is removed, not kept “for reference”.

---

## ❓ FAQ

**Q: Can DNS block Facebook Reels but keep Facebook working?**
A: No. Reels live at `facebook.com/reel/<id>` — the same domain as the feed. Blocking the domain blocks the whole app; blocking `fbcdn.net` also kills photos, stories and Messenger attachments. Use **ShortsGuard** for the Reels surface.

**Q: Can DNS block YouTube Shorts?**
A: No. `youtube.com/shorts/<id>` is a path on the normal YouTube domain. ShortsGuard hides the shelf/tab and redirects `/shorts/<id>` to the normal watch page.

**Q: Will ShortsGuard break Messenger or DMs?**
A: No. `messenger.com`, `facebook.com/messages`, `instagram.com/direct` and `web.whatsapp.com` are explicitly allowlisted, and no media CDN is touched.

**Q: What about TikTok?**
A: Focus Mode keeps TikTok working. If you want it gone, the **DNS Hard Block** profile blocks TikTok / Likee / Kwai / SnackVideo completely — but that is opt-in because those apps stop working entirely.

**Q: What is Kahf Guard (KahfDNS)?**
A: A family/halal filtering resolver at `medium.kahfguard.com` (DoT + DoH). It blocks ads, trackers, malware, adult content and gambling, enforces SafeSearch, and keeps Facebook / YouTube / TikTok working. Query logs auto-delete within 48 hours. It was live-verified before being added — see [Full DNS System](#-full-dns-system--one-profile-every-device).

**Q: Android says “Private DNS provider hostname can't be resolved”.**
A: The hostname is wrong or the resolver is down. Double-check spelling; temporarily switch to **Automatic** and try another hostname (e.g. `dns.google`).

**Q: Do these filtering DNS services block YouTube / WhatsApp / essential sites?**
A: Only if the domain is on their blocklist. `dns-family.adguard.com` and `family-filter-dns.cleanbrowsing.org` block adult/mixed content; `p3.freedns.controld.com` also blocks social domains (and therefore the apps). Use `none`-tagged endpoints for zero filtering.

**Q: Is my DNS traffic encrypted on plain home Wi-Fi?**
A: Between your device and the resolver, yes. The resolver itself sees your queries — that is why no-log providers (Quad9, Mullvad, Wikimedia, Njalla, …) are labelled.

**Q: VPN on?**
A: VPN and Private DNS coexist fine. The VPN encrypts all traffic; Private DNS encrypts the lookup stage. Both together is belt and suspenders.

**Q: `hostnames.txt` contains comments (`#`) — can I paste it somewhere?**
A: It is for humans. Paste **one hostname**, not lines starting with `#`.

---

## 🇧🇩 বাংলা গাইড

### ১. Android Private DNS সেটআপ (৬০ সেকেন্ড)

1. **Settings → Network & internet → Private DNS** খুলুন।
2. **Private DNS provider hostname** নির্বাচন করুন।
3. **শুধু একটি** hostname পেস্ট করুন, যেমন:
   - অ্যাড ব্লক: `dns.adguard-dns.com`
   - ফ্যামিলি-সেফ: `family.cloudflare-dns.com`
   - অ্যাড + ফ্যামিলি + জুয়া + SafeSearch: `medium.kahfguard.com` (Kahf Guard)
   - ম্যালওয়্যার ব্লক: `security.cloudflare-dns.com`
   - ফিল্টার ছাড়া: `1dot1dot1dot1.cloudflare-dns.com`
4. **Save** চাপুন।
5. যাচাই: <https://1.1.1.1/help> খুলে দেখুন “Using DNS over TLS (DoT)” লেখা আছে কি না।

> **মনে রাখুন:** পুরো লিস্ট পেস্ট করবেন না। `doh.` দিয়ে শুরু হওয়া hostname Android Private DNS-এ কাজ করে না — সেগুলো ব্রাউজার/Windows-এর DoH সেটিংসে ব্যবহার করুন।

### ২. Facebook Reels / YouTube Shorts / Instagram Reels ব্লক, কিন্তু অ্যাপ চালু

**DNS দিয়ে এটি সম্ভব নয়।** কারণ `facebook.com/reel/123`, `youtube.com/shorts/abc`, `instagram.com/reels/xyz` — সবই সাধারণ ফিডের **একই ডোমেইনের ভেতরের path**। ডোমেইন ব্লক করলে পুরো Facebook/Instagram/YouTube বন্ধ হয়ে যাবে; `fbcdn.net` ব্লক করলে সব ছবি, স্টোরি, ভিডিও ও Messenger-এর অ্যাটাচমেন্টও ভেঙে যাবে।

**সমাধান — ShortsGuard:**
1. **ShortsGuard** ট্যাব খুলুন (ওয়েবসাইটে)।
2. **Userscript** ইনস্টল করুন (Tampermonkey/Violentmonkey), অথবা **uBlock Origin**-এ `shortsguard-ublock.txt` পেস্ট করুন।
3. এরপর:
   - Facebook চালু থাকবে, Reels ট্যাব/শেলফ লুকিয়ে যাবে।
   - YouTube চালু থাকবে, Shorts লুকিয়ে যাবে; `/shorts/<id>` সাধারণ watch পেজে যাবে।
   - Instagram চালু থাকবে, Reels লুকিয়ে যাবে।
   - TikTok চালু থাকবে (চাইলে DNS Hard Block দিয়ে পুরো TikTok বন্ধ করা যাবে)।
   - Messenger ও DM আগের মতোই কাজ করবে।

### ৩. Full DNS System — এক প্রোফাইল, সব ডিভাইস

ওয়েবসাইটের **DNS System** ট্যাবে প্রোফাইল ও ডিভাইস বেছে নিন — hostname, DoH URL, IPv4 কপি করুন বা রেডি config ডাউনলোড করুন। একই ফাইল রিপোর `system/<profile>/` ফোল্ডারেও আছে (Windows PowerShell, macOS, Linux, Stubby, dnsmasq, AdGuard Home, Pi-hole)।

- 🧸 **Kids Guard** (ডিফল্ট): অ্যাড, ট্র্যাকার, ম্যালওয়্যার, অ্যাডাল্ট + SafeSearch — `dns-family.adguard.com`
- 🕌 **Kahf Guard**: অ্যাড, ম্যালওয়্যার, অ্যাডাল্ট, জুয়া + SafeSearch — `medium.kahfguard.com`
- 🎯 **Ad Block**: শুধু অ্যাড/ট্র্যাকার — `dns.adguard-dns.com`
- 👨‍👩‍👧 **Family Safe**: ম্যালওয়্যার + অ্যাডাল্ট — `family.cloudflare-dns.com`
- 🕵️ **Privacy**: ফিল্টার ছাড়া, no-log — `dns.quad9.net`

Facebook, Messenger, YouTube, Instagram, TikTok ও WhatsApp — সবই চালু থাকবে। Reels/Shorts আলাদা করে ShortsGuard দিয়ে বন্ধ করুন।

### ৪. dnsctl — PC/Laptop-এ এক কমান্ডে DNS switch + live ping

রিপোর `scripts/dnsctl.py` দিয়ে PC/Laptop-এ যেকোনো সময় যেকোনো DNS-এ switch করা যায়, সাথে **live latency (ping)** দেখা যায়:

```bash
python scripts/dnsctl.py status        # এখন DNS কী আছে
python scripts/dnsctl.py test          # সব প্রোফাইলের live ping (UDP/DoT/DoH)
python scripts/dnsctl.py fastest       # কে সবচেয়ে দ্রুত — live measure করে
python scripts/dnsctl.py fastest --apply   # দ্রুততমটা Apply করে দেয়
python scripts/dnsctl.py use kahfguard # যেকোনো সময় যেকোনোটায় switch
python scripts/dnsctl.py reset         # আগের মতো (DHCP) ফেরত
```

- Windows/Mac/Linux — সব একই কমান্ডে কাজ করে (Windows-এ Administrator/UAC চায়; Mac/Linux-এ sudo)।
- Android-এ: `python scripts/dnsctl.py mobile kahfguard` → Private DNS hostname দেয়, Settings → Network & internet → Private DNS-এ বসিয়ে Save।
- iPhone/iPad-এ: `python scripts/dnsctl.py export mobileconfig kahfguard` → `.mobileconfig` install করুন।
- Router-এ: `python scripts/dnsctl.py router kahfguard` → AdGuard Home/Pi-hole/dnsmasq সেটিং।
- `--dry-run` দিলে কিছু বদলায় না, শুধু দেখানো হয়। `reset`-এ সব undo।

### ৫. Smart Advisor

ওয়েবসাইটের **Smart Advisor** ট্যাবে আপনার ডিভাইস, অঞ্চল ও প্রয়োজন বলুন — এটি সেরা DNS এবং সেটআপ ধাপ দেখাবে। সবকিছু ব্রাউজারেই চলে; কোনো ডেটা কোথাও যায় না। চাইলে CLI-ও ব্যবহার করতে পারেন:

```bash
python scripts/advisor.py --device android --region bangladesh --block malware --keep facebook,messenger,youtube,instagram,tiktok
```

### ৬. বাংলাদেশের জন্য নোট

এই লিস্টে বাংলাদেশ-হোস্টেড কোনো পাবলিক এনক্রিপ্টেড রিজলভার নেই। সিঙ্গাপুর, ভারত ও গ্লোবাল anycast endpointগুলো বাংলাদেশ থেকে সবচেয়ে কম লেটেন্সি দেয় — দু-তিনটি টেস্ট করে দ্রুততমটি রাখুন।

---

## ⚠️ Disclaimer

- Hostnames belong to their respective operators and may change, rate-limit or shut down without notice. **Test before relying on one for security-critical use.**
- “No-logging” and filtering claims are **self-declared** by each provider; this list compiles public documentation, not audits.
- China-based resolvers (AliDNS, DNSPod, 360) operate under local laws — choose according to your threat model.
- `ibksturm.synology.me` is a personal/self-hosted resolver — expect occasional downtime.
- ShortsGuard relies on each site's current DOM. A major redesign can break a selector; update `data/guard-profiles.json` and rebuild.

---

## 📜 License & credits

MIT © 2024 [A.K.M. Tanzir Ahmed](https://github.com/iamtanzir) — fork freely, PRs welcome.

Original list by **@tanzir786 / @iamtanzir**. v2.2 (Nov 2026): 67 live-verified endpoints / 38 providers, Kids Guard, Full DNS System with per-profile configs, Kahf Guard, health checker, ShortsGuard, Smart Advisor, interactive site and full docs.
