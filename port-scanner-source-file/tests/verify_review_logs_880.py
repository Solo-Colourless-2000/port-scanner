#!/usr/bin/env python3
"""Verify 801-880 automated records and both exact manual hashes."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1]
sha=lambda x:hashlib.sha256(Path(x).read_bytes()).hexdigest()
manifest=json.loads((R/'SOURCE_MANIFEST.json').read_text())
expected={'pre':sha(R/'audit/BASELINE_800_MANUAL.html'),'post':sha(R/'audit/BASELINE_880_MANUAL.html')}
all_records=[]
for phase,first in [('pre',801),('post',841)]:
    records=[json.loads(s) for s in (R/'audit'/f'REVIEW_ROUNDS_{first}_{first+39}.jsonl').read_text().splitlines()]
    assert len(records)==40
    assert [r['round'] for r in records]==list(range(first,first+40))
    assert all(r['phase']==phase and r['html_sha256']==expected[phase] and r['result']=='PASS' for r in records)
    assert all(len(r['checks'])==19 and all(r['checks'].values()) for r in records)
    assert all(r['original_lines']==946 and r['portfolio_lines']==237 and r['diff_lines']==(389 if phase=='pre' else 411) for r in records)
    all_records.extend(records)
assert expected['pre']!=expected['post']
print('PASS: eighty repeated automated checks, 40 before and 40 after; exact distinct artifact hashes; 19 checks per round')
print('These are machine rechecks, not eighty independent human full readings.')
