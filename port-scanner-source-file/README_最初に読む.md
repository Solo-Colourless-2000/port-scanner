# ポートスキャナ自作・ペネトレーションテスト開発マニュアル（984周記録・改訂版）

このZIPは、ユーザーが最初に提供した『ポートスキャナ自作ではじめるペネトレーションテスト』のサンプルZIPを**唯一の原典**とし、別に提供されたSNAKE開発マニュアルのレイアウトを参考に制作した日本語教材です。新しい成果物として作った `portfolio_lab/` 以下のPythonは原典ソースではありません。技術的に可能なこと、試験で実証したこと、まだ検証していないことを区別してお読みください。

## 最初に開くもの

`portscanner_pentest_development_manual_v984_20261117.html` をブラウザで開きます。HTMLは単体で表示可能です。ダークテーマ、目次、検索、工程チェック、コードコピー、文字サイズ変更、スマートフォン用ナビゲーションを備えています。HTML自体のためにWebサーバーやインターネット接続は不要です。

ZIPには3つの学習ルートがあります。どれを学んでいるかで、実行ディレクトリと扱うファイルが変わります。

1. **原典の再現**：43ファイル・946行を107工程で段階的に編集します。`original_source.zip` が基準です。古い脆弱な環境・危険なサンプルを安易に実行しないでください。
2. **既存の転職用見本**：`portfolio_lab/scanner.py`、`tests/test_scanner.py`、CI設定の237行を19工程で理解します。Pythonの標準ライブラリだけで動作し、既定で自分のloopbackだけを検査します。
3. **独立した発展機能**：`portfolio_lab/report_diff.py` と `tests/test_report_diff.py` の513行を10工程で交互に作り、保存済みJSONを**ネットワーク通信なし**で比較します。

## 1. ZIPを展開する

```sh
mkdir -p ~/Documents/portscanner-study
cd ~/Documents/portscanner-study
unzip /path/to/portscanner_pentest_manual_v984_20261117.zip
ls -la
```

`/path/to/...` は実際の保存先へ変更してください。`unzip` がない場合は `python3 -m zipfile -e ZIPファイル名 展開先フォルダ` を利用できます。展開後に、`original_source.zip`、HTML、`portfolio_lab/`、`tools/`、`tests/` が存在する場所を「展開先ルート」と呼びます。プロジェクトのテストコマンドは、ここか `portfolio_lab/` で実行するものに分かれます。`pwd` で現在地を確認してください。

## 2. 原典の43ファイルを自分で入力する

展開先ルートで次を実行します。

```sh
python3 tools/prepare_workspace.py
```

`learning_workspace/pentest-starting-with-port-scanner-main/` に、原典の編集対象を空ファイルとして準備します。既存の同名フォルダを勝手に上書きしない仕様です。HTMLの「構成と編集順序」から、各工程のファイル・元ソース行番号・追記位置を確認し、コードを少しずつ入力してください。ファイルを切り替えながら進め、すでに入力した行を不注意に消さないでください。全107工程の完了後、次で原典とのSHA-256を検証します。

```sh
python3 tools/check_workspace.py
```

**重要：** 完全一致することは、古いDockerイメージ、意図的に脆弱なLog4j/BIND/SSH環境、Go/Cの危険なコードが現在のOSで安全に実行できる保証ではありません。原典の一部に末尾改行のないファイルがあるため、エディタが改行を追加すると、処理上同じに見えてもバイト一致しないことがあります。危険な演習の実行は明示的な許可を受けた隔離環境に限ってください。

## 3. ポートフォリオ用スキャナを安全に試す

以下は**自分のPCのloopbackのみ**を使う例です。2つのターミナルを使います。まずターミナルAで `portfolio_lab/` に移動し、ローカルHTTPを起動します。

```sh
cd portfolio_lab
python3 -m http.server 8765 --bind 127.0.0.1
```

ターミナルBで同じディレクトリへ移動し、スキャンを実行します。

