# セキュリティエンジニア応募用：TCP Connect観測・差分比較ポートフォリオ実制作手順

この手順は、同梱の **AI作成学習見本** `scanner.py` / `report_diff.py` とテストを読んで理解した後、**自分の判断で再実装・改善した作品と実測証拠を作る**ためのものです。原典の書籍サンプルや本教材の見本を、そのまま本人が独自に設計した成果だと説明しないでください。自分が実際に検証した範囲だけを実績に書きます。

検査対象は自分の端末の `127.0.0.1` のみ。外部ホスト、会社の設備、他人のネットワークは使いません。`--authorized` は自己申告のフラグであって許可を取得・証明するものではありません。

## 1. 作業の位置と終了条件を決める

完成版ZIPを解凍したフォルダの `portfolio_lab/` に移動します。以降のサンプルは、断りがない限りこのディレクトリで実行します。`pwd` で現在位置を確認してください。`python3 --version` でPython 3.11以上を確認します。

```sh
pwd
python3 --version
python3 scanner.py --help
python3 report_diff.py --help
python3 -m unittest discover -s tests -v
```

`--help` は `argparse` が表示する実行可能なオプションを確認するための引数です。スキャンはしません。`unittest` の `-m` は標準ライブラリのモジュールを起動し、`discover` は指定した `tests` ディレクトリからテストを検索、`-v` は各テスト名・結果を表示します。同梱の見本にはスキャナ14件、比較ツール37件の計51件のテストがあります。この数は将来の自作版に追加したテスト数とは別に記録してください。

期待する停止条件は、未許可の対象指定を拒否すること、既存の `before.json` / `after.json` / `difference.json` を勝手に上書きしないこと、ループバック以外の通信を起こさないことです。

## 2. まずソースの役割とデータの流れを図にする

`scanner.py` は引数を検証し、1ポートずつ `socket.connect_ex()` を実行し、`state` と `errno` をJSONへ保存します。`report_diff.py` は**ネットワーク接続をしません**。既にある2つのJSONを読み込み、対象IP、スコープ、timeout、ポート集合、UTC日時と各行の状態を確かめ、状態が変わったポートを報告します。

```text
利用者のCLI入力
  -> scanner.py: parse_ports / check_scope / probe
  -> before.json / after.json
  -> report_diff.py: read_report / compare
  -> difference.json
  -> 本人の試験記録 + Gitコミット + 制約説明
```

`errno=0` は `connect_ex` の成功、`state=open` はその成功を説明するための名前です。今回の比較ツールは成功 `open` と0が対応するか確認します。ただし、`errno` の非ゼロ値はOS差があるため、111のような特定値を全OSの失敗状態に固定しません。**JSONは手作業で編集可能**なので、検査合格は観測の真実性を証明しません。

## 3. 自分で追加する要件を先に決める

まず見本を使わず、日本語で `docs/REQUIREMENTS.md` を自分の言葉で書きます。最低限、次の条件を書いてから実装してください。

- 対象を初期状態で127.0.0.1へ限定する理由。RFC1918の許可済みラボへ広げる場合の事前許可・停止条件。
- 1〜32ポート、番号は1〜65535、重複・空値・ASCII以外の数字を拒否する理由。
- 1件ごとの接続タイムアウト0.1〜3.0秒、`open` / `refused` / `timeout` / `unreachable` / `error_or_unknown` を区別する理由。
- JSONスキーマのキー名、`timestamp_utc` のUTC条件、成功/失敗とerrnoが一致する条件。
- 差分比較は同じtarget、scope、timeout、ポート集合で行い、前時刻が後時刻より古いこと。
- JSONの保存先が存在するとき上書きしない理由。脅威モデルにシンボリックリンクや改ざん入力の注意を入れる。

設計判断を記録するとき、単に「安全だから」ではなく「どんな誤入力をどの箇所で拒否するか」まで書きます。

## 4. 個人リポジトリを作成し、見本の転載と分ける

新しいディレクトリを作り、本人が作ったファイルだけを置きます。ここに元教材の `original_source.zip`、古い脆弱なコンテナ、過去版HTMLを丸ごとコピーしないでください。`.gitignore` には秘密情報・実測JSON・Pythonの生成ファイルなどを自分の判断で指定します。

```sh
mkdir -p ~/Documents/tcp-audit-portfolio/docs ~/Documents/tcp-audit-portfolio/tests
cd ~/Documents/tcp-audit-portfolio
git init
git status --short
```

`mkdir -p` は親ディレクトリも必要に応じて作成します。`git init` はこのディレクトリをGit管理の対象にするだけで、GitHub公開はしません。`git status --short` は未追跡・変更済みファイルを短い表示で確認します。保存先は一例なので本人の環境に合わせてください。原典の使用条件は同梱原典のREADME本文で確認してください。

## 5. 失敗するテストを最初に書く

