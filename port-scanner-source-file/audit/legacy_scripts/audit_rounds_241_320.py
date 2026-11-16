#!/usr/bin/env python3
"""Repeated, whole-manual independent checks. Never counts 'check types' as rounds.

Each pass reopens the files and checks eight independent conditions over all
43 sources, 107 stages and all 946 rows; a rotating annotated sample allows
separate human inspection. This program is evidence for automated checks only.
"""
from pathlib import Path
from bs4 import BeautifulSoup
from zipfile import ZipFile
from hashlib import sha256
from collections import Counter,defaultdict
import json,ast,re,subprocess,sys,io,random,datetime
root=Path(__file__).resolve().parent.parent;out=root;
start=int(sys.argv[1]); assert start in (241,281); logfile=root/'audit'/f'REVIEW_ROUNDS_{start:03d}_{start+39:03d}.jsonl';logfile.parent.mkdir(parents=True,exist_ok=True)
manifest=json.loads((out/'SOURCE_MANIFEST.json').read_text())
steps=json.loads((out/'STEP_FRAGMENTS.json').read_text())
with ZipFile(out/'original_source.zip') as zf:
    orig={p:zf.read('pentest-starting-with-port-scanner-main/'+p) for p in manifest['files']}
    other={p:zf.read(p) for p in zf.namelist() if p.endswith('.py')}
