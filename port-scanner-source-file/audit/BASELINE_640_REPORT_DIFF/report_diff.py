#!/usr/bin/env python3
"""Compare two locally stored TCP Connect reports without network traffic."""
import argparse
from datetime import datetime
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
    try:
        report = json.loads(raw, object_pairs_hook=no_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ValueError(f"{path}: invalid UTF-8 JSON") from exc
    if not isinstance(report, dict):
        raise ValueError(f"{path}: expected a JSON object")
    target = report.get("target")
    if type(target) is not str:
        raise ValueError(f"{path}: target must be text, not a JSON number")
    try:
        ipaddress.IPv4Address(target)
    except (ipaddress.AddressValueError, TypeError) as exc:
        raise ValueError(f"{path}: target must be a literal IPv4 address") from exc
    timestamp = report.get("timestamp_utc")
    try:
        parsed = datetime.fromisoformat(timestamp)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{path}: timestamp_utc must be ISO 8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{path}: timestamp_utc must specify a timezone")
    timeout = report.get("timeout_seconds")
    if type(timeout) not in (int, float) or not math.isfinite(timeout):
        raise ValueError(f"{path}: timeout_seconds must be a finite number")
    if not 0.1 <= timeout <= 3.0:
        raise ValueError(f"{path}: timeout_seconds outside scanner limits")
    if not isinstance(report.get("scope"), str) or not report["scope"]:
        raise ValueError(f"{path}: missing scan scope")
    rows = report.get("results")
    if not isinstance(rows, list) or not 1 <= len(rows) <= 32:
        raise ValueError(f"{path}: results must contain 1 to 32 entries")
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(f"{path}: each result must be an object")
        port, state, code = row.get("port"), row.get("state"), row.get("errno")
        if type(port) is not int or not 1 <= port <= 65535 or port in seen:
            raise ValueError(f"{path}: invalid or duplicate port")
        if type(state) is not str or state not in STATES:
            raise ValueError(f"{path}: invalid state for port {port}")
        if type(code) is not int:
            raise ValueError(f"{path}: errno must be an integer")
        seen.add(port)
    return report


def compare(before: dict, after: dict) -> dict:
    if before["target"] != after["target"]:
        raise ValueError("reports target different IPv4 addresses")
    if before["scope"] != after["scope"]:
        raise ValueError("reports have different declared scan scopes")
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
        "before_timestamp_utc": before["timestamp_utc"],
        "after_timestamp_utc": after["timestamp_utc"],
        "ports_checked": len(old),
        "state_changes": changes,
        "unchanged_ports": len(old) - len(changes),
        "note": "TCP observations only; a state change does not prove vulnerability.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", required=True, type=Path)
    parser.add_argument("--after", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
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
