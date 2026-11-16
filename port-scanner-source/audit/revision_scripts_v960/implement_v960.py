from pathlib import Path
r=Path(__file__).parent
p=r/'portfolio_lab/report_diff.py';s=p.read_text()
a='''    if not isinstance(report, dict):
        raise ValueError(f"{path}: expected a JSON object")
    target = report.get("target")
'''
b='''    if not isinstance(report, dict):
        raise ValueError(f"{path}: expected a JSON object")
    required_report_fields = {"timestamp_utc", "target", "scope", "timeout_seconds", "results"}
    if set(report) != required_report_fields:
        missing = sorted(required_report_fields - report.keys())
        unexpected = sorted(report.keys() - required_report_fields)
        raise ValueError(f"{path}: report fields mismatch; missing={missing}, unexpected={unexpected}")
    target = report.get("target")
'''
assert s.count(a)==1;s=s.replace(a,b)
a='''        if not isinstance(row, dict):
            raise ValueError(f"{path}: each result must be an object")
        port, state, code = row.get("port"), row.get("state"), row.get("errno")
'''
b='''        if not isinstance(row, dict):
            raise ValueError(f"{path}: each result must be an object")
        required_row_fields = {"port", "state", "errno"}
        if set(row) != required_row_fields:
            missing = sorted(required_row_fields - row.keys())
            unexpected = sorted(row.keys() - required_row_fields)
            raise ValueError(f"{path}: result fields mismatch; missing={missing}, unexpected={unexpected}")
        port, state, code = row.get("port"), row.get("state"), row.get("errno")
'''
assert s.count(a)==1;s=s.replace(a,b)
a='''    parser.add_argument("--before", required=True, type=Path)
    parser.add_argument("--after", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        if args.before.resolve() == args.after.resolve():
            raise ValueError("before and after must be different files")
'''
b='''    parser.add_argument("--before", type=Path, help="earlier JSON report for comparison")
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
'''
assert s.count(a)==1;s=s.replace(a,b)
p.write_text(s)

t=r/'portfolio_lab/tests/test_report_diff.py';s=t.read_text()
a='''    def test_duplicate_port_is_rejected(self):
'''
b='''    def test_report_rejects_unknown_and_missing_fields(self):
        for mode in ("unknown", "missing"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as folder:
                report = example()
                if mode == "unknown":
                    report["injected_field"] = "not part of scanner output"
                else:
                    del report["timeout_seconds"]
                with self.assertRaisesRegex(ValueError, "report fields mismatch"):
                    read_report(self.write_report(folder, report))

    def test_result_rejects_unknown_and_missing_fields(self):
        for mode in ("unknown", "missing"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as folder:
                report = example()
                if mode == "unknown":
                    report["results"][0]["unexpected"] = True
                else:
                    del report["results"][0]["errno"]
                with self.assertRaisesRegex(ValueError, "result fields mismatch"):
                    read_report(self.write_report(folder, report))

    def test_duplicate_port_is_rejected(self):
'''
assert s.count(a)==1;s=s.replace(a,b)
a='''    def test_cli_rejects_same_input_file(self):
'''
b='''    def test_validate_cli_accepts_one_valid_report(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "before.json"
            path.write_text(json.dumps(example()), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "report_diff.py", "--validate", str(path)],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("VALID:", result.stdout)
            self.assertIn("ports=2", result.stdout)
            self.assertEqual(sorted(x.name for x in Path(folder).iterdir()), ["before.json"])

    def test_validate_cli_rejects_tampered_input(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "tampered.json"
            modified = example()
            modified["results"][0]["additional"] = "bad field"
            path.write_text(json.dumps(modified), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "report_diff.py", "--validate", str(path)],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("result fields mismatch", result.stderr)
            self.assertNotIn("VALID:", result.stdout)

    def test_validate_cli_rejects_ambiguous_arguments(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "before.json"
            path.write_text(json.dumps(example()), encoding="utf-8")
            commands = (
                ["--validate", str(path), "--before", str(path)],
                ["--validate", str(path), "--output", str(Path(folder) / "evidence.json")],
                ["--before", str(path)],
            )
            for options in commands:
                with self.subTest(options=options):
                    result = subprocess.run(
                        [sys.executable, "report_diff.py", *options],
                        capture_output=True, text=True,
                    )
                    self.assertEqual(result.returncode, 2)
            self.assertEqual(sorted(x.name for x in Path(folder).iterdir()), ["before.json"])

    def test_cli_rejects_same_input_file(self):
'''
assert s.count(a)==1;s=s.replace(a,b)
t.write_text(s)
print('report lines',len(p.read_text().splitlines(keepends=True)),'test lines',len(t.read_text().splitlines(keepends=True)))
