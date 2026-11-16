#!/usr/bin/env python3
"""Eighty incremental repeated mechanical audits; 40 before and 40 after substantive revision.
Each pass reopens source code, HTML, fragment instructions and checks multiple invariants.
These iterations are NOT semantic human full reviews.
"""
from __future__ import annotations
import ast, hashlib, json, re, sys, zipfile
from collections import defaultdict
from pathlib import Path
from lxml import html as lhtml
R=Path(__file__).resolve().parents[1]
phase=sys.argv[1] if len(sys.argv)>1 else ''
assert phase in ('pre','post')
first=881 if phase=='pre' else 921
out=R/'audit'/f'REVIEW_ROUNDS_{first}_{first+39}.jsonl'
old=R/'audit'/'BASELINE_880_MANUAL.html'
current=R/'audit/BASELINE_960_MANUAL.html'
base_pf=R/'audit'/'BASELINE_880_PORTFOLIO'

def hashb(b):return hashlib.sha256(b).hexdigest()
def raw(el):return ''.join(el.itertext())
def audit(n):
    checks={}
    hb=(old if phase=='pre' else current).read_bytes()
    dom=lhtml.fromstring(hb)
    sm=json.loads((R/'SOURCE_MANIFEST.json').read_bytes())
    origfr=json.loads((R/'STEP_FRAGMENTS.json').read_bytes())
    source=R/'original_source.zip'
    with zipfile.ZipFile(source) as zipf:
        checks['zip_crc']=zipf.testzip() is None
        checks['zip_original_sha256']=hashb(source.read_bytes())==sm['source_sha256']
        originals={p:zipf.read('pentest-starting-with-port-scanner-main/'+p) for p in sm['files']}
    checks['original_43_hashes']=len(originals)==43 and all(hashb(originals[p])==sm['files'][p]['sha256'] for p in originals)
    chunks=defaultdict(dict);notes=0; tokens=0
    for st in origfr:
        nodes=dom.xpath(f'//article[@id="step-{st["step"]:03d}"]')
        assert len(nodes)==1
        lines=nodes[0].xpath('.//code[contains(@class,"source-lines")]/span[@data-line]')
        cells=nodes[0].xpath('.//table[contains(@class,"line-analysis")]//tbody/tr')
        assert len(lines)==len(cells)==st['end']-st['start']+1
        for pos,el,cell in zip(range(st['start'],st['end']+1),lines,cells):
            assert int(el.get('data-line'))==pos and pos not in chunks[st['path']]
            line=raw(el);chunks[st['path']][pos]=line;notes+=1
            exp=cell.xpath('.//*[contains(@class,"syntactic")]')
            assert exp and len(raw(exp[0]).strip())>8
            if line.strip():
                els=cell.xpath('.//ul[contains(@class,"token-notes")]/li')
                assert els and all(len(raw(x).strip())>=4 for x in els)
                tokens+=len(els)
    checks['original_107_steps']=len(origfr)==107 and len(dom.xpath('//article[contains(@class,"lesson-step")]'))==107
    checks['original_946_notes']=notes==946
    checks['original_reconstructed_bytes']=len(chunks)==43 and all(''.join(chunks[p][i] for i in sorted(chunks[p])).encode()==originals[p] for p in originals)
    checks['original_line_coverage']=all(sorted(chunks[p])==list(range(1,m['lines']+1)) for p,m in sm['files'].items())
    checks['python_AST_original']=all(ast.parse(b.decode()) is not None for p,b in originals.items() if p.endswith('.py'))
    pf=json.loads((R/'PORTFOLIO_FRAGMENTS.json').read_bytes())
    records=defaultdict(dict);pc=0
    for st in pf['steps']:
        art=dom.xpath(f'//article[@id="portfolio-step-{st["stage"]:02d}"]')
        assert len(art)==1
        lines=art[0].xpath('.//code[contains(@class,"portfolio-source-lines")]/span[@data-line]')
        ann=art[0].xpath('.//tr[contains(@class,"portfolio-code-annotation")]')
        assert len(lines)==len(ann)==st['end']-st['start']+1
        for i,el,row in zip(range(st['start'],st['end']+1),lines,ann):
            assert int(el.get('data-line'))==i and i not in records[st['path']]
            assert int(row.get('data-line'))==i and row.get('data-file')==st['path']
            assert len(raw(row).strip())>18
            records[st['path']][i]=raw(el);pc+=1
    currentpf=R/'portfolio_lab' if phase=='post' else base_pf
    checks['portfolio_all_bytes']=len(records)==3 and all(''.join(records[p][i] for i in sorted(records[p])).encode()==(currentpf/p).read_bytes() for p in records)
    checks['portfolio_19_stage_cards']=len(dom.xpath('//article[contains(@class,"portfolio-task")]'))==19
    checks['portfolio_all_notes']=pc==sum(len(x) for x in records.values()) and all(sorted(records[p])==list(range(1,len(records[p])+1)) for p in records)
    for p in ('scanner.py','tests/test_scanner.py'):
        assert ast.parse((currentpf/p).read_text()) is not None
    df=json.loads((R/'REPORT_DIFF_FRAGMENTS.json').read_bytes())
    dr=defaultdict(dict);dn=0
    for st in df['steps']:
        art=dom.xpath(f'//article[@id="diff-step-{st["stage"]:02d}"]')
        assert len(art)==1
        ln=art[0].xpath('.//code[contains(@class,"diff-source-lines")]/span[@data-line]')
        ex=art[0].xpath('.//tr[contains(@class,"diff-code-annotation")]')
        assert len(ln)==len(ex)==st['end']-st['start']+1
        for i,el,row in zip(range(st['start'],st['end']+1),ln,ex):
            assert int(el.get('data-line'))==i and i not in dr[st['path']]
            assert row.get('data-file')==st['path'] and int(row.get('data-line'))==i
            assert len(raw(row).strip())>=(24 if raw(el).strip() else 20)
            dr[st['path']][i]=raw(el);dn+=1
    checks['diff_10_stage_cards']=len(dom.xpath('//article[contains(@class,"report-diff-step")]'))==10
    checks['diff_all_bytes']=len(dr)==2 and all(''.join(dr[p][i] for i in sorted(dr[p])).encode()==(currentpf/p).read_bytes() for p in dr)
    checks['diff_all_notes']=dn==sum(len(x) for x in dr.values()) and all(sorted(dr[p])==list(range(1,len(dr[p])+1)) for p in dr)
    toc=dom.xpath('//button[contains(@class,"toc-item") and @data-target]')
    ids={x.get('id') for x in dom.xpath('//*[@id]')}
    checks['toc_all_valid']=len(toc)>=14 and all(x.get('data-target') in ids for x in toc)
    checks['sections']=len(dom.xpath('//section[contains(@class,"manual-section")]'))>=17
    checks['usage_cards']=len(dom.xpath('//article[contains(@class,"ops-command")]'))==40
    checks['safety_topics']=all(x in raw(dom) for x in ('127.0.0.1','原典','ポートフォリオ','権限','安全','GitHub'))
    lines_by_path={p:originals[p].decode().splitlines(keepends=True) for p in originals}
    names=sorted(originals)
    samples=[(names[(i*7+n)%43],1+((i*19+n)%len(lines_by_path[names[(i*7+n)%43]]))) for i in range(24)]
    checks['rotating_24_samples']=all(chunks[p][idx]==lines_by_path[p][idx-1] for p,idx in samples)
    assert all(checks.values()),{k:v for k,v in checks.items() if not v}
    return {'round':n,'phase':phase,'html_sha256':hashb(hb),'original_lines':notes,'portfolio_lines':pc,'diff_lines':dn,'token_explanations':tokens,'checks':checks,'source_samples':samples,'result':'PASS'}

existing=[json.loads(x) for x in out.read_text().splitlines()] if out.exists() else []
assert [x['round'] for x in existing]==list(range(first,first+len(existing)))
with out.open('a') as stream:
    for i in range(first+len(existing),first+40):
        record=audit(i)
        stream.write(json.dumps(record,ensure_ascii=False)+'\n')
        stream.flush()
        if (i-first+1)%10==0:print(f'{phase} {i-first+1}/40: {len(record["checks"])} checks/round PASS',flush=True)
print('COMPLETE: forty repeated source/HTML machine checks; separate from semantic review')
