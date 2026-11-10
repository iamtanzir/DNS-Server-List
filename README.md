# 🛡️ Private DNS Server List

**A curated, ready-to-use collection of public DNS-over-TLS (DoT) and DNS-over-HTTPS (DoH) endpoints — with a searchable interactive website, machine-readable data, and one-tap setup instructions.**

[![Validate DNS data](https://github.com/iamtanzir/DNS-Server-List/actions/workflows/validate.yml/badge.svg)](https://github.com/iamtanzir/DNS-Server-List/actions/workflows/validate.yml)
[![GitHub Pages](https://img.shields.io/badge/demo-interactive%20list-58a6ff)](https://iamtanzir.github.io/DNS-Server-List/)
[![License: MIT](https://img.shields.io/badge/license-MIT-3fb950)](LICENSE)
[![Endpoints](https://img.shields.io/badge/endpoints-85%20%2F%2042%20providers-d2a8ff)](data/dns-servers.json)

🌐 **Live interactive list:** <https://iamtanzir.github.io/DNS-Server-List/> — search, filter by capability (ads / malware / family / social), and copy any hostname with one click.

> বাংলায় পড়ুন: [দ্রুত শুরু (বাংলা গাইড)](#-বাংলা-গাইড) — Android Private DNS কীভাবে সেট করবেন।

---

## 📑 Contents

- [Why encrypted DNS?](#-why-encrypted-dns)
- [Quick start — Android Private DNS](#-quick-start--android-private-dns)
- [Quick picks](#-quick-picks)
- [The full list (85 endpoints / 42 providers)](#-the-full-list)
- [DoT vs DoH — which one do I need?](#-dot-vs-doh--which-one-do-i-need)
- [Setup on other platforms](#-setup-on-other-platforms) — Windows · macOS · Linux · Chrome/Firefox · Router
- [Interactive website](#-interactive-website) — run locally or deploy to GitHub Pages
- [Repository structure](#-repository-structure)
- [Contributing](#-contributing)
- [FAQ](#-faq)
- [⚠️ Disclaimer](#️-disclaimer)

---

## ❓ Why encrypted DNS?

Plain DNS (port 53) is **unencrypted and unauthenticated** — your ISP (or anyone on the network) can see and tamper with every domain you look up. Encrypted DNS fixes this:

| Protocol | Port | Analogy | Best for |
|----------|------|---------|----------|
| **DoT** — DNS over TLS | 853 | VPN for DNS | Android *Private DNS*, routers, system-wide DoT |
| **DoH** — DNS over HTTPS | 443 | Normal HTTPS traffic | Browsers, OSes with DoH support, restrictive networks |

Benefits: privacy (ISP can't snoop your lookups), integrity (no DNS spoofing/poisoning), plus optional **content filtering** — block ads, malware, phishing, or adult sites at the DNS level for *every app on the phone*, no app-by-app setup needed.

---

## 🚀 Quick start — Android Private DNS

1. Open **Settings** → **Network & internet** → **Private DNS**
   *(on some phones: Settings → Connections → More connection settings → Private DNS)*
2. Select **Private DNS provider hostname**
3. Paste **ONE** hostname from the list below, e.g.:
   ```
   security.cloudflare-dns.com
   ```
4. Tap **Save** — done. All apps now use encrypted, filtered DNS.

> ⚠️ **Pick only one hostname.** Do not paste the whole list.
> ⚠️ Hostnames marked **DoH-only** (`doh.cleanbrowsing.org`, `doh.dnslify.com`) do **not** work in Android Private DNS — use them in browser/OS DoH settings instead. Everything marked **DoT** or **DoT+DoH** works.

Verify it works: visit <https://1.1.1.1/help> (should show *"Using DNS over TLS (DoT)"*) or <https://www.cloudflare.com/ssl/encrypted-dns/>.

---

## 🏆 Quick picks

| You want… | Use this hostname |
|---|---|
| Best all-round speed + privacy | `1dot1dot1dot1.cloudflare-dns.com` |
| Block malware everywhere | `security.cloudflare-dns.com` or `dns.quad9.net` |
| Block **ads** device-wide | `dns.adguard-dns.com` or `adblock.doh.mullvad.net` |
| Family-safe (ads + adult) | `family.cloudflare-dns.com` or `dns-family.adguard.com` |
| Block ads + malware + **social media** | `p3.freedns.controld.com` |
| Pure privacy, zero logging, non-profit | `dns.quad9.net` (`dns10.quad9.net` = no filter) |
| Ad + malware block, Germany | `dnsforge.de` |
| China users | `dns.alidns.com` (AliDNS) or `dot.pub` (DNSPod) |
| Japan users | `public.dns.iij.jp` |
| Blocks malware + ads + social, free no account | `p3.freedns.controld.com` (ControlD) |
| Custom blocklists, per device | [NextDNS](https://nextdns.io) — `dns.nextdns.io` |
| Mullvad-style no logs | `doh.mullvad.net` |

---

## 📋 The full list

**Protocol key:** `DoT` = Android Private DNS · `DoH` = browser/OS HTTPS DNS · `DoT+DoH` = both.
**Filters key:** `none` = unfiltered · `ads` = ad/tracker blocking · `malware` = malware/phishing · `adult` = adult content · `social` = social-media domains.

| # | Provider | Hostname | Protocol | Filters | Region |
|---|----------|----------|----------|---------|--------|
| 1 | Cloudflare | `1dot1dot1dot1.cloudflare-dns.com` | DoT+DoH | none | global |
| 2 | Cloudflare | `family.cloudflare-dns.com` | DoT+DoH | malware, adult | global |
| 3 | Cloudflare | `security.cloudflare-dns.com` | DoT+DoH | malware | global |
| 4 | Google Public DNS | `dns.google` | DoT+DoH | none | global |
| 5 | Quad9 | `dns.quad9.net` | DoT+DoH | malware | global |
| 6 | Quad9 | `dns10.quad9.net` | DoT+DoH | none | global |
| 7 | Quad9 | `dns11.quad9.net` | DoT+DoH | malware | global |
| 8 | CleanBrowsing | `doh.cleanbrowsing.org` | DoH | none | global |
| 9 | CleanBrowsing | `family-filter-dns.cleanbrowsing.org` | DoT+DoH | adult | global |
| 10 | CleanBrowsing | `adult-filter-dns.cleanbrowsing.org` | DoT+DoH | adult | global |
| 11 | CleanBrowsing | `security-filter-dns.cleanbrowsing.org` | DoT+DoH | malware | global |
| 12 | NextDNS | `dns.nextdns.io` | DoT+DoH | none | global |
| 13 | NextDNS | `anycast.dns.nextdns.io` | DoT+DoH | none | global |
| 14 | AdGuard DNS | `dns.adguard-dns.com` | DoT+DoH | ads | global |
| 15 | AdGuard DNS | `dns-family.adguard.com` | DoT+DoH | ads, adult | global |
| 16 | AdGuard DNS | `dns-unfiltered.adguard.com` | DoT+DoH | none | global |
| 17 | OpenDNS (Cisco Umbrella) | `dns.opendns.com` | DoT+DoH | malware | global |
| 18 | Rubyfish DNS | `dns.rubyfish.cn` | DoT | none | china |
| 19 | SWITCH DNS | `dns.switch.ch` | DoT | none | switzerland |
| 20 | FutureDNS | `dns.futuredns.me` | DoT | malware | global |
| 21 | Comss One DNS | `dns.comss.one` | DoT | none | russia |
| 22 | Comss One DNS | `dns.east.comss.one` | DoT | none | russia |
| 23 | CIRA Canadian Shield | `private.canadianshield.cira.ca` | DoT | none | canada |
| 24 | CIRA Canadian Shield | `protected.canadianshield.cira.ca` | DoT | malware | canada |
| 25 | CIRA Canadian Shield | `family.canadianshield.cira.ca` | DoT | malware, adult | canada |
| 26 | BlahDNS | `dot-fi.blahdns.com` | DoT | none | finland |
| 27 | BlahDNS | `dot-jp.blahdns.com` | DoT | none | japan |
| 28 | BlahDNS | `dot-de.blahdns.com` | DoT | none | germany |
| 29 | Snopyta DNS | `fi.dot.dns.snopyta.org` | DoT | none | finland |
| 30 | DNS For Family | `dns-dot.dnsforfamily.com` | DoT | adult | global |
| 31 | CZ.NIC ODVR | `odvr.nic.cz` | DoT | none | czechia |
| 32 | AliDNS (Alibaba) | `dns.alidns.com` | DoT | none | china |
| 33 | CFIEC Public DNS | `dns.cfiec.net` | DoT | none | china |
| 34 | 360 Secure DNS | `dot.360.cn` | DoT | malware | china |
| 35 | IIJ Public DNS | `public.dns.iij.jp` | DoT | none | japan |
| 36 | DNSPod Public DNS+ | `dot.pub` | DoT | none | china |
| 37 | Privacy-First DNS (tiar.app) | `dot.tiarap.org` | DoT | none | singapore |
| 38 | Privacy-First DNS (tiar.app) | `jp.tiar.app` | DoT | none | japan |
| 39 | OSZX DNS | `dns.oszx.co` | DoT | none | global |
| 40 | PumpleX DNS | `dns.pumplex.com` | DoT | none | global |
| 41 | Applied Privacy DNS | `dot1.applied-privacy.net` | DoT | none | austria |
| 42 | DeCloudUs DNS | `dns.decloudus.com` | DoT | none | usa |
| 43 | Lelux DNS | `resolver-eu.lelux.fi` | DoT | none | finland |
| 44 | DNS Forge | `dnsforge.de` | DoT | ads, malware | germany |
| 45 | Fondation Restena DNS | `kaitain.restena.lu` | DoT | none | luxembourg |
| 46 | FFMUC DNS | `dot.ffmuc.net` | DoT | none | germany |
| 47 | Digitale Gesellschaft DNS | `dns.digitale-gesellschaft.ch` | DoT | none | switzerland |
| 48 | LibreDNS | `dot.libredns.gr` | DoT | none | greece |
| 49 | ibksturm DNS | `ibksturm.synology.me` | DoT | none | germany |
| 50 | DNS Privacy (Stubby / no-log projects) | `getdnsapi.net` | DoT | none | global |
| 51 | DNS Privacy (Stubby / no-log projects) | `dnsovertls.sinodun.com` | DoT | none | uk |
| 52 | DNS Privacy (Stubby / no-log projects) | `dnsovertls1.sinodun.com` | DoT | none | uk |
| 53 | DNS Privacy (Stubby / no-log projects) | `unicast.censurfridns.dk` | DoT | none | denmark |
| 54 | DNS Privacy (Stubby / no-log projects) | `anycast.censurfridns.dk` | DoT | none | denmark |
| 55 | DNS Privacy (Stubby / no-log projects) | `dns.cmrg.net` | DoT | none | global |
| 56 | DNS Privacy (Stubby / no-log projects) | `dns.larsdebruin.net` | DoT | none | global |
| 57 | DNS Privacy (Stubby / no-log projects) | `dns-tls.bitwiseshift.net` | DoT | none | global |
| 58 | DNS Privacy (Stubby / no-log projects) | `ns1.dnsprivacy.at` | DoT | none | austria |
| 59 | DNS Privacy (Stubby / no-log projects) | `ns2.dnsprivacy.at` | DoT | none | austria |
| 60 | DNS Privacy (Stubby / no-log projects) | `dns.bitgeek.in` | DoT | none | india |
| 61 | DNS Privacy (Stubby / no-log projects) | `dns.neutopia.org` | DoT | none | global |
| 62 | DNS Privacy (Stubby / no-log projects) | `privacydns.go6lab.si` | DoT | none | slovenia |
| 63 | DNS Privacy (Stubby / no-log projects) | `dot.securedns.eu` | DoT | none | europe |
| 64 | DNS Privacy (Stubby / no-log projects) | `dnsotls.lab.nic.cl` | DoT | none | chile |
| 65 | DNS Privacy (Stubby / no-log projects) | `tls-dns-u.odvr.dns-oarc.net` | DoT | none | global |
| 66 | AhaDNS | `dot.nl.ahadns.net` | DoT | none | netherlands |
| 67 | AhaDNS | `dot.in.ahadns.net` | DoT | none | india |
| 68 | AhaDNS | `dot.la.ahadns.net` | DoT | none | usa |
| 69 | AhaDNS | `dot.ny.ahadns.net` | DoT | none | usa |
| 70 | AhaDNS | `dot.pl.ahadns.net` | DoT | none | poland |
| 71 | AhaDNS | `dot.it.ahadns.net` | DoT | none | italy |
| 72 | AhaDNS | `dot.es.ahadns.net` | DoT | none | spain |
| 73 | AhaDNS | `dot.no.ahadns.net` | DoT | none | norway |
| 74 | AhaDNS | `dot.chi.ahadns.net` | DoT | none | usa |
| 75 | Seby DNS | `dot.seby.io` | DoT | none | global |
| 76 | DNSlify | `doh.dnslify.com` | DoH | none | global |
| 77 | Rethink DNS | `max.rethinkdns.com` | DoT+DoH | none | global |
| 78 | ControlD (Free DNS) | `p0.freedns.controld.com` | DoT+DoH | none | global |
| 79 | ControlD (Free DNS) | `p1.freedns.controld.com` | DoT+DoH | malware | global |
| 80 | ControlD (Free DNS) | `p2.freedns.controld.com` | DoT+DoH | malware, ads | global |
| 81 | ControlD (Free DNS) | `p3.freedns.controld.com` | DoT+DoH | malware, ads, social | global |
| 82 | Mullvad DNS | `doh.mullvad.net` | DoT+DoH | none | global |
| 83 | Mullvad DNS | `adblock.doh.mullvad.net` | DoT+DoH | ads | global |
| 84 | Arapurayil DNS | `dns.arapurayil.com` | DoT | none | india |
| 85 | Dandelion Sprout DNS | `dandelionsprout.asuscomm.com` | DoT | none | global |

A plain copy-paste hostname list is also in [`hostnames.txt`](hostnames.txt) (DoT endpoints only), and the full structured data lives in [`data/dns-servers.json`](data/dns-servers.json).

---

## 🆚 DoT vs DoH — which one do I need?

| | DoT (`dns.google` style) | DoH (`https://.../dns-query`) |
|---|---|---|
| **Android Private DNS** | ✅ Native support | ❌ Not supported |
| **Windows 11** | ❌ | ✅ Settings → DNS over HTTPS |
| **macOS / Linux** | via stubby/dnsmasq | via systemd-resolved / browser |
| **Chrome / Firefox** | ❌ | ✅ Built-in "Secure DNS" |
| **Speed** | Slightly faster (dedicated port) | Indistinguishable in practice |
| **Censorship resistance** | Easy to block port 853 | Hard to block (looks like HTTPS) |

**Rule of thumb:** Android → use the `DoT`/`DoT+DoH` hostnames above. Browsers → use DoH. Both are end-to-end encrypted.

---

## 💻 Setup on other platforms

### Windows 10 (21H2+) / Windows 11
Settings → **Network & internet** → your connection → **DNS server assignment** → **Manual** → enable **IPv4**, enter:
- Preferred: `1.1.1.1` · Alternate: `1.0.0.1` (Cloudflare) — or `8.8.8.8` / `8.8.4.4` (Google) — or `9.9.9.9` / `149.112.112.112` (Quad9)
- Under *Preferred DNS encryption* choose **Encrypted only (DNS over HTTPS)**.

### macOS
System Settings → **Network** → select interface → **Details…** → **DNS** → `+` → add e.g. `1.1.1.1`, `1.0.0.1`. For full DoH, install [DNS Cloak](https://procyong.com/dnscloak/) or use `/etc/resolver` + a DoT proxy ([stubby](https://getdnsapi.net/stubby/)).

### Linux (systemd-resolved)
```bash
# /etc/systemd/resolved.conf  — or drop-in /etc/systemd/resolved.conf.d/dns.conf
[Resolve]
DNS=1.1.1.1#security.cloudflare-dns.com 9.9.9.9#dns.quad9.net
DNSOverTLS=yes
```
Then: `sudo systemctl restart systemd-resolved` and check with `resolvectl status`.

### Chrome / Brave / Edge
Settings → **Privacy and security** → **Security** → **Use secure DNS** → choose provider or **Custom**:
`https://dns.google/dns-query` · `https://cloudflare-dns.com/dns-query` · `https://dns.adguard-dns.com/dns-query`

### Firefox
Settings → **Privacy & Security** → **DNS over HTTPS** → *Increased Protection* → provider: **Cloudflare** / **NextDNS** / custom `https://dns.google/dns-query`.

### Router (whole network)
Most routers (OpenWrt, pfSense, AsusWRT-Merlin, MikroTik) support DNS-over-TLS forwarding. On OpenWrt:
```sh
opkg update && opkg install stubby
# set /etc/config/stubby to use e.g. dns.quad9.net, then point DHCP DNS to the router
```
On stock routers: set the DNS servers to the filtered IPs (e.g. AdGuard `94.140.14.14` / `94.140.15.15`) — encryption is router-to-upstream only on advanced firmwares.

---

## 🌐 Interactive website

`index.html` is a **self-contained** interactive version of the list: live search, filter chips (All / Unfiltered / Ad-Blocking / Malware Shield / Family-Safe / Social Block / DoT / DoH), one-click copy, dark & light themes, fully offline-friendly.

### Run locally
Just double-click `index.html`, or:
```bash
python -m http.server 8000   # then open http://localhost:8000
```

### Publish to GitHub Pages (free)
1. Repo **Settings → Pages**
2. **Source: GitHub Actions**
3. Push to `main` — the included [`pages.yml`](.github/workflows/pages.yml) workflow deploys automatically
4. Your list is live at `https://<username>.github.io/DNS-Server-List/`

### Regenerate after editing the data
```bash
python scripts/build_site.py     # re-inlines data/dns-servers.json into index.html
python scripts/validate.py       # sanity-check the JSON (85 endpoints, unique hosts…)
python scripts/export_hosts.py   # regenerate hostnames.txt
```

---

## 📁 Repository structure

```
├── index.html              # Self-contained interactive site (built, open in any browser)
├── site/template.html      # Site template (data placeholder → rebuilt by build_site.py)
├── data/dns-servers.json   # ⭐ Source of truth — structured data for all 42 providers
├── hostnames.txt           # Plain list of DoT hostnames (auto-generated)
├── scripts/
│   ├── validate.py         # JSON + hostname validator (runs in CI)
│   ├── export_hosts.py     # dns-servers.json → hostnames.txt
│   └── build_site.py       # template + JSON → index.html
├── .github/workflows/
│   ├── validate.yml        # CI: validate data on every push/PR
│   └── pages.yml           # CD: deploy the site to GitHub Pages
├── DNS-Server-List         # Original plain-text list (kept for compatibility)
└── LICENSE                 # MIT
```

---

## 🤝 Contributing

Found a dead resolver or a new one? Adding entries is 3 steps:

1. **Fork** and edit `data/dns-servers.json` — copy an existing provider block:
   ```json
   {
     "id": "mydns",
     "name": "My DNS",
     "website": "https://example.com",
     "hosts": [
       { "host": "dns.example.com", "label": "Standard", "protocol": "dot",
         "filters": ["none"], "region": "global", "notes": "" }
     ]
   }
   ```
   Rules: unique lowercase hostnames, `protocol` ∈ `dot | doh | dot+doh`, `filters` ∈ `none | ads | malware | adult | social`.
2. **Validate & rebuild:**
   ```bash
   python scripts/validate.py && python scripts/export_hosts.py && python scripts/build_site.py
   ```
3. **Open a PR** — CI (`validate.yml`) must pass and will show you the endpoint count.

Please only submit resolvers you have actually tested (e.g. `ping` + `nslookup -type=A example.com dns.example.com` or set it as your Private DNS and browse for a day).

---

## ❓ FAQ

**Q: Android says "Private DNS provider hostname can't be resolved".**
A: The hostname is wrong or the resolver is down. Double-check spelling; if unsure, temporarily switch to **Automatic** and try another hostname from the list (e.g. `dns.google`).

**Q: Do these filtering DNS services block YouTube/WhatsApp/essential sites?**
A: Only if the domain is on their blocklist — `dns-family.adguard.com` and `family-filter-dns.cleanbrowsing.org` block adult/mixed content, `p3.freedns.controld.com` also blocks social domains. Use `none`-tagged endpoints if you want zero filtering.

**Q: Is my DNS traffic encrypted with plain home Wi-Fi?**
A: Only between your device and the resolver (that's what DoT/DoH gives you). The resolver itself sees your queries — that's why providers with a no-logging policy (Quad9, Mullvad, Applied Privacy…) are listed.

**Q: Will ad-blocking DNS break app logins / captive portals?**
A: Rarely, but it can. If an app misbehaves, temporarily switch Private DNS to **Off**.

**Q: VPN on?**
A: VPN and Private DNS coexist fine. VPN encrypts all traffic; Private DNS encrypts the lookup stage. With a trustworthy VPN, either alone is OK; both together = belt and suspenders.

**Q: `hostnames.txt` contains comments (`#`) — can I paste it somewhere?**
A: It's for humans. Paste **one hostname**, not lines starting with `#`.

---

## 🇧🇩 বাংলা গাইড

**Private DNS কী?** সাধারণ DNS ট্রাফিক এনক্রিপ্ট করা থাকে না — আপনার ISP (বা নেটওয়ার্কের যে কেউ) দেখতে পারে আপনি কোন সাইটে যাচ্ছেন। Private DNS (DoT) সেটা এনক্রিপ্ট করে দেয় এবং DNS লেভেলে **অ্যাড / ম্যালওয়্যার / অ্যাডাল্ট সাইট ব্লক** করতে পারে — ফোনের সব অ্যাপের জন্য, কোনো আলাদা অ্যাপ ছাড়াই।

**সেট করবেন যেভাবে (Android):**
1. **Settings → Network & internet → Private DNS**
2. **Private DNS provider hostname** সিলেক্ট করুন
3. যেকোনো **একটি** hostname পেস্ট করুন:
   - অ্যাড ব্লক করতে → `dns.adguard-dns.com`
   - ফ্যামিলি-সেফ → `family.cloudflare-dns.com`
   - ম্যালওয়্যার ব্লক → `security.cloudflare-dns.com`
   - একদম ফিল্টার ছাড়া → `1dot1dot1dot1.cloudflare-dns.com`
4. **Save** — ব্যস! 🎉

**সতর্কতা:** পুরো লিস্ট নয়, শুধু একটি hostname বসিয়ে দিন। `doh.` দিয়ে শুরু হওয়া hostname (যেমন `doh.dnslify.com`) Android Private DNS-এ কাজ করে না — ওগুলো ব্রাউজার/Windows-এর DoH সেটিংসে ব্যবহার করুন।

---

## ⚠️ Disclaimer

- Hostnames belong to their respective operators and may change, rate-limit, or shut down without notice. **Test before relying on one for security-critical use.**
- "No-logging" and filtering claims are **self-declared** by each provider; this list compiles public documentation, not audits.
- China-based resolvers (AliDNS, DNSPod, 360, CFIEC, Rubyfish) operate under local laws — choose according to your threat model.
- `ibksturm.synology.me` and `dandelionsprout.asuscomm.com` are personal/self-hosted resolvers — expect occasional downtime.

---

## 📜 License & credits

MIT © 2024 [A.K.M. Tanzir Ahmed](https://github.com/iamtanzir) — fork freely, PRs welcome.

Original list by **@tanzir786 / @iamtanzir**. Data restructured & site by the same author — v2.0 (Nov 2026): structured JSON, validator, interactive GitHub Pages site, full docs.
