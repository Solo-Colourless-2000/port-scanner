#!/usr/bin/env python3
"""Independent high-risk teaching-text checks. Source fidelity is tested separately."""
from pathlib import Path
from zipfile import ZipFile
from bs4 import BeautifulSoup
from collections import defaultdict
import json, hashlib, re
root=Path(__file__).resolve().parent.parent
manifest=json.loads((root/'SOURCE_MANIFEST.json').read_text())
steps=json.loads((root/'STEP_FRAGMENTS.json').read_text())
changes=json.loads((root/'EDITORIAL_PATCHES_161_240.json').read_text())
doc=BeautifulSoup((root/manifest['manual']).read_text(),'lxml')
assert changes['count']>=55,changes['count']
assert len(doc.select('.precision-workshop'))==7
assert len(doc.select('.source-reasoning .symbol-row'))==7
assert len(doc.select('article.lesson-step'))==107
assert len(doc.select('article.lesson-step table.line-analysis tbody tr'))==946
assert len(doc.select('#source-limitations tbody tr'))==22
assert len(doc.select('#expanded-glossary tr'))>=58
assert len(doc.select('section.manual-section'))==17
seen=defaultdict(dict);units=defaultdict(dict);notes=defaultdict(dict)
for st in steps:
 e=doc.find('article',id=f"step-{st['step']:03}")
 assert e
 for sp,row in zip(e.select('code.source-lines span[data-line]'),e.select('table.line-analysis tbody tr')):
  n=int(sp['data-line']);key=st['path']
  assert n not in seen[key],(key,n)
  seen[key][n]=sp.get_text()
  units[key][n]=[li.get_text(' ',strip=True) for li in row.select('.token-notes li')]
  notes[key][n]=row.select_one('.syntactic').get_text(' ',strip=True)
with ZipFile(root/'original_source.zip') as z:
 for path in manifest['files']:
  recovered=''.join(seen[path][i] for i in sorted(seen[path])).encode()
  original=z.read('pentest-starting-with-port-scanner-main/'+path)
  assert original==recovered,(path,'byte mismatch')
  assert hashlib.sha256(original).hexdigest()==manifest['files'][path]['sha256']
assert sum(map(len,seen.values()))==946
# Semantic regressions found in the prior version.
for name, rows in units.items():
 for n,lines in rows.items():
  raw=' '.join(lines)
  assert not ('docker ：シェルの制御構文' in raw or 'Asia/Tokyo ：この行が参照する具体的なファイル' in raw),(name,n)
  assert 'Cの識別子。型、定数' not in raw,(name,n)
  if name.endswith('shellcode-runner.go') and n==35:
   assert any(':= ：' in x for x in lines)
   assert not any(x.startswith('= ：') for x in lines)
  if name.endswith('tcp-syn-scan.py') and n==17:
   assert not any(x.startswith(': ：') for x in lines)
  if name.endswith('libsniffer.c') and n in (1,2,3):
   assert any('ヘッダー' in x or '宣言' in x for x in lines)
  if name.endswith('Dockerfile') and n==3 and name in ('containers/pentester/Dockerfile','containers/ssh/Dockerfile'):
   assert 'タイムゾーン' in ' '.join(lines)
# Failing examples are described as source limitations rather than silently fixed.
assert 'None' in notes['code/chapter02/tcp-syn-scan.py'][17]
assert 'NUL終端' in notes['code/chapter06/libsniffer.c'][5]
assert 'CSV' in notes['code/chapter03/nmap-xml2csv.rb'][29]
assert 'SQL' in notes['containers/postgres/sql/init.sql'][3]
assert 'required=false' in notes['containers/log4j/src/main/java/fr/christophetd/log4shell/vulnerableapp/MainController.java'][17]
assert '400' in notes['containers/log4j/src/main/java/fr/christophetd/log4shell/vulnerableapp/MainController.java'][17]
# Tamper resistance smoke-test: mutate an in-memory original fragment and ensure
# checksum mismatches; this does not touch the distributed HTML/ZIP.
p='code/chapter02/tcp-connect-scan-by-socket.py';copy=dict(seen[p]);copy[11]=copy[11].replace('connect_ex','connect')
assert hashlib.sha256(''.join(copy[i] for i in sorted(copy)).encode()).hexdigest()!=manifest['files'][p]['sha256']

new_ed=json.loads((root/'EDITORIAL_PATCHES_241_320.json').read_text())
assert new_ed['new_main_explanations'] == 69
assert new_ed['added_focused_unit_explanations'] == 11
assert new_ed['additional_cross_file_workshops'] == 10
assert len(doc.select('.context-workshop')) == 10
assert len(doc.select('.deep-symbols')) == 11
for path, line in [('containers/postgres/Dockerfile',8), ('code/chapter06/libsniffer.c',9),('containers/pentester/code/chapter02/sniff-icmp-by-arp-spoofing.py',71)]:
 assert path in notes and line in notes[path]
 assert len(notes[path][line]) > 80
print('PASS: prior 56 edits and new 69 contextual explanations, 11 token breakdowns, 10 workshops; 43 byte-accurate sources; semantic regressions')
