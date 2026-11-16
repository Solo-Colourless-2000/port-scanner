#!/usr/bin/env python3
"""Locally verify scanner -> two JSON files -> report_diff, no outside network."""
from pathlib import Path
import json, socket, subprocess, sys, tempfile, time
ROOT=Path(__file__).resolve().parents[1]/'portfolio_lab'
with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as listener, tempfile.TemporaryDirectory() as tmp:
    listener.bind(('127.0.0.1',0))
    listener.listen(1)
    port=listener.getsockname()[1]
    out=Path(tmp)
    before,after,delta=(out/x for x in ('before.json','after.json','difference.json'))
    def scan(destination):
        r=subprocess.run([sys.executable,'scanner.py','--target','127.0.0.1','--ports',str(port),'--output',str(destination)],cwd=ROOT,text=True,capture_output=True)
        assert r.returncode==0,r.stderr
        return json.loads(destination.read_text())
    pre=scan(before)
    assert pre['results'][0]['state']=='open',pre
    listener.close()
    time.sleep(0.03)
    post=scan(after)
    assert post['results'][0]['state']=='refused',post
    # A standalone schema check precedes the offline comparison; it does not scan.
    for saved in (before, after):
        validated = subprocess.run([sys.executable, 'report_diff.py', '--validate', str(saved)], cwd=ROOT, text=True, capture_output=True)
        assert validated.returncode == 0, validated.stderr
        assert 'VALID:' in validated.stdout, validated.stdout
    r=subprocess.run([sys.executable,'report_diff.py','--before',str(before),'--after',str(after),'--output',str(delta)],cwd=ROOT,text=True,capture_output=True)
    assert r.returncode==0,r.stderr
    doc=json.loads(delta.read_text())
    assert doc['state_changes']==[{'port':port,'before':'open','after':'refused'}],doc
    assert doc['unchanged_ports']==0 and doc['ports_checked']==1
    print('PASS: owned 127.0.0.1 listener open->refused, two saved scanner reports and offline difference JSON. port=',port)
