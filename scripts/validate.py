#!/usr/bin/env python3
"""Validate the repository's data files and generated artifacts.

Checks data/dns-servers.json:
  * JSON shape, vocabulary (protocols / filters / privacy)
  * required fields, unique provider ids and hostnames
  * valid hostnames, valid IPv4 addresses, https DoH URLs
  * DoH URL present whenever the protocol claims DoH
  * warnings for suspicious combos (doh.* used as a DoT host, "none"+other)

Checks data/guard-profiles.json:
  * required fields on profiles / targets / domain groups / redirects
  * every target referenced by a profile exists
  * valid domains, compilable redirect regexes, all rule sets present

Checks generated artifacts:
  * blocklists/*.txt exist and match data/guard-profiles.json
  * exported domains appear in every DNS rule format
  * guard/extension/shorts-guard.js matches guard/shorts-guard.user.js

Checks data/dns-system.json and system/:
  * profile / platform / config shape and placeholders
  * every profile hostname exists in data/dns-servers.json
  * system/<profile>/ files match the JSON templates exactly

Run:  python scripts/validate.py            # errors fail, warnings do not
      python scripts/validate.py --strict   # warnings fail too (CI can use this)
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DNS_DATA = ROOT / "data" / "dns-servers.json"
GUARD_DATA = ROOT / "data" / "guard-profiles.json"
SYSTEM_DATA = ROOT / "data" / "dns-system.json"
SYSTEM_DIR = ROOT / "system"

HOST_RE = re.compile(r"^(?=.{1,253}$)(?!-)[a-z0-9-]{1,63}(?<!-)(\.(?!-)[a-z0-9-]{1,63}(?<!-))*$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
IPV4_RE = re.compile(r"^(25[0-5]|2[0-4]\d|1?\d?\d)(\.(25[0-5]|2[0-4]\d|1?\d?\d)){3}$")
URL_RE = re.compile(r"^https://[^\s/]+\.[^\s]+$")

VALID_FILTERS = {"none", "ads", "malware", "adult", "social"}
VALID_PROTOCOLS = {"dot", "doh", "dot+doh"}
VALID_PRIVACY = {"no-log", "minimal-log", "unknown"}
REQUIRED_RULES = ("ublock", "adguard", "adguardhome", "hosts", "dnsmasq")
DOH_HOST_ALLOWLIST = {"doh.mullvad.net", "adblock.doh.mullvad.net"}  # serve DoT on :853 too
EXPECTED_BLOCKLISTS = (
    "shortsguard-ublock.txt",
    "shortsguard-adguard.txt",
    "shortsguard-adguardhome.txt",
    "shortsguard-hosts.txt",
    "shortsguard-dnsmasq.txt",
    "shortsguard-domains.txt",
)
EXPORT_GROUPS = {"tiktok", "likee", "kwai", "snackvideo"}
SYSTEM_SCHEMA = "dns-system/v1"
SYSTEM_PLACEHOLDER_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")
SYSTEM_PLACEHOLDERS = {"PROFILE_NAME", "ANDROID_HOST", "DOH_URL", "IPV4", "IPV4_ALT", "DOT_HOST"}

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


# --------------------------------------------------------------------------- #
# DNS data
# --------------------------------------------------------------------------- #
def validate_dns() -> tuple[int, int]:
    try:
        doc = json.loads(DNS_DATA.read_text(encoding="utf-8"))
    except FileNotFoundError:
        err(f"{DNS_DATA} not found")
        return 0, 0
    except json.JSONDecodeError as exc:
        err(f"invalid JSON in {DNS_DATA}: {exc}")
        return 0, 0

    for field in ("schema", "title", "updated", "filters", "protocols", "providers"):
        if not doc.get(field):
            err(f"dns: missing top-level field '{field}'")
    if doc.get("schema") != "dns-server-list/v2":
        warn(f"dns: unexpected schema {doc.get('schema')!r} (expected 'dns-server-list/v2')")

    filters_vocab = doc.get("filters") or {}
    protocols_vocab = doc.get("protocols") or {}
    privacy_vocab = doc.get("privacy") or {}
    if set(filters_vocab) != VALID_FILTERS:
        err(f"dns: 'filters' keys must be {sorted(VALID_FILTERS)}, got {sorted(filters_vocab)}")
    if set(protocols_vocab) != VALID_PROTOCOLS:
        err(f"dns: 'protocols' keys must be {sorted(VALID_PROTOCOLS)}, got {sorted(protocols_vocab)}")
    if set(privacy_vocab) != VALID_PRIVACY:
        err(f"dns: 'privacy' keys must be {sorted(VALID_PRIVACY)}, got {sorted(privacy_vocab)}")

    providers = doc.get("providers")
    if not isinstance(providers, list) or not providers:
        err("dns: 'providers' must be a non-empty list")
        return 0, 0

    seen_providers: dict[str, int] = {}
    seen_hosts: dict[str, str] = {}
    host_count = 0
    filter_counts = {f: 0 for f in VALID_FILTERS}

    for i, provider in enumerate(providers):
        where = provider.get("name") or provider.get("id") or f"providers[{i}]"
        for field in ("id", "name", "hosts"):
            if not provider.get(field):
                err(f"{where}: missing required field '{field}'")

        pid = str(provider.get("id", ""))
        if pid and not SLUG_RE.match(pid):
            err(f"{where}: id '{pid}' is not a lowercase slug")
        if pid in seen_providers:
            err(f"{where}: duplicate provider id '{pid}'")
        seen_providers[pid] = i

        website = provider.get("website")
        if website and not str(website).startswith(("https://", "http://")):
            err(f"{where}: website must start with http(s)://")
        privacy = provider.get("privacy")
        if privacy is None:
            warn(f"{where}: missing 'privacy' policy")
        elif privacy not in VALID_PRIVACY:
            err(f"{where}: privacy '{privacy}' not in {sorted(VALID_PRIVACY)}")

        hosts = provider.get("hosts") or []
        if not isinstance(hosts, list) or not hosts:
            err(f"{where}: 'hosts' must be a non-empty list")
            continue

        for j, entry in enumerate(hosts):
            host = str((entry or {}).get("host", "")).strip().lower()
            tag = f"{where} -> hosts[{j}] ({host or 'no host'})"

            if not host:
                err(f"{tag}: missing 'host'")
                continue
            if not HOST_RE.match(host):
                err(f"{tag}: '{host}' is not a valid DNS hostname")
            if host in seen_hosts:
                err(f"{tag}: duplicate host (already used by {seen_hosts[host]})")
            seen_hosts[host] = where
            host_count += 1

            protocol = entry.get("protocol")
            if protocol not in VALID_PROTOCOLS:
                err(f"{tag}: protocol '{protocol}' not in {sorted(VALID_PROTOCOLS)}")

            filters = entry.get("filters")
            if not isinstance(filters, list) or not filters:
                err(f"{tag}: 'filters' must be a non-empty list")
            else:
                bad = [f for f in filters if f not in VALID_FILTERS]
                if bad:
                    err(f"{tag}: unknown filters {bad}")
                for f in filters:
                    if f in filter_counts:
                        filter_counts[f] += 1
                if "none" in filters and len(filters) > 1:
                    warn(f"{tag}: 'none' combined with other filters")
                if len(set(filters)) != len(filters):
                    err(f"{tag}: duplicate filters {filters}")

            for field in ("label", "region"):
                if not str(entry.get(field, "")).strip():
                    warn(f"{tag}: empty '{field}'")

            doh = entry.get("doh")
            if protocol in ("doh", "dot+doh"):
                if not doh:
                    err(f"{tag}: protocol '{protocol}' requires a 'doh' URL")
                elif not URL_RE.match(str(doh)):
                    err(f"{tag}: doh '{doh}' is not an https URL")
            elif doh:
                warn(f"{tag}: 'doh' present but protocol is '{protocol}'")

            if protocol in ("dot", "dot+doh") and host.startswith("doh.") and host not in DOH_HOST_ALLOWLIST:
                warn(f"{tag}: host starts with 'doh.' — usually DoH-only, check DoT on :853")

            ipv4 = entry.get("ipv4")
            if ipv4 is not None:
                if not isinstance(ipv4, list) or not ipv4:
                    err(f"{tag}: 'ipv4' must be a non-empty list")
                else:
                    for ip in ipv4:
                        if not IPV4_RE.match(str(ip)):
                            err(f"{tag}: '{ip}' is not a valid IPv4 address")

            if entry.get("notes") is not None and not isinstance(entry["notes"], str):
                err(f"{tag}: 'notes' must be a string")

    print(f"DNS data  : {len(providers)} providers, {host_count} endpoints")
    print("Filters   : " + ", ".join(f"{k}={v}" for k, v in filter_counts.items()))
    return len(providers), host_count


# --------------------------------------------------------------------------- #
# ShortsGuard data
# --------------------------------------------------------------------------- #
def validate_guard() -> int:
    try:
        doc = json.loads(GUARD_DATA.read_text(encoding="utf-8"))
    except FileNotFoundError:
        err(f"{GUARD_DATA} not found")
        return 0
    except json.JSONDecodeError as exc:
        err(f"invalid JSON in {GUARD_DATA}: {exc}")
        return 0

    for field in ("schema", "version", "title", "honest_limit", "profiles", "targets", "rules"):
        if not doc.get(field):
            err(f"guard: missing top-level field '{field}'")

    limit = doc.get("honest_limit") or {}
    for lang in ("en", "bn"):
        if not str(limit.get(lang, "")).strip():
            err(f"guard: honest_limit.{lang} is empty")

    target_ids = set()
    for i, target in enumerate(doc.get("targets") or []):
        where = f"guard.targets[{i}]"
        for field in ("id", "app", "surface", "dns", "focus", "hard", "note"):
            if field not in target:
                err(f"{where}: missing '{field}'")
        tid = target.get("id")
        if tid in target_ids:
            err(f"{where}: duplicate target id '{tid}'")
        target_ids.add(tid)

    profiles = doc.get("profiles") or []
    if not isinstance(profiles, list) or not profiles:
        err("guard: 'profiles' must be a non-empty list")
    seen_profiles = set()
    for i, profile in enumerate(profiles):
        where = profile.get("name") or f"guard.profiles[{i}]"
        for field in ("id", "name", "layer", "tagline", "blocks", "keeps", "does", "install"):
            if not profile.get(field):
                err(f"{where}: missing required field '{field}'")
        pid = profile.get("id")
        if pid in seen_profiles:
            err(f"{where}: duplicate profile id '{pid}'")
        seen_profiles.add(pid)
        for blocked in profile.get("blocks") or []:
            if blocked in target_ids:
                continue
            if str(blocked).split("-")[0] in {"facebook", "instagram", "youtube", "tiktok"}:
                err(f"{where}: blocks '{blocked}' but no such target exists")

    seen_domains: dict[str, str] = {}
    for group in doc.get("domain_groups") or []:
        where = f"guard.domain_groups[{group.get('id', '?')}]"
        if not group.get("id") or not group.get("label") or not group.get("domains"):
            err(f"{where}: id, label and domains are required")
        if not str(group.get("breaks", "")).strip():
            warn(f"{where}: 'breaks' is empty — say what stops working")
        for domain in group.get("domains") or []:
            if not HOST_RE.match(str(domain)):
                err(f"{where}: '{domain}' is not a valid domain")
            if domain in seen_domains and seen_domains[domain] != group.get("id"):
                warn(f"{where}: '{domain}' also listed in {seen_domains[domain]}")
            seen_domains[str(domain)] = str(group.get("id"))

    rules = doc.get("rules") or {}
    for key in REQUIRED_RULES:
        if not str(rules.get(key, "")).strip():
            err(f"guard.rules: missing rule set '{key}'")

    # Exported domains must stay in sync with every DNS rule format.
    exported: list[str] = []
    for group in doc.get("domain_groups") or []:
        if group.get("id") in EXPORT_GROUPS:
            exported.extend(group.get("domains") or [])

    def suffixes(domain: str) -> list[str]:
        parts = domain.split(".")
        return [".".join(parts[i:]) for i in range(len(parts) - 1)]

    hosts_rules = str(rules.get("hosts", ""))
    adguard_rules = str(rules.get("adguardhome", ""))
    dnsmasq_rules = str(rules.get("dnsmasq", ""))
    for domain in dict.fromkeys(exported):
        if f"0.0.0.0 {domain}" not in hosts_rules:
            err(f"guard.rules.hosts: missing exported domain '{domain}'")
        if not any(f"||{s}^" in adguard_rules for s in suffixes(domain)):
            err(f"guard.rules.adguardhome: no rule covers '{domain}'")
        if not any(f"address=/{s}/" in dnsmasq_rules for s in suffixes(domain)):
            err(f"guard.rules.dnsmasq: no rule covers '{domain}'")

    # Generated rule files must be byte-identical to the JSON text (no drift).
    for name, key in (
        ("shortsguard-ublock.txt", "ublock"),
        ("shortsguard-adguard.txt", "adguard"),
        ("shortsguard-adguardhome.txt", "adguardhome"),
        ("shortsguard-hosts.txt", "hosts"),
        ("shortsguard-dnsmasq.txt", "dnsmasq"),
    ):
        path = ROOT / "blocklists" / name
        if not path.exists():
            continue  # reported by the EXPECTED_BLOCKLISTS loop
        text = str(rules.get(key, ""))
        expected = text if text.endswith("\n") else text + "\n"
        if path.read_text(encoding="utf-8") != expected:
            err(f"blocklists/{name} is out of date (run scripts/build_guard.py)")

    domains_path = ROOT / "blocklists" / "shortsguard-domains.txt"
    if domains_path.exists():
        lines = {
            line.strip()
            for line in domains_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")
        }
        for domain in dict.fromkeys(exported):
            if domain not in lines:
                err(f"blocklists/shortsguard-domains.txt: missing '{domain}'")

    for i, redirect in enumerate(doc.get("redirects") or []):
        where = f"guard.redirects[{i}]"
        pattern = redirect.get("pattern")
        try:
            re.compile(pattern or "")
        except re.error as exc:
            err(f"{where}: invalid regex ({exc})")
        if not str(redirect.get("target", "")).startswith("https://"):
            err(f"{where}: target must be an https URL")

    for i, guide in enumerate(doc.get("install_guides") or []):
        where = f"guard.install_guides[{i}]"
        if not guide.get("id") or not guide.get("title") or not guide.get("steps"):
            err(f"{where}: id, title and steps are required")

    # Generated artifacts
    for name in EXPECTED_BLOCKLISTS:
        path = ROOT / "blocklists" / name
        if not path.exists():
            err(f"missing generated file: {path.relative_to(ROOT)} (run scripts/build_guard.py)")
        elif path.stat().st_size == 0:
            err(f"generated file is empty: {path.relative_to(ROOT)}")

    userscript = ROOT / "guard" / "shorts-guard.user.js"
    extension_copy = ROOT / "guard" / "extension" / "shorts-guard.js"
    if not userscript.exists():
        err("missing guard/shorts-guard.user.js")
    elif not extension_copy.exists():
        err("missing guard/extension/shorts-guard.js (run scripts/build_guard.py)")
    elif userscript.read_bytes() != extension_copy.read_bytes():
        err("guard/extension/shorts-guard.js is out of date (run scripts/build_guard.py)")

    print(f"ShortsGuard: {len(profiles)} profiles, {len(target_ids)} targets, {len(seen_domains)} domains")
    return len(profiles)


# --------------------------------------------------------------------------- #
# Full DNS system
# --------------------------------------------------------------------------- #
def validate_system() -> int:
    try:
        doc = json.loads(SYSTEM_DATA.read_text(encoding="utf-8"))
    except FileNotFoundError:
        err(f"{SYSTEM_DATA} not found")
        return 0
    except json.JSONDecodeError as exc:
        err(f"invalid JSON in {SYSTEM_DATA}: {exc}")
        return 0

    for field in ("schema", "version", "updated", "title", "intro", "profiles", "platforms", "configs"):
        if not doc.get(field):
            err(f"system: missing top-level field '{field}'")
    if doc.get("schema") != SYSTEM_SCHEMA:
        warn(f"system: unexpected schema {doc.get('schema')!r} (expected {SYSTEM_SCHEMA!r})")

    intro = doc.get("intro") or {}
    for lang in ("en", "bn"):
        if not str(intro.get(lang, "")).strip():
            err(f"system: intro.{lang} is empty")

    try:
        dns_doc = json.loads(DNS_DATA.read_text(encoding="utf-8"))
        dns_hosts = {
            str(entry.get("host", "")).lower()
            for provider in dns_doc.get("providers", [])
            for entry in provider.get("hosts", [])
        }
    except Exception:
        dns_hosts = set()

    configs = doc.get("configs") or {}
    if not isinstance(configs, dict) or not configs:
        err("system: 'configs' must be a non-empty object")
        configs = {}
    for name, lines in configs.items():
        if not isinstance(lines, list) or not lines:
            err(f"system.configs[{name}]: must be a non-empty list of lines")
            continue
        for line in lines:
            if not isinstance(line, str):
                err(f"system.configs[{name}]: every line must be a string")
                continue
            for match in SYSTEM_PLACEHOLDER_RE.finditer(line):
                if match.group(1) not in SYSTEM_PLACEHOLDERS:
                    err(f"system.configs[{name}]: unknown placeholder {match.group(0)}")

    profiles = doc.get("profiles") or []
    if not isinstance(profiles, list) or not profiles:
        err("system: 'profiles' must be a non-empty list")
    seen_profiles: set[str] = set()
    for i, profile in enumerate(profiles):
        where = profile.get("name") or f"system.profiles[{i}]"
        for field in ("id", "name", "icon", "badge", "summary", "summary_bn",
                      "keeps", "android", "doh", "ipv4", "dot_host", "notes"):
            if not profile.get(field):
                err(f"{where}: missing required field '{field}'")
        pid = str(profile.get("id", ""))
        if pid and not SLUG_RE.match(pid):
            err(f"{where}: id '{pid}' is not a lowercase slug")
        if pid in seen_profiles:
            err(f"{where}: duplicate profile id '{pid}'")
        seen_profiles.add(pid)

        for key in ("android", "dot_host"):
            host = str(profile.get(key, ""))
            if host and not HOST_RE.match(host):
                err(f"{where}: '{host}' is not a valid hostname")
            if dns_hosts and host and host not in dns_hosts:
                err(f"{where}: {key} '{host}' is not in data/dns-servers.json (unverified)")

        doh = str(profile.get("doh", ""))
        if doh and not URL_RE.match(doh):
            err(f"{where}: doh '{doh}' is not an https URL")

        ipv4 = profile.get("ipv4")
        if not isinstance(ipv4, list) or len(ipv4) < 2:
            err(f"{where}: 'ipv4' needs at least two addresses")
        else:
            for ip in ipv4:
                if not IPV4_RE.match(str(ip)):
                    err(f"{where}: '{ip}' is not a valid IPv4 address")

        if not isinstance(profile.get("blocks"), list):
            err(f"{where}: 'blocks' must be a list (use [] for no filtering)")
        if not isinstance(profile.get("keeps"), list) or not profile.get("keeps"):
            err(f"{where}: 'keeps' must be a non-empty list")
        if not isinstance(profile.get("notes"), list):
            err(f"{where}: 'notes' must be a list")
        if not isinstance(profile.get("safesearch"), bool):
            warn(f"{where}: 'safesearch' should be true/false")

    platforms = doc.get("platforms") or []
    if not isinstance(platforms, list) or not platforms:
        err("system: 'platforms' must be a non-empty list")
    seen_platforms: set[str] = set()
    for i, platform in enumerate(platforms):
        where = platform.get("name") or f"system.platforms[{i}]"
        for field in ("id", "name", "icon", "summary", "steps"):
            if not platform.get(field):
                err(f"{where}: missing required field '{field}'")
        pid = str(platform.get("id", ""))
        if pid in seen_platforms:
            err(f"{where}: duplicate platform id '{pid}'")
        seen_platforms.add(pid)
        if not isinstance(platform.get("steps"), list) or not platform.get("steps"):
            err(f"{where}: 'steps' must be a non-empty list")
        files = platform.get("files") or ([platform.get("file")] if platform.get("file") else [])
        if not isinstance(files, list):
            err(f"{where}: 'files' must be a list")
            files = []
        for name in files:
            if name not in configs:
                err(f"{where}: config file '{name}' is not in system.configs")

    # Generated files must match the JSON templates exactly.
    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location("build_system", ROOT / "scripts" / "build_system.py")
        build_system = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(build_system)
    except Exception as exc:  # pragma: no cover - only when the script is broken
        err(f"system: cannot load scripts/build_system.py ({exc})")
        build_system = None

    if build_system is not None:
        for profile in profiles:
            pid = profile.get("id")
            if not pid:
                continue
            folder = SYSTEM_DIR / pid
            for name, lines in configs.items():
                if name == "safesearch.conf":
                    continue  # written once at system/safesearch.conf
                path = folder / name
                if not path.exists():
                    err(f"missing generated file: {path.relative_to(ROOT)} (run scripts/build_system.py)")
                    continue
                try:
                    expected = build_system.render(lines, profile)
                except Exception as exc:
                    err(f"system.configs[{name}]: cannot render ({exc})")
                    continue
                if path.read_text(encoding="utf-8") != expected:
                    err(f"{path.relative_to(ROOT)} is out of date (run scripts/build_system.py)")

        if "safesearch.conf" in configs and profiles:
            path = SYSTEM_DIR / "safesearch.conf"
            if not path.exists():
                err("missing generated file: system/safesearch.conf (run scripts/build_system.py)")
            elif path.read_text(encoding="utf-8") != build_system.render(configs["safesearch.conf"], profiles[0]):
                err("system/safesearch.conf is out of date (run scripts/build_system.py)")

        readme = SYSTEM_DIR / "README.md"
        if not readme.exists() or readme.stat().st_size == 0:
            err("missing generated file: system/README.md (run scripts/build_system.py)")

    print(f"DNS system: {len(profiles)} profiles, {len(platforms)} platforms, {len(configs)} configs")
    return len(profiles)


def main() -> int:
    strict = "--strict" in sys.argv[1:]
    validate_dns()
    validate_guard()
    validate_system()

    print(f"Warnings  : {len(warnings)}")
    for w in warnings:
        print(f"  warn: {w}")

    if errors:
        print(f"\n{len(errors)} error(s):")
        for e in errors:
            print(f"  - {e}")
        return 1

    if strict and warnings:
        print("\n--strict: treating warnings as errors.")
        return 1

    print("\nOK — data files and generated artifacts are valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
