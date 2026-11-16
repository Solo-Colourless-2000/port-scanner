"""Create v960 solely from the v880 ZIP's HTML/source/fragment records.
The original repository is not edited. New source lines are explained in Japanese.
"""
from pathlib import Path
from lxml import html as H, etree as E
from hashlib import sha256
from difflib import SequenceMatcher
from collections import defaultdict
import json, re
R=Path(__file__).parent
old=R/'audit/BASELINE_880_MANUAL.html'
new=R/'portscanner_pentest_development_manual_v960_20261117.html'
dom=H.fromstring(old.read_bytes())
frpath=R/'REPORT_DIFF_FRAGMENTS.json'
fr=json.loads(frpath.read_text())
old_annotations={(x['path'],x['line']):x['explanation'] for x in fr['annotations']}
old_files=defaultdict(dict)
for step in fr['steps']:
    art=dom.xpath(f'//article[@id="diff-step-{step["stage"]:02d}"]')[0]
    for line in art.xpath('.//code[contains(@class,"diff-source-lines")]/span[@data-line]'):
        old_files[step['path']][int(line.get('data-line'))]=''.join(line.itertext())
old_files={p:[d[n] for n in sorted(d)] for p,d in old_files.items()}

# Rewritten or newly authored explanations: indexed by the exact NEW line number.
core={
37:'トップレベルで受理する五つのフィールド名を集合リテラル{...}で定義する。順序は意味を持たない。timestamp_utcはUTCの観測日時、targetはIPv4、scopeは許可範囲、timeout_secondsは接続待ち時間、resultsはポート結果の配列。',
38:'set(report)は辞書reportのキーを集合へ変換する。!= は集合が一致しない場合にTrue。必須キーが足りないときも余分なキーがあるときもif内部で拒否する。ここで値そのものの妥当性を検査したわけではない。',
39:'required_report_fields - report.keys() は必要なキー集合から現在あるキーを引く集合差。欠落したキーだけが残る。sorted()で文字列名を一定の順に並べ、エラー出力が再現しやすいリストにする。',
40:'report.keys() - required_report_fields は実際の辞書から許可キー集合を引く集合差で、余分な項目を検出する。sorted() は出力順のばらつきを防ぎ、欠落との違いを利用者に示す。',
41:'raiseは処理を中断してValueErrorを発生させる。f文字列の{path}に入力ファイル、{missing}と{unexpected}に欠落・余分なキー名を埋め込む。正規のフィールド集合が一致しない限り後続の比較を実行しない。',
88:'結果行の各辞書に許すキーを集合{port,state,errno}で定義。portはポート番号、stateは観測した接続状態、errnoはOS由来の整数エラーコード。top-levelの五項目とは別のスキーマである。',
89:'set(row)はこのポート結果辞書が持つキーの集合。!=で必要な三つのキー集合との完全一致を要求するため、欠落と隠れた追加フィールドの両方を検出する。',
90:'required_row_fields - row.keys() という集合差で結果行から欠落したキーを求める。sortedは名前をソートし、メッセージを読みやすくする。',
91:'row.keys() - required_row_fields で不明な追加キーを取り出す。例えば結果行にunexpected:trueが追加されている場合、その名前を報告できる。',
92:'結果行のschema不一致をValueErrorとして中断する。f文字列の{path}は読み込んだファイル、{missing}は欠落、{unexpected}は余分なキーを表す。ここで止まれば状態比較へ不正データが到達しない。',
141:'parser.add_argumentはCLIオプションを登録する。"--before" は前回の観測JSONのパス。type=Pathで文字列をPathオブジェクトへ変換し、helpは--helpに表示される。requiredを外し、単一ファイル検証モードと両立させた。',
142:'"--after" は後の観測JSONを指定する引数。type=Pathはファイルの存在やJSONの正しさまで検査する機能ではなく、後段のread_reportが内容を検証する。helpは利用者向け説明。',
143:'"--validate" は保存済みJSONを一件だけ検査する新しいモード。parser.add_argumentで登録し、type=PathによりPathとして受け取る。比較処理を実行せず、オフライン検証に使う。',
144:'"--output" は比較結果の新規保存先。type=Pathはパス型へ変換し、helpで--helpに説明を出す。単独検証時には出力ファイルを作らないため、--validateとの併用を後で拒否する。',
147:'args.validate is not Noneで単独検証オプションが指定されたかを調べる。is notはNoneオブジェクトとの同一性比較。指定されていなければ従来の2ファイル比較の処理へ進む。',
148:'orで3条件を結び、--before、--after、--outputのいずれかが指定されたなら単独検証の引数組合せとして禁止する。is not Noneで空文字やFalseではなく指定有無を判定する。',
149:'raise ValueErrorは矛盾するオプションの組合せを拒否する。エラーメッセージで--validateと併用できない三つの引数を明示する。下のexceptがparser.errorへ変換するので終了コード2となる。',
150:'read_report(args.validate)に指定パスを渡し、JSON構文とスキーマ・値を検証済みの辞書として受け取る。ここでネットワークへの接続は発生しない。検査が失敗すれば例外となり次のVALID表示に進まない。',
151:'printのf文字列でVALID、入力ファイル、target、portsの件数を出す。validated["target"]はIPv4文字列、len(validated["results"])は結果行数。これは形式上の妥当性を意味し、観測の真正性を保証しない。',
152:'return 0はmain()を成功として終了する。検証モードで比較の処理に進まないための早期return。ファイルを新規作成しないこともこのモードの特徴。',
153:'args.before is None または args.after is Noneなら、2ファイル比較に必要な入力が揃っていない。orはどちらか一方の欠落でもTrue。--validate未指定時の必須条件をここで検査する。',
154:'raise ValueErrorで2つの入力パスの欠落を利用者へ知らせる。従来のrequired=Trueを外したため、条件分岐で必要な引数の組を検査する方式になった。',
}
# Blank and test method explanations are deliberately contextual: tests do not generate traffic.
tests={
51:'test_で始まるunittestメソッドを定義し、JSON最上位の5フィールドについて未知キーと欠落キーを拒否することを検査する。selfはテストインスタンス。',
52:'forでunknownとmissingの2ケースを繰り返す。丸括弧のタプルに記した文字列が順にmodeへ代入される。',
53:'withでsubTestとTemporaryDirectoryを同時に管理する。subTestは失敗時にmodeを表示し、folderは他ケースと隔離された自動削除対象の一時ディレクトリ。',
54:'example()から正しい見本レポートのPython辞書を作る。個別ケースで変更する前の基準データ。',
55:'if mode == "unknown"で未知のフィールドを追加する分岐を選ぶ。==は文字列の値比較、末尾コロンはインデントされたブロックの開始。',
56:'report["injected_field"]へ値を代入し、仕様にないトップレベルのキーを意図的に混入させる。比較コードではこのキーを使わないがスキーマ検査は拒否する。',
57:'elseはunknownでないmissingケースを処理する分岐。直前のif条件と対になっている。',
58:'delで辞書から必須キーtimeout_secondsを削除し、欠落ケースを作る。timeout値の範囲外ではなく、キーそのものがないケースを試す。',
59:'assertRaisesRegexはValueErrorが送出され、エラー文字列にreport fields mismatchを含むことを要求する。予期した理由で拒否できるかを調べる。',
60:'write_reportで一時JSONへ保存しread_reportで読み込む。未知キー・欠落キーの両方が後段へ到達せず拒否されることを確認する。',
62:'結果配列results内の一件ずつに必要な3項目が揃うかを検査するunittestメソッドを定義。トップレベルの検査とは別に行う。',
63:'forに2ケースunknownとmissingを指定し、結果行に余分なキーを追加するケースと必須キーを削除するケースを走らせる。',
64:'subTest(mode=mode)はどちらの異常入力で失敗したかを表示する。TemporaryDirectory()は実ファイルを汚さないための一時領域。',
65:'example()で正常レポートを作る。配列resultsに既に2件のポート状態が設定されている。',
66:'if mode == "unknown"は、結果行へ未知キーを追加する分岐。末尾コロンで処理ブロックを開始する。',
67:'report["results"][0]で最初のポート結果辞書を参照し、キーunexpectedに真偽値Trueを追加する。結果行のスキーマ違反を作る。',
68:'elseはmissingケースに切り替える。unknown以外のケースはここで必須キー削除へ進む。',
69:'del report["results"][0]["errno"]で最初の結果行からerrnoキーを削除し、必須情報の欠落を再現する。',
70:'ValueErrorとresult fields mismatchというメッセージの両方を要求する。形式違反の場所が報告されるか確認する。',
71:'一時ファイルとして保存した不正な結果行をread_reportへ渡す。呼出しで例外が送出されれば意図した拒否テストが成立する。',
243:'test_validate_cli_accepts_one_valid_reportは、新設した--validate引数による正常な単一ファイル検証の終了コード・出力・ファイル作成有無を調べるメソッド。',
244:'TemporaryDirectory()をwithで開き、外部のファイルを変更しない一時フォルダを用意する。抜けると自動削除される。',
245:'Path(folder) / "before.json"は、一時フォルダ内のJSON保存先を示す。Pathに対する/はパス結合演算子で数値除算ではない。',
246:'json.dumps(example())は正常辞書をJSON文字列に変換し、write_textがUTF-8で一時ファイルへ保存する。',
247:'subprocess.run(...)の呼出しを開始する。別Pythonプロセスとして実際のCLIを試すので、関数を直接呼ぶテストとは異なる。',
248:'sys.executableはテスト実行中のPythonのパス。report_diff.pyの--validateにpathを文字列化して渡し、シェルを介さずリスト引数として起動する。',
249:'capture_output=Trueは標準出力・標準エラーを取得し、text=Trueで文字列として取り出す。',
250:'subprocess.runの閉じ括弧。ここで外部コマンドが終了するまで待ち、結果をresultへ格納する。',
251:'assertEqualでプロセスのreturncodeが成功値0か検証。失敗した場合にresult.stderrも表示して調査できる。',
252:'assertInで標準出力result.stdoutにVALID:が含まれるかを調べる。通過した形式検査の表示を検証する。',
253:'assertInでports=2という結果数が標準出力に表示されることを確認する。ポートの開閉状態を検証しているわけではない。',
254:'Path(folder).iterdir()で一時フォルダ内の項目を列挙し、sortedで名前を並べる。before.json以外に出力ファイルが新規生成されていないことを要求する。',
256:'未知キーを含むファイルを--validateが不正と報告するかを検証するunittestメソッドを定義する。',
257:'一時フォルダを生成し、改変した入力レポートを他のテストやユーザーファイルから隔離する。',
258:'tampered.jsonという一時入力ファイルのパスをPathと/で作る。tamperedはテスト用の偽データを示す名前。',
259:'example()が作る正常な辞書をmodifiedに保持し、次行で意図的に書き換える。',
260:'results配列の最初の辞書にadditionalという余分なキーを追加する。実際に署名やハッシュを検証しているわけではなく、JSON構造上の改変ケースである。',
261:'json.dumpsで改変済み辞書を文字列化し、UTF-8で入力ファイルを作る。',
262:'別プロセスのreport_diff.pyを実際に起動するsubprocess.runの開始行。',
263:'sys.executableで現在のPythonを指定し、report_diff.py --validateとtampered.jsonのパスを引数リストで渡す。',
264:'capture_output=Trueで端末に表示する文面を回収し、text=Trueで文字列として読む。',
265:'subprocess.run呼出しを閉じて、その実行結果をresultへ確定する。',
266:'assertEqualで不正入力時にCLIが終了コード2を返すことを確認する。0の成功ではテスト失敗となる。',
267:'assertInで標準エラーにresult fields mismatchが表示されることを検証する。入力検証の具体的な拒否理由を確認する。',
268:'assertNotInは標準出力にVALID:がないことを要求し、エラーを成功と誤表示する問題を防ぐ。',
270:'互いに矛盾するCLI引数の組合せを拒否するかを調べるunittestメソッド。ユーザー操作の異常系を検証する。',
271:'TemporaryDirectoryで作成した専用フォルダを使い、作業ディレクトリの既存ファイルを消さない。',
272:'before.jsonという正常入力の保存先パスを一時フォルダ内に作る。',
273:'exampleの正常データをjson.dumpsでJSON化し、一時入力ファイルへUTF-8で保存する。',
274:'commandsというタプルの開始行。次の三つの引数リストをsubTestで順に試す。',
275:'--validateと--beforeを同時に指定した禁止ケース。どちらも同じpathを使い、比較モードとの混在を検査する。',
276:'--validateと--outputを同時指定する禁止ケース。出力先パスも一時領域に限定して実データを保護する。',
277:'--beforeだけで--afterがない禁止ケース。比較には二つの入力が必要であることを検証する。',
278:'タプルcommandsの閉じ括弧。三種類の異常引数を一つの繰返しテストへ渡す。',
279:'for options in commandsで三つの引数リストを順番にテストし、組合せごとにCLIを起動する。',
280:'subTest(options=options)は失敗した引数組をテスト結果に表示するための文脈マネージャー。',
281:'subprocess.run(...)の開始。ユーザーが実行するCLI引数を別プロセスでテストする。',
282:'[sys.executable, "report_diff.py", *options]の*はoptionsリストの要素を展開し、実際のコマンドライン引数へ並べる。',
283:'capture_output=Trueでエラー表示を回収し、text=Trueで文字列へデコードする。',
284:'subprocess.run呼出しの閉じ括弧。resultに終了コード等が格納される。',
285:'assertEqualで、どの不正引数も終了コード2になったかを確認する。エラー処理の回帰検査である。',
286:'フォルダ内がbefore.jsonだけであることを確認し、不正な引数によって余分な出力を作っていないことを証明するテスト。',
}

