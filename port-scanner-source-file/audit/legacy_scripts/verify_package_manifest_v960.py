#!/usr/bin/env python3
"""Check a locally extracted release against the SHA-256 manifest (not a signature)."""
from pathlib import Path
import hashlib, json
R=Path(__file__).resolve().parents[1]
manifest=json.loads((R/'PACKAGE_MANIFEST_v960.json').read_text(encoding='utf-8'))
expected=manifest['files']
assert len(expected)>=100
for name,digest in expected.items():
    p=R/name
    assert p.is_file(),f'missing {name}'
    actual=hashlib.sha256(p.read_bytes()).hexdigest()
    assert actual==digest,f'checksum mismatch: {name}'
actual_paths={p.relative_to(R).as_posix() for p in R.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
assert actual_paths==set(expected)|{'PACKAGE_MANIFEST_v960.json'},sorted(actual_paths^set(expected))[:20]
print(f'PASS: {len(expected)} distributable file SHA-256 checks; manifest self-excluded. Checksums are not cryptographic provenance.')
