"""Offline comparison tests: no real sockets or external networks."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from report_diff import compare, read_report


def example(timestamp="2026-11-16T10:00:00+00:00", target="127.0.0.1"):
    return {
        "timestamp_utc": timestamp,
        "target": target,
        "scope": "127.0.0.0/8 (loopback only)",
        "timeout_seconds": 0.5,
        "results": [
            {"port": 8765, "state": "open", "errno": 0},
            {"port": 8766, "state": "refused", "errno": 111},
        ],
    }


class ReportReadingTests(unittest.TestCase):
    def write_report(self, folder, value):
        dest = Path(folder) / "report.json"
        dest.write_text(json.dumps(value), encoding="utf-8")
        return dest

    def test_valid_report(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(len(read_report(self.write_report(folder, example()))["results"]), 2)

    def test_bad_json_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.json"
            path.write_text("{unfinished", encoding="utf-8")
            with self.assertRaises(ValueError):
                read_report(path)

    def test_duplicate_port_is_rejected(self):
        report = example()
        report["results"].append(report["results"][0].copy())
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "duplicate"):
                read_report(self.write_report(folder, report))

    def test_boolean_port_is_not_integer_port(self):
        report = example()
        report["results"][0]["port"] = True
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                read_report(self.write_report(folder, report))

    def test_unknown_state_is_rejected(self):
        report = example()
        report["results"][0]["state"] = "filtered"
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "invalid state"):
                read_report(self.write_report(folder, report))

    def test_nonstring_state_is_rejected(self):
        report = example()
        report["results"][0]["state"] = []
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "invalid state"):
                read_report(self.write_report(folder, report))

    def test_duplicate_json_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "duplicate.json"
            path.write_text('{"target":"127.0.0.1","target":"127.0.0.2"}')
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                read_report(path)

    def test_integer_ipv4_target_is_rejected(self):
        report = example()
        report["target"] = 2130706433
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "must be text"):
                read_report(self.write_report(folder, report))

    def test_naive_time_is_rejected(self):
        report = example(timestamp="2026-11-16T10:00:00")
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "timezone"):
                read_report(self.write_report(folder, report))

    def test_non_utc_offset_is_rejected(self):
        report = example(timestamp="2026-11-16T19:00:00+09:00")
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "must use UTC"):
                read_report(self.write_report(folder, report))

    def test_loopback_scope_cannot_claim_private_host(self):
        report = example(target="192.168.56.7")
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "does not cover target"):
                read_report(self.write_report(folder, report))

    def test_rejects_public_or_noncanonical_lab_scope(self):
        report = example(target="8.8.8.8")
        report["scope"] = "8.8.8.0/24"
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "private /24"):
                read_report(self.write_report(folder, report))
        report["scope"] = "8.8.8.1/24"
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "valid IPv4 CIDR"):
                read_report(self.write_report(folder, report))

    def test_accepts_declared_private_lab_scope(self):
        report = example(target="192.168.56.7")
        report["scope"] = "192.168.56.0/24"
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(read_report(self.write_report(folder, report))["scope"], "192.168.56.0/24")

    def test_nonfinite_timeout_is_rejected(self):
        report = example()
        report["timeout_seconds"] = float("nan")
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "finite"):
                read_report(self.write_report(folder, report))

    def test_oversized_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "huge.json"
            path.write_bytes(b" " * (1024 * 1024 + 1))
            with self.assertRaisesRegex(ValueError, "1 MiB"):
                read_report(path)


class ComparisonTests(unittest.TestCase):
    def test_changed_port_and_sorted_result(self):
        earlier = example()
        later = example("2026-11-16T10:01:00+00:00")
        later["results"][0].update(state="refused", errno=111)
        delta = compare(earlier, later)
        self.assertEqual(delta["state_changes"], [{"port": 8765, "before": "open", "after": "refused"}])
        self.assertEqual(delta["unchanged_ports"], 1)

    def test_same_status_is_no_change_even_if_errno_differs(self):
        earlier = example()
        later = example("2026-11-16T10:01:00+00:00")
        later["results"][1]["errno"] = 999
        self.assertEqual(compare(earlier, later)["state_changes"], [])

    def test_mismatched_target_rejected(self):
        with self.assertRaisesRegex(ValueError, "different IPv4"):
            compare(example(), example("2026-11-16T10:01:00+00:00", "127.0.0.2"))

    def test_mismatched_timeout_is_rejected(self):
        earlier = example()
        later = example("2026-11-16T10:01:00+00:00")
        later["timeout_seconds"] = 3.0
        with self.assertRaisesRegex(ValueError, "same TCP connection timeout"):
            compare(earlier, later)

    def test_comparison_preserves_conditions(self):
        earlier = example()
        later = example("2026-11-16T10:01:00+00:00")
        result = compare(earlier, later)
        self.assertEqual(result["timeout_seconds"], earlier["timeout_seconds"])
        self.assertEqual(result["scope"], earlier["scope"])

    def test_mismatched_ports_rejected(self):
        later = example("2026-11-16T10:01:00+00:00")
        later["results"].pop()
        with self.assertRaisesRegex(ValueError, "same port set"):
            compare(example(), later)

    def test_mismatched_scope_rejected(self):
        later = example("2026-11-16T10:01:00+00:00")
        later["scope"] = "127.0.0.0/8 (another description)"
        with self.assertRaisesRegex(ValueError, "scopes"):
            compare(example(), later)

    def test_backwards_time_rejected(self):
        with self.assertRaisesRegex(ValueError, "earlier"):
            compare(example(), example("2026-11-16T09:59:00+00:00"))


class OfflineCLITests(unittest.TestCase):
    def test_cli_output_and_overwrite_protection(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            before = root / "before.json"
            after = root / "after.json"
            output = root / "difference.json"
            before.write_text(json.dumps(example()), encoding="utf-8")
            later = example("2026-11-16T10:01:00+00:00")
            later["results"][0].update(state="refused", errno=111)
            after.write_text(json.dumps(later), encoding="utf-8")
            cmd = [sys.executable, "report_diff.py", "--before", str(before), "--after", str(after), "--output", str(output)]
            first = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            saved = output.read_text(encoding="utf-8")
            self.assertEqual(json.loads(saved)["state_changes"][0]["port"], 8765)
            second = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(second.returncode, 2)
            self.assertEqual(output.read_text(encoding="utf-8"), saved)

    def test_cli_rejects_same_input_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "same.json"
            path.write_text(json.dumps(example()), encoding="utf-8")
            run = subprocess.run([sys.executable, "report_diff.py", "--before", str(path), "--after", str(path)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 2)
            self.assertIn("different files", run.stderr)


class ReportStateConsistencyTests(unittest.TestCase):
    def test_open_with_nonzero_errno_is_rejected(self):
        report = example()
        report["results"][0]["errno"] = 111
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "incorrect.json"
            path.write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "open requires errno 0"):
                read_report(path)

    def test_non_open_with_zero_errno_is_rejected(self):
        report = example()
        report["results"][1]["errno"] = 0
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "incorrect.json"
            path.write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "non-open state cannot have errno 0"):
                read_report(path)

    def test_nonzero_unknown_errno_is_retained(self):
        report = example()
        report["results"][1].update(state="error_or_unknown", errno=999)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "uncertain.json"
            path.write_text(json.dumps(report), encoding="utf-8")
            self.assertEqual(read_report(path)["results"][1]["errno"], 999)


if __name__ == "__main__":
    unittest.main()
