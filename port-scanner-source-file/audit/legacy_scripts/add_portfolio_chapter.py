#!/usr/bin/env python3
"""Insert the practical portfolio chapter into the original source-aligned manual.
Every portfolio source line has its own handwritten context explanation.
"""
from pathlib import Path
from hashlib import sha256
from collections import defaultdict
import html
import importlib.util
import json
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
manual=ROOT/'portscanner_pentest_SNAKE_style_480round_refined_manual_20261116.html'
bs=BeautifulSoup(manual.read_text(encoding='utf-8'),'lxml')
spec=importlib.util.spec_from_file_location('pn', ROOT/'tests/portfolio_notes.py')
notesmod=importlib.util.module_from_spec(spec);spec.loader.exec_module(notesmod)
files={'scanner.py':notesmod.SCANNER,'tests/test_scanner.py':notesmod.TESTS,'.github/workflows/tests.yml':notesmod.WORKFLOW}
source={p:(ROOT/'portfolio_lab'/p).read_text().splitlines(keepends=True) for p in files}
for p,n in files.items():
    missing=[i for i,l in enumerate(source[p],1) if l.strip() and i not in n]
    assert not missing,(p,missing)

def el(tag,text=None,**attrs):
    x=bs.new_tag(tag,attrs={k.replace('_','-'):v for k,v in attrs.items()})
    if text is not None: x.string=text
    return x

def P(parent,*texts):
    for t in texts:parent.append(el('p',t))

def listitems(parent,items,ordered=False):
    u=el('ol' if ordered else 'ul')
    for item in items:u.append(el('li',item))
    parent.append(u)
    return u

def box(parent,kind,heading,content):
    a=el('div',**{'class':f'precision-box portfolio-{kind}'})
    a.append(el('h4',heading));a.append(el('p',content));parent.append(a)

portfolio=el('section',id='portfolio',**{'class':'manual-section','data-title':'転職ポートフォリオ制作・新規実装と証拠'})
hero=el('div',**{'class':'section-hero'});hero.append(el('div','PORTFOLIO / SECURITY ENGINEERING',**{'class':'section-kicker'}));hero.append(el('h1','実際に提出できるポートフォリオへ発展させる'));hero.append(el('p','学習教材の原典再現と、採用担当者へ見せる自分の成果物は別に管理する。安全な小規模実装、テスト、設計根拠、検査証拠、公開・説明までを、ファイル間を往復しながら組み上げる。',**{'class':'lead'}));portfolio.append(hero)
box(portfolio,'warning','最初に区別すること','原典『ポートスキャナ自作ではじめるペネトレーションテスト』のコードを手入力した結果は「学習実績」であり、そのまま「自作の独自設計」と称して提出しない。この章のportfolio_lab/は今回新たに作成した独立の学習用見本であり、利用者自身の実績ではない。これを出発点に、自分で機能を考え、テストし、証拠を記録した範囲をポートフォリオとして説明する。')
intro=el('div',**{'class':'chapter-narrative'});intro.append(el('h2','全体像：何を作るか、何を見せるか'))
P(intro,'この章では原典の TCP Connect スキャンを題材に、「接続結果の観測と誤判定の防止」を目的とした別の小型CLIを作る。出力はJSON、標準動作は127.0.0.1のみ、ポート上限32件、明示CIDRによる許可ラボ制限、ユニットテスト11件を備える。再現可能な検証記録を付けて初めて「成果を検証できるポートフォリオ」となる。', '元の原典サンプルのコード片をそのまま転載するのではなく、問題設定、エラーの分類、入力・スコープ制限、レポートとテストを新しく設計する。原典リポジトリのREADME「サンプルコード」の利用条件も確認し、引用元と自分の変更点をREADMEに明示する。')
listitems(intro,['原典の学習：ソケット版の接続成功0と、失敗時のerrnoが非0になることを理解する。','要件設計：誤った第三者スキャンをしない初期値と、許可対象だけに限定する仕組みを決める。','開発・試験：scanner.py ↔ tests/test_scanner.py ↔ GitHub Actionsを往復しながら実装する。','検証証拠：コマンド、OS、Python版、コミットSHA、期待値、実際の出力、失敗と改修を残す。','公開・面接：設計図、制限、脅威モデル、未検証事項を説明し、原典と自作範囲を混同しない。'],True)
portfolio.append(intro)
rootmap=el('div',**{'class':'chapter-body'});rootmap.append(el('h2','新しい独立プロジェクトのファイル構成'))
code_tree='''portfolio_lab/\n  scanner.py                 # 実行できるTCP Connect検査CLI\n  tests/test_scanner.py       # 入力と127.0.0.1の実通信テスト\n  .github/workflows/tests.yml # CIの例（公開前にActionsの依存を確認）\n  docs/ARCHITECTURE.md        # 設計判断と原典との比較\n  docs/THREAT_MODEL.md        # 誤スキャン、結果漏えい、誤判定への対策\n  docs/TEST_REPORT_TEMPLATE.md # 検証報告書の記入欄\n  docs/PUBLICATION_CHECKLIST.md # 公開前の安全・出典確認\n  README.md                   # 独立作品の説明・使い方\n  .gitignore                  # 一時レポートと環境ファイルの除外\n  evidence/                   # 公開可能な証拠だけを置く\n'''
wrap=el('div',**{'class':'terminal-wrap'});pre=el('pre');pre.append(el('code',code_tree));wrap.append(pre);rootmap.append(wrap)
P(rootmap,'これらのファイルはZIP内に実際に収録してある。ここからは空の portfolio_lab/ を自分で作り、短いコード片を順に追加する場合を想定している。付属の完成例をコピーして成功しただけなら「環境構築の再現」であって「自作実装の実績」とは区別する。')
portfolio.append(rootmap)

