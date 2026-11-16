#!/usr/bin/env python3
"""Execute only harmless commands and negative/positive checks. No Docker, exploit, raw packet or shellcode execution."""
from pathlib import Path
from zipfile import ZipFile
from subprocess import run
from tempfile import TemporaryDirectory
from socket import socket,AF_INET,SOCK_STREAM
from time import sleep
import json,shutil,os,sys
R=Path(__file__).resolve().parent.parent
m=json.loads((R/'SOURCE_MANIFEST.json').read_text())
with TemporaryDirectory(prefix='portscan-safe-qa-') as tmp:
    tmp=Path(tmp)
    dest=tmp/'workspace'
    x=run(['python3',str(R/'tools/prepare_workspace.py'),'--output',str(dest)],capture_output=True,text=True,timeout=70)
    assert x.returncode==0,x.stderr
    root=dest/'pentest-starting-with-port-scanner-main'
    assert root.is_dir()
    x=run(['python3',str(R/'tools/check_workspace.py'),'--root',str(root)],capture_output=True,text=True,timeout=50)
    assert x.returncode!=0 and "'EMPTY': 43" in x.stdout,x.stdout
    with ZipFile(R/'original_source.zip') as z:
        for p in m['files']:
            (root/p).write_bytes(z.read('pentest-starting-with-port-scanner-main/'+p))
    x=run(['python3',str(R/'tools/check_workspace.py'),'--root',str(root)],capture_output=True,text=True,timeout=50)
    assert x.returncode==0 and "'MATCH': 43" in x.stdout,x.stdout
    cmd=['sh',str(root/'code/chapter03/portscan-tcp-all.sh'),'-h']
    x=run(cmd,capture_output=True,text=True,timeout=10,cwd=tmp)
    assert x.returncode==0 and 'Usage:' in x.stdout,(x.returncode,x.stderr,x.stdout)
    assert not (tmp/'results').exists(),'Help must not execute Nmap'
    if shutil.which('go'):
        env=os.environ.copy();env['CGO_ENABLED']='1';env['GOCACHE']=str(tmp/'gocache');
        go=run(['go','build','-o',str(tmp/'not-executed-shellcode-binary'),str(root/'code/chapter05/shellcode-runner.go')],capture_output=True,text=True,timeout=110,env=env)
        assert go.returncode==0,go.stderr
        assert (tmp/'not-executed-shellcode-binary').is_file()
    if shutil.which('gcc'):
        cc=run(['gcc','-std=c11','-Wall','-Wextra','-Wpedantic','-fsyntax-only',str(root/'code/chapter06/libsniffer.c')],capture_output=True,text=True,timeout=30)
        assert cc.returncode==0,cc.stderr
    # Actual textbook socket scanner with local listener.
    listener=socket(AF_INET,SOCK_STREAM);listener.bind(('127.0.0.1',0));listener.listen(1)
    port=listener.getsockname()[1]
    x=run(['python3',str(root/'code/chapter02/tcp-connect-scan-by-socket.py'),'127.0.0.1',str(port)],capture_output=True,text=True,timeout=12)
    assert x.returncode==0 and f'TCP port {port} is open' in x.stdout,x
    listener.close()
    x=run(['python3',str(root/'code/chapter02/tcp-connect-scan-by-socket.py'),'127.0.0.1',str(port)],capture_output=True,text=True,timeout=12)
    assert x.returncode==0 and f'TCP port {port} is closed' in x.stdout,x
print('PASS: workspace negative/positive hash checks, original help only, local socket open/closed, optional Go build and C compile-only. No offensive samples run.')
