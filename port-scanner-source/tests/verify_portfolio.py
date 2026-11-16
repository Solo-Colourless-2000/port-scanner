#!/usr/bin/env python3
"""Verify 19 interleaved portfolio tasks, every source line and 13 tests."""
from pathlib import Path
from collections import defaultdict
import json
from hashlib import sha256
import subprocess
import sys
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'SOURCE_MANIFEST.json').read_text())
parts=json.loads((ROOT/'PORTFOLIO_FRAGMENTS.json').read_text())
soup=BeautifulSoup((ROOT/manifest['manual']).read_text(),'lxml')
section=soup.find('section',id='portfolio');assert section
cards=section.select('article.portfolio-task');assert len(cards)==19
assert len(section.select('input[data-portfolio-done]'))==19
seen=defaultdict(dict)
for part in parts['steps']:
    card=section.find('article',id=f"portfolio-step-{part['stage']:02d}")
    assert card,part
    spans=card.select('code.portfolio-source-lines span[data-line]')
    rows=card.select('tr.portfolio-code-annotation')
    assert len(spans)==len(rows)==part['end']-part['start']+1
    for no,span,row in zip(range(part['start'],part['end']+1),spans,rows):
        assert int(span['data-line'])==no
        assert int(row['data-line'])==no and row['data-file']==part['path']
        explanation=row.select_one('p')
        assert explanation and len(explanation.get_text(strip=True))>=12
        raw=span.get_text()
        if raw.strip():
            assert len(explanation.get_text(strip=True))>=30
            assert row.select_one('code.portfolio-line-source').get_text().strip()==raw.strip()
        assert no not in seen[part['path']]
        seen[part['path']][no]=raw
assert set(seen)==set(parts['files'])
for name, meta in parts['files'].items():
    code=''.join(seen[name][i] for i in sorted(seen[name])).encode()
    assert sha256(code).hexdigest()==meta['sha256']
    assert (ROOT/'portfolio_lab'/name).read_bytes()==code
    assert len(seen[name])==meta['lines']
assert sum(len(v) for v in seen.values())==237
assert sum(bool(x.strip()) for x in seen['scanner.py'].values())==103
r=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=ROOT/'portfolio_lab',capture_output=True,text=True,timeout=40)
assert r.returncode==0,r.stderr
assert 'Ran 51 tests' in r.stderr,r.stderr
# The scanner CLI's --help has no network action; it must be accessible.
r=subprocess.run([sys.executable,'scanner.py','--help'],cwd=ROOT/'portfolio_lab',capture_output=True,text=True,timeout=15)
assert r.returncode==0 and '--authorized' in r.stdout and '--scope-cidr' in r.stdout
print('PASS: 19 portfolio tasks, 237 exact code lines, 237 individual annotations, 51 total unittest/loopback tests (14 scanner + 37 report comparison), CLI help')