def note_for(path,n,line,oldn,old_lines):
    if not line.strip():return '空行。直前の入力検証またはテスト処理と次の処理単位を区切る。Pythonではこの空行だけで条件や関数のスコープは変わらない。'
    mapping=core if path=='report_diff.py' else tests
    if n in mapping:return mapping[n]
    raise AssertionError(f'No human written explanation for changed line {path}:{n}: {line.rstrip()}')

new_annotations=[];changed=[]
for path,old_lines in old_files.items():
    new_lines=(R/'portfolio_lab'/path).read_text().splitlines(keepends=True)
    matcher=SequenceMatcher(None,old_lines,new_lines,autojunk=False)
    old_by_new={}
    for tag,i1,i2,j1,j2 in matcher.get_opcodes():
        if tag=='equal':
            for a,b in zip(range(i1,i2),range(j1,j2)):
                old_by_new[b+1]=a+1
    stages=[s for s in fr['steps'] if s['path']==path]
    starts=[]
    for stage in stages:
        matches=[n for n,o in old_by_new.items() if o==stage['start']]
        assert matches,(path,stage['start'])
        starts.append(min(matches))
    assert starts==sorted(starts)
    for j,stage in enumerate(stages):
        stage['start']=starts[j]
        stage['end']=(starts[j+1]-1 if j+1<len(stages) else len(new_lines))
        article=dom.xpath(f'//article[@id="diff-step-{stage["stage"]:02d}"]')[0]
        codes=article.xpath('.//code[contains(@class,"diff-source-lines")]')[0]
        tbody=article.xpath('.//tr[contains(@class,"diff-code-annotation")]')[0].getparent()
        for child in list(codes):codes.remove(child)
        codes.text=None
        for child in list(tbody):tbody.remove(child)
        for n in range(stage['start'],stage['end']+1):
            line=new_lines[n-1]
            span=E.SubElement(codes,'span',{'data-line':str(n),'data-file':path});span.text=line
            tr=E.SubElement(tbody,'tr',{'class':'diff-code-annotation','data-file':path,'data-line':str(n)})
            td=E.SubElement(tr,'td');td.text='L'+str(n)
            details=E.SubElement(tr,'td');cd=E.SubElement(details,'code',{'class':'one-line diff-line-source'});cd.text=line.rstrip('\n')
            oldn=old_by_new.get(n)
            if oldn is not None and line==old_lines[oldn-1]:
                exp=old_annotations[(path,oldn)]
            else:
                exp=note_for(path,n,line,oldn,old_lines)
                if line.strip():changed.append({'file':path,'line':n,'source':line.rstrip(),'explanation':exp})
            assert len(exp)>25 or oldn is not None,(path,n)
            p=E.SubElement(details,'p',{'class':'syntactic'});p.text=exp
            new_annotations.append({'path':path,'line':n,'code':line,'explanation':exp})
        travel=article.xpath('./div[contains(@class,"file-travel")]')
        if travel:
            for el in travel[0].iter():
                if el.text:el.text=re.sub(r'L\d+〜L\d+',f'L{stage["start"]}〜L{stage["end"]}',el.text)
                if el.tail:el.tail=re.sub(r'L\d+〜L\d+',f'L{stage["start"]}〜L{stage["end"]}',el.tail)
    fr['files'][path]={'lines':len(new_lines),'sha256':sha256(''.join(new_lines).encode()).hexdigest()}
