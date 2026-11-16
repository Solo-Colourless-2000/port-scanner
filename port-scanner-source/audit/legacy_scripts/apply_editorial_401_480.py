#!/usr/bin/env python3
"""Apply independently written source-aware corrections to the attached manual.
The original source code spans are never edited.
"""
from pathlib import Path
import json
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
old=ROOT/'portscanner_pentest_SNAKE_style_400round_refined_manual_20261116.html'
new=ROOT/'portscanner_pentest_SNAKE_style_480round_refined_manual_20261116.html'
steps=json.loads((ROOT/'STEP_FRAGMENTS.json').read_text())
soup=BeautifulSoup(old.read_text(encoding='utf-8'),'lxml')
A='code/chapter02/tcp-connect-scan-by-socket.py'
B='code/chapter02/tcp-connect-scan-v1.py'
C='code/chapter02/tcp-connect-scan-v2.py'
D='code/chapter02/tcp-syn-scan.py'
E='code/chapter03/nmap-xml2csv.rb'
F='code/chapter03/portscan-tcp-all.sh'
G='containers/postgres/Dockerfile'
H='code/chapter05/shellcode-runner.go'
I='code/chapter06/libsniffer.c'
J='containers/log4j/src/main/java/fr/christophetd/log4shell/vulnerableapp/MainController.java'
K='containers/pentester/code/chapter02/sniff-icmp-by-arp-spoofing.py'
L='containers/pentester/Dockerfile'
# Every update is tied to a specific code line and its actual execution context.
updates={
 (A,7):'`sys.argv` の先頭要素 `[0]` は起動したスクリプト名であり、`[1]` から利用者の引数となる。ここでは第1引数を検査対象の文字列にするが、IPv4かどうか・許可済み対象かどうかは確かめていない。引数がない場合は `IndexError`。完成後の改善版では入力とスコープを先に検証する。',
 (A,8):'`int(sys.argv[2])` は第2引数を10進整数と解釈しようとする。入力が `abc` なら `ValueError`、2引数目がなければ `IndexError`、負数や65536でもこの行だけでは防げない。ポートの許容範囲を確認する処理は追加されていない。',
 (A,14):'`if errno == 0:` は `connect_ex` が0を返した場合だけ「TCP接続に成功した」と判断する条件。ここで `errno` は標準ライブラリのモジュール名ではなく、L11で定義されたローカル整数変数。`==` は値の比較であり、`=` の代入とは別。',
 (B,17):'`sr1(syn_packet)` は送信と、1個の応答の受信を一緒に試みるScapyの関数。返り値が `None` なら応答を得られなかった状態であり、TCPの閉鎖を意味しない。原典は `timeout` を指定せず、L22でNoneを検査せずに `haslayer` するため停止待ちや例外を招く。',
 (B,29):'`sr1(ack_packet, timeout=3)` はACKを送った後、最初の応答パケットを最大約3秒待つ。通常のTCPハンドシェイクの3番目のACK自体に即時の返答は必須ではない。ここでNoneになってもACKが送れなかった証拠にはならないうえ、Scapyが構成したパケットの送信とOSのTCP接続状態は同じではない。',
 (B,36):'`print(...)` は `SYN+ACK` が見つからなかった分岐を一律 `closed` と表示する。しかしTCPのRSTを確認したことを意味しない。ICMPや想定外のTCPフラグもあり得て、無応答のNoneならL22の `haslayer` が先に例外になる。改善版では `refused`、`timeout`、`unreachable` 等を分けて表示する。',
 (C,38):'`ack=response_packet.seq + 1` は最初に受信したSYN+ACKのシーケンス番号から算出したACK値をFINパケットに再利用する。相手からデータを追加受信した場合にはACK番号を更新する必要がある。原典は受信バイト数と再送などの状態を追っていない。',
 (C,45):'`response_fin_packet.haslayer(TCP)` に渡す応答が `None` なら `AttributeError` の可能性がある。FINへの最初の返答がACKのみである場合もあり、単独の応答パケットからTCPセッション全体の終了可否を結論できない。原典に `is not None` の判定も状態遷移の管理もない。',
 (C,54):'`sr1(ack_packet_after_fin, timeout=3)` は最後のACKを送った後、追加応答を待つが戻り値は保存しない。通常はそのACKに対するさらなるACKを要求しないため、Noneは当然あり得る。これを「切断完了の実証」とするのは誤りで、接続の終了は双方向FIN/ACKやタイムアウトなど状態全体で扱う。',
 (D,17):'`if (` の開き括弧で条件式を複数行へ分割し、まず `response_packet.haslayer(TCP)` を調べる。`and` は左が偽なら右を評価しないが、`response_packet` 自体がNoneである場合の属性参照は防げない。コロンはこの行にはなく、次行にある。',
 (E,4):'`ARGV[0]` はRubyスクリプト起動時の第1引数を読み出す。L15の `opt.parse(ARGV)` より前に評価するため、先頭に `-o` を置いた場合はXMLファイル名を `-o` と誤認する恐れがある。使い方の説明ではXML入力を先頭に置くか、作者が入力解析を改良する必要がある。',
 (E,29):'`result += host.ip + "\\t"` は `host.ip` の文字列の後へタブ文字を付けて結果文字列へ追加する。これはホストの最初のopenポートが見つかった時だけ実行される。ファイル名は `.csv` でも、列1がIP、列2が `80(http), 443(https)` のような人間向け表示なので、RFCに沿うCSVレコードとは言い切れない。',
 (E,35):'`result.end_with?(\'), \', \')\')` はRubyの `end_with?` に2つの候補末尾を渡し、どちらかと一致すれば真になる。実際に追加する区切りはポートごとの `), ` であり、単独の `)` の場合でもL36が末尾2文字を切り落とすため、前段の結果生成が変わると有効な文字が失われ得る。',
 (E,36):'`result.slice(0...-2)` は先頭位置0から末尾の2文字を除く手前までを抽出する。`...` はRubyの終点除外範囲、`-2` は末尾から2文字手前の位置。この処理はL32で追加した `, ` を削る用途だが、L35の判定には `)` だけのケースも含むため、汎用的な区切り文字処理ではない。',
 (E,45):'`File.open(output_file, \'w\') do |f|` は結果ファイルを開き、ブロック内でファイルオブジェクトを `f` という名前で利用する。`w` は既存ファイルを切り詰めて上書きし、`do |f|` の縦棒はシェルのパイプではなくRubyのブロック引数区切り。原典には上書き確認がない。',
 (F,11):'`"$#"` は位置引数の個数を表し、`-eq 0` は整数としてゼロと比較する。原典が排除するのは「引数0個」だけなので、引数1個の場合は後の `$2` が `set -u` により未定義変数エラーを起こし得る。ポートフォリオでは必要数と許容形式の両方を検証する。',
 (F,33):'バッククォートによる `cat $2` の出力を `hosts` に代入する。`$2` は引用符で囲われずシェルの単語分割やパス名展開の影響を受け得る。またファイル内の改行は後で `for h in $hosts` の単語分割へ渡るため、複数値を厳密な1行1アドレスとして扱っていない。',
 (F,47):'`echo $h | tr "/" "_"` はCIDRのスラッシュだけをアンダースコアへ置換してファイル名部分に使う。`|` は標準出力から標準入力へつなぐパイプで、ORでもScapyのレイヤー結合でもない。スラッシュ以外の特殊文字や空白の検証はしないので、入力を信頼してはいけない。',
 (F,52):'この `echo` は「今から実行する想定コマンド」を表示するだけで、実際にスキャンするのはL57の `sudo nmap`。表示文にはL57にある `${timing_template}` が含まれていないため、利用者がL52の表示だけを見ても実際のタイミング指定を完全に再現できない。ログには引数の全体を保存するべき。',
 (G,8):'`RUN` はイメージビルド時のシェル命令。`echo ... >> /etc/postgresql/pg_hba.conf` はそのパスに追記しようとするが、原典の公式 `postgres:15.1` イメージでは通常、稼働する `pg_hba.conf` は初期化済みデータディレクトリ（`PGDATA`）に作られる。`/etc/postgresql/` が存在しなければビルド自体が失敗し、存在しても稼働側設定に反映される保証はない。',
 (H,12):'Cの `fork()` は成功時に親へ正の子PID、子へ0、失敗時に-1を返す。`if(fork())` は子の0だけを偽として継続させ、親と失敗時の-1では `return` する。親が子終了を `wait` しないためプロセス回収が不十分になり得る。子プロセスであることはシェルコードの安全な隔離を意味しない。',
 (H,18):'`MAP_ANONYMOUS | MAP_PRIVATE` はファイルに紐付けない非共有メモリの割り当てを指定するフラグ集合。`-1` は匿名マッピングのファイルディスクリプタ、`0` はオフセット。実行権限 `PROT_EXEC` はL17で指定され、このL18自体が「安全な」メモリを作っているわけではない。',
 (H,44):'`C.call((*C.char)(unsafe.Pointer(&shellCodeBin[0])),` はGoスライスの先頭アドレスをCの `char *` に変換して渡す。`&` はアドレス取得、`[0]` は最初の要素、`unsafe.Pointer` は型安全性を外す変換。空スライスで`[0]`参照がpanicし、入力バイトが有効なコードかどうかの確認もないので実行しない。',
 (I,5):'`int SSL_write(SSL *ssl, const void *buf, int num)` はOpenSSLの同名関数と一致させた関数シグネチャ。`SSL *` は接続オブジェクト、`const void *` は長さが別管理の任意バイト列、`int num` は要求送信サイズを表す。元のAPIをフックして通信内容を記録する意図だが、バッファがNUL終端文字列であるという保証は存在しない。',
 (I,9):'`fprintf(logfile, "%s\\n", (char *)buf)` は `buf` をC文字列と仮定してログへ書こうとする。`%s` はNULが見つかるまで読んでしまい、APIの `num` バイト数を無視する。範囲外読取りや秘密情報の記録につながり得るうえ、`logfile` がNULLの場合も検査されていない。安全なバイト列処理と最小限のログ保護の双方が必要。',
 (I,10):'`fclose(logfile)` はFILEストリームのバッファを処理してクローズする。しかし前行の `fopen` は失敗するとNULLを返すため、この行に無条件で到達する設計は未定義動作につながり得る。フックの対象が通信処理なので、ログの失敗が元の通信へ影響する点も問題。',
 (J,17):'`public String index(@RequestHeader("X-Api-Version") String apiVersion)` はJavaのpublicメソッド。SpringはHTTP要求のヘッダー `X-Api-Version` を `String` 引数へ束縛する。ヘッダーの指定がない場合は（原典でrequired=falseにしていないため）通常400応答になり得る。「GET /を呼べば必ず200」とは限らない。',
 (J,18):'`logger.info("Received ..." + apiVersion)` は、固定文字列とHTTPヘッダー由来の `apiVersion` を連結し、Log4jへ渡す。文字列の `+` は連結、`logger.info` はINFOレベルのログ出力。演習アプリの危険性は入力がログ処理に入る経路にあり、HTTP応答本文のreturnとは独立している。脆弱な依存関係を外部公開しない。',
 (K,58):'`enable_ip_forward()` の実行によりLinuxカーネルのIPv4転送設定が変更される。原典では変更前の値を保存しておらず、Ctrl+C時にも元に戻していない。さらに例外を拾うtry節の外で実行されるため、この操作自体が失敗しても「復元処理」に進まない。実行試験はしない。',
 (K,61):'`sniff_process.start()` はL60で生成した子プロセスを実際に起動する。後続には `terminate()` / `join()` がないので親の終了後に残る可能性があり、受信終了も待たない。ネットワーク復元とは別に子プロセスの寿命を管理する必要がある。',
 (K,71):'`restore(destination, target)` はARPマッピングを逆方向にも元へ戻そうと試みるが、成功判定・再確認をしていない。加えてIP転送設定を元へ戻す行や、起動したsniff子プロセスを停止・回収する行がない。Ctrl+Cでメッセージが出たことを完全復旧と取り違えない。',
 (L,23):'`./msfinstall` は前の行でダウンロードされた外部インストーラを実行する。`RUN` 中の実行はコンテナイメージのビルド時に起こるため、利用者がDocker Composeを起動した瞬間に外部スクリプトが動く可能性がある。原典にはチェックサム検証がないので、検証できない環境ではビルドしない。',
}
logs=[]
for (path,n),after in updates.items():
    st=next(x for x in steps if x['path']==path and x['start']<=n<=x['end'])
    article=soup.find('article',id=f"step-{st['step']:03d}")
    assert article
    tr=article.select('table.line-analysis tbody tr')[n-st['start']]
    block=tr.select_one('.syntactic');assert block
    before=block.get_text(' ',strip=True)
    assert after!=before, (path,n)
    block.clear();block.append(after)
    logs.append({'path':path,'line':n,'source':article.select('code.source-lines span[data-line]')[n-st['start']].get_text().strip(), 'previous':before,'revised':after})
