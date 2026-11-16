#!/usr/bin/env python3
"""Verify the separate 10-step, 513-line offline report comparison lesson."""
from collections import defaultdict
from hashlib import sha256
from pathlib import Path
import ast, json, subprocess, sys
from bs4 import BeautifulSoup
R=Path(__file__).resolve().parent.parent
f=json.loads((R/'REPORT_DIFF_FRAGMENTS.json').read_text())
manifest=json.loads((R/'SOURCE_MANIFEST.json').read_text())
h=BeautifulSoup((R/manifest['manual']).read_text(),'lxml')
sec=h.find('section',id='report-compare')
assert sec and len(sec.select('article.report-diff-step'))==10
assert len(sec.select('input[data-diff-done]'))==10
assert len(f['steps'])==10
seen=defaultdict(dict);notes=defaultdict(dict)
for s in f['steps']:
    step=sec.find('article',id=f"diff-step-{s['stage']:02d}")
    assert step and s['path'] in step.get_text()
    raw=step.select('code.diff-source-lines span[data-line]')
    explanations=step.select('tr.diff-code-annotation')
    assert len(raw)==len(explanations)==s['end']-s['start']+1
    for n,code,row in zip(range(s['start'],s['end']+1),raw,explanations):
        assert int(code['data-line'])==n==int(row['data-line'])
        assert code['data-file']==s['path']==row['data-file']
        assert n not in seen[s['path']]
        seen[s['path']][n]=code.get_text()
        expl=row.select_one('p.syntactic')
        assert expl and len(expl.get_text(strip=True))>=(30 if code.get_text().strip() else 15)
        if code.get_text().strip():
            assert row.select_one('code.diff-line-source')
            assert 'この行「' not in expl.get_text()
        notes[s['path']][n]=expl.get_text(' ',strip=True)
assert set(seen)==set(f['files'])=={'report_diff.py','tests/test_report_diff.py'}
assert sum(len(x) for x in seen.values())==513
for path,meta in f['files'].items():
    relevant=[s for s in f['steps'] if s['path']==path]
    assert relevant[0]['start']==1 and relevant[-1]['end']==meta['lines']
    assert all(a['end']+1==b['start'] for a,b in zip(relevant,relevant[1:]))
    rebuilt=''.join(seen[path][n] for n in sorted(seen[path])).encode()
    assert rebuilt==(R/'portfolio_lab'/path).read_bytes()
    assert sha256(rebuilt).hexdigest()==meta['sha256']
    ast.parse(rebuilt.decode())
    assert len(seen[path])==meta['lines']
for field in ('state_changes','unchanged_ports','target','scope','--before','--after','--output','--validate','127.0.0.1','python3 -m unittest','Git'):
    assert field in sec.get_text(' ',strip=True),field
run=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-q'],cwd=R/'portfolio_lab',capture_output=True,text=True,timeout=50)
assert run.returncode==0,run.stderr
assert 'Ran 51 tests' in run.stderr
help_run=subprocess.run([sys.executable,'report_diff.py','--help'],cwd=R/'portfolio_lab',capture_output=True,text=True)
assert help_run.returncode==0 and '--before' in help_run.stdout and '--validate' in help_run.stdout
print('PASS: 10 interleaved steps; exactly 513 byte-matched source lines with 513 annotations; 51 test methods; offline CLI help')