fr['annotations']=sorted(new_annotations,key=lambda x:(x['path'],x['line']))

# Enhanced source-centered explanation of security meaning, not mere source identity.
head=dom.xpath('//head/title')
if head:head[0].text='ポートスキャナ開発とペネトレーションテスト入門｜第960周改訂版'
home=dom.xpath('//section[@id="home"]')[0]
home.insert(0,H.fragment_fromstring('''<aside class="source-architecture-note" id="v960-summary"><h3>第960周改訂：JSONの閉じたスキーマと単独検証CLI</h3><p>原典の43ファイル・946行・107工程は変更せず、転職用の独立したレポート比較プログラムを改良しました。保存済みJSONの最上位5項目と結果行3項目を正確に検査し、余分なキーや欠落したキーを拒否します。新設の <code>--validate</code> は1件の報告書をオフライン検証します。</p><p>実際の通信とファイル形式の検証、証拠の真正性は別の問題です。検証が <code>VALID</code> でも観測結果が本物であるとは限りません。自分で作った改善点、失敗したテストと修正、実測した結果をGit履歴・テスト報告に結び付ける学習課題を追加しました。</p></aside>'''))

usage=dom.xpath('//section[@id="usage"]')[0]
usage.insert(1,H.fragment_fromstring('''<div class="chapter-narrative" id="v960-workflow"><h2>完成物の使い方：取得→単独検証→比較→証拠化</h2><p>「スキャンできた」と「レポートの形式が正しい」は別の状態です。 <code>portfolio_lab/</code> に移動して <code>python3 scanner.py --help</code>、<code>python3 report_diff.py --help</code> の順に引数を確認します。ローカルHTTP待受の開始後に <code>python3 scanner.py --target 127.0.0.1 --ports 8765,8766 --timeout 0.5 --output before.json</code> を実行します。</p><p>次に <code>python3 report_diff.py --validate before.json</code> を実行します。ここで検査するのはファイルの構造であり、ネットワーク通信を再実行する操作ではありません。サーバーを停止してafter.jsonを取得したら <code>python3 report_diff.py --validate after.json</code>、続けて <code>python3 report_diff.py --before before.json --after after.json --output difference.json</code> を実行します。出力先が存在すれば上書き拒否です。</p><p>さらに <code>portfolio_lab/docs/VALIDATION_AND_PORTFOLIO_EVIDENCE_V960.md</code> に実行ディレクトリ、引数、想定結果、異常入力、後片付け、試験証拠、GitHub公開前の確認を詳記しました。対象は必ず自分のloopbackから始め、第三者のネットワークを無断で検査しないでください。</p></div>'''))

