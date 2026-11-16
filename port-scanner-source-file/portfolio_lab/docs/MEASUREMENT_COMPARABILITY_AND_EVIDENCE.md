# TCP Connect観測の比較条件・異常入力・転職用証拠の作成

この文書は、ユーザー提供の書籍サンプルを変更したものではなく、本教材が新規に作った `portfolio_lab/` の実装・テストに対応する学習ガイドです。以下のコマンドは**自分のPCの127.0.0.1**だけで実施します。入力JSONの`scope`は自称の文字列であり、第三者のスキャンを許可する仕組みではありません。

## 1. なぜ「ポートが変化した」だけで結論を出せないのか

`open` は指定先のTCP接続が成立した観測結果、`refused` は拒否された観測結果です。タイムアウトの秒数が変われば、同じポートでも`timeout`に分類される可能性が変わります。したがって、レポート比較では対象IPv4、scope、ポート集合**およびtimeout_secondsを同一**とし、異なる時刻に得た結果だけを比較します。`state_changes`が空でも、脆弱性がないこと、サービスが稼働していないこと、ファイアウォールが正しいことは証明しません。

レポートの`timestamp_utc`はUTC時刻の契約です。`2026-11-16T10:00:00+00:00` は受理し、`2026-11-16T19:00:00+09:00` は**同一瞬間を指していても**入力契約に反するため拒否します。後者を単純に`+00:00`へ書き換えると時刻が9時間ずれるので、証拠ファイルの手編集で解決しないでください。

## 2. 安全なローカル実演（3つの端末作業）

以下の各コマンドは配布ZIP展開後の `portfolio_lab/` 内で実行します。`pwd`で現在位置を確認してください。Python3以外のネットワーク検査ツールは不要です。

**端末A**：一時HTTPサーバーをloopbackだけに公開します。

```sh
python3 -m http.server 8765 --bind 127.0.0.1
```

`-m`はモジュール起動、`8765`は待受ポート、`--bind 127.0.0.1`は接続をloopbackへ限定します。失敗時は`ss -ltn`で8765の使用状況を確認します。既存プロセスを無理に停止しないでください。

**端末B**：同じポート集合、同じタイムアウトで1回目を観測します。

```sh
python3 scanner.py --target 127.0.0.1 --ports 8765,8766 --timeout 0.5 --output before.json
python3 -m json.tool before.json
```

`--target`が対象IPv4、`--ports`がカンマ区切りのTCPポート、`--timeout 0.5`が各TCP接続の制限秒数、`--output`は**上書きを拒否して新規作成**するJSONのパスです。`before.json`が既にある場合は別の名前を選んでください。公開インターネットに接続する操作ではありません。

**端末A**で`Ctrl+C`を押して停止します。**端末B**で以下を実行します。

```sh
python3 scanner.py --target 127.0.0.1 --ports 8765,8766 --timeout 0.5 --output after.json
python3 report_diff.py --before before.json --after after.json --output difference.json
python3 -m json.tool difference.json
```

予期する観測例は8765が`open`→`refused`です。ただし環境・ほかのプロセス・OSの状態次第で異なります。差分JSONには`target`、`scope`、`timeout_seconds`、観測日時、`ports_checked`、`state_changes`、`unchanged_ports`が入ります。過去のファイル名やJSONを削除・上書きせず、実行時刻とコミットSHAとともに記録してください。

## 3. 比較条件の不一致を再現する（ネットワーク接続不要）

ユニットテストを使えば、実際のルータやファイアウォールに接続せず「異なるタイムアウトを拒否する」「UTC以外の時差を拒否する」「scopeの宣言矛盾を拒否する」挙動を再現できます。

```sh
python3 -m unittest tests.test_report_diff.ComparisonTests.test_mismatched_timeout_is_rejected -v
python3 -m unittest tests.test_report_diff.ReportReadingTests.test_non_utc_offset_is_rejected -v
python3 -m unittest tests.test_report_diff.ReportReadingTests.test_loopback_scope_cannot_claim_private_host -v
python3 -m unittest tests.test_scanner.ScopeTests.test_noncanonical_cidr_returns_valueerror -v
python3 -m unittest discover -s tests -v
```

