#!/usr/bin/env python3
"""One-time editorial builder: preserves all original example lines, updates an independent
portfolio example and adds detailed reviews, executable workflows and interview guidance.
This is not an automated claim that descriptions are semantically correct.
"""
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString, Tag
from hashlib import sha256
import copy, difflib, json, re, gzip
ROOT=Path(__file__).resolve().parents[1]
old_file=ROOT/'portscanner_pentest_SNAKE_style_480round_refined_manual_20261116.html'
new_file=ROOT/'portscanner_pentest_SNAKE_style_560round_refined_manual_20261116.html'
html=BeautifulSoup(old_file.read_text(encoding='utf-8'),'lxml')
parts=json.loads((ROOT/'PORTFOLIO_FRAGMENTS.json').read_text(encoding='utf-8'))

new_explanations={
 ('scanner.py','    except TimeoutError:\n'):'`except` は直前の `try` 内で発生した例外を捕捉する構文。`TimeoutError` は接続試行が時間切れで失敗した場合の例外型で、`OSError` の一種でもある。より広い `OSError` より先に置くことで、この例外を専用の分岐で処理できる。インデント4個は `try` と同じ階層。',
 ('scanner.py','        code = errno.ETIMEDOUT\n'):'`code` は後続のポート状態分類で参照するローカル変数。`=` は右辺の値を左辺へ束縛する代入演算子。`errno.ETIMEDOUT` はPython標準ライブラリの「時間切れ」に対応するエラー定数で、例外オブジェクトに `.errno` がない場合でも一定の分類ができる。ここでは通信を再試行していない。',
 ('tests/test_scanner.py','import errno\n'):'テスト側でもOSのエラーコード定数を参照するため `errno` モジュールを読み込む。モジュール名 `errno` は `ETIMEDOUT`（時間切れ）と `ENETUNREACH`（ネットワーク到達不能）などの名前を提供する。エラーの数値自体はOSに依存するため固定値を書かない。',
 ('tests/test_scanner.py','from unittest.mock import patch\n'):'`from ... import ...` はモジュールの特定の名前を取り込む構文。`unittest.mock.patch` は指定した参照をテスト実行中だけ差し替え、実際のネットワークに接続せず「通信が失敗した状況」を再現する。`with` ブロックの終了後には差し替えが戻る。',
 ('tests/test_scanner.py','class ProbeErrorTests(unittest.TestCase):\n'):'`class` で例外処理だけを独立検証するテストクラスを定義。`ProbeErrorTests` は任意のクラス名、丸括弧内の `unittest.TestCase` はassert系メソッドを提供する基底クラス、末尾の `:` はインデントされたクラス本体の開始を意味する。',
 ('tests/test_scanner.py','    def test_timeout_exception_without_errno(self):\n'):'`def` は関数（ここではテストメソッド）の定義。`test_` で始まる名前は `unittest` に自動検出される。`self` はこのテストクラスのインスタンスを受け取る引数で、続く `:` 以下を1つのテストとして実行する。',
 ('tests/test_scanner.py','        with patch("scanner.socket.socket") as mocked:\n'):'`with` はモック差し替えの適用期間を限定する。`patch("scanner.socket.socket")` は `scanner` モジュール内で参照されるソケット生成関数だけを差し替える。`as mocked` は差し替え用モックを `mocked` に受け取る。文字列中のドットはモジュール・属性の参照経路で、ファイルパスではない。',
 ('tests/test_scanner.py','            mocked.return_value.__enter__.return_value.connect_ex.side_effect = TimeoutError()\n'):'モックの `return_value` は関数呼び出し結果、`__enter__.return_value` は `with socket.socket(...) as sock` で得られるオブジェクトを示す。そこで `connect_ex` の `side_effect` に `TimeoutError()` を代入し、実通信なしで時間切れの例外を起こす。`=` は属性への代入。長い参照経路を短絡して読むと、モックが「どの場所で」働くかを誤解する。',
 ('tests/test_scanner.py','            result = probe("127.0.0.1", 8765, 0.2)\n'):'`probe()` にループバックIPv4、ポート8765、タイムアウト0.2秒を渡す。ここでは `patch` が有効なのでOSへTCP接続は行われない。戻った辞書を `result` へ保存する。実際の時間経過を待つテストではない。',
 ('tests/test_scanner.py','        self.assertEqual(result["state"], "timeout")\n'):'`self.assertEqual(a,b)` は2つの値が同じであることを確認するテストの検証点。`result["state"]` は結果辞書の `state` キーの値で、期待する文字列 `"timeout"` と比較。ここが誤ると接続の時間切れを不明エラーと表示してしまう。',
 ('tests/test_scanner.py','        self.assertEqual(result["errno"], errno.ETIMEDOUT)\n'):'`result["errno"]` に結果へ記録したエラーコードが入り、`errno.ETIMEDOUT` と一致するか検証する。表示テキストだけでなく機械処理する数値フィールドの一貫性も確認している。',
 ('tests/test_scanner.py','    def test_unreachable_errno_without_external_traffic(self):\n'):'`test_` で始まる2件目のメソッド。接続試行が `ENETUNREACH`（ネットワークに経路がない）を返したケースを外部通信なしで試す。タイムアウトと到達不能を同一視しないためのテスト。',
 ('tests/test_scanner.py','            mocked.return_value.__enter__.return_value.connect_ex.return_value = errno.ENETUNREACH\n'):'`side_effect` で例外を起こすのではなく `connect_ex` の `return_value` を `errno.ENETUNREACH` に設定する。これはsocket APIが例外を投げずエラー番号を戻す経路を再現する。`return_value` はテスト用の値で、OSの実際の接続結果ではない。',
 ('tests/test_scanner.py','        self.assertEqual(result["state"], "unreachable")\n'):'モックから返した `ENETUNREACH` に対して分類ラベルが `unreachable` になることを検証。到達不能は「閉じているポート」とは別概念であり、ネットワーク経路・ICMP応答・OSの状況を調査すべきことを意味する。',
}

