#!/usr/bin/env python3
"""Unpack the attached source ZIP and blank only the 43 manually edited sources."""
import argparse
from pathlib import Path
from zipfile import ZipFile
import json, sys
P=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser(description='Create an editable learning_workspace from the supplied source ZIP.')
parser.add_argument('--output',default='learning_workspace',help='Output directory, relative to bundle root by default.')
args=parser.parse_args()
root=Path(args.output)
if not root.is_absolute():root=P/root
if root.exists():sys.exit('The destination already exists; refusing to overwrite: '+str(root))
m=json.loads((P/'SOURCE_MANIFEST.json').read_text(encoding='utf-8'))
with ZipFile(P/'original_source.zip') as z:
    for info in z.infolist():
        if info.is_dir():continue
        parts=Path(info.filename).parts
        if len(parts)<2 or parts[0]!='pentest-starting-with-port-scanner-main' or '..' in parts or Path(info.filename).is_absolute():
            sys.exit('Unsafe path in ZIP: '+info.filename)
        dest=root/Path(info.filename)
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(z.read(info))
        # Preserve executable permissions recorded by the uploaded ZIP.
        # The original gradlew and several shell scripts are 0755.
        if info.create_system == 3:
            file_mode=(info.external_attr >> 16) & 0o777
            if file_mode:
                dest.chmod(file_mode)
for p in m['files']:
    dest=root/'pentest-starting-with-port-scanner-main'/p
    if not dest.is_file():sys.exit('Missing editable file: '+p)
    dest.write_bytes(b'')
print('READY',root/'pentest-starting-with-port-scanner-main')
print('Blank editable files:',len(m['files']))
print('Original binary/vendor assets remain in place.')