# Reinforce source attribution in the introduction by referencing the actual origin.
intro=soup.find('section',id='prepare')
note=soup.new_tag('div',attrs={'class':'precision-box','id':'source-license-guidance'})
h=soup.new_tag('h4');h.string='原典の利用条件とポートフォリオ公開範囲';note.append(h)
p=soup.new_tag('p');p.string='原典リポジトリのREADME「サンプルコード」には、コードの一部を自分のプログラムに使う場合の条件、大部分の転載やコード例の配布時の扱い、出典表示の例が記されています。READMEそのものを読まずに「すべて自由なライセンス」と決めつけないでください。今回のポートフォリオ見本は原典を再配布した作品ではなく、学習テーマを踏まえた別実装として扱います。';note.append(p)
intro.append(note)
# Change version markers without claiming full human review cycles.
soup.title.string='ポートスキャナ自作・ペネトレーションテスト開発マニュアル｜累計480周の自動反復監査・ポートフォリオ制作章'
for t in soup.select('h1'):
 if '400周' in t.get_text():t.string=t.get_text().replace('400周','480周')
new.write_text(str(soup),encoding='utf-8')
(ROOT/'EDITORIAL_PATCHES_401_480.json').write_text(json.dumps({'source':'user-uploaded previous 400-round ZIP; original_source.zip in same bundle', 'nature':'manual code reading, independent from automated repetitive checks','source_line_rewrites':logs,'count':len(logs)},ensure_ascii=False,indent=2),encoding='utf-8')
print('changed',len(logs),'source explanations; provisional output',new)