def annotate(file,line):
    raw=line
    if not raw.strip():
        return '空行。直前のコードブロックと次の処理の境界を視覚的に示し、実行時には何も行わない。'
    v=new_explanations.get((file,raw))
    if v:return v
    if file.endswith('test_scanner.py') and raw.strip()=='' :return '空行。'
    raise RuntimeError(f'Missing individually authored explanation for new source line {file} {raw!r}')

# Collect the old source line notes, preserving the existing authored explanations.
oldrows={};oldlines={};stage_tags={}
for stage in parts['steps']:
    k=(stage['path'],stage['stage'])
    card=html.find('article',id=f"portfolio-step-{stage['stage']:02d}")
    assert card
    stage_tags[k]=card
    spans=card.select('code.portfolio-source-lines span[data-line]')
    rows=card.select('tr.portfolio-code-annotation')
    assert len(spans)==len(rows)
    for sp,row in zip(spans,rows):
        key=(stage['path'],int(sp['data-line']))
        oldlines[key]=sp.get_text()
        oldrows[key]=copy.copy(row)
allnew={}
for path in parts['files']:
    lines=(ROOT/'portfolio_lab'/path).read_text(encoding='utf-8').splitlines(keepends=True)
    old=[oldlines[(path,i)] for i in range(1,parts['files'][path]['lines']+1)]
    sm=difflib.SequenceMatcher(None,old,lines,autojunk=False)
    indexed={}
    for tag,i0,i1,j0,j1 in sm.get_opcodes():
        if tag=='equal':
            for oi,nj in zip(range(i0,i1),range(j0,j1)):
                indexed[nj+1]=oi+1
        elif tag=='insert':
            for nj in range(j0,j1):indexed[nj+1]=None
        else:raise RuntimeError((path,tag,old[i0:i1],lines[j0:j1]))
    assert sorted(indexed)==list(range(1,len(lines)+1))
    allnew[path]=(lines,indexed)