ranges=[]
stages=[
 ('01','要件・許可・範囲を紙に書く',None,None,None,'原典のコピーとは別の要件を定義する。','自分が所有する127.0.0.1だけを標準対象にし、ポートは最大32件、応答なしをclosedと断定しないという受け入れ条件を決める。', ['docs/ARCHITECTURE.md と docs/THREAT_MODEL.md に目的・境界・停止条件を書く。','許可済みVM以外へスキャン対象を広げない。'], 'READMEに対象・目的・制限を書けている。'),
 ('02','scanner.py の土台とプライベートIPの定義','scanner.py',1,15,'importと定数の準備。','まず起動可能なモジュールの骨格を作る。IPv4のプライベート範囲は自動的に「許可済み」とならない点を区別する。',['各importがどの関数で使われるか対応させる。','RFC1918の3範囲の意味と127/8との違いを説明する。'],'定数をIPネットワークとして参照できる。'),
 ('03','テスト側に最初の正常系を書いておく','tests/test_scanner.py',1,15,'テストを先に書く。','実務ではまず何を成功とみなすかをテストで定義する。最初は未実装関数がありimportに失敗しても、すべて完成してから検査できる。',['assertEqualは何を比較しているか説明する。','テストを実行する場所はportfolio_lab直下とする。'],'期待する「22,80,443 → 整数リスト」が明文化された。'),
 ('04','parse_ports の入力チェックを実装','scanner.py',16,29,'文字列から安全な整数リストへ。','入力の個数・記号・範囲・重複は別々に検証する。番号0や65536を一律「ネットワーク障害」としない。',['カンマ・split・any・setの役割を追う。','入力が不正ならスキャン開始前にエラーへ進む。'],'どの入力を拒否するか関数で決まった。'),
 ('05','不正入力のテストを追加','tests/test_scanner.py',16,25,'負のケースも先に決める。','壊れた入力に対して止まることは、サイバーセキュリティのツールでは正常系と同じくらい重要になる。',['0/65536、重複、範囲文字列、空欄、33件を試す。','subTestで失敗した入力値を区別する。'],'拒否すべき6種類の例と上限を検証できる。'),
 ('06','check_scope で誤スキャン防止','scanner.py',30,51,'ターゲットと許可範囲を照合。','最初は127/8のloopbackに限定。外へ広げる場合でもIPv4リテラル、RFC1918、/24以下、明示CIDR、許可フラグを要求する。',['IPv4AddressとIPv4Networkの役割を分けて覚える。','`--authorized` は書面許可を得たという技術的証明ではない。'],'範囲外のIPをTCP接続前に拒否できる。'),
 ('07','対象範囲のテストを書く','tests/test_scanner.py',26,50,'境界の破れを再現するテスト。','通してよいloopbackと、拒否すべきスコープ逸脱・公開IPv4・過大CIDRを別々に試す。',['テストはcheck_scopeの純粋な入力チェックで、外部IPへ接続しない。','「明示フラグはあるが範囲外」という組合せを入れる。'],'許可対象制限の正常系・異常系が揃った。'),
 ('08','probe で接続結果を分類','scanner.py',52,71,'TCP connectとerrnoの分類。','ソケットの生成と接続成功を区別し、0/open、拒否/refused、時間切れ/timeout、到達不能/unreachable、そのほかを分類する。',['withでソケットが閉じられる理由を確認する。','タイムアウトはフィルタ確定を意味しない。'],'openと非0エラーの意味を混同していない。'),
 ('09','127.0.0.1だけの統合テスト','tests/test_scanner.py',51,68,'loopbackで実際に接続する。','OSに空きポートを選ばせるため、固定値8765の競合でテストが壊れにくい。外部宛てスキャンをCIで実行しない。',['bind(...,0)とlisten(1)の違いを確認する。','リスナーを閉じた後のrefusedには短い競合余地がある。'],'開いたポートと接続拒否の挙動を観測できる。'),
 ('10','引数解析と検証を実装','scanner.py',72,87,'argparseでCLIを組み立てる。','正しい入力を受け取ってからprobeを呼ぶため、入力の不正が通信開始前に検出される。',['--timeoutの0.1〜3.0は秒数の制限。','--scope-cidrと--authorizedは別々の必須条件として扱う。'],'--helpが読め、誤設定時は通信前に停止する。'),
 ('11','JSON報告と安全な終了','scanner.py',88,112,'操作結果を保存・表示する。','タイムスタンプ、対象IP、宣言した範囲、タイムアウト、各ポートの結果をまとめる。既存ファイルへの上書きは拒否する。',['JSONに保存する値と画面表示を分けて読む。','`__name__=="__main__"` の条件がimport時の副作用を防ぐ。'],'コマンドでJSONを見られる。既存ファイルを上書きしない。'),
 ('12','テストファイルを完成して実行','tests/test_scanner.py',69,89,'実行エントリを設置。','ここまでscanner.pyとtests/test_scanner.pyの実装が揃っている。 `python3 -m unittest discover -s tests -v` を実行して11件の結果を確認する。',['READMEにはテスト環境と結果の数字を記載する。','失敗すればログを保存し、修正後に再実行する。'],'11件のテストをローカルで実行できる。'),
 ('13','GitHub Actionsで検査を自動化','.github/workflows/tests.yml',1,13,'pushとPRで実行するCIの見本。','環境差を減らすためPythonバージョンを指定し、unittestをリポジトリで動かす。外部Actionsのバージョンと権限は公開時に再確認。',['YAMLのインデントはジョブ、steps、withの階層を作る。','このCIは127.0.0.1のみのテストで、外部スキャンをしない。'],'テストをCIで再実行する仕組みを説明できる。'),
 ('14','ローカル実演を2つの端末で行う',None,None,None,'TCPの開閉を自分の端末で再現。','ターミナルAでHTTPサーバーを127.0.0.1:8765にだけ起動。ターミナルBで8765,8766を検査し、HTTPサーバー停止後に同じコマンドを再実行する。',['A：python3 -m http.server 8765 --bind 127.0.0.1','B：python3 scanner.py --target 127.0.0.1 --ports 8765,8766 --timeout 0.5','AでCtrl+C後、Bを再実行して変化を見る。'],'待受中openと停止後refusedの実測値を記録した。'),
 ('15','JSON・実行環境・失敗証拠を残す',None,None,None,'再現可能な評価材料を作る。','docs/TEST_REPORT_TEMPLATE.mdにOS、Python、日時、許可スコープ、実行コマンド、期待結果、実測結果、コミットSHA、失敗時の修正を記録する。',['python3 --version と git rev-parse HEAD の結果を記録する。','python3 scanner.py --target 127.0.0.1 --ports 8765,8766 --output report-local.json','report-local.jsonにはIP等を含むため、公開前に匿名化・安全性を確認する。'],'画面だけではなくコマンド・レポート・コード版の対応が示せる。'),
 ('16','独立のREADME・脅威モデルを完成',None,None,None,'コードが何のためにあるか説明する。','READMEには要件、インストール不要な依存、CLI、状態分類、再現手順、限界、出典、原典との違いを記載。脅威モデルには誤対象・漏えい・誤判定・可用性を含める。',['原典 `tcp-connect-scan-by-socket.py` と自作版の違いを表にする。','対象・スコープの許可はツールだけで証明できないと記す。'],'初見の第三者が再現し、限界を判断できる文書がある。'),
 ('17','GitHub公開前のチェックと安全な公開',None,None,None,'勝手に公開しないためのレビュー。','Gitへ追加する前に資格情報、IP、ログ、外部由来のコードを調べる。出典・原典利用条件の範囲を確認し、自分が実装した変更をコミットで説明できるようにする。',['git status --short で対象を確認し、git diff --cached で公開予定の差分を見る。','git init、git add、git commit の後に公開先とアクセス権を確認する。','最初はprivateでレビューし、公開前にdocs/PUBLICATION_CHECKLIST.mdを埋める。'],'原典の丸写し・秘密情報の漏えいを防いだ公開準備ができた。'),
 ('18','面接用の説明・実演を作る',None,None,None,'目立つ画面より問題解決の証拠。','3〜5分で「なぜ作ったか」「原典の何を理解したか」「自分で変えた点」「想定した誤用」「テストの失敗と修正」「残る限界」を話す。端末で実際に127.0.0.1の開閉を見せる。',['例：原典は非0をclosedとまとめていたが、私はerrno別に状態を分けた。','例：入力ミスで別ホストへ接続しないようloopback既定、CIDR必須、32件制限とした。','例：今後の課題はIPv6・レポートの原子保存・OS別errno差の検証。'],'技術選択を根拠とともに説明し、実演で再現できる。'),
 ('19','自分だけの追加実装を行い、再テスト',None,None,None,'例題から自分の成果へ。','このサンプルを提出するだけで終わらせず、自分で要求を定めて差分機能を実装・テストする。例は安全なJSON差分、結果の履歴比較、OS別エラー分類の改善、保存の原子性。第三者を対象にする新機能は不要。',['1つの改善要件をREADMEとissueに記録する。','修正前の失敗テスト→コード変更→成功テストの履歴を残す。','ユーザーの実績として話すのは、自分で判断・実装・検証した箇所だけ。'],'実装判断・失敗からの改善を客観的に示せる。'),
]

