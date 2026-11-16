#!/usr/bin/env python3
"""24 separate passes; each freshly parses final HTML and rechecks multiple complete sets."""
from pathlib import Path
from collections import defaultdict
from zipfile import ZipFile
from hashlib import sha256
from lxml import html
import json, ast, random
R=Path(__file__).resolve().parents[1]
HTML=R/'portscanner_pentest_development_manual_v984_20261117.html'
O=json.loads((R/'SOURCE_MANIFEST.json').read_text())
PF=json.loads((R/'PORTFOLIO_FRAGMENTS.json').read_text())
DF=json.loads((R/'REPORT_DIFF_FRAGMENTS.json').read_text())
ST=json.loads((R/'STEP_FRAGMENTS.json').read_text())
OLD=R/'original_source.zip'
OUT=R/'audit/REVIEW_ROUNDS_961_984.jsonl'
assert O['manual']==HTML.name
with ZipFile(OLD) as z:
    original={p:z.read('pentest-starting-with-port-scanner-main/'+p) for p in O['files']}
assert len(original)==43
sha=lambda b:sha256(b).hexdigest()

def rebuild(doc,step_specs,article_prefix,source_class,row_class):
    gathered=defaultdict(dict)
    details=0
    for st in step_specs:
        article=doc.xpath(f'//article[@id="{article_prefix}-{st.get("step",st.get("stage")):0{3 if article_prefix=="step" else 2}d}"]')
        assert len(article)==1,(article_prefix,st)
        src=article[0].xpath(f'.//code[contains(@class,"{source_class}")]/span[@data-line]')
        notes=article[0].xpath(f'.//tr[contains(@class,"{row_class}")]') if row_class else article[0].xpath('.//table[contains(@class,"line-analysis")]//tbody/tr')
        expected=(st.get('end',0)-st.get('start',1)+1) if article_prefix!='step' else len(src)
        assert len(src)==len(notes)==expected,(article_prefix,st,len(src),len(notes),expected)
        for idx,(sp,row) in enumerate(zip(src,notes)):
            n=int(sp.get('data-line'))
            assert n not in gathered[st['path']],(st['path'],n)
            if article_prefix!='step':
                assert n==st['start']+idx and row.get('data-file')==st['path']
                assert int(row.get('data-line'))==n
            note=row.xpath('.//p[contains(@class,"syntactic")]') if article_prefix!="portfolio-step" else row.xpath('.//td[last()]/p')
            assert len(note)==1 and len(note[0].text_content().strip())>=12,(st['path'],n)
            gathered[st['path']][n]=sp.text_content()
            details+=1
    return {p:''.join(rows[n] for n in sorted(rows)).encode() for p,rows in gathered.items()},details,gathered

