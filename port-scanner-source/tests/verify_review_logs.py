#!/usr/bin/env python3
"""Check all 800 recorded automated pass records and the relevant baseline/final hashes.

This checks recorded automated passes, NOT human reading 800 full texts.
"""
from pathlib import Path
import gzip
import json
from hashlib import sha256
R=Path(__file__).resolve().parent.parent
names=['REVIEW_ROUNDS_01_40.jsonl','REVIEW_ROUNDS_41_80.jsonl',
       'REVIEW_ROUNDS_081_120.jsonl','REVIEW_ROUNDS_121_160.jsonl',
       'REVIEW_ROUNDS_161_200.jsonl','REVIEW_ROUNDS_201_240.jsonl',
       'REVIEW_ROUNDS_241_280.jsonl','REVIEW_ROUNDS_281_320.jsonl',
       'REVIEW_ROUNDS_321_360.jsonl','REVIEW_ROUNDS_361_400.jsonl',
       'REVIEW_ROUNDS_401_440.jsonl','REVIEW_ROUNDS_441_480.jsonl',
       'REVIEW_ROUNDS_481_520.jsonl','REVIEW_ROUNDS_521_560.jsonl',
       'REVIEW_ROUNDS_561_600.jsonl','REVIEW_ROUNDS_601_640.jsonl',
       'REVIEW_ROUNDS_641_680.jsonl','REVIEW_ROUNDS_681_720.jsonl',
       'REVIEW_ROUNDS_721_760.jsonl','REVIEW_ROUNDS_761_800.jsonl']
old={'source_rebuild','original_sha256','line_note_coverage','grammar_and_symbols',
      'navigation_integrity','glossary_and_pitfalls','editing_order','safety_boundaries'}
recent={'original_archive_integrity','all_file_byte_reconstruction','line_annotation_coverage',
        'lexical_and_contextual_fidelity','language_grammar','step_edit_order',
        'HTML_navigation_and_accessibility','safety_and_usage','source_grounded_manual_claims','rotating_line_sample'}
new={'archive_provenance','source_byte_reconstruction','all_line_explanations',
     'symbol_and_context_tests','syntax_and_xml','step_edit_continuity',
     'navigation_and_code_integrity','security_and_documentation','rotating_sample_review'}
latest={'archive_and_source_hashes','source_reassembly_all_lines','source_explanations_all_lines',
        'portfolio_reassembly_and_notes','source_specific_semantic_regression','syntax_and_configuration',
        'interleaved_development_order','navigation_accessibility_and_layout_markers',
        'operational_portfolio_and_permission_guidance','rotating_real_code_context_sample'}
records=[]
for filename in names:
    raw=(R/'audit'/filename).read_text(encoding='utf-8').splitlines()
    assert len(raw)==40,(filename,len(raw))
    records.extend(json.loads(x) for x in raw)
assert len(records)==800
assert [r['round'] for r in records]==list(range(1,801))
for r in records:
    if r['round']>=721:
        assert r['result']=='PASS' and len(r['checks'])==19
        assert r['original_lines']==946 and len(r['source_samples'])==24
        assert r['portfolio_lines']==237 and r['diff_lines']==(357 if r['round']<=760 else 389)
        assert r['checks']['original_reconstructed_bytes'] and r['checks']['diff_all_bytes']
        continue
    if r['round']>=641:
        assert r['result']=='PASS' and len(r['checks'])>=18
        assert r['source_files']==43 and r['source_lines']==946
        assert r['diff_lines']==(292 if r['round']<=680 else 357)
        assert r['portfolio_lines']==(233 if r['round']<=680 else 237)
        assert len(r['rotating_sources'])==24
        continue
    if r['round']>=561:
        assert len(r['checks'])==(11 if r['round']<=600 else 12) and len(r['samples_source'])==48 and len(r['samples_portfolio'])==24
        assert r['results']['source_files']==43 and r['results']['source_lines']==946
        continue
    current=old if r['round']<=320 else new if r['round']<=400 else recent if r['round']<=480 else latest
    assert set(r['checks_per_round'])==set(r['outcomes'])==current,r['round']
    if r['round']>=241:
        assert r['manual_sha256'] and len(r['manual_sha256'])==64
    if r['round']<=320:
        assert r['outcomes']['source_rebuild']=='43/43'
        assert r['outcomes']['original_sha256']=='43/43'
        assert r['outcomes']['line_note_coverage']=='946/946'
        assert len(r['sample'])==(13 if r['round']<=80 else 32)
        assert r['checked_utc']
    elif r['round']<=400:
        assert '43/43' in r['outcomes']['source_byte_reconstruction']
        assert '946/946' in r['outcomes']['all_line_explanations']
        assert len(r['samples'])==64
        assert r['verified_at_utc']
    elif r['round']<=480:
        assert '43/43' in r['outcomes']['all_file_byte_reconstruction']
        assert '946/946' in r['outcomes']['line_annotation_coverage']
        assert len(r['samples'])==64
        assert r['verified_at_utc']
    else:
        assert '43/43' in r['outcomes']['source_reassembly_all_lines']
        assert '946' in r['outcomes']['source_explanations_all_lines']
        assert len(r['samples'])==48 and len(r['portfolio_samples'])==24
        assert r['verified_at_utc']