source_segments=defaultdict(list)
fragment_records=[]
for ix,title,path,start,end,sublead,description,bullets,done in stages:
    art=el('article',id=f'portfolio-step-{ix}',**{'class':'portfolio-task','data-search-title':title})
    art.append(el('div',f'PORTFOLIO STEP {ix} / 19',**{'class':'step-number'}))
    art.append(el('h2',title))
    art.append(el('p',description,**{'class':'portfolio-lead'}))
    if path:
        art.append(el('div','編集するファイル：portfolio_lab/'+path+f' / 原典とは独立の新規ファイル / L{start}–L{end}',**{'class':'source-position'}))
        art.append(el('p',sublead))
        chunk=source[path][start-1:end]
        assert len(chunk)==end-start+1
        pane=el('div',**{'class':'code-wrap portfolio-code-box'})
        pane.append(el('button','コードをコピー',**{'class':'copy-btn','type':'button'}))
        pre=el('pre');c=el('code',**{'class':'portfolio-source-lines'})
        for line,body in enumerate(chunk,start):
            s=el('span',**{'data-line':str(line)})
            s.append(body)
            c.append(s)
            source_segments[path].append((line,body))
            fragment_records.append({'stage':int(ix),'path':path,'line':line,'code':body})
        pre.append(c);pane.append(pre);art.append(pane)
        art.append(el('h3','追加する各行の意味と構成要素'))
        table=el('table',**{'class':'status-table portfolio-line-table'})
        hdr=el('thead');thr=el('tr');thr.append(el('th','行'));thr.append(el('th','コードと具体的な説明'));hdr.append(thr);table.append(hdr)
        tbody=el('tbody')
        for n,body in enumerate(chunk,start):
            row=el('tr',**{'class':'portfolio-code-annotation','data-file':path,'data-line':str(n)})
            row.append(el('td',f'L{n}'))
            td=el('td');td.append(el('code',body.rstrip('\r\n') if body.strip() else '(空行)',**{'class':'portfolio-line-source'}))
            td.append(el('p',files[path][n] if body.strip() else '空行。ここで直前の宣言・処理のまとまりを区切り、次の関数・テスト群を読みやすくしている。'))
            row.append(td);tbody.append(row)
        table.append(tbody);art.append(table)
    else:
        art.append(el('div','実行前に読む・成果を記録する',**{'class':'source-position'}))
        art.append(el('p',sublead))
    art.append(el('h3','作業と確認'))
    listitems(art,bullets,True)
    box(art,'checkpoint','この工程が終わったら',done)
    portfolio.append(art)
