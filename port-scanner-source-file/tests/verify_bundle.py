#!/usr/bin/env python3
"""Verify exact original bytes and every HTML code/explanation line (no network)."""
from pathlib import Path
from zipfile import ZipFile
from hashlib import sha256
from collections import defaultdict
from bs4 import BeautifulSoup
import subprocess, tempfile, json, ast, shutil
P=Path(__file__).resolve().parent.parent
m=json.loads((P/'SOURCE_MANIFEST.json').read_text(encoding='utf-8'))
st=json.loads((P/'STEP_FRAGMENTS.json').read_text(encoding='utf-8'))
archive=P/'original_source.zip'
assert sha256(archive.read_bytes()).hexdigest()==m['source_sha256']
assert len(st)==107 and len(m['files'])==43
html=BeautifulSoup((P/m['manual']).read_text(encoding='utf-8'),'html.parser')
assert len(html.select('section.manual-section'))==17, len(html.select('section.manual-section'))
assert len(html.select('article.lesson-step'))==len(st)
assert len(html.select('article.ops-command'))==40
assert len(html.select('#usage .operation-parts'))==40
assert all(len(a.select('.operation-parts li')) >= 2 for a in html.select('#usage .ops-command'))
assert len(html.select('article.lesson-step tr:has(.one-line)'))==sum(v['lines'] for v in m['files'].values())
assert len(html.select('input[data-done]'))==len(st)
seen=defaultdict(list)
with ZipFile(archive) as z:
    for step in st:
        k=step['step'];p=step['path'];a,b=step['start'],step['end']
        el=html.find('article',id=f'step-{k:03d}')
        assert el is not None
        code=el.select_one('code.source-lines')
        spans=code.find_all('span',attrs={'data-line':True})
        assert len(spans)==b-a+1,(k,len(spans),b-a+1)
        assert [int(x['data-line']) for x in spans]==list(range(a,b+1)),k
        for sp in spans:seen[p].append((int(sp['data-line']),sp.get_text()))
        expl=el.select('table.line-analysis tbody tr')
        assert len(expl)==len(spans)
        for row,sp in zip(expl,spans):
            assert row.select_one('td').get_text(strip=True)=='L'+sp['data-line']
            assert row.select_one('.syntactic').get_text(strip=True)
            assert (not sp.get_text().strip()) or row.select_one('ul.token-notes li').get_text(strip=True)
    assert set(seen)==set(m['files'])
    total=0
    for p,meta in m['files'].items():
        numbered=sorted(seen[p]);orig=z.read('pentest-starting-with-port-scanner-main/'+p)
        assert [n for n,s in numbered]==list(range(1,meta['lines']+1))
        rebuilt=''.join(line for n,line in numbered).encode('utf-8')
        assert rebuilt==orig,(p,len(rebuilt),len(orig))
        assert sha256(rebuilt).hexdigest()==meta['sha256']
        total+=len(numbered)
    # Language grammar syntax, without running the original exploit demos.
    py,sh,rb=0,0,0
    for fname in z.namelist():
        if fname.endswith('.py'):
            ast.parse(z.read(fname).decode('utf-8'),filename=fname);py+=1
        if fname.startswith('pentest-starting-with-port-scanner-main/code/') and fname.endswith('.sh'):
            with tempfile.NamedTemporaryFile(suffix='.sh') as f:
                f.write(z.read(fname));f.flush();subprocess.run(['sh','-n',f.name],check=True,capture_output=True);sh+=1
        if fname.endswith('.rb') and shutil.which('ruby'):
            with tempfile.NamedTemporaryFile(suffix='.rb') as f:
                f.write(z.read(fname));f.flush();subprocess.run(['ruby','-c',f.name],check=True,capture_output=True);rb+=1
print('PASS: 107 ordered steps, 43 byte-identical sources,',total,'line explanations; static Python',py,'Shell',sh,'Ruby',rb)