portfolio=dom.xpath('//section[@id="portfolio"]')[0]
portfolio.insert(1,H.fragment_fromstring('''<div class="chapter-narrative" id="v960-portfolio-guide"><h2>転職用実践課題：何を自分で改善したかが伝わる証拠</h2><p>今回の新機能は見本コードの改善であり、教材をそのまま提出しても独自の開発実績にはなりません。作業開始時の状態をGitで記録し、<code>--validate</code>が必要な理由を自分の言葉で説明し、余分なJSONキーを受け入れる旧版のテスト失敗、実装変更、成功した回帰テストを別々に保存してください。スコープ制約、失敗時の終了コード、入力上限、レポートの真正性を証明できない理由を設計書へ記載します。</p><p>提出物の例は「自作改善ソース」「requirementsと使い方」「単体・異常系テスト」「脅威モデル」「期待値と実測値の対応表」「Gitコミット履歴」「公開前チェック」です。証拠に掲載するIP・ログ・資格情報を確認し、原典ソースや脆弱な演習環境をそのまま公開しないでください。</p></div>'''))

report=dom.xpath('//section[@id="report-compare"]')[0]
report.insert(1,H.fragment_fromstring('''<div class="chapter-narrative" id="v960-json-reading"><h2>読解演習：集合差と引数モードを行ごとに理解する</h2><p><code>required_report_fields</code> はトップレベルの許可キー集合です。<code>set(report)</code> は入力辞書に実際にあるキーを集め、<code>!=</code> で一致を比較します。<code>required_report_fields - report.keys()</code> は必要だが存在しないキー、<code>report.keys() - required_report_fields</code> は存在するが許可されないキーです。いずれも <code>sorted(...)</code> で読みやすく整理して <code>ValueError</code> にします。結果行にも同じ仕組みで3キーを要求します。</p><p><code>--validate</code> は <code>argparse.add_argument</code> でパスとして登録します。引数の欠落をチェックする場所を比較処理本体へ移し、<code>args.validate is not None</code> で検証モードを選びます。他の比較引数と同時指定なら拒否し、単独なら <code>read_report</code> を呼び <code>VALID</code> と対象ポート数を表示して <code>return 0</code> で終了します。<strong>重要：</strong>この表示は入力の形式検査成功を示すだけで、データの改ざん検出や実際のポート状態の再測定ではありません。</p><p>手元で <code>python3 -m unittest discover -s tests -v</code> を実行し、未知キー、必須キーの削除、CLIの引数組合せ、上書き拒否を含むテストを確認してください。コード片とテストは異なるファイルに分かれ、10工程で交互に編集する構成です。</p></div>'''))