# Check completeness of the portfolio example, including trailing blank lines.
for p,lines in source.items():
    reconstructed=''.join(v for n,v in sorted(source_segments[p]))
    assert reconstructed==''.join(lines),(p,'file content mismatch')
    assert [n for n,v in sorted(source_segments[p])]==list(range(1,len(lines)+1)),p
    for n,line in enumerate(lines,1):
        if line.strip():assert n in files[p],(p,n)

finish=el('div',**{'class':'chapter-body'});finish.append(el('h2','採用担当者へ説明する資料の完成形'))
P(finish,'READMEの先頭には、30秒で分かる要約（何を検査するか、対象範囲、主な改善点、テスト状況）を書く。次に「目的→設計図→検証手順→実測証拠→制限→自分の判断の記録」の順で示す。原典コードの再現スクリーンショットだけでは、問題の定義と自分の貢献を証明できない。','セキュリティエンジニア採用では、発見の数を盛るより、通信とOSエラーを正しく解釈し、対象・証拠・権限を管理し、障害を再現して説明できることが重要。ネットワーク運用・CLI調査の経験を示したい場合は、実行ログから結論へ至る判断を順序立てて説明すると伝わりやすい。')
listitems(finish,['GitHub README：用途、特長、起動方法、検査範囲、テスト結果、出典、制限。','docs/ARCHITECTURE.md：構成図、なぜ標準ソケット、なぜ直列・32件制限か。','docs/THREAT_MODEL.md：対象誤指定、情報漏えい、誤判定、サービス負荷の対策と残余リスク。','docs/TEST_REPORT_TEMPLATE.mdを実際の試験報告書として埋めたもの：日時、Python版、コミットSHA、入力、期待、観測、失敗と修正。','1〜2分の実演動画、または端末A/Bの操作・出力スクリーンショット。無許可のネットワークIPは含めない。','面接用メモ：自分で追加したコードと、原典から学んだ点を区別した短い説明。'],True)
portfolio.append(finish)
box(portfolio,'warning','原典の再配布・利用条件','ユーザー提供の原典READMEは、書籍コードの一部を自分のプログラムに使う場合と、コード例の販売・配布や大部分の転載を区別している。原文と付属物の個別ライセンスを読んで判断すること。GitHubへ原典ZIP、脆弱コンテナ、教材全文、第三者のロゴなどを無条件でアップロードしない。新規作品を公開するなら、自分で著作権を持つ部分と引用部分を明示する。')
nav=el('div',**{'class':'section-nav'});nav.append(el('button','前の章',**{'class':'nav-btn prev','data-nav':'prev'}));nav.append(el('button','次の章',**{'class':'nav-btn next','data-nav':'next'}));portfolio.append(nav)
main=bs.select_one('main#main');sources=bs.find('section',id='sources');sources.insert_before(portfolio)
side=bs.find('aside',id='sidebar');entry=el('button',**{'class':'toc-item','data-target':'portfolio','type':'button'});entry.append(el('span','転職ポートフォリオ制作',**{'class':'toc-title'}))
usage_btn=side.find('button',attrs={'data-target':'usage'})
assert usage_btn;usage_btn.insert_after(entry)
css='''
/* Portfolio writing lab (new chapter): retains the supplied SNAKE palette. */
.portfolio-task {margin:24px 0;padding:28px;background:var(--paper);border:1px solid var(--line);border-top:4px solid var(--orange);box-shadow:var(--shadow);scroll-margin-top:90px;overflow-wrap:anywhere}.portfolio-task h2{color:var(--pink)}.portfolio-task h3{color:var(--teal);margin-top:24px}
.portfolio-lead {font-size:1.04em;color:#e4eddf}
.portfolio-code-box pre {max-height:520px;overflow:auto}
.portfolio-source-lines span{display:block;white-space:pre;min-height:1.5em}
.portfolio-source-lines span::before{content:attr(data-line);display:inline-block;width:3.4em;color:#d2bb90;border-right:1px solid #5f553f;margin-right:.8em;user-select:none}
.portfolio-line-table{width:100%;table-layout:fixed}
.portfolio-line-table th:first-child,.portfolio-line-table td:first-child{width:65px;text-align:center;white-space:nowrap}
.portfolio-line-table td:last-child{overflow-wrap:anywhere}
.portfolio-line-source{display:block;white-space:pre-wrap;color:#f0d7a7;border:1px solid #64523a;padding:5px 8px;background:#252017;font-size:.84em;overflow-wrap:anywhere}
.portfolio-line-table p{margin:8px 0 2px;color:#d6e1e5;line-height:1.73}
.portfolio-warning{border-color:#7c5b43;background:#2b231d}
.portfolio-checkpoint{border-color:#44694e;background:#17241b}
@media(max-width:650px){.portfolio-line-table,.portfolio-line-table tbody,.portfolio-line-table tr,.portfolio-line-table td{display:block;width:100%!important}.portfolio-line-table thead{display:none}.portfolio-line-table tr{border-bottom:1px solid #405057;margin-bottom:12px;padding:8px}.portfolio-line-table td:first-child{text-align:left;color:var(--orange);font-weight:bold}.portfolio-task{padding:16px}.portfolio-source-lines span::before{width:2.7em;margin-right:.6em}}
@media print {.portfolio-task{break-inside:auto}.portfolio-code-box pre{max-height:none}.portfolio-line-table td{color:#111!important}.portfolio-line-source{background:#fff!important;color:#111!important}}
'''
style=bs.new_tag('style');style.string=css;bs.head.append(style)
# Versions in prose only. Keep all source line codes unmodified.
home=bs.find('section',id='home')
box(home,'checkpoint','今回の追加：就職活動に使う別実装と証拠','原典を再現する107工程とは別に、ポートフォリオ制作19工程を追加。独立のscanner.py（112行）・テスト（89行）・CI YAML（13行）を、ファイルを行き来する開発順で各行ごとに解説。コードの行番号とZIP内の実ファイルが一致するように照合している。')
# Adjust only authoring-specific references; preserve previous 40 usage cards as historical content.
first=bs.find('section',id='prepare')
P(first,'ポートフォリオのために作る独立作品の手順は、目次の「転職ポートフォリオ制作」から開始する。原典の43ファイルと独立サンプルの3ソースは別の検証対象である。提出用には自分で要件を決め、設計・修正した範囲を正直に明記する。')
# Add separate portfolio progress controls independent from the original 107 source-rebuild checkboxes.
for art in portfolio.select('article.portfolio-task'):
    check=el('label',**{'class':'step-check portfolio-progress'})
    cb=el('input',**{'type':'checkbox','data-portfolio-done':art['id'],'aria-label':'ポートフォリオ工程の確認'});check.append(cb)
    check.append(el('span','この工程を自分の手で実施し、記録したらチェック'))
    art.append(check)
