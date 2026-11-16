#!/usr/bin/env python3
"""Compare the learner's authored files to the uploaded repository snapshot."""
import argparse,json,hashlib,difflib
from pathlib import Path
P=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser(description='Check written source files against the original attached ZIP.')
parser.add_argument('--root',default='learning_workspace/pentest-starting-with-port-scanner-main',help='Directory containing code/ and containers/.')
args=parser.parse_args()
root=Path(args.root)
if not root.is_absolute():root=P/root
m=json.loads((P/'SOURCE_MANIFEST.json').read_text(encoding='utf-8'))
counts={'MATCH':0,'EMPTY':0,'DIFFER':0,'MISSING':0}
for name,entry in m['files'].items():
    file=root/name
    if not file.is_file():key='MISSING'
    elif not file.stat().st_size:key='EMPTY'
    elif hashlib.sha256(file.read_bytes()).hexdigest()==entry['sha256']:key='MATCH'
    else:key='DIFFER'
    counts[key]+=1
    if key!='MATCH':print(key,name)
print('SUMMARY',counts,'total',len(m['files']))
raise SystemExit(0 if counts['MATCH']==len(m['files']) else 1)