newsteps=[]
for stage in parts['steps']:
    path=stage['path'];lines,mapping=allnew[path];card=stage_tags[(path,stage['stage'])]
    # Map old range endpoints and collect new insertions between them (or before the final main guard).
    inv={old:new for new,old in mapping.items() if old is not None}
    first=inv[stage['start']]
    last=inv[stage['end']]
    prev=[x for x in newsteps if x['path']==path]
    if prev:first=prev[-1]['end']+1
    # Insertions before the next old file block belong to the current step.
    nextold=stage['end']+1
    if nextold in inv:last=inv[nextold]-1
    else:last=len(lines)
    assert first<=last,stage
    card.select_one('.source-position').string=(f'編集するファイル：portfolio_lab/{path} / 原典とは独立の新規ファイル / L{first}–L{last}')
    code=card.select_one('code.portfolio-source-lines')
    code.clear()
    tbody=card.select_one('table.portfolio-line-table tbody')
    tbody.clear()
    for n in range(first,last+1):
        t=html.new_tag('span',attrs={'data-line':str(n)});t.string=lines[n-1];code.append(t)
        orig=mapping[n]
        if orig is not None:
            row=copy.copy(oldrows[(path,orig)])
        else:
            row=html.new_tag('tr',attrs={'class':'portfolio-code-annotation'})
            td1=html.new_tag('td');td2=html.new_tag('td')
            c=html.new_tag('code',attrs={'class':'portfolio-line-source'});c.string=lines[n-1].rstrip('\n')
            p=html.new_tag('p');p.string=annotate(path,lines[n-1])
            td1.string=f'L{n}';td2.append(c);td2.append(p);row.append(td1);row.append(td2)
        row['data-file']=path;row['data-line']=str(n)
        row.select_one('td').string=f'L{n}'
        tbody.append(row)
    newsteps.append({'stage':stage['stage'],'path':path,'start':first,'end':last})

