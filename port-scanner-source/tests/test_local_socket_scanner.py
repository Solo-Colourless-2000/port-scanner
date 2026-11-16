#!/usr/bin/env python3
"""Behavior smoke test for the unmodified scanner against a local loopback listener only."""
from pathlib import Path
from subprocess import run
from socket import socket, AF_INET, SOCK_STREAM
from zipfile import ZipFile
from tempfile import TemporaryDirectory
from threading import Thread

zip_path=Path(__file__).resolve().parent.parent/'original_source.zip'
member='pentest-starting-with-port-scanner-main/code/chapter02/tcp-connect-scan-by-socket.py'
with ZipFile(zip_path) as z, TemporaryDirectory() as td:
    script=Path(td)/'socket_scanner.py'
    script.write_bytes(z.read(member))
    listener=socket(AF_INET,SOCK_STREAM)
    listener.settimeout(5)
    listener.bind(('127.0.0.1',0))
    listener.listen(1)
    port=listener.getsockname()[1]
    seen=[]
    def accept_once():
        conn,_=listener.accept();seen.append(True);conn.close()
    t=Thread(target=accept_once,daemon=True);t.start()
    result=run(['python3',str(script),'127.0.0.1',str(port)],capture_output=True,text=True,timeout=5)
    assert result.returncode==0 and f'TCP port {port} is open' in result.stdout,result
    t.join(timeout=5)
    assert seen,'listener did not accept'
    listener.close()
    result=run(['python3',str(script),'127.0.0.1',str(port)],capture_output=True,text=True,timeout=5)
    assert result.returncode==0 and f'TCP port {port} is closed' in result.stdout,result
print('PASS: unmodified socket scanner reports an open loopback listener and closed loopback port')