まず `tests/test_input.py` に不正なポート、対象範囲外、重複ポート、既存ファイル上書きのテストを作ります。成功ケースは `127.0.0.1` のみで実施します。次に状態とerrnoの矛盾を拒否するテストを考えます。

検査設計例：

| ID | 入力の組 | 期待する挙動 | 実測証拠 |
|---|---|---|---|
| P01 | `--ports 8765,8766` | 重複のない番号として受理 | CLIと単体テスト |
| P02 | `--ports 8765,8765` | 入力エラーで停止 | stderrと終了コード |
| P03 | `--target 8.8.8.8` のみ | ネットワーク通信前に拒否 | CLIのエラー・テスト |
| P04 | `state=open, errno=111` | JSONを不正として拒否 | 異常系単体テスト |
| P05 | `state=refused, errno=0` | JSONを不正として拒否 | 異常系単体テスト |
| P06 | `state=error_or_unknown, errno=999` | 非ゼロの未知errnoを保持 | 正常系単体テスト |
| P07 | target/port一致・timeout不一致 | 比較を拒否 | 単体テスト |
| P08 | beforeとafterの時刻が逆 | 比較を拒否 | 単体テスト |
| P09 | 既存の出力パスへ2回保存 | 元のファイルを変更せず拒否 | ハッシュと終了コード |

テスト記録には、実際のテスト名、日時、Pythonバージョン、コミットSHA、入力、期待結果、実測結果を併記してください。「テストを増やした」だけでは何を守れるようにしたか伝わりません。

## 6. ローカルの実測、期待値と実測値の違い

**端末A**：必ず自分のPCのloopbackだけでHTTPサーバーを起動します。

```sh
python3 -m http.server 8765 --bind 127.0.0.1
```

`-m http.server` はPythonの標準HTTPサーバーモジュール、`8765` はTCPポート、`--bind 127.0.0.1` はloopbackだけで待ち受ける指定です。この端末は待受のため起動状態を維持します。起動できなければ `ss -ltn` で8765の利用状況を確認し、他のプログラムを無断終了しないでください。

**端末B**：配布見本の `portfolio_lab/` 内で、まず1回目の結果を保存します。

```sh
pwd
python3 scanner.py --target 127.0.0.1 --ports 8765,8766 --timeout 0.5 --output before.json
python3 -m json.tool before.json
```

`--target` は対象IPv4、`--ports` はカンマ区切り、`--timeout 0.5` は各TCP接続に対するタイムアウト秒数、`--output` は新規作成するJSON名です。ファイルが既にあれば失敗します。`json.tool` は保存内容の構文検査と整形表示です。予想は8765がopen、8766がrefusedですが、実測は他プロセスやOSに依存します。

端末Aで **Ctrl+C** によりHTTPサーバーを停止し、端末Bで2回目を取得します。

```sh
python3 scanner.py --target 127.0.0.1 --ports 8765,8766 --timeout 0.5 --output after.json
python3 report_diff.py --before before.json --after after.json --output difference.json
python3 -m json.tool difference.json
```

`--before` は最初の観測、`--after` は後の観測。`--output` は差分結果の保存先で、既存ファイルは上書きしません。通常は8765に `open -> refused` と記録されますが、その結果は各自のPCで実測してください。8766が別プロセスで待受中なら拒否ではなくopenになり得ます。差分を得ただけで脆弱性を発見したとは言えません。

### よくあるエラーと直し方

| 症状 | 原因の確認 | 対処 |
|---|---|---|
| `output already exists` | 前回のJSONファイルが残っている | 上書きせず、別のファイル名を指定して履歴を保持する |
| `before must have an earlier timestamp` | 実行順が逆か保存ファイルを取り違えた | `timestamp_utc` を確認し、改ざんせず新しい観測を取り直す |
| `reports must use the same TCP connection timeout` | 観測時の `--timeout` が異なる | 同じ設定で両方の測定をやり直す |
| `open requires errno 0` | 状態とOS戻り値が矛盾している | JSONの手編集・取り違え・古い出力元を疑い、元の計測を再実行する |
| `non-open state cannot have errno 0` | 失敗名の状態に成功値が入っている | 値を機械的に書き換えず、生成元のコードと保存処理を確認する |
| `No module named scanner` | `portfolio_lab/` 外からテストを起動した | `pwd`と作業ディレクトリを確認し、`cd portfolio_lab`後に再実行する |
| `Connection refused` | 待受がない、サービス停止、別プロセスによる利用 | サーバー端末の表示と`ss -ltn`を確認する |

## 7. 画面操作とHTML教材の進捗

HTMLをブラウザで直接開き、左の目次から「転職ポートフォリオ制作」と「レポート比較」を選びます。各工程のファイル名・追記行・説明を確認し、**ファイルを交互に編集**してください。検索欄は設定名・関数名で検索します。工程完了チェックは手元の自己管理であり、確認できた実績の証明ではありません。ブラウザの保存制限によって進捗が失われる可能性があるため、GitとMarkdownの作業ログでも記録を残します。

