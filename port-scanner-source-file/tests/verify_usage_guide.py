#!/usr/bin/env python3
"""Check independent usage instructions and cross-file factual alignment."""
from pathlib import Path
from bs4 import BeautifulSoup
from zipfile import ZipFile
import json
R=Path(__file__).resolve().parent.parent
m=json.loads((R/'SOURCE_MANIFEST.json').read_text())
s=BeautifulSoup((R/m['manual']).read_text(),'lxml')
usage=s.find('section',id='usage')
assert usage
cards=usage.select('article.ops-command')
assert len(cards)==40
assert len(usage.select('.ops-intro'))==10
for c in cards:
    title=c.select_one('h3')
    code=c.select_one('.terminal-wrap pre code')
    assert title and code and len(code.get_text(strip=True))>=6
    assert c.select_one('.operation-parts li strong')
    assert '実行結果の読み方' in c.get_text()
    assert '失敗時の確認' in c.get_text()
text=usage.get_text(' ',strip=True)
for value in ['127.0.0.1','8765','8766','--directory','-sT','-Pn','-oX','ruby-nmap','pg_hba.conf','-p-','X-Api-Version','SNMP','docker compose up -d','docker compose down','--root']:
    # source has no SNMP, do not assert unrelated technology.
    if value=='SNMP': continue
    assert value in text,value
with ZipFile(R/'original_source.zip') as z:
    prefix='pentest-starting-with-port-scanner-main/'
    compose=z.read(prefix+'containers/compose.yaml').decode()
    assert all(x in compose for x in ['10.8.9.2','10.8.9.7','127.0.0.1:5432:5432','privileged: true'])
    ruby=z.read(prefix+'code/chapter03/nmap-xml2csv.rb').decode()
    assert 'nmap_file = ARGV[0]' in ruby and 'host.ip + "\\t"' in ruby
    shell=z.read(prefix+'code/chapter03/portscan-tcp-all.sh').decode()
    assert '-p- -PS22,80,443 -sS' in shell and 'sudo nmap' in shell
    assert z.read(prefix+'containers/pentester/code/chapter03/target-hosts.txt').decode().strip()=='10.8.9.0/24'
    assert z.read(prefix+'containers/pentester/code/chapter03/exclude-hosts.txt').decode().strip()=='10.8.9.7'
    assert z.read(prefix+'containers/postgres/sql/init.sql').decode().splitlines()[2]=='\\c sample;'
print('PASS: 40 detailed usage cards in 10 subsections; commands, arguments, outcomes, failure conditions and source-specific caveats present.')
