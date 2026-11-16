#!/usr/bin/env python3
"""Verify additional 80 machine-audit records and distinct before/after SHA-256 hashes."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
current=R/'audit/BASELINE_960_MANUAL.html'
old=R/'audit/BASELINE_880_MANUAL.html'
assert sha(current)!=sha(old)
for phase,first,expected in [('pre',881,sha(old)),('post',921,sha(current))]:
    rows=[json.loads(x) for x in (R/'audit'/f'REVIEW_ROUNDS_{first}_{first+39}.jsonl').read_text().splitlines()]
    assert len(rows)==40
    assert [r['round'] for r in rows]==list(range(first,first+40))
    assert all(r['phase']==phase and r['html_sha256']==expected and r['result']=='PASS' for r in rows)
    assert all(len(r['checks'])==19 and all(r['checks'].values()) for r in rows)
    assert all(r['original_lines']==946 and r['portfolio_lines']==237 for r in rows)
    assert all(r['diff_lines']==(411 if phase=='pre' else 497) for r in rows)
    assert all(len(r['source_samples'])==24 for r in rows)
print('PASS: 40 baseline checks plus 40 final-version checks, 19 checks per pass, correct hashes.')
print('These are repeated automated checks, not 80 independent semantic full readings.')
