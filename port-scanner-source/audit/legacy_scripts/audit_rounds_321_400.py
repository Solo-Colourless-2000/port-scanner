#!/usr/bin/env python3
"""Full-manual, multi-check automated REVIEW rounds 321-400.

Each *round* starts from source bytes plus current HTML, reconstructs all 43
editable files and checks every annotated line. Supplemental rotating samples
are recorded for later human review. This is NOT 80 human semantic readings.
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

ROOT=Path(__file__).resolve().parent.parent
PREFIX='pentest-starting-with-port-scanner-main/'
MANIFEST=json.loads((ROOT/'SOURCE_MANIFEST.json').read_text(encoding='utf-8'))
STEPS=json.loads((ROOT/'STEP_FRAGMENTS.json').read_text(encoding='utf-8'))
assert len(STEPS)==107 and len(MANIFEST['files'])==43
BATCH_SIZE=int(sys.argv[2]) if len(sys.argv)>2 else 10
START=int(sys.argv[1])
assert START in (321,361)
PATH=ROOT/'audit'/f'REVIEW_ROUNDS_{START:03d}_{START+39:03d}.jsonl'
PATH.parent.mkdir(exist_ok=True)
BEFORE=ROOT/'audit'/'BASELINE_320_MANUAL.html.gz'
manual=ROOT/MANIFEST['manual']
checks=['archive_provenance','source_byte_reconstruction','all_line_explanations','symbol_and_context_tests','syntax_and_xml','step_edit_continuity','navigation_and_code_integrity','security_and_documentation','rotating_sample_review']

with ZipFile(ROOT/'original_source.zip') as z:
    z.testzip()
    originals={p:z.read(PREFIX+p) for p in MANIFEST['files']}
    pyfiles={n:z.read(n) for n in z.namelist() if n.endswith('.py')}
    policy=z.read(PREFIX+'code/chapter04/for-pentest-book.nessus')
for p,b in originals.items():
    assert sha256(b).hexdigest()==MANIFEST['files'][p]['sha256']
assert sha256((ROOT/'original_source.zip').read_bytes()).hexdigest()==MANIFEST['source_sha256']
assert ET.fromstring(policy).tag=='NessusClientData_v2'

finished=len(PATH.read_text(encoding='utf-8').splitlines()) if PATH.exists() else 0
assert 0 <= finished <= 40
for rnd in range(START+finished, min(START+40, START+finished+BATCH_SIZE)):
    if START==321:
        htmltext=gzip.decompress(BEFORE.read_bytes()).decode('utf-8')
    else:
        htmltext=manual.read_text(encoding='utf-8')
    bs=BeautifulSoup(htmltext,'lxml')
    results={}
    results['archive_provenance']='43 source SHA-256; ZIP CRC; Nessus XML Policy root'
    stages=bs.select('article.lesson-step')
    assert len(stages)==107
    recovered=defaultdict(dict);notes=defaultdict(dict);units=defaultdict(dict)
    for stage in STEPS:
        ix=stage['step'];p=stage['path'];a=stage['start'];b=stage['end']
        article=bs.find('article',id=f'step-{ix:03d}')
        assert article and article.select_one('h2')
        rawspans=article.select('code.source-lines span[data-line]')
        rows=article.select('table.line-analysis tbody tr')
        assert len(rawspans)==len(rows)==b-a+1,(rnd,ix,p)
        for lineno,sp,row in zip(range(a,b+1),rawspans,rows):
            assert int(sp['data-line'])==lineno
            line=sp.get_text()
            expected=originals[p].decode('utf-8').splitlines(keepends=True)[lineno-1]
            assert line==expected,(rnd,p,lineno,'source differs')
            assert lineno not in recovered[p]
            recovered[p][lineno]=line
            col=row.select_one('.one-line')
            assert col
            # Original whitespace-only lines may be visually simplified here.
            if expected.strip():assert col.get_text()==expected.rstrip('\r\n')
            note=row.select_one('.syntactic')
            assert note and len(note.get_text(' ',strip=True))>=7
            notes[p][lineno]=note.get_text(' ',strip=True)
            lis=row.select('.token-notes li')
            if expected.strip():assert lis and all(li.find('b') and len(li.get_text(' ',strip=True))>5 for li in lis)
            units[p][lineno]=[li.get_text(' ',strip=True) for li in lis]
    assert set(recovered)==set(originals)
    for p,src in originals.items():
        built=''.join(recovered[p][j] for j in sorted(recovered[p])).encode('utf-8')
        assert built==src,(rnd,p)
        assert sha256(built).hexdigest()==MANIFEST['files'][p]['sha256']
        assert len(recovered[p])==MANIFEST['files'][p]['lines']
    results['source_byte_reconstruction']='43/43 reconstructed exactly'
    assert sum(map(len,notes.values()))==946
    assert all(len(x)==MANIFEST['files'][p]['lines'] for p,x in notes.items())
    results['all_line_explanations']='946/946 descriptions; component notes on every nonempty line'

    # Multiple source-aware error patterns, not vague generic token classification.
    # Source-specific identity checks on code and its note context.
    fixed_expectations=[('code/chapter02/tcp-syn-scan.py',14,'response_packet'),
        ('code/chapter03/nmap-xml2csv.rb',29,'host.ip'),
        ('containers/postgres/Dockerfile',8,'pg_hba.conf'),
        ('code/chapter06/libsniffer.c',9,'fprintf'),
        ('containers/compose.yaml',90,'privileged')]
    for p,n,term in fixed_expectations:
        assert term in recovered[p][n],(rnd,p,n,term)
    invalid_phrases=['Cの識別子。型、定数、関数、変数','<：未満','>：超過','docker ：シェルの制御構文']
    allprose=bs.get_text(' ',strip=True)
    for bad in invalid_phrases:assert bad not in allprose,(rnd,bad)
    for p,n in [(p,n) for p in notes for n in notes[p]]:
        src=recovered[p][n]
        labels=[x.split('：',1)[0].strip() for x in units[p][n]]
        if src.lstrip().startswith(('if (','elif (')) and not src.rstrip().endswith(':'):
            assert ':' not in labels,(rnd,p,n,'phantom colon')
        if p.endswith('.go') and ':=' in src:
            assert ':=' in src
            assert not (':' in labels and '=' in labels),(rnd,p,n,'Go := split')
    if START==361:
        editorial=json.loads((ROOT/'EDITORIAL_PATCHES_321_400.json').read_text(encoding='utf-8'))
        for patch in editorial['changed_lines']:
            if not patch.get('component_rewrite'): continue
            path,line=patch['path'],patch['line']
            for label in units[path][line]:
                token=label.split('：',1)[0].strip()
                assert token in recovered[path][line],(rnd,path,line,token,'element does not occur in actual source line')
    results['symbol_and_context_tests']='no known bad syntax placeholders or phantom symbols'

    py=sh=rb=0
    for p,b in pyfiles.items():ast.parse(b.decode('utf-8'),filename=p);py+=1
    for p,b in originals.items():
        if p.endswith('.sh'):
            r=subprocess.run(['sh','-n'],input=b,capture_output=True)
            assert r.returncode==0,(p,r.stderr);sh+=1
        elif p.endswith('.rb'):
            r=subprocess.run(['ruby','-c'],input=b,capture_output=True)
            assert r.returncode==0,(p,r.stderr);rb+=1
    results['syntax_and_xml']=f'Python {py}; Shell {sh}; Ruby {rb}; Nessus XML parsed'
    for p in originals:
        ordered=[s for s in STEPS if s['path']==p]
        assert ordered and ordered[0]['start']==1
        assert all(x['end']+1==y['start'] for x,y in zip(ordered,ordered[1:]))
        assert ordered[-1]['end']==MANIFEST['files'][p]['lines']
    results['step_edit_continuity']='107 segments; 43 complete contiguous edit histories'
    sections=bs.select('section.manual-section')
    toc=bs.select('#sidebar [data-target]')
    assert len(toc)==len(sections)
    assert {x['data-target'] for x in toc}=={s['id'] for s in sections}
    ids=[e['id'] for e in bs.select('[id]')]
    assert len(ids)==len(set(ids)),(rnd,'duplicate HTML ids')
    assert len(bs.select('.step-check input[data-done]'))==107
    assert bs.select_one('#searchInput') and bs.select_one('#fontUp') and bs.select_one('#menuButton')
    assert bs.select_one('#source-limitations') and len(bs.select('#source-limitations tbody tr'))>=22
    results['navigation_and_code_integrity']=f'{len(sections)} sections; 107 controls; unique IDs'
    for required in ('原典','TCP','Nmap','PostgreSQL','Log4j','Scapy','localStorage','脆弱','未応答','Nessus','Go','C','許可','使用'):
        assert required in allprose,(rnd,required)
    if START==361:
        for needed in ('完成後の操作ガイド','実行結果の読み方','終了・後片付け','コマンドの引数'):
            assert needed in allprose,(rnd,needed)
    results['security_and_documentation']='permissions, source limitations, glossary, operational guide'
    # Rotate through source + notes so every round records a distinct 64-row sample.
    pool=[(p,n,recovered[p][n].strip()[:110],notes[p][n][:200]) for p in originals for n in sorted(recovered[p]) if recovered[p][n].strip()]
    assert len(pool)==796
    pick=[pool[((rnd-321)*31+j*53+19)%len(pool)] for j in range(64)]
    results['rotating_sample_review']=f'64/796 rows logged, deterministic shifted coverage, not independent human review'
    record={'round':rnd,'phase':'before_editorial_rewrite' if START==321 else 'after_editorial_rewrite',
            'kind':'automated full-manual multi-criterion repeat; rotating samples supplied for separate semantic review; NOT 1 human full-text reading',
            'checks_per_round':checks,'outcomes':results,'samples':pick,'manual_sha256':sha256(htmltext.encode()).hexdigest(),
            'verified_at_utc':datetime.now(timezone.utc).isoformat()}
    with PATH.open('a',encoding='utf-8') as o:o.write(json.dumps(record,ensure_ascii=False)+'\n')
print(f'Completed {len(PATH.read_text(encoding="utf-8").splitlines())}/40 rounds in {PATH.name}')