# Make names and counts current in prose. Never rewrite original source code spans.
renames={
'portscanner_pentest_development_manual_v880_20261117.html':new.name,
'portscanner_pentest_manual_v880_20261117.zip':'portscanner_pentest_manual_v960_20261117.zip',
'880周改訂版':'960周改訂版',
'累計880周':'累計960周',
'第880周':'第960周',
'全44件':'全49件',
'44件の':'49件の',
'44件を':'49件を',
'411行':'497行',
}
for e in dom.iter():
    if e.tag in ('script','style'):continue
    if e.get('data-line') is not None:continue
    if e.text:
        for a,b in renames.items():e.text=e.text.replace(a,b)
    if e.tail:
        for a,b in renames.items():e.tail=e.tail.replace(a,b)

frpath.write_text(json.dumps(fr,ensure_ascii=False,indent=2)+'\n')
sm=json.loads((R/'SOURCE_MANIFEST.json').read_text());sm['manual']=new.name
(R/'SOURCE_MANIFEST.json').write_text(json.dumps(sm,ensure_ascii=False,indent=2)+'\n')
new.write_bytes(H.tostring(dom,method='html',encoding='utf-8',doctype='<!DOCTYPE html>'))
(R/'EDITORIAL_PATCHES_881_960.json').write_text(json.dumps({'source':'original user-supplied v880 archive','version':'960','changes':changed,'narrative_sections':['v960-summary','v960-workflow','v960-portfolio-guide','v960-json-reading']},ensure_ascii=False,indent=2)+'\n')
print('created',new.name,new.stat().st_size,fr['files'],'new distinct source-line notes',len(changed))