ここでの`python3 -m unittest`はPython標準のテスト実行機構、`-v`は各テスト名と結果を表示する指定です。`tests.test_report_diff.ComparisonTests.test_mismatched_timeout_is_rejected`は`tests`モジュール内のクラス名とテストメソッド名を指定します。テストが通った結果と、実通信で結果が変わった事実を混同しないでください。

## 4. `IPv4Network(..., strict=True)` と例外捕捉の注意

`IPv4Network('192.168.56.0/24', strict=True)`はネットワークアドレスに揃ったCIDRです。一方、`192.168.56.3/24`はホスト部が残った記法です。環境によってはこのケースで通常の`ValueError`が送出されるため、`AddressValueError`と`NetmaskValueError`だけを捕捉しても足りません。スキャナの`check_scope`と比較ツールの`read_report`で`except ValueError as exc:`を採用し、元の例外を連鎖させて利用者に入力エラーを提示します。

ただし、**例外の捕捉が適切であることと、ネットワーク上の操作を許可されていることは別問題**です。`--authorized`は利用者の宣言を受け取るだけで、ネットワーク所有者から許可を取得する機能ではありません。

## 5. 証拠の真正性について正確に説明する

```sh
python3 --version
uname -a
git status --short
git rev-parse HEAD
sha256sum before.json after.json difference.json
python3 -m unittest discover -s tests -v
```

`sha256sum`は現在のファイル内容からハッシュを計算します。**ファイルが後から変わればハッシュも変わる**という確認には使えますが、原則としてハッシュだけで「誰がいつ取得したか」「実際にスキャンしたか」は証明できません。実測の出力、測定操作の履歴、日時（タイムゾーン付き）、テスト結果、ソースのコミットSHA、許可範囲と停止条件を同じ記録にまとめます。公開前には実IPや機密ログを含めないか再確認してください。

## 6. 採用担当者へ見せる改善実績の作り方

1. **要件**：同じポートでもタイムアウト値が異なれば比較しない、と決めた理由を数行で書きます。
2. **失敗するテスト**：元コードに`test_mismatched_timeout_is_rejected`を追加し、修正前には失敗したことを自分の環境で確認・記録します。教材に収録されたテスト結果を自分の実測値に転記してはいけません。
3. **修正**：比較関数の一致判定と出力フィールドを実装し、CLIまで動作を確認します。
4. **異常系**：UTCでない日時、不正CIDR、scope矛盾、上書き拒否のテストを走らせます。
5. **再現性**：環境情報、正確なコマンド、期待値・実測値、コミットSHAを記録し、第三者がREADMEだけで追試できるか試します。
6. **限界**：JSONは利用者が作り変えられること、errnoの数値はOSにより異なること、スキャン結果から脆弱性を断定できないことを明示します。
7. **公開**：元の書籍サンプルや未許可のコードを新規リポジトリに混ぜず、自分で設計した差分、出典、テスト証拠を明示します。

### 記録のひな型

```text
Test ID:
Date and timezone:
OS / kernel / Python:
Git commit SHA:
Authorised scope (owned loopback only in this lab):
Command and cwd:
Expected state / rejection:
Actual output / exit code (measured, not copied from this guide):
Evidence file name and SHA-256:
Changed source lines and reason:
Limitations and next improvements:
```

このひな型の空欄は自分の測定値で埋めてください。先に作成した教材の実行ログを改変して「自分の成果」にするものではありません。

**参照**：本配布ZIPの`portfolio_lab/scanner.py`、`report_diff.py`、`tests/test_scanner.py`、`tests/test_report_diff.py`、および添付原典ZIP。検査した範囲と未実測の範囲は`REVIEW_REPORT.txt`で区別します。