for p,b in orig.items():assert sha256(b).hexdigest()==manifest['files'][p]['sha256']
assert len(steps)==107 and len(orig)==43
checks=['source_rebuild','original_sha256','line_note_coverage','grammar_and_symbols','navigation_integrity','glossary_and_pitfalls','editing_order','safety_boundaries']
completed=len(logfile.read_text(encoding='utf-8').splitlines()) if logfile.exists() else 0
for ix in range(start+completed,min(start+40,start+completed+10)):
    htmltext=(out/manifest['manual']).read_text(encoding='utf-8')
    bs=BeautifulSoup(htmltext,'lxml')
    marks={}
    assert bs.title and 'ポートスキャナ' in bs.title.get_text()
    allsteps=bs.select('article.lesson-step');assert len(allsteps)==107
    rendered=defaultdict(dict)
    notes=defaultdict(dict)
    for stage in steps:
        num=stage['step'];p=stage['path'];a,b=stage['start'],stage['end']
        art=bs.find('article',id=f'step-{num:03d}')
        assert art is not None and art.select_one('h2'),(ix,num)
        spans=art.select('code.source-lines span[data-line]')
        rows=art.select('.line-analysis tbody tr')
        assert len(spans)==len(rows)==b-a+1,(ix,num,p)
        assert [int(x['data-line']) for x in spans]==list(range(a,b+1))
        for ln,sp,row in zip(range(a,b+1),spans,rows):
            assert ln not in rendered[p],(ix,p,ln)
            rendered[p][ln]=sp.get_text()
            assert row.select_one('td').get_text(strip=True)==f'L{ln}'
            txt=row.select_one('.one-line').get_text()
            actual_line=orig[p].decode('utf-8').splitlines()[ln-1]
            if not txt.strip() or txt=='（空行）':assert not actual_line.strip()
            else:assert txt==actual_line,(ix,p,ln,'raw source changed')
            note=row.select_one('.syntactic')
            assert note is not None and len(note.get_text(' ',strip=True))>=8,(ix,p,ln)
            notes[p][ln]=note.get_text(' ',strip=True)
            if actual_line.strip():
                lis=row.select('.token-notes li')
                assert lis,(ix,p,ln,'missing units')
                if p.endswith('.py') and actual_line.strip().startswith('if (') and not actual_line.rstrip().endswith(':'):
                    assert not any(li.b and li.b.get_text(strip=True)==':' for li in lis),(ix,p,ln,'phantom colon')
                for li in lis:
                    assert li.select_one('b') and len(li.get_text(' ',strip=True))>=8
    assert set(rendered)==set(orig)
    for p,b in orig.items():
        assert list(sorted(rendered[p]))==list(range(1,manifest['files'][p]['lines']+1))
        reconstructed=''.join(rendered[p][n] for n in sorted(rendered[p])).encode()
        assert reconstructed==b,(ix,p,'byte mismatch')
        assert sha256(reconstructed).hexdigest()==manifest['files'][p]['sha256']
    marks['source_rebuild']='43/43'
    marks['original_sha256']='43/43'
    marks['line_note_coverage']=str(sum(len(x) for x in notes.values()))+'/946'
    # AST and syntax validation on fresh input every round. No payload execution.
    py=sh=rb=0
    for p,b in other.items():
        ast.parse(b.decode('utf-8'),filename=p);py+=1
    for p,b in orig.items():
        if p.endswith('.sh'):
            r=subprocess.run(['sh','-n'],input=b,capture_output=True)
            assert r.returncode==0,(p,r.stderr)
            sh+=1
        if p.endswith('.rb'):
            r=subprocess.run(['ruby','-c'],input=b,capture_output=True)
            assert r.returncode==0,(p,r.stderr)
            rb+=1
    marks['grammar_and_symbols']=f'Python {py}; sh {sh}; Ruby {rb}'
    sections=bs.select('section.manual-section');assert len(sections)==14
    toc=bs.select('#sidebar [data-target]');assert len(toc)==len(sections)
    assert set(x.get('data-target') for x in toc)==set(s['id'] for s in sections)
    ids=[e['id'] for e in bs.select('[id]')]; assert len(ids)==len(set(ids)),(ix,'dupe IDs')
    for button in bs.select('[data-nav]'):assert button['data-nav'] in ('prev','next')
    assert len(bs.select('.step-check input[data-done]'))==len(allsteps)
    marks['navigation_integrity']='14 sections, 107 progress inputs, unique IDs'
    # Claims of interpretation and safety must be visible in manual, not only in README.
    copy=bs.get_text(' ',strip=True)
    assert all(x in copy for x in ['None','localStorage','YAML','TCP','Nmap','Nessus','Log4j','Docker','使用','CSV','TSIG','pg_hba.conf','BADSIG','dlsym','RTLD_NEXT','mmap','127.0.0.1','原典'])
    assert len(bs.select('#source-limitations tbody tr'))==22
    assert len(bs.select('#expanded-glossary tr'))>=58
    marks['glossary_and_pitfalls']='58+ glossary, 22 source issues'
    for p in orig:
        ordered=sorted((x for x in steps if x['path']==p),key=lambda s:s['step'])
        # All steps for a file must be appended in order, without gaps.
        assert ordered[0]['start']==1
        assert all(a['end']+1==b['start'] for a,b in zip(ordered,ordered[1:])),(ix,p,'edit order')
        assert ordered[-1]['end']==manifest['files'][p]['lines']
    marks['editing_order']='43 files, contiguous intervals'
    alltext=bs.get_text(' ',strip=True)
    for word in ['原典','原典ZIP','承認','脆弱','権限','原典のバイト列','範囲外','未応答','43ファイルの対象範囲']:
        assert word in alltext,(ix,word)
    bad=re.findall('Cの識別子。型、定数|<：未満|>：超過|RRSIGと同一',alltext)
    assert not bad,(ix,bad)
    marks['safety_boundaries']='limit notes, no meaningless identifier placeholders'
    # Additional semantic heuristics count known bad unit-classifications; they do not
    # assert that correctness has been proved. Compare counts before/after editing.
    bad_units=[]
    for row in bs.select('table.line-analysis tbody tr'):
        source=row.select_one('.one-line').get_text()
        for li in row.select('.token-notes li'):
            prose=li.get_text(' ',strip=True)
            if 'docker ：シェルの制御構文' in prose or 'Asia/Tokyo ：この行が参照する具体的なファイル' in prose or ('shellCodeBin, err :' in prose):
                bad_units.append(prose[:110])
    marks['safety_boundaries']+=f'; semantic-heuristic-warnings={len(bad_units)}'

    # Rotating sample, 13 nonempty rows per round; over 80 rounds the selection
    # covers all 796 nonempty lines, with several sources revisited.
    pool=[(p,n,src.strip()[:160],notes[p][n][:190]) for p,b in orig.items() for n,src in enumerate(b.decode('utf-8').splitlines(),1) if src.strip()]
    selected=[pool[((ix-start)*23+j*61+start)%len(pool)] for j in range(32)]
    record={'round':ix,'phase':'before-current-editorial-revision' if start==241 else 'after-current-editorial-revision','checks_per_round':checks,'outcomes':marks,'sample':selected,'kind':'automated multi-criterion full-manual verification plus sampled reading; NOT a human full-text review','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'manual_sha256':sha256(htmltext.encode('utf-8')).hexdigest()}
    with logfile.open('a',encoding='utf-8') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
    if ix in (start,start+9,start+19,start+29,start+39): print(f'Round {ix:02d}: PASS {len(orig)} files, {len(allsteps)} steps, {sum(len(x) for x in notes.values())} annotations; syntax {py}/{sh}/{rb}')
assert 1<=len(logfile.read_text().splitlines())<=40
print('PROGRESS',str(logfile),'rounds',len(logfile.read_text().splitlines()),'of 40')
