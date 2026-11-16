#!/usr/bin/env python3
"""Verify 24 distinct, multi-check final-version audits and their exact HTML hash."""
from pathlib import Path
import json, hashlib
R=Path(__file__).resolve().parents[1]
html=R/'portscanner_pentest_development_manual_v984_20261117.html'
digest=hashlib.sha256(html.read_bytes()).hexdigest()
path=R/'audit/REVIEW_ROUNDS_961_984.jsonl'
rows=[json.loads(line) for line in path.read_text().splitlines()]
assert len(rows)==24,len(rows)
assert [r['round'] for r in rows]==list(range(961,985))
for item in rows:
    assert item['html_sha256']==digest
    assert item['result']=='PASS'
    assert len(item['checks'])>=15 and all(item['checks'].values())
    assert item['source_lines']==946 and item['portfolio_lines']==237 and item['report_diff_lines']==513
    assert len(item['samples'])==24
print('PASS: exactly 24 separate repeated audits, each with multiple checks, correct final HTML hash and source totals.')
print('This is automated repetition plus separate human-directed semantic edits, not 24 human full readings.')
