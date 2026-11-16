#!/usr/bin/env python3
"""Verify a fully extracted v984 release. SHA-256 checks are not origin authentication."""
from pathlib import Path
from hashlib import sha256
import json
R=Path(__file__).resolve().parents[1]
manifest=json.loads((R/'PACKAGE_MANIFEST_v984.json').read_text())
expected=manifest['files']
assert len(expected)>100
for rel,digest in expected.items():
    p=R/rel
    assert p.is_file(),f'missing: {rel}'
    assert sha256(p.read_bytes()).hexdigest()==digest,f'mismatch: {rel}'
actual={p.relative_to(R).as_posix() for p in R.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
assert actual==set(expected)|{'PACKAGE_MANIFEST_v984.json'}, sorted(actual ^ (set(expected)|{'PACKAGE_MANIFEST_v984.json'}))[:20]
print('PASS:',len(expected),'file SHA-256 comparisons and exact contents; no extraneous files')