```sh
cd portfolio_lab
python3 scanner.py --help
python3 scanner.py --target 127.0.0.1 --ports 8765,8766 --timeout 0.5
python3 scanner.py --target 127.0.0.1 --ports 8765,8766 --output before.json
```

`--target` はIPv4リテラル、`--ports` は最大32件のカンマ区切りポート、`--timeout` は各接続の最大待機秒数（0.1〜3.0）、`--output` は新規作成するJSONです。8765が待ち受けていれば通常は `open`、8766に待受がなければ通常は `refused` です。これは脆弱性の発見ではなく、接続結果の観測です。どちらもOSやほかのプロセスの影響を受けます。

ターミナルAで `Ctrl+C` を押してサーバーを停止します。停止後、ターミナルBで次を実行します。

```sh
python3 scanner.py --target 127.0.0.1 --ports 8765,8766 --output after.json
python3 report_diff.py --before before.json --after after.json --output difference.json
python3 -m json.tool difference.json
```

`--before` と `--after` には、**同一IPv4・同一scope・同一ポート集合を、異なる時刻に測定したファイル**を指定してください。`--output difference.json` は比較結果を新規保存します。`state_changes` は状態が変わったポートの一覧、`unchanged_ports` は変化なしのポート数、`ports_checked` は比較対象のポート総数です。`errno` だけが変わっても状態変化としては数えません。

ファイルがすでに存在する場合、スキャナと比較ツールは上書きを拒否します。古い証拠を勝手に削除せず、別の出力ファイル名を選んでください。JSONには対象IPなどの情報が含まれるため、公開前に内容を確認してください。比較ツール自身はネットワーク通信を行いません。詳細は `portfolio_lab/docs/REPORT_DIFF_BUILD_GUIDE.md` を参照してください。

## 4. テストの実行と結果の判断

**展開先ルート**から教材の全体検証を実行します。別の場所に `cd` しているとパスが合いません。

```sh
python3 tests/verify_bundle.py
python3 tests/verify_portfolio.py
python3 tests/verify_report_diff_lesson.py
python3 tests/check_editorial_correctness.py
python3 tests/verify_usage_guide.py
python3 tests/verify_review_logs.py
python3 tests/test_local_socket_scanner.py
python3 tests/test_safe_usage.py
python3 tests/test_end_to_end_report_diff.py
```

教材の検証にはBeautifulSoup・lxmlが必要です。依存パッケージの対象バージョンは `tests/requirements.txt` を参照してください。原典のShell/Ruby構文検査にはそれぞれのツールが必要な場合があります。攻撃コードを実行する検証ではありません。

**`portfolio_lab/` 内**からPythonの全51件のテストを実行します。こちらはPython 3.11以降の標準ライブラリだけで動きます。

```sh
cd portfolio_lab
python3 --version
python3 -m unittest discover -s tests -v
```

旧来のスキャナが14件、新しい比較機能が30件です。Pythonの `unittest` が通っても、任意のOS・ネットワーク環境での安全な動作が証明されたわけではありません。テストは`127.0.0.1`の実ソケット、モックで再現した異常系、ローカルJSONの検査を含みます。

## 5. セキュリティエンジニア転職用の成果物にする

原典を書き写したものと、教材に付属する独立サンプルをそのまま提出したものは、**自分で設計した開発実績にはなりません**。具体的な作業手順はHTMLの「転職ポートフォリオ制作」と「発展実装：2回のTCP観測結果を比較する」、および `portfolio_lab/docs/PORTFOLIO_BUILD_GUIDE.md`、`REPORT_DIFF_BUILD_GUIDE.md` に記載しています。最低限、次の作業を自分で実施してください。