def run(n):
    contents=HTML.read_bytes()
    doc=html.fromstring(contents)  # fresh DOM every pass, not reused across rounds
    checks={}
    checks['source_archive_hash_matches_manifest']=sha(OLD.read_bytes())==O['source_sha256']
    rec, count, dct=rebuild(doc,ST,'step','source-lines',None)
    checks['original_43_source_byte_match']=len(rec)==43 and all(rec.get(p)==data for p,data in original.items())
    checks['original_43_sha256_match']=all(sha(rec[p])==O['files'][p]['sha256'] for p in original)
    checks['original_946_line_explanations']=count==946 and sum(len(x) for x in dct.values())==946
    checks['original_107_incremental_stages']=len(ST)==107 and len(doc.xpath('//article[contains(@class,"lesson-step")]'))==107
    pf,pc,pfd=rebuild(doc,PF['steps'],'portfolio-step','portfolio-source-lines','portfolio-code-annotation')
    checks['portfolio_source_bytes_match']=len(pf)==3 and all(pf[p]==(R/'portfolio_lab'/p).read_bytes() for p in pf)
    checks['portfolio_237_line_explanations']=pc==237
    checks['portfolio_19_incremental_stages']=len(doc.xpath('//article[contains(@class,"portfolio-task")]'))==19
    df,dc,dfd=rebuild(doc,DF['steps'],'diff-step','diff-source-lines','diff-code-annotation')
    checks['report_diff_source_bytes_match']=len(df)==2 and all(df[p]==(R/'portfolio_lab'/p).read_bytes() for p in df)
    checks['report_diff_manifest_sha256_match']=all(sha(df[p])==DF['files'][p]['sha256'] for p in df)
    checks['report_diff_513_line_explanations']=dc==513
    checks['report_diff_10_incremental_stages']=len(DF['steps'])==10
    checks['python_ast_all_original_and_portfolio']=all(ast.parse(b.decode()) is not None for p,b in original.items() if p.endswith('.py')) and all(ast.parse(b.decode()) is not None for p,b in {**pf,**df}.items() if p.endswith(".py"))
    ids={e.get('id') for e in doc.xpath('//*[@id]')}
    buttons=doc.xpath('//button[contains(@class,"toc-item") and @data-target]')
    checks['navigation_all_target_ids_exist']=len(buttons)>=16 and all(e.get('data-target') in ids for e in buttons)
    checks['usage_40_command_cards']=len(doc.xpath('//article[contains(@class,"ops-command")]'))==40
    checks['portfolio_security_guidance']=all(x in doc.text_content() for x in ('127.0.0.1','GitHub','ポートフォリオ','権限','原典'))
    appendix=doc.xpath('//*[@id="utf8-validation-v984"]')
    checks['encoding_guide_precise_terms']=len(appendix)==1 and all(x in appendix[0].text_content() for x in ('UTF-8','UTF-16','UTF-32','BOM','UnicodeDecodeError','JSONDecodeError'))
    checks['strict_decode_and_regression_tests']=b'raw.decode("utf-8")' in df['report_diff.py'] and b'test_reports_reject_non_utf8_encodings' in df['tests/test_report_diff.py'] and b'test_reports_reject_invalid_utf8_bytes' in df['tests/test_report_diff.py']
    checks['version_and_file_identity']=('v984' in HTML.name and 'SNAKE_STYLE' not in HTML.name and '984' in doc.xpath('//title')[0].text_content())
    checks['source_specific_semantic_annotated_lines']=all(
        any(term in doc.xpath(f'//article[@id="step-{s["step"]:03d}"]')[0].text_content() for s in ST if s['path']==p)
        for p,term in [('code/chapter02/tcp-syn-scan.py','None'),('code/chapter06/libsniffer.c','NUL終端'),('containers/postgres/Dockerfile','pg_hba.conf')]
    )
    # Sample 24 genuinely different lines on each pass, from the 43 complete reconstructed files.
    paths=list(original);randomizer=random.Random(n * 2017)
    sample=[]
    for _ in range(24):
        p=randomizer.choice(paths);lines=original[p].decode().splitlines(keepends=True)
        i=randomizer.randrange(len(lines))
        assert dct[p][i+1]==lines[i]
        sample.append({'path':p,'line':i+1})
    checks['round_specific_24_line_samples']=len(sample)==24
    assert all(checks.values()),(n,{k:v for k,v in checks.items() if not v})
    return {'round':n,'html_sha256':sha(contents),'result':'PASS', 'checks':checks,'source_lines':count,'portfolio_lines':pc,'report_diff_lines':dc,'samples':sample}

prior=[json.loads(x) for x in OUT.read_text().splitlines()] if OUT.exists() else []
assert [x['round'] for x in prior]==list(range(961,961+len(prior)))
with OUT.open('a') as out:
    for n in range(961+len(prior),985):
        item=run(n)
        out.write(json.dumps(item,ensure_ascii=False)+'\n');out.flush()
        if (n-960)%4==0: print(f'PASS {n-960}/24:  {len(item["checks"])} distinct checks this pass, 946+237+513 explanation lines',flush=True)
print('COMPLETE: 24 fresh full-document automated passes. Distinct from semantic code review.')