assert all('semantic-heuristic-warnings=13' in r['outcomes']['safety_boundaries'] for r in records[160:200])
assert all('semantic-heuristic-warnings=0' in r['outcomes']['safety_boundaries'] for r in records[200:320])
manifest=json.loads((R/'SOURCE_MANIFEST.json').read_text())
pre_240=sha256(gzip.decompress((R/'audit/BASELINE_240_MANUAL.html.gz').read_bytes())).hexdigest()
pre_320=sha256(gzip.decompress((R/'audit/BASELINE_320_MANUAL.html.gz').read_bytes())).hexdigest()
pre_400=sha256(gzip.decompress((R/'audit/BASELINE_400_MANUAL.html.gz').read_bytes())).hexdigest()
post_480=sha256(gzip.decompress((R/'audit/BASELINE_480_MANUAL.html.gz').read_bytes())).hexdigest()
pre_480=sha256(gzip.decompress((R/'audit/BASELINE_480_MANUAL.html.gz').read_bytes())).hexdigest()
post_560=sha256(gzip.decompress((R/'audit/BASELINE_560_MANUAL.html.gz').read_bytes())).hexdigest()
post_640=sha256(gzip.decompress((R/'audit/BASELINE_640_MANUAL.html.gz').read_bytes())).hexdigest()
post_720=sha256((R/'audit/BASELINE_720_MANUAL.html').read_bytes()).hexdigest()
post_800=sha256((R/'audit/BASELINE_800_MANUAL.html').read_bytes()).hexdigest()
assert {r['manual_sha256'] for r in records[240:280]}=={pre_240}
assert {r['manual_sha256'] for r in records[280:320]}=={pre_320}
assert {r['manual_sha256'] for r in records[320:360]}=={pre_320}
assert {r['manual_sha256'] for r in records[360:400]}=={pre_400}
assert pre_240!=pre_320!=pre_400
assert {r['manual_sha256'] for r in records[400:440]}=={pre_400}
assert {r['manual_sha256'] for r in records[440:480]}=={post_480}
assert pre_400!=post_480
assert {r['manual_sha256'] for r in records[480:520]}=={pre_480}=={post_480}
assert {r['manual_sha256'] for r in records[520:560]}=={post_560}
assert pre_480!=post_560
assert {r['html_sha256'] for r in records[560:600]}=={post_560}
assert {r['html_sha256'] for r in records[600:640]}=={post_640}
assert post_560!=post_640
assert {r['html_sha256'] for r in records[640:680]}=={post_640}
assert {r['html_sha256'] for r in records[680:720]}=={post_720}
assert post_640 != post_720
assert {r['html_sha256'] for r in records[720:760]}=={post_720}
assert {r['html_sha256'] for r in records[760:800]}=={post_800}
assert post_720!=post_800
assert records[0]['round']==1 and records[-1]['round']==800
print('PASS: 800 consecutive automated passes; rounds 721-760 baseline and 761-800 final revision have correct SHA-256.')
print('LIMITATION: automated checks do not represent 800 independent human semantic full-text readings.')
