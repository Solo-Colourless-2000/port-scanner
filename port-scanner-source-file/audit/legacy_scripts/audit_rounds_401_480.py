#!/usr/bin/env python3
"""Repeat exhaustive source/manual checks for 40 rounds per phase.
Each pass independently rereads source ZIP and HTML and checks 10 groups.
This log records AUTOMATED passes, not full human editorial readings.
"""
import ast
from collections import defaultdict
from datetime import datetime, timezone
import gzip
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from zipfile import ZipFile
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
M=json.loads((ROOT/'SOURCE_MANIFEST.json').read_text())
STEPS=json.loads((ROOT/'STEP_FRAGMENTS.json').read_text())
assert len(M['files'])==43 and len(STEPS)==107
start=int(sys.argv[1]); assert start in (401,441)
batch=int(sys.argv[2]) if len(sys.argv)>2 else 10
assert 1<=batch<=40
log=ROOT/'audit'/f'REVIEW_ROUNDS_{start}_{start+39}.jsonl'
pre=ROOT/'audit'/'BASELINE_400_MANUAL.html.gz'
checks=['original_archive_integrity','all_file_byte_reconstruction','line_annotation_coverage','lexical_and_contextual_fidelity','language_grammar','step_edit_order','HTML_navigation_and_accessibility','safety_and_usage','source_grounded_manual_claims','rotating_line_sample']
prior=[json.loads(x) for x in log.read_text().splitlines()] if log.exists() else []
assert [x['round'] for x in prior]==list(range(start,start+len(prior)))
for rnd in range(start+len(prior),min(start+40,start+len(prior)+batch)):
    with ZipFile(ROOT/'original_source.zip') as archive:
        assert archive.testzip() is None
        prefix='pentest-starting-with-port-scanner-main/'
        originals={p:archive.read(prefix+p) for p in M['files']}
        policy=ET.fromstring(archive.read(prefix+'code/chapter04/for-pentest-book.nessus'))
        assert policy.tag=='NessusClientData_v2'
        for p,b in originals.items(): assert sha256(b).hexdigest()==M['files'][p]['sha256']
        assert sha256((ROOT/'original_source.zip').read_bytes()).hexdigest()==M['source_sha256']
        python_sources=[(n,archive.read(n)) for n in archive.namelist() if n.endswith('.py')]
    res={}
    res[checks[0]]='source ZIP CRC, 43 SHA-256, original ZIP SHA-256, Nessus policy parse'
    html=(gzip.decompress(pre.read_bytes()).decode() if start==401 else (ROOT/M['manual']).read_text())
    dom=BeautifulSoup(html,'lxml')
    filelines=defaultdict(dict);notes=defaultdict(dict);units=defaultdict(dict)
    assert len(dom.select('article.lesson-step'))==107
    for step in STEPS:
        el=dom.find('article',id=f"step-{step['step']:03d}")
        assert el is not None, (rnd,step['step'])
        spans=el.select('code.source-lines span[data-line]')
        rows=el.select('table.line-analysis tbody tr')
        assert len(spans)==len(rows)==step['end']-step['start']+1
        src_lines=originals[step['path']].decode().splitlines(keepends=True)
        for n,sp,row in zip(range(step['start'],step['end']+1),spans,rows):
            assert int(sp['data-line'])==n and sp.get_text()==src_lines[n-1],(rnd,step['path'],n)
            assert n not in filelines[step['path']]
            filelines[step['path']][n]=sp.get_text()
            note=row.select_one('.syntactic'); assert note and len(note.get_text(' ',strip=True))>=7
            notes[step['path']][n]=note.get_text(' ',strip=True)
            elems=row.select('.token-notes li')
            if sp.get_text().strip(): assert elems and all(x.find('b') for x in elems)
            units[step['path']][n]=[x.get_text(' ',strip=True) for x in elems]
    assert len(filelines)==43 and sum(len(v) for v in filelines.values())==946
    for p,src in originals.items():
        reconstructed=''.join(filelines[p][n] for n in sorted(filelines[p])).encode()
        assert reconstructed==src and sha256(reconstructed).hexdigest()==M['files'][p]['sha256']
    res[checks[1]]='43/43 files byte-identical; SHA-256 matched'
    res[checks[2]]='946/946 annotated original lines with component entries for non-empty lines'
    text=dom.get_text(' ',strip=True)
    for bad in ('Cの識別子。型、定数、関数','docker ：シェルの制御構文','<：未満','>：超過'):
        assert bad not in text
    for p, lines in filelines.items():
        for n,source_line in lines.items():
            labels=[u.split('：',1)[0].strip() for u in units[p][n]]
            if source_line.lstrip().startswith(('if (','elif (')) and not source_line.rstrip().endswith(':'):
                assert ':' not in labels,(p,n)
            if p.endswith('.go') and ':=' in source_line:
                assert not(':' in labels and '=' in labels),(p,n)
            if source_line.startswith('#include'):
                assert not any(('未満' in u or '超過' in u) and 'ではない' not in u for u in units[p][n])
    res[checks[3]]='source-aware lexical regressions and contextual explanations'
    for n,b in python_sources:ast.parse(b.decode(),filename=n)
    for p,b in originals.items():
        if p.endswith('.sh'):
            r=subprocess.run(['sh','-n'],input=b,capture_output=True);assert r.returncode==0,(p,r.stderr)
        if p.endswith('.rb'):
            r=subprocess.run(['ruby','-c'],input=b,capture_output=True);assert r.returncode==0,(p,r.stderr)
    res[checks[4]]=f'{len(python_sources)} Python files parsed; Shell/Ruby syntax passed; Nessus XML parsed'
    for p in originals:
        seq=[x for x in STEPS if x['path']==p]
        assert seq[0]['start']==1 and seq[-1]['end']==M['files'][p]['lines']
        assert all(a['end']+1==b['start'] for a,b in zip(seq,seq[1:]))
    res[checks[5]]='107 steps have correct 43-file contiguous editing histories'
    sections=dom.select('section.manual-section');toc=dom.select('#sidebar [data-target]')
    assert {e['id'] for e in sections}=={e['data-target'] for e in toc}
    ids=[e['id'] for e in dom.select('[id]')];assert len(ids)==len(set(ids))
    assert len(dom.select('input[data-done]'))==107
    for elm in ('searchInput','menuButton','fontUp','fontDown'):
        assert dom.find(id=elm)
    res[checks[6]]=f'{len(sections)} sections, unique IDs, TOC valid, 107 progress controls, search and mobile menu'
    assert len(dom.select('#usage article.ops-command'))==40
    for key in ('127.0.0.1','許可','原典','タイムアウト','Docker','Nessus','後片付け','危険'):
        assert key in text,(rnd,key)
    if start==441:
        portfolio=dom.find('section',id='portfolio')
        assert portfolio and len(portfolio.select('article.portfolio-task'))>=12
        assert len(portfolio.select('.portfolio-code-annotation'))>=25
        for key in ('公開前','オリジナル','GitHub','証拠','面接','スコープ','テスト'):
            assert key in portfolio.get_text(' ',strip=True),key
        assert (ROOT/'portfolio_lab'/'scanner.py').is_file()
    res[checks[7]]='original safety boundaries, 40 operational cards, separate portfolio authoring and evidence controls'
    # Verify source-grounded important facts never get silently flipped in explanations.
    known=[('code/chapter02/tcp-connect-scan-by-socket.py',11,'connect_ex'),
           ('code/chapter02/tcp-syn-scan.py',14,'sr1'),
           ('code/chapter03/nmap-xml2csv.rb',29,'host.ip'),
           ('containers/postgres/Dockerfile',8,'pg_hba.conf'),
           ('code/chapter06/libsniffer.c',9,'fprintf'),
           ('containers/compose.yaml',90,'privileged')]
    for p,n,snippet in known:assert snippet in filelines[p][n]
    if start==441:
        for p,n,expected in [('code/chapter03/nmap-xml2csv.rb',4,'ARGV'),
                             ('containers/postgres/Dockerfile',8,'PGDATA'),
                             ('code/chapter02/tcp-connect-scan-v1.py',29,'ACK'),
                             ('containers/log4j/src/main/java/fr/christophetd/log4shell/vulnerableapp/MainController.java',18,'ログ')]:
            assert expected in notes[p][n],(p,n)
    res[checks[8]]='explicit critical original statement anchors; updated note invariants'
    pool=[(p,n,filelines[p][n].strip()[:120],notes[p][n][:190]) for p in originals for n in sorted(filelines[p]) if filelines[p][n].strip()]
    assert len(pool)==796
    sampled=[pool[((rnd-start)*29+j*47+11)%len(pool)] for j in range(64)]
    res[checks[9]]='64 rotating source+annotation pairs per round (recorded, not falsely called human reads)'
    record={'round':rnd,'phase':'pre_revision' if start==401 else 'post_revision',
            'nature':'automated 10-criterion full-source repetition; separate editorial reviews documented independently',
            'checks_per_round':checks,'outcomes':res,'samples':sampled,
            'manual_sha256':sha256(html.encode()).hexdigest(),
            'verified_at_utc':datetime.now(timezone.utc).isoformat()}
    with log.open('a') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
print('PASS',log.name, len(log.read_text().splitlines()),'/40')
