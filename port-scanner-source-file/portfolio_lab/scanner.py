#!/usr/bin/env python3
"""Small, deliberately scope-limited TCP connect audit for a learning lab."""
import argparse
import errno
import ipaddress
import json
import socket
from datetime import datetime, timezone
from pathlib import Path

RFC1918 = tuple(ipaddress.ip_network(net) for net in (
    "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"
))


def parse_ports(text: str) -> list[int]:
    pieces = text.split(",")
    if not 1 <= len(pieces) <= 32:
        raise ValueError("specify 1 to 32 comma-separated ports")
    if any(not part.isascii() or not part.isdecimal() for part in pieces):
        raise ValueError("each port must contain ASCII digits only")
    ports = [int(part) for part in pieces]
    if any(not 1 <= port <= 65535 for port in ports):
        raise ValueError("port numbers must be between 1 and 65535")
    if len(ports) != len(set(ports)):
        raise ValueError("duplicate ports are not accepted")
    return ports


def check_scope(target: str, scope_text: str | None, authorized: bool) -> str:
    try:
        address = ipaddress.IPv4Address(target)
    except ipaddress.AddressValueError as exc:
        raise ValueError("target must be a literal IPv4 address") from exc
    if address.is_loopback and scope_text is None:
        return "127.0.0.0/8 (loopback only)"
    if not authorized or scope_text is None:
        raise ValueError("non-default scope requires --scope-cidr and --authorized")
    try:
        network = ipaddress.IPv4Network(scope_text, strict=True)
    except ValueError as exc:
        raise ValueError("scope-cidr must be a valid IPv4 network") from exc
    if network.prefixlen < 24:
        raise ValueError("a lab scope must be /24 or narrower")
    if not any(network.subnet_of(private) for private in RFC1918):
        raise ValueError("lab scope must be within an RFC1918 private range")
    if address not in network:
        raise ValueError("target is outside the declared scope")
    return str(network)


def probe(target: str, port: int, timeout: float) -> dict:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            code = sock.connect_ex((target, port))
    except TimeoutError:
        code = errno.ETIMEDOUT
    except OSError as exc:
        code = exc.errno if exc.errno is not None else -1
    if code == 0:
        state = "open"
    elif code == errno.ECONNREFUSED:
        state = "refused"
    elif code == errno.ETIMEDOUT:
        state = "timeout"
    elif code in (errno.EHOSTUNREACH, errno.ENETUNREACH):
        state = "unreachable"
    else:
        state = "error_or_unknown"
    return {"port": port, "state": state, "errno": code}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", default="127.0.0.1")
    parser.add_argument("--ports", default="8765,8766")
    parser.add_argument("--timeout", type=float, default=0.5)
    parser.add_argument("--scope-cidr", default=None)
    parser.add_argument("--authorized", action="store_true")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    try:
        ports = parse_ports(args.ports)
        scope = check_scope(args.target, args.scope_cidr, args.authorized)
        if not 0.1 <= args.timeout <= 3.0:
            raise ValueError("timeout must be between 0.1 and 3 seconds")
    except ValueError as exc:
        parser.error(str(exc))
    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "target": args.target,
        "scope": scope,
        "timeout_seconds": args.timeout,
        "results": [probe(args.target, port, args.timeout) for port in ports],
    }
    output = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        destination = Path(args.output)
        try:
            with destination.open("x", encoding="utf-8") as file:
                file.write(output)
        except FileExistsError:
            parser.error("output already exists; refusing to overwrite")
        except OSError as exc:
            parser.error(f"cannot write output: {exc}")
        print(f"report written to {destination}")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
