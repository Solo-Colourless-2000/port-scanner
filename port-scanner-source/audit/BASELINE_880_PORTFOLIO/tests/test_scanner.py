"""Unit and loopback integration tests for the example scanner."""
import errno
import socket
import unittest
from unittest.mock import patch
import subprocess
import sys
import tempfile
from pathlib import Path

from scanner import check_scope, parse_ports, probe


class ParsePortTests(unittest.TestCase):
    def test_accepts_distinct_valid_ports(self):
        self.assertEqual(parse_ports("22,80,443"), [22, 80, 443])

    def test_rejects_invalid_ranges_and_duplicate(self):
        for value in ("0", "65536", "22,22", "22-80", "", "1,"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_ports(value)

    def test_rejects_more_than_32_ports(self):
        with self.assertRaises(ValueError):
            parse_ports(",".join(str(x) for x in range(1, 34)))


class ScopeTests(unittest.TestCase):
    def test_loopback_allowed_by_default(self):
        self.assertIn("loopback", check_scope("127.0.0.1", None, False))

    def test_private_address_needs_explicit_scope_and_consent(self):
        with self.assertRaises(ValueError):
            check_scope("192.168.56.3", None, False)
        self.assertEqual(
            check_scope("192.168.56.3", "192.168.56.0/24", True),
            "192.168.56.0/24",
        )

    def test_out_of_scope_and_public_address_are_rejected(self):
        for target, scope in (
            ("192.168.57.3", "192.168.56.0/24"),
            ("8.8.8.8", "8.8.8.0/24"),
        ):
            with self.subTest(target=target), self.assertRaises(ValueError):
                check_scope(target, scope, True)

    def test_noncanonical_cidr_returns_valueerror(self):
        with self.assertRaisesRegex(ValueError, "valid IPv4 network"):
            check_scope("192.168.56.3", "192.168.56.3/24", True)

    def test_broad_scope_is_rejected(self):
        with self.assertRaises(ValueError):
            check_scope("10.1.1.1", "10.0.0.0/8", True)


class ProbeTests(unittest.TestCase):
    def test_open_loopback_listener(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen(1)
            port = listener.getsockname()[1]
            result = probe("127.0.0.1", port, 0.5)
            self.assertEqual(result["state"], "open")
            self.assertEqual(result["errno"], 0)

    def test_refused_after_listener_closes(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        result = probe("127.0.0.1", port, 0.5)
        self.assertEqual(result["state"], "refused")


class CommandLineTests(unittest.TestCase):
    def test_output_is_created_once_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "evidence.json"
            command = [sys.executable, "scanner.py", "--ports", "8765", "--output", str(path)]
            first = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            saved = path.read_text(encoding="utf-8")
            second = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(second.returncode, 2)
            self.assertEqual(path.read_text(encoding="utf-8"), saved)

    def test_external_target_fails_before_network_use(self):
        command = [sys.executable, "scanner.py", "--target", "8.8.8.8", "--ports", "53"]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("scope", result.stderr)


class ProbeErrorTests(unittest.TestCase):
    def test_timeout_exception_without_errno(self):
        with patch("scanner.socket.socket") as mocked:
            mocked.return_value.__enter__.return_value.connect_ex.side_effect = TimeoutError()
            result = probe("127.0.0.1", 8765, 0.2)
        self.assertEqual(result["state"], "timeout")
        self.assertEqual(result["errno"], errno.ETIMEDOUT)

    def test_unreachable_errno_without_external_traffic(self):
        with patch("scanner.socket.socket") as mocked:
            mocked.return_value.__enter__.return_value.connect_ex.return_value = errno.ENETUNREACH
            result = probe("127.0.0.1", 8765, 0.2)
        self.assertEqual(result["state"], "unreachable")


if __name__ == "__main__":
    unittest.main()
