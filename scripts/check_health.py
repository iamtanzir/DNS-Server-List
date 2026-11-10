#!/usr/bin/env python3
"""Live health-check every endpoint in data/dns-servers.json.

Every check performs a REAL DNS lookup, not just a TCP connect:

  * DoT  -> TLS handshake on port 853 + a length-prefixed DNS query for
            example.com/A, then parses the response header (rcode/answers).
  * DoH  -> POST application/dns-message to the endpoint's DoH URL, with a
            GET ?name=...&type=A (application/dns-json) fallback.

Results are written to data/health.json so the website can show a live
green/amber/red badge next to every hostname.

Status vocabulary
  ok        query answered (NOERROR and NXDOMAIN are both valid answers)
  cert      DNS answered, but the TLS certificate did not verify with the
            local trust store (often an outdated root store on the checking
            machine, not a broken resolver)
  http2     DoH-only endpoint that requires HTTP/2 (this checker speaks
            HTTP/1.1); the endpoint is alive
  refused   TCP connection refused
  timeout   no response within --timeout
  nxdomain  the endpoint hostname itself does not resolve
  error     anything else (recorded with the message)

Usage
  python scripts/check_health.py                    # all endpoints
  python scripts/check_health.py --host dns.google  # one endpoint
  python scripts/check_health.py --only-dot
  python scripts/check_health.py --timeout 6 --workers 24
  python scripts/check_health.py --no-write         # do not touch health.json
  python scripts/check_health.py --strict           # exit 1 if any host is dead

A red badge is useful information, not a build error, so the default exit
status is 0. CI uses --strict only where a human asks for it.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import http.client
import json
import shutil
import socket
import ssl
import struct
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "dns-servers.json"
OUT = ROOT / "data" / "health.json"

QUERY_NAME = "example.com"
QID = 0x5347  # "SG" — arbitrary, just non-zero
ALIVE = {"ok", "cert", "http2"}


# --------------------------------------------------------------------------- #
# DNS wire format helpers
# --------------------------------------------------------------------------- #
def build_query(name: str = QUERY_NAME, qtype: int = 1) -> bytes:
    """A minimal recursive DNS query (no EDNS so every resolver accepts it)."""
    header = struct.pack("!HHHHHH", QID, 0x0100, 1, 0, 0, 0)  # RD=1
    qname = b"".join(bytes((len(label),)) + label.encode("ascii") for label in name.split(".")) + b"\x00"
    return header + qname + struct.pack("!HH", qtype, 1)  # QTYPE A, QCLASS IN


def parse_response(data: bytes) -> tuple[int, int]:
    """Return (rcode, answer_count). Raises ValueError on a truncated packet."""
    if len(data) < 12:
        raise ValueError(f"short DNS response ({len(data)} bytes)")
    _qid, flags, _qdcount, ancount = struct.unpack("!HHHH", data[:8])
    if flags & 0x0200:
        raise ValueError("truncated (TC) response")
    return flags & 0x000F, ancount


def recv_exact(sock, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("connection closed mid-response")
        buf += chunk
    return buf


def resolve_addresses(host: str, port: int) -> list[str]:
    """All addresses for a host, IPv4 first (IPv6 is often broken locally)."""
    infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    addrs: list[str] = []
    for info in infos:
        addr = info[4][0]
        if addr not in addrs:
            addrs.append(addr)
    addrs.sort(key=lambda a: ":" in a)  # IPv4 before IPv6
    return addrs


def describe_error(exc: BaseException) -> str:
    msg = str(exc).strip().splitlines()[0] if str(exc).strip() else ""
    return f"{type(exc).__name__}: {msg}"[:200]


# --------------------------------------------------------------------------- #
# DoT
# --------------------------------------------------------------------------- #
def _dot_query(addr: str, host: str, timeout: float, context: ssl.SSLContext) -> dict:
    raw = socket.create_connection((addr, 853), timeout=timeout)
    raw.settimeout(timeout)
    try:
        with context.wrap_socket(raw, server_hostname=host) as tls:
            query = build_query()
            tls.sendall(struct.pack("!H", len(query)) + query)
            length = struct.unpack("!H", recv_exact(tls, 2))[0]
            rcode, answers = parse_response(recv_exact(tls, length))
            return {"rcode": rcode, "answers": answers}
    finally:
        try:
            raw.close()
        except OSError:
            pass


def check_dot(host: str, timeout: float) -> dict:
    started = time.perf_counter()
    result: dict = {"status": "error", "latency_ms": None}

    try:
        addresses = resolve_addresses(host, 853)
    except socket.gaierror as exc:
        result.update(status="nxdomain", error=f"hostname does not resolve: {exc}")
        return result
    if not addresses:
        result.update(status="nxdomain", error="hostname has no addresses")
        return result
    result["ip"] = addresses[0]

    verified = ssl.create_default_context()
    cert_error: str | None = None
    failures: list[tuple[str, BaseException]] = []

    # Pass 1 — verified TLS, trying every address.
    for addr in addresses:
        try:
            result.update(status="ok", **_dot_query(addr, host, timeout, verified))
            result["latency_ms"] = round((time.perf_counter() - started) * 1000)
            return result
        except ssl.SSLCertVerificationError as exc:
            cert_error = describe_error(exc)
            break  # same certificate on every address; go to pass 2
        except BaseException as exc:  # noqa: BLE001 - classify below
            failures.append((addr, exc))

    # Pass 2 — the chain did not verify; retry unverified so we can tell a
    # healthy resolver from a dead one.
    if cert_error:
        insecure = ssl._create_unverified_context()
        for addr in addresses:
            try:
                result.update(status="cert", cert_error=cert_error, **_dot_query(addr, host, timeout, insecure))
                result["latency_ms"] = round((time.perf_counter() - started) * 1000)
                return result
            except BaseException as exc:  # noqa: BLE001
                failures.append((addr, exc))

    result["latency_ms"] = round((time.perf_counter() - started) * 1000)
    kinds = {type(exc).__name__ for _addr, exc in failures}
    if failures and all(isinstance(exc, (socket.timeout, TimeoutError)) for _a, exc in failures):
        result.update(status="timeout", error=f"no answer on port 853 within {timeout:g}s")
    elif failures and all(isinstance(exc, ConnectionRefusedError) for _a, exc in failures):
        result.update(status="refused", error="port 853 refused the connection")
    elif failures:
        result.update(status="error", error=describe_error(failures[-1][1]))
    else:
        result.update(status="error", error="no usable address")
    if cert_error:
        result["cert_error"] = cert_error
    return result


# --------------------------------------------------------------------------- #
# DoH
# --------------------------------------------------------------------------- #
def _doh_http(url: str, timeout: float, verify: bool, _depth: int = 0) -> dict:
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https" or not parts.hostname:
        raise ValueError(f"not an https URL: {url}")
    context = ssl.create_default_context() if verify else ssl._create_unverified_context()
    path = parts.path or "/"

    attempts = [
        (
            "POST",
            path + (("?" + parts.query) if parts.query else ""),
            build_query(),
            {
                "Content-Type": "application/dns-message",
                "Accept": "application/dns-message",
                "User-Agent": "dns-server-list-health/1.0",
            },
            "wire",
        ),
        (
            "GET",
            path + (("&" if parts.query else "?") + f"name={QUERY_NAME}&type=A"),
            None,
            {"Accept": "application/dns-json", "User-Agent": "dns-server-list-health/1.0"},
            "json",
        ),
    ]

    last: BaseException | None = None
    for method, target, body, headers, kind in attempts:
        # A fresh connection per attempt: a failed request leaves http.client's
        # socket unusable ("CannotSendRequest: Request-sent").
        conn = http.client.HTTPSConnection(parts.hostname, parts.port or 443, timeout=timeout, context=context)
        try:
            conn.request(method, target, body=body, headers=headers)
            resp = conn.getresponse()
            payload = resp.read()
            if resp.status in (301, 302, 303, 307, 308):
                location = resp.getheader("Location")
                if location and _depth < 3:
                    return _doh_http(urllib.parse.urljoin(url, location), timeout, verify, _depth + 1)
                raise ValueError(f"HTTP {resp.status} without a usable Location")
            if resp.status in (400, 404, 405, 415):
                last = ValueError(f"HTTP {resp.status} {resp.reason}")
                continue
            if resp.status == 505:
                return {"status": "http2", "error": "server requires HTTP/2 (works in browsers)", "url": url}
            if resp.status >= 300:
                raise ValueError(f"HTTP {resp.status} {resp.reason}")
            if kind == "json":
                doc = json.loads(payload)
                rcode = int(doc.get("Status", -1))
                if rcode < 0:
                    raise ValueError("JSON response has no Status field")
                answers = len(doc.get("Answer") or [])
            else:
                rcode, answers = parse_response(payload)
            return {"status": "ok", "rcode": rcode, "answers": answers, "method": method, "url": url}
        except ssl.SSLCertVerificationError:
            raise
        except BaseException as exc:  # noqa: BLE001
            last = exc
        finally:
            try:
                conn.close()
            except OSError:
                pass
    raise last or ConnectionError("no response")


CURL = shutil.which("curl")
CURL_MARK = b"__SG_STATUS__"


def _decode_doh_body(payload: bytes) -> dict:
    if payload.lstrip().startswith(b"{"):
        doc = json.loads(payload)
        rcode = int(doc.get("Status", -1))
        if rcode < 0:
            raise ValueError("JSON response has no Status field")
        return {"rcode": rcode, "answers": len(doc.get("Answer") or []), "method": "GET-json"}
    rcode, answers = parse_response(payload)
    return {"rcode": rcode, "answers": answers, "method": "POST"}


def _doh_curl(url: str, timeout: float, insecure: bool) -> dict:
    """curl handles HTTP/2, HTTP/3 negotiation and redirects — all of which
    some public DoH servers require. Returns the *effective* URL too."""
    cmd = [CURL, "-sS", "--location", "--max-time", str(timeout), "--proto", "=https",
           "-H", "content-type: application/dns-message",
           "-H", "accept: application/dns-message",
           "--data-binary", "@-",
           "-w", CURL_MARK.decode() + "%{http_code} %{url_effective}",
           url]
    if insecure:
        cmd.insert(1, "-k")
    try:
        proc = subprocess.run(cmd, input=build_query(), capture_output=True, timeout=timeout + 5)
    except subprocess.TimeoutExpired:
        raise TimeoutError(f"curl timed out after {timeout:g}s") from None

    if proc.returncode != 0:
        message = proc.stderr.decode("utf-8", "replace").strip() or f"curl exit {proc.returncode}"
        if "certificate" in message.lower() or "ssl" in message.lower():
            raise ssl.SSLCertVerificationError(message)
        if "timed out" in message.lower():
            raise TimeoutError(message)
        raise ConnectionError(message[:200])

    body, marker, meta = proc.stdout.rpartition(CURL_MARK)
    if not marker:
        raise ValueError("curl produced no status marker")
    code_text, _, final_url = meta.decode("utf-8", "replace").partition(" ")
    code = int(code_text or 0)
    if code == 505:
        return {"status": "http2", "error": "server requires HTTP/2 (works in browsers)", "url": final_url or url}
    if code != 200:
        raise ValueError(f"HTTP {code}")
    decoded = _decode_doh_body(body)
    decoded.update(status="ok", url=final_url or url)
    return decoded


def _doh_http2_probe(url: str, timeout: float) -> dict:
    """Some servers (Mullvad, HE) refuse HTTP/1.1 but negotiate h2 via ALPN.
    That is still a working DoH endpoint in every browser, so report it as such."""
    parts = urllib.parse.urlsplit(url)
    context = ssl.create_default_context()
    try:
        context.set_alpn_protocols(["h2", "http/1.1"])
    except NotImplementedError:
        pass
    with socket.create_connection((parts.hostname, parts.port or 443), timeout=timeout) as raw:
        with context.wrap_socket(raw, server_hostname=parts.hostname) as tls:
            if tls.selected_alpn_protocol() == "h2":
                return {"status": "http2", "error": "HTTP/2-only DoH (works in browsers)", "url": url}
    raise ConnectionError("server did not negotiate HTTP/2")


def check_doh(url: str, timeout: float) -> dict:
    started = time.perf_counter()
    result: dict = {"status": "error", "latency_ms": None, "url": url}
    http09 = False

    probes = []
    if CURL:
        probes.append(lambda verify: _doh_curl(url, timeout, insecure=not verify))
    probes.append(lambda verify: _doh_http(url, timeout, verify=verify))

    for probe in probes:
        try:
            result.update(probe(True))
            break
        except ssl.SSLCertVerificationError as exc:
            cert_error = describe_error(exc)
            try:
                result.update(probe(False))
                result["status"] = "cert"
                result["cert_error"] = cert_error
                break
            except BaseException as exc2:  # noqa: BLE001
                result.update(status="error", cert_error=cert_error, error=describe_error(exc2))
        except (socket.timeout, TimeoutError):
            result.update(status="timeout", error=f"no answer within {timeout:g}s")
        except ConnectionRefusedError:
            result.update(status="refused", error="connection refused")
        except BaseException as exc:  # noqa: BLE001
            message = describe_error(exc)
            if "HTTP/0.9" in message or "BadStatusLine" in message:
                http09 = True
            result.update(status="error", error=message)

    if http09 and result["status"] == "error":
        try:
            result.update(_doh_http2_probe(url, timeout))
        except BaseException:  # noqa: BLE001 - keep the original error
            pass

    result["latency_ms"] = round((time.perf_counter() - started) * 1000)
    return result


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def candidate_doh_urls(entry: dict) -> list[str]:
    """Preferred URL first, then the conventional fallbacks used by most servers."""
    urls: list[str] = []
    if entry.get("doh"):
        urls.append(entry["doh"])
    host = entry["host"]
    urls += [f"https://{host}/dns-query", f"https://{host}/"]
    seen: set[str] = set()
    return [u for u in urls if not (u in seen or seen.add(u))]


def check_entry(entry: dict, timeout: float) -> dict:
    proto = entry["protocol"]
    out: dict = {"protocol": proto}
    if proto in ("dot", "dot+doh"):
        out["dot"] = check_dot(entry["host"], timeout)
    if proto in ("doh", "dot+doh"):
        tried: list[str] = []
        best: dict | None = None
        for url in candidate_doh_urls(entry):
            res = check_doh(url, timeout)
            tried.append(f"{url} -> {res.get('error') or res['status']}")
            if res["status"] in ALIVE:
                best = res
                break
        out["doh"] = best or {"status": "error", "error": "; ".join(tried)}

    checks = [v for k, v in out.items() if k in ("dot", "doh")]
    if checks and all(c["status"] in ALIVE for c in checks):
        out["overall"] = "ok"
    elif any(c["status"] in ALIVE for c in checks):
        out["overall"] = "partial"
    else:
        out["overall"] = "dead"
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", action="append", help="only check this hostname (repeatable)")
    parser.add_argument("--only-dot", action="store_true", help="skip DoH checks")
    parser.add_argument("--only-doh", action="store_true", help="skip DoT checks")
    parser.add_argument("--timeout", type=float, default=6.0)
    parser.add_argument("--workers", type=int, default=24)
    parser.add_argument("--no-write", action="store_true")
    parser.add_argument("--strict", action="store_true", help="exit 1 if an endpoint is dead")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    doc = json.loads(DATA.read_text(encoding="utf-8"))
    wanted = {h.lower() for h in (args.host or [])}
    entries: list[dict] = []
    for provider in doc["providers"]:
        for entry in provider["hosts"]:
            if wanted and entry["host"].lower() not in wanted:
                continue
            if args.only_dot and entry["protocol"] == "doh":
                continue
            if args.only_doh and entry["protocol"] == "dot":
                continue
            entries.append(entry)

    if not entries:
        print("No endpoints matched.", file=sys.stderr)
        return 1

    if not args.quiet:
        print(f"Checking {len(entries)} endpoint(s) with {args.workers} workers, {args.timeout:g}s timeout…\n")

    results: dict[str, dict] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(check_entry, entry, args.timeout): entry for entry in entries}
        for fut in concurrent.futures.as_completed(futures):
            entry = futures[fut]
            try:
                results[entry["host"]] = fut.result()
            except BaseException as exc:  # noqa: BLE001 - never lose a host to a crash
                results[entry["host"]] = {"overall": "dead", "error": describe_error(exc)}

    rows = sorted(results.items(), key=lambda kv: (kv[1]["overall"] != "ok", kv[0]))
    if not args.quiet:
        icon = {"ok": "OK  ", "partial": "PART", "dead": "DEAD"}
        for host, res in rows:
            parts = []
            for proto in ("dot", "doh"):
                if proto in res:
                    r = res[proto]
                    latency = f"{r.get('latency_ms')}ms" if r.get("latency_ms") is not None else "-"
                    detail = r.get("error") or r.get("cert_error") or ""
                    parts.append(f"{proto}:{r['status']}/{latency}{(' ' + detail) if detail else ''}")
            print(f"[{icon[res['overall']]}] {host:<42} {' | '.join(parts)}")

    ok = sum(1 for r in results.values() if r["overall"] == "ok")
    partial = sum(1 for r in results.values() if r["overall"] == "partial")
    dead = sum(1 for r in results.values() if r["overall"] == "dead")
    if not args.quiet:
        print(f"\n{ok} healthy · {partial} partial · {dead} dead · {len(results)} checked")
        for host, res in rows:
            if res["overall"] == "dead":
                why = res.get("error") or (res.get("dot") or {}).get("error") or (res.get("doh") or {}).get("error")
                print(f"  dead: {host} — {why}")

    if not args.no_write:
        snapshot = {
            "schema": "dns-health/v1",
            "checked": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "query": f"{QUERY_NAME}/A",
            "summary": {"checked": len(results), "healthy": ok, "partial": partial, "dead": dead},
            "results": results,
        }
        OUT.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        if not args.quiet:
            print(f"Wrote {OUT.relative_to(ROOT)}")

    return 1 if (args.strict and dead) else 0


if __name__ == "__main__":
    sys.exit(main())