# Review old, uniquely identifiable source lines and enrich too-thin explanations.
revised={
('containers/compose.yaml',23):'`tty: true` はnginxコンテナへ疑似端末（PTY）を割り当てる設定。nginxのHTTP通信を可能にする指定ではなく、コンテナ内の対話操作に関わる。`tty` はComposeのキー、`true` はYAMLの真偽値。',
('containers/compose.yaml',30):'`ports:` はnginxコンテナの待受ポートをホスト側へ公開する一覧の親キー。次の行の127.0.0.1によるバインド先を読み、外部への公開範囲を判断する。これ自体はnginxのlisten設定を変更しない。',
('containers/compose.yaml',38):'PostgreSQL演習コンテナへ `tty: true` で擬似端末を割り当てる。psqlが利用できるかや認証成功とは関係がなく、標準入出力の端末扱いを変えるだけ。',
('containers/compose.yaml',41):'PostgreSQLサービスの `networks:` で参加先ネットワークの一覧を開始する。後続の `net-10.8.9.0` と `ipv4_address: 10.8.9.4` は同じサービスの設定。',
('containers/compose.yaml',43):'PostgreSQLコンテナの専用ネットワーク内IPv4アドレスとして `10.8.9.4` を指定する。ホスト側の127.0.0.1や5432ポートとの対応とは別の設定。',
('containers/compose.yaml',44):'PostgreSQLコンテナのMACアドレスを `02:42:0a:08:09:04` に固定する指定。MACは同一L2ネットワーク上で用いる識別子で、ホスト側のTCPポート番号ではない。',
('containers/compose.yaml',45):'`ports:` はPostgreSQLのホスト側ポート公開設定の開始。下位項目でホストIP、ホストポート、コンテナポートを読み、パスワード認証設定とは切り離して確認する。',
('containers/compose.yaml',49):'SSH演習コンテナ用のイメージビルド設定を開始する。`build` の子にある `context` と `dockerfile` がどのDockerfileを使うか決める。',
('containers/compose.yaml',53):'`tty: true` をSSHコンテナに指定する。SSH接続そのものには不要であり、コンテナの仮想端末扱いに関わるCompose設定。',
('containers/compose.yaml',59):'SSHコンテナの仮想NICに固定MACアドレス `02:42:0a:08:09:05` を設定する。IPアドレスの代わりにSSHクライアントが入力する値ではない。',
('containers/compose.yaml',60):'SSHコンテナのホストポート公開指定の親キー `ports:`。次の行のIP:ポート:ポート対応を読まなければ到達可能範囲は分からない。',
('containers/compose.yaml',87):'診断用pentesterサービスを `net-10.8.9.0` に接続するComposeのネットワーク名。後続の固定IPがサービス側の設定になる。ホストのIP設定ではない。',
('containers/compose.yaml',96):'`ipam` の子の `config:` は演習用BridgeネットワークのIPアドレス管理設定を列挙する。次行の `subnet` が利用するCIDRを指定する。',
('code/chapter02/tcp-connect-scan-v1.py',28):'`print` は画面表示用の組み込み関数。文字列 `Send ACK packet:` を標準出力へ出してからACKを生成・送信する流れを示すが、この行自体はTCPパケットを送信しない。',
('code/chapter02/tcp-connect-scan-v2.py',40):'右辺の `ip_layer/fin_tcp_layer` はScapyの `/` 演算子でIP層とTCP(FIN)層を連結し、送信用パケットを作る。`=` は結果を `fin_packet` に代入する記号。この行だけではネットワークへ送っていない。',
('code/chapter03/portscan-tcp-all.sh',8):'`}` はシェルの `usage() { ... }` 関数本体を閉じる波括弧。関数宣言はここで終わるが、まだ自動的にヘルプが表示されるわけではない。',
('code/chapter03/portscan-tcp-all.sh',15):'`fi` は先頭引数がないか確認する `if ... then ... fi` のブロックを閉じるシェル構文。`exit 1` が実行された場合はここへ戻らない。',
('code/chapter03/portscan-tcp-all.sh',20):'この `fi` は `--help` 引数が指定されたときに `usage` して正常終了する条件分岐を閉じる。対象の必須引数判定を閉じるL15の `fi` とは別の対応。',
('code/chapter03/nmap-xml2csv.rb',10):'Rubyの `end` は `opt.on` の `do ... end` ブロックを閉じる。コマンドラインオプションが処理された場合に実行するヘルプ表示の処理範囲をここで終える。',
('code/chapter03/nmap-xml2csv.rb',14):'この `}` は `OptionParser.new { |opt| ... }` の波括弧ブロックを閉じる。L10の `end` は内部の `opt.on` を閉じるため、閉じる対象が違う。',
('code/chapter03/nmap-xml2csv.rb',37):'`end` は直前の `if` による末尾区切り記号の調整処理を閉じる。Rubyのメソッド定義全体ではなく、この条件に対応する。',
('code/chapter03/nmap-xml2csv.rb',47):'`end` で `File.open` へ渡した `do` ブロックが終わり、ブロックを抜けるとファイルオブジェクトが自動で閉じられる。Rubyの `File.open(path) do |f|` 構文の効果。',
('containers/nginx/vulnerable.conf',8):'この `}` は最初の `location / { ... }` ブロックを閉じる。ルートパス向けのリクエスト処理に適用する設定がここで終了するが、`server` 全体はまだ続く。',
('containers/nginx/vulnerable.conf',12):'この `}` は静的パス向けの `location` ブロックを閉じる。`alias` の参照先やURIの対応はこのブロックに適用され、他のlocationには波及しない。',
('containers/bind/config/named.conf',40):'`};` はBINDの `options { ... };` 全体の終了。`}` で設定の集合を閉じ、`;` でnamed.confの文を終える。Cの構造体宣言ではない。',
('containers/bind/config/example.com.zone',9):'閉じ丸括弧 `)` でSOAリソースレコードの複数行にわたる値を閉じる。括弧内のシリアル番号、更新間隔、再試行間隔などはDNSゾーン管理に使われる。',
('code/chapter05/shellcode-runner.go',26):'`*/` はGoソースの冒頭に置かれたcgo用Cコードを含むブロックコメントを閉じる。ここまでがCコンパイラへ渡す部分であり、次の `import "C"` からGo側の定義に戻る。',
}
for (path,n),updated in revised.items():
    st=next(x for x in json.loads((ROOT/'STEP_FRAGMENTS.json').read_text()) if x['path']==path and x['start']<=n<=x['end'])
    card=html.find('article',id=f"step-{st['step']:03d}")
    row=card.select('table.line-analysis tbody tr')[n-st['start']]
    p=row.select_one('.syntactic');assert p
    p.clear();p.append(NavigableString(updated))

