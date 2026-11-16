#!/usr/bin/env python3
"""Compare two locally stored TCP Connect reports without network traffic."""
import argparse
from datetime import datetime, timedelta
import ipaddress
import json
import math
from pathlib import Path

MAX_REPORT_BYTES = 1024 * 1024
STATES = frozenset({"open", "refused", "timeout", "unreachable", "error_or_unknown"})


def read_report(path: Path) -> dict:
    with path.open("rb") as stream:
        raw = stream.read(MAX_REPORT_BYTES + 1)
    if len(raw) > MAX_REPORT_BYTES:
        raise ValueError(f"{path}: report exceeds 1 MiB")
    def no_duplicate_keys(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                raise ValueError(f"duplicate JSON key: {key}")
            obj[key] = value
        return obj
    def reject_nonstandard_constant(value):
        raise ValueError(f"{path}: non-standard JSON constant {value}")
    try:
        report = json.loads(
            raw, object_pairs_hook=no_duplicate_keys,
            parse_constant=reject_nonstandard_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ValueError(f"{path}: invalid UTF-8 JSON") from exc
    if not isinstance(report, dict):
        raise ValueError(f"{path}: expected a JSON object")
    required_report_fields = {"timestamp_utc", "target", "scope", "timeout_seconds", "results"}
    if set(report) != required_report_fields:
        missing = sorted(required_report_fields - report.keys())
        unexpected = sorted(report.keys() - required_report_fields)
        raise ValueError(f"{path}: report fields mismatch; missing={missing}, unexpected={unexpected}")
    target = report.get("target")
    if type(target) is not str:
        raise ValueError(f"{path}: target must be text, not a JSON number")
    try:
        target_address = ipaddress.IPv4Address(target)
    except (ipaddress.AddressValueError, TypeError) as exc:
        raise ValueError(f"{path}: target must be a literal IPv4 address") from exc
    timestamp = report.get("timestamp_utc")
    try:
        parsed = datetime.fromisoformat(timestamp)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{path}: timestamp_utc must be ISO 8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{path}: timestamp_utc must specify a timezone")
    if parsed.utcoffset() != timedelta(0):
        raise ValueError(f"{path}: timestamp_utc must use UTC (+00:00)")
    timeout = report.get("timeout_seconds")
    if type(timeout) not in (int, float) or not math.isfinite(timeout):
        raise ValueError(f"{path}: timeout_seconds must be a finite number")
    if not 0.1 <= timeout <= 3.0:
        raise ValueError(f"{path}: timeout_seconds outside scanner limits")
    if not isinstance(report.get("scope"), str) or not report["scope"]:
        raise ValueError(f"{path}: missing scan scope")
    declared_scope = report["scope"]
    if declared_scope == "127.0.0.0/8 (loopback only)":
        if not target_address.is_loopback:
            raise ValueError(f"{path}: loopback scope does not cover target")
    else:
        try:
            network = ipaddress.IPv4Network(declared_scope, strict=True)
        except ValueError as exc:
            raise ValueError(f"{path}: scope must be a valid IPv4 CIDR") from exc
        private_ranges = tuple(ipaddress.IPv4Network(cidr) for cidr in (
            "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"
        ))
        if network.prefixlen < 24 or not any(network.subnet_of(base) for base in private_ranges):
            raise ValueError(f"{path}: scope must be a private /24 or narrower lab subnet")
        if target_address not in network:
            raise ValueError(f"{path}: target is outside declared scope")
    rows = report.get("results")
    if not isinstance(rows, list) or not 1 <= len(rows) <= 32:
        raise ValueError(f"{path}: results must contain 1 to 32 entries")
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(f"{path}: each result must be an object")
        required_row_fields = {"port", "state", "errno"}
        if set(row) != required_row_fields:
            missing = sorted(required_row_fields - row.keys())
            unexpected = sorted(row.keys() - required_row_fields)
            raise ValueError(f"{path}: result fields mismatch; missing={missing}, unexpected={unexpected}")
        port, state, code = row.get("port"), row.get("state"), row.get("errno")
        if type(port) is not int or not 1 <= port <= 65535 or port in seen:
            raise ValueError(f"{path}: invalid or duplicate port")
        if type(state) is not str or state not in STATES:
            raise ValueError(f"{path}: invalid state for port {port}")
        if type(code) is not int:
            raise ValueError(f"{path}: errno must be an integer")
        if state == "open" and code != 0:
            raise ValueError(f"{path}: open requires errno 0 (port {port})")
        if state != "open" and code == 0:
            raise ValueError(f"{path}: non-open state cannot have errno 0 (port {port})")
        seen.add(port)
    return report


def compare(before: dict, after: dict) -> dict:
    if before["target"] != after["target"]:
        raise ValueError("reports target different IPv4 addresses")
    if before["scope"] != after["scope"]:
        raise ValueError("reports have different declared scan scopes")
    if before["timeout_seconds"] != after["timeout_seconds"]:
        raise ValueError("reports must use the same TCP connection timeout")
    old = {row["port"]: row for row in before["results"]}
    new = {row["port"]: row for row in after["results"]}
    if set(old) != set(new):
        raise ValueError("reports must contain the same port set")
    if datetime.fromisoformat(before["timestamp_utc"]) >= datetime.fromisoformat(after["timestamp_utc"]):
        raise ValueError("before must have an earlier timestamp than after")
    changes = [
        {"port": port, "before": old[port]["state"], "after": new[port]["state"]}
        for port in sorted(old)
        if old[port]["state"] != new[port]["state"]
    ]
    return {
        "target": before["target"],
        "scope": before["scope"],
        "timeout_seconds": before["timeout_seconds"],
        "before_timestamp_utc": before["timestamp_utc"],
        "after_timestamp_utc": after["timestamp_utc"],
        "ports_checked": len(old),
        "state_changes": changes,
        "unchanged_ports": len(old) - len(changes),
        "note": "TCP observations only; a state change does not prove vulnerability.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path, help="earlier JSON report for comparison")
    parser.add_argument("--after", type=Path, help="later JSON report for comparison")
    parser.add_argument("--validate", type=Path, help="check one JSON report without comparing it")
    parser.add_argument("--output", type=Path, help="create a new comparison JSON file")
    args = parser.parse_args()
    try:
        if args.validate is not None:
            if args.before is not None or args.after is not None or args.output is not None:
                raise ValueError("--validate cannot be combined with --before, --after, or --output")
            validated = read_report(args.validate)
            print(f"VALID: {args.validate} (target={validated['target']}, ports={len(validated['results'])})")
            return 0
        if args.before is None or args.after is None:
            raise ValueError("--before and --after are required unless --validate is supplied")
        if args.before.resolve() == args.after.resolve():
            raise ValueError("before and after must be different files")
        comparison = compare(read_report(args.before), read_report(args.after))
        content = json.dumps(comparison, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(content)
            print(f"comparison written to {args.output}")
        else:
            print(content, end="")
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