1. 何を観測・比較するのか要件と完了条件を自分の言葉で定義する。対象は自分のloopbackから始める。
2. 自分の作業用Gitリポジトリを作り、**見本から何を変更するか**をIssueやREADMEに記録する。
3. 自分で追加する機能に対して、失敗することを期待するテストを先に作り、失敗を保存する。
4. 変更したコードを実装し、正常系・異常系テスト・ローカル統合テストを再実行する。
5. 実行OS、Pythonバージョン、日時、コマンド、期待結果、実結果、終了コード、コミットSHAを記録する。
6. アーキテクチャ、脅威モデル、制限事項、エラー解釈、公開前のチェックリストを更新する。
7. GitHubに公開する前に、ステージしたファイルを `git diff --cached` で確認し、資格情報、実環境ログ、原典ZIP、脆弱なコンテナ、非公開データを除く。
8. READMEの実行手順だけで第三者が自分のPC上で再現できるかを確認する。
9. 面接で「学んだ部分」「自分で設計・改善した部分」「最初に失敗した点」「修正と証拠」「まだ保証できないこと」を分けて説明する。

原典READMEの「サンプルコード」には再利用条件の記載があります。参考元の表記だけで大量転載の許諾になるわけではありません。出典・帰属・再配布の条件を確認し、原典のZIPを丸ごとGitHubへ公開しないでください。`--authorized` は許可を自動取得する機能ではないため、第三者のネットワークに勝手にスキャンを行わないでください。

## 6. 960周監査の意味と実測の限界

今回の追加80周は、提供された880周版に対する**881〜920周（修正前40周）**と、今回の最終HTMLに対する**921〜960周（修正後40周）**です。各周は複数系統の機械的な照合を含みます。「80項目のチェックを1回ずつ実行して80周」と数えていません。

ただし、**累計960周は人間が全文を960回精読したという意味ではありません**。今回の厳格なJSON入力検証と行別解説の改訂、テストとブラウザでの実測は、反復自動監査とは別の活動です。

**実際に確認したこと：** 原典43ファイル・946行・107工程のバイト一致、従来の独立実装237行・19工程の一致、新設比較機能513行・10工程の一致、Python51件のユニット/統合テスト、ローカルTCPの開放→拒否の差分、PC1440pxとスマホ390pxの新章表示と主要操作。

**今回も未確認のこと：** 意図的に脆弱なDocker環境や攻撃コードの実行、Nmap→Rubyの全工程の実動作、ブラウザを本当に再読み込みした後のlocalStorage復元。ブラウザ検証環境がlocalhostへのページ移動を拒否したため、表示と操作はページ内容の直接読み込みで確認しています。未実測の機能を「検証済み」とは記載しません。

詳しい監査内容と修正履歴は `REVIEW_REPORT.txt`、`CHANGELOG.md`、`audit/REVIEW_ROUNDS_641_680.jsonl`、`audit/REVIEW_ROUNDS_681_720.jsonl`、`EDITORIAL_PATCHES_641_720.json` を参照してください。

## 7. 960周改訂版で追加された比較条件と例外処理

`report_diff.py` は前後の `timeout_seconds` も一致していることを要求します。`timestamp_utc` は `+00:00` のUTC時刻だけを受け付けます。`scope` は対象IPv4と整合している必要があります。手元のJSONの値を後から書き換えるのではなく、両スキャンを同じオプションで測定し直してください。

`portfolio_lab/docs/MEASUREMENT_COMPARABILITY_AND_EVIDENCE.md` に、loopbackだけで行う測定・異常系テスト・ハッシュとコミットを使った証拠管理・転職用ポートフォリオの作成手順を追加しています。新しいテスト内訳はscanner14件、比較ツール35件の合計51件です。

## 8. 960周改訂版：状態とerrnoの整合性

保存済みJSONの `state="open"` と `errno=0` は対応が必要です。`state="open", errno=111` や `state="refused", errno=0` の矛盾を `report_diff.py` が拒否し、3件の回帰テストを追加しました。見本は全51件のPythonテストが通過する設計です。どのOSでも111が拒否の番号だと仮定しません。

完成後の運用・検証・GitHub公開・面接向け成果物の制作手順は `portfolio_lab/docs/PORTFOLIO_OPERATOR_MANUAL.md` を参照してください。**見本コードをそのまま本人の制作実績と称さず**、本人が実装した差分と自分の環境で取得した証拠を残してください。