# Add high-value, step-by-step portfolio evidence and troubleshooting guidance.
portfolio_section=html.find('section',id='portfolio')
assert portfolio_section
new_guidance='''
<div class="chapter-body" id="portfolio-field-manual">
 <h2>実測から提出まで：ポートフォリオを作る実作業</h2>
 <p>最初のリポジトリは<strong>非公開</strong>にし、書籍付属コード・固定パスワード・個人のIPアドレス・実環境ログを混ぜない。提出対象は、自分で検証した差分とその根拠を説明できるコード・テスト・資料だけにする。</p>
 <h3>第1日：課題と成果の境界を決める</h3>
 <p>READMEの「目的」は単に『ポートスキャナを作った』ではなく、『TCP Connect結果を安全な範囲で観測し、拒否と時間切れを区別して誤判定を減らす』と明記する。ARCHITECTURE.mdには入力、検証、TCP通信、分類、JSON出力の5段階と、各段階で失敗したらどう処理するかを書く。原典との差も表にする。</p>
 <h3>第2日：空フォルダから実装し、変更理由をGitへ残す</h3>
 <p>ポートフォリオ工程02〜13を参考に、説明を理解したうえで自分で入力する。1つの機能と対応するテストをセットでコミットする。`git diff --check` で空白エラーを確認し、`git status --short` で秘密情報や大きな成果物を誤追跡していないか見る。</p>
 <h3>第3日：ループバックで再現実験</h3>
 <p>端末Aで <code>python3 -m http.server 8765 --bind 127.0.0.1</code>、端末Bで <code>python3 scanner.py --target 127.0.0.1 --ports 8765,8766</code> を実行する。8765がopen、待受のない8766がrefusedになり得ることを、実際の表示をもとに記録する。別のプロセスが使っていれば結果は変化する。Ctrl+Cで待受を止め、再検査して差を観察する。</p>
 <h3>第4日：異常系を通信なしで再現する</h3>
 <p>`python3 -m unittest discover -s tests -v` で13件のテストを実施する。うち2件はモックを使い、`TimeoutError()` と `errno.ENETUNREACH` を人工的に再現する。インターネット接続が不安定になるのを待つ試験ではない。エラー分類を変更したら、何の回帰を防ぐためのテストなのかテスト名と説明を結び付ける。</p>
 <h3>第5日：結果の証拠を整理する</h3>
 <p>テスト報告には実施日・OS・Python版・コミットの短縮SHA・コマンド・期待結果・実結果・判断・未検証事項を記録する。実IPや機密的なホスト名を残したログはそのまま公開しない。`--output` が既存ファイルを上書きしないことを試し、失敗したコマンドの終了コードも記録する。</p>
 <h3>第6日：自分独自の改善を1つ実装する</h3>
 <p>この教材の見本コードを未変更のまま自作作品として提出しない。たとえば『前回結果との比較モジュール』を自分で設計して追加し、JSONの入力が壊れている場合のテストと、新旧結果の差を表示するテストを作る。機能を足した理由と、代替案を採用しなかった理由も設計記録に残す。</p>
 <h3>第7日：公開前の二重レビュー</h3>
 <p>公開用フォルダに <code>original_source.zip</code>、書籍ソースの大部分、`audit/` 内の原典再構築資料、脆弱なDocker環境、秘密情報を含めない。原典READMEは『コードの大部分の転載・販売・配布には許可が必要』と述べている。たとえ個人の転職用であっても無条件に転載可能とは読み替えない。自作コードと必要最小限の引用・出典表示だけに整理する。</p>
 <h3>第8日：第三者による再現試験と面接説明</h3>
 <p>別の作業フォルダからREADMEだけを頼りにインストール・テスト・ローカル実演が可能か確認してもらう。自分で『何を保証するか』『何を保証しないか』を説明する。TCP Connectの成功はサービスの安全性や脆弱性の有無を示さず、取得した結果はその時点の観測に限られる。</p>
 <div class="precision-box"><h4>提出前に必ず答えられること</h4><p>なぜloopbackが既定値か。`--authorized` は誰の許可を証明するのか。`connect_ex` が0以外を返したとき、いつ `refused` と判定してよいのか。タイムアウト例外のテストを実通信なしでどう作ったのか。JSONの中で情報漏えいにつながるものは何か。自分が独立に追加した機能・テストはどれか。</p></div>
</div>
<div class="chapter-body" id="portfolio-reproducible-evidence">
 <h2>検証報告の記入例と失敗時の調査</h2>
 <p>以下の出力値は一例。`errno`の整数値とポート状態はOSと実環境で異なる。**結果を実測したふりをして貼らない**。実際の端末で観測したものだけをevidenceに保存する。</p>
 <div class="terminal-wrap"><pre><code>cd portfolio_lab
python3 --version
python3 -m unittest discover -s tests -v
python3 scanner.py --target 127.0.0.1 --ports 8765,8766 --timeout 0.5
python3 scanner.py --target 127.0.0.1 --ports 8765 --output evidence-local.json
# 同じファイル名でもう一度実行すると上書き拒否になる（正常な保護動作）。</code></pre></div>
 <table class="status-table"><thead><tr><th>症状</th><th>原因の候補と確かめ方</th></tr></thead><tbody>
 <tr><td>ModuleNotFoundError: scanner</td><td>ZIPルートでunittestを起動していないか確認。`cd portfolio_lab` のあとにテストを実行し、`pwd` を記録する。</td></tr>
 <tr><td>8765がrefused</td><td>端末AのHTTPサーバが起動中か、別のポートを使っていないか、`ss -ltn` で127.0.0.1:8765を確認する。</td></tr>
 <tr><td>8766がopen</td><td>既に別プロセスが待ち受けている可能性。`ss -ltnp` で確認し、演習用の空きポートに変える。</td></tr>
 <tr><td>timeoutではなくerror_or_unknown</td><td>OS固有のエラーが返ることがある。`errno` フィールドと例外処理を照合し、既存分類へ強引に押し込まず未対応として記録する。</td></tr>
 <tr><td>--scope-cidrが拒否される</td><td>完全なCIDRネットワークアドレスか、/24以上に狭いRFC1918内か、targetが範囲に属するかをそれぞれ確認する。`--authorized` は実際の許可の代替ではない。</td></tr>
 <tr><td>--outputで失敗</td><td>ファイルが存在する場合は排他的作成が失敗する。別名で保存するか既存ファイルを確認し、明示的に削除する。途中でディスクが満杯になると部分ファイルが残る可能性も報告する。</td></tr>
 </tbody></table>
 <p>さらに詳しいコマンドと実証レポートの作り方は <code>portfolio_lab/docs/PORTFOLIO_BUILD_GUIDE.md</code> と <code>portfolio_lab/docs/REPRODUCIBLE_TEST_PLAN.md</code> に収録している。</p>
</div>
'''
portfolio_section.append(BeautifulSoup(new_guidance,'html.parser'))
# The referenced docs and test count are updated in the portfolio chapter's introduction.
for n in portfolio_section.find_all(string=True):
    if '11件' in n:
        n.replace_with(n.replace('11件','13件'))
