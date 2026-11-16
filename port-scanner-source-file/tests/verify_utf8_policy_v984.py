#!/usr/bin/env python3
"""Reproduce previous encoding acceptance and new strict UTF-8 rejection."""
from pathlib import Path
from tempfile import TemporaryDirectory
import importlib.util, json, subprocess, sys
R=Path(__file__).resolve().parents[1]

def load(path, module_name):
    spec=importlib.util.spec_from_file_location(module_name,path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
old=load(R/'audit/BASELINE_960_REPORT_DIFF.py','previous_reportdiff')
new=load(R/'portfolio_lab/report_diff.py','revised_reportdiff')
example={
 'timestamp_utc':'2026-11-16T10:00:00+00:00',
 'target':'127.0.0.1',
 'scope':'127.0.0.0/8 (loopback only)',
 'timeout_seconds':0.5,
 'results':[{'port':8765,'state':'open','errno':0}],
}
with TemporaryDirectory() as tmp:
    path=Path(tmp)/'report.json'
    for encoding in ('utf-16','utf-32','utf-8-sig'):
        path.write_bytes(json.dumps(example).encode(encoding))
        assert old.read_report(path)['target']=='127.0.0.1',encoding
        try:
            new.read_report(path)
        except ValueError as exc:
            assert 'invalid UTF-8 JSON' in str(exc),encoding
        else:
            raise AssertionError(f'{encoding} accepted unexpectedly')
    path.write_bytes(json.dumps(example).encode('utf-8'))
    assert new.read_report(path)['target']=='127.0.0.1'
    cli=subprocess.run([sys.executable,str(R/'portfolio_lab/report_diff.py'),'--validate',str(path)],capture_output=True,text=True)
    assert cli.returncode==0 and 'VALID' in cli.stdout,cli.stderr
    path.write_bytes(json.dumps(example).encode('utf-16'))
    cli=subprocess.run([sys.executable,str(R/'portfolio_lab/report_diff.py'),'--validate',str(path)],capture_output=True,text=True)
    assert cli.returncode==2 and 'invalid UTF-8 JSON' in cli.stderr,cli.stderr
print('PASS: previous version accepted UTF-16/32/BOM; revised version rejects them; plain UTF-8 succeeds; CLI exits 2 for invalid encoding')