progress_script='''
(()=>{
'use strict';
const key='portscanner-portfolio-progress-480';
const checks=[...document.querySelectorAll('input[data-portfolio-done]')];
let state={};try{state=JSON.parse(localStorage.getItem(key)||'{}')||{}}catch(_){}
checks.forEach(c=>{c.checked=!!state[c.dataset.portfolioDone];c.addEventListener('change',()=>{state[c.dataset.portfolioDone]=c.checked;try{localStorage.setItem(key,JSON.stringify(state))}catch(_){}})});
})();'''
script=bs.new_tag('script');script.string=progress_script;bs.body.append(script)
manual.write_text(str(bs),encoding='utf-8')
# verify that source line snippets exactly concatenate to corresponding sample files
(ROOT/'PORTFOLIO_FRAGMENTS.json').write_text(json.dumps({'files':{p:{'sha256':sha256(''.join(lines).encode()).hexdigest(),'lines':len(lines),'nonblank_annotated':sum(bool(l.strip()) for l in lines)} for p,lines in source.items()},'steps':[{'stage':int(ix),'path':p,'start':a,'end':b} for ix,title,p,a,b,*_ in stages if p],'all_line_fragments':fragment_records},ensure_ascii=False,indent=2),encoding='utf-8')
print('Added 19 portfolio tasks,',len(fragment_records),'source lines; manual',manual.stat().st_size,'bytes')