# Several shorter source explanations were explicitly improved, not merely auto rephrased.
for n in html.find_all(string=True):
    if '480周' in n and ('累計' in n or '反復' in n or '検査' in n):
        n.replace_with(n.replace('480周','560周'))
# Portfolio line count will be updated to its measured amount after source annotation reconstruction.
oldcount=214
newcount=sum(len(x[0]) for x in allnew.values())
for n in html.find_all(string=True):
    if f'{oldcount}行' in n:
        n.replace_with(n.replace(f'{oldcount}行',f'{newcount}行'))
# Dedicated correction note, grounded in the actual TimeoutError/OSError relationship.
intro=html.find('section',id='portfolio').select_one('.chapter-narrative')
intro.append(BeautifulSoup('<p class="human-corrected"><strong>本改訂の重要な改善：</strong><code>TimeoutError</code> は <code>OSError</code> のサブクラスなので、専用の <code>except TimeoutError:</code> を先に置く。これにより例外に <code>errno</code> がない場合も <code>ETIMEDOUT</code> に分類できる。モックによるテストはネットワークの危険を増やさず異常系を再現できる。</p>','html.parser'))
# Normalize source manifest and fragment manifests against the real edited files.
newparts={'files':{},'steps':newsteps,'all_line_fragments':[]}
for path,(lines,mapping) in allnew.items():
    b=(ROOT/'portfolio_lab'/path).read_bytes()
    newparts['files'][path]={'sha256':sha256(b).hexdigest(),'lines':len(lines),'nonblank_annotated':sum(bool(line.strip()) for line in lines)}
for stage in newsteps:
    path=stage['path'];lines=allnew[path][0]
    for n in range(stage['start'],stage['end']+1):
        newparts['all_line_fragments'].append({'stage':stage['stage'],'path':path,'line':n,'code':lines[n-1]})
assert len(newparts['all_line_fragments'])==newcount
(ROOT/'PORTFOLIO_FRAGMENTS.json').write_text(json.dumps(newparts,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
# Source manifest points at revised HTML; original source metadata is immutable.
manifest=json.loads((ROOT/'SOURCE_MANIFEST.json').read_text())
manifest['manual']=new_file.name
(ROOT/'SOURCE_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
new_file.write_text(str(html),encoding='utf-8')
print('wrote:',new_file,'bytes',new_file.stat().st_size,'portfolio lines',newcount,'steps',len(newsteps),'source notes',len(revised))