コード全体を先に貼って「開発した」とするのではなく、`scanner.py`の入力検証、`tests/test_scanner.py`の異常系、次に `report_diff.py` の入力検証、`tests/test_report_diff.py` の比較異常系、最後にCLI統合テストの順で往復します。途中でテストが赤くなる場合は実装中の関数不足と、本当の不具合を区別してください。

## 8. Gitコミットと再現可能な証拠

個人リポジトリで実装とテストが動いたら、関係ファイルだけをステージングします。次はあくまで例で、実際に作ったファイル名に置き換えてください。

```sh
git status --short
git diff --stat
git add README.md docs/ tests/
git diff --cached --stat
git diff --cached
git commit -m "Document loopback TCP measurement tests"
git rev-parse HEAD
```

`git add` でステージングする対象を限定します。`git diff --cached` は**実際にコミット対象になる**内容を表示し、秘密鍵、APIキー、個人IP、機器名、実測JSONを誤って公開する事故を防ぎます。まだないファイルを `git add` に列挙したときはエラーになるため、現在の作業に応じて調整します。`git rev-parse HEAD` は最後のコミットIDを取得します。ハッシュは後から内容を照合する手掛かりですが、観測の真正性やスキャン権限をそれ自体で証明しません。

`docs/TEST_REPORT.md` には、試験日時（JST/UTCを明示）、実機OSとカーネル、Python、検査対象、期待と実測、実際のコマンドと作業ディレクトリ、終了コード、コミットSHA、ログファイルのSHA-256、未検証事項を書きます。スクリーンショットだけ、ユニットテスト件数だけ、AI作成のテスト結果の転載だけでは不十分です。

## 9. 提出前に揃える7点

| 提出物 | 最低限必要な内容 |
|---|---|
| `README.md` | 何を測るツールか、対象制限、導入、例、終了、限界、作成者が実装した範囲 |
| `docs/ARCHITECTURE.md` | ファイル間データフロー、接続処理、JSON入力検証の境界、例外分類の理由 |
| `docs/THREAT_MODEL.md` | 誤った対象への接続、JSON改ざん、上書き競合、情報漏えいへの対策と残るリスク |
| `tests/` | 成功・失敗・境界・上書き拒否・状態とerrno不一致・時刻/条件不一致の試験 |
| `docs/TEST_REPORT.md` | 自分の環境で実測した出力、日時、コミット、対象と許可、未検証事項 |
| `docs/PUBLICATION_CHECKLIST.md` | 原典利用条件、秘密情報、ログ、依存先とActions権限を公開前に確認した記録 |
| `docs/INTERVIEW_GUIDE.md` | 選んだ要件、困った点、修正の差分、検証方法、次に改善する点 |

**評価に向いた説明例：**「Pythonの標準socketで自分のPCのTCPポートを観測する学習ツールを自分で再実装しました。異常なJSONで誤った差分が出る問題を見つけ、観測状態とerrnoが矛盾する入力を拒否しました。失敗テストを追加して修正前後の挙動を検証し、記録したGitコミットと試験条件をREADMEから追えるようにしました。」これは**本人が実際に再実装・修正・検証した場合だけ**の説明文です。

## 10. 安全性・真正性・制約を偽らない

`state_changes`はTCP接続の観測差分であって、脆弱性、侵入、サービス障害の原因を断定するものではありません。`errno`の数値、通信結果、ファイアウォール動作はOS・環境によって変わり得ます。タイムアウト一致は必要条件の一つですが、同一経路・同一負荷・同一ファイアウォール規則が保証されたわけではありません。

- `--authorized` の指定は適法性・所有権・許可の証明ではありません。
- JSONには人為的に作成した内容を入れられます。入力検証に合格したことは、観測事実の真正性の証明ではありません。
- ハッシュはファイルの同一性確認に使えますが、誰がいつ測定したかは別の証拠が必要です。
- 本ZIPの原典アーカイブをそのまま公開しないでください。原典READMEの利用条件を確認してください。
- 原典に含まれる脆弱なDocker環境、ARP妨害、シェルコード実行などはこのポートフォリオ用の安全なloopback手順には含めません。

**一次資料：** このZIPの `portfolio_lab/scanner.py`、`report_diff.py`、両テスト、`README.md`、書籍サンプル `original_source.zip`。他の既存Libraryファイルから技術的な内容を補っていません。


## 単独検証コマンドと成果物の証拠化

比較前に `python3 report_diff.py --validate before.json` と `python3 report_diff.py --validate after.json` を実行してください。実行したディレクトリ、終了コード、標準出力・標準エラーを記録します。出力が `VALID` でも実測を証明するわけではなく、JSONが現在のプログラムの受理条件を満たすだけです。複数引数モードは `--before ... --after ...`、単独検証モードは `--validate ...` で、混用できません。

再現試験の入力異常（未知キー・欠落キー）、異常系テスト、GitHubへの公開前確認については `VALIDATION_AND_EVIDENCE.md` を読み、サンプルの見本から自分が改良した差分を残してください。