## 9. 960周改訂版：厳格なJSONと新版ファイル名

本教材のZIP・メインHTMLには、別プロジェクト名を連想させるファイル名を使用しません。今後のリリースも題材の「ポートスキャナ」を基準とした名前で統一します。過去版の監査ログには旧版の基準ハッシュを保存していますが、現在開くべきHTMLはルートの **portscanner_pentest_development_manual_v984_20261117.html** です。

Python標準の `json.loads()` は既定で `NaN`、`Infinity`、`-Infinity` を受け取りますが、標準JSONの正しい数値ではありません。新版 `report_diff.py` は `parse_constant` にエラー関数を指定して拒否し、不正な余分キーも処理へ渡しません。また `1e400` のように文法上正しい指数表記が浮動小数点の無限大になる場合は `math.isfinite()` で拒否します。

検証は `cd portfolio_lab && python3 -m unittest discover -s tests -v` で51件。実際に何件通過したかと実行日時・OS・Pythonバージョン・Gitコミット番号を自分の証拠として記録してください。付属の実装は学習見本であり、自作の実装作業と区別してください。

## 10. 960周改訂：JSON 1件を単独検証する方法

`portfolio_lab/` へ移動し、`python3 report_diff.py --validate before.json` を実行します。形式に問題がなければ `VALID: before.json (target=127.0.0.1, ports=2)` のような表示と終了コード0が得られます。不正な入力は終了コード2です。`--validate` と `--before` / `--after` / `--output` は組み合わせられません。

新版はJSONの最上位に5キー、各結果行に3キーの**完全一致**を要求します。余分なフィールドを拒否し、不足しているフィールドも具体的に報告します。これは入力の妥当性検査であり、データが未改変・実測済みだという保証ではありません。

**詳しい実行手順、エラー調査、転職用証拠の作り方**は `portfolio_lab/docs/VALIDATION_AND_PORTFOLIO_EVIDENCE_V960.md` を参照してください。原典43ファイル・946行・107工程は変更していません。スキャナの独立見本237行・19工程も維持し、レポート比較見本513行・10工程へ更新しました。Pythonテストは51件です。

追加監査ログは `audit/REVIEW_ROUNDS_881_920.jsonl` と `audit/REVIEW_ROUNDS_921_960.jsonl`、確認には `python3 tests/verify_review_logs_960.py` を使用します。全体の精査・制限事項は `REVIEW_REPORT.txt` に記載しています。


## 11. 984周改訂：JSON文字コードの厳格化と回帰試験

前回版の `report_diff.py` はUTF-8 JSONを前提としていましたが、`json.loads(raw)` にバイト列を直接渡したため、PythonがUTF-16・UTF-32・BOM付きUTF-8を自動判定して受理していました。これは入力仕様と実装の不一致です。今回 `raw.decode("utf-8")` を明示的に挿入し、`json.loads(text)` へ変更しました。仕様は **UTF-8（BOMなし）** です。文字コードが異なる場合や壊れたバイト列は、利用者に `invalid UTF-8 JSON` のエラーを返します。

変更したのは比較ツールの入力処理と異常系テストです。**原典43ファイルには変更を加えていません。** 独立スキャナは237行、比較ツール教材は513行、Pythonテストは51件です。詳しい操作方法は `portfolio_lab/docs/UTF8_JSON_INPUT_POLICY_V984.md` に記載しています。

`cd portfolio_lab` の後、`python3 -m unittest discover -s tests -v` と `python3 report_diff.py --help` を実行します。標準のスキャナ出力を `--validate` で検査し、UTF-16/BOM付き入力については新設テストで拒否結果を確認できます。手元のJSONを勝手に上書きしないことと、入力検証は観測の真正性を証明しないことを区別してください。

今回の追加監査は **961〜984周の24回の反復自動検査**です。各周は複数項目を繰り返し検証します。24回の人手による全文精読とは異なり、別途ソースの意味を読み直して上記の不一致を修正しています。
