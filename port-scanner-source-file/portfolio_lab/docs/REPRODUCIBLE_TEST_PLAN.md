# 再現できる試験計画とログの残し方

## 1. テスト環境の固定

実施日時（JST/UTCを明記）、Pythonバージョン、`python3 --version`、OSとカーネル、Gitコミット短縮SHA、作業ディレクトリを記録する。例示値は実測値に書き換える。ネットワーク許可が必要な試験は、事前に所有者・対象・ポート・日時・停止条件を書いた許可記録がない限り実施しない。この見本は127.0.0.1で完結できる。

## 2. 試験ケース

| ID | 操作または関数 | 期待結果 | 検証方法 |
|---|---|---|---|
| T01 | `parse_ports('22,80,443')` | 整数リストを返す | unittest |
| T02 | `parse_ports('22,22')` | 重複を拒否 | unittest |
| T03 | `parse_ports('0')`, `'65536'` | 有効範囲外を拒否 | unittest |
| T04 | `check_scope('8.8.8.8',None,False)` | 対象範囲外で停止しネットワーク未接続 | 別プロセスのCLIテスト |
| T05 | `check_scope('192.168.56.3','192.168.56.0/24',True)` | 明示範囲のみ許可 | unittest。第三者への使用許可は別途必要 |
| T06 | loopbackでTCP待受あり | 通常 `open` と0が得られる | 一時的な実ソケット |
| T07 | loopbackで待受なし | 通常 `refused` | 一時的な実ソケット。OSの差に注意 |
| T08 | `connect_ex` が `TimeoutError()` を送出 | `state='timeout'` とETIMEDOUT | `patch` によるモック。外部通信しない |
| T09 | `connect_ex` がENETUNREACHを返す | `state='unreachable'` | `patch` によるモック。外部通信しない |
| T10 | `--output` と同じパスで2回実行 | 2回目は終了コード2、既存ファイルの中身は維持 | CLIからの統合テスト |
| T11 | `--target 8.8.8.8` | スコープエラーで停止 | CLIテスト。外部通信しない |

現在の全14件のスキャナ用unittestメソッドは複数の境界値を内部で確認するため、上表の試験ID数と一致しない。テストクラスの各メソッドも確認し、使っていない試験を「通過」と書かない。

## 3. 実行コマンド

```sh
# 展開先ルートから
cd portfolio_lab
python3 --version
python3 -m unittest discover -s tests -v
python3 scanner.py --help
python3 scanner.py --target 127.0.0.1 --ports 8765,8766 --timeout 0.5
```

コマンドと出力は同じファイルに日付・OS・実行ディレクトリとともに残す。テスト成功のスクリーンショットだけでは、リポジトリのどのコミットの結果なのかを後から確認できないのでコミット情報も必須。

## 4. 失敗を含む報告書の実例フォーマット

```text
Test ID: T08
Date/time: <実測日時・タイムゾーン>
OS / Python: <実測環境>
Commit: <実際のコミットSHA>
Command: python3 -m unittest discover -s tests -v
Expected: TimeoutError() => timeout / errno.ETIMEDOUT
Actual: <実際の出力を転記>
Judgement: PASS / FAIL / BLOCKED
Notes: unittest.mock.patchでsocket.socketを置換したため外部接続なし
Limitations: 実際のルータやファイアウォールが同じerrnoを返す証明ではない
```

## 5. 部分的にしか検証していない結果をどう書くか

`unittest` が通ったことはCI・テスト対象の動作を示すだけです。権限のある全ネットワークで再現する証拠にはなりません。socketタイムアウトの処理はモックによる単体テストと、loopback上の接続成功・拒否の統合テストに分けて報告します。OSにより `ETIMEDOUT` 等の整数が異なるので、意味のある定数名も併記します。

## 6. 実環境のログを公開しない

JSONには対象IP、日時、ポート情報が含まれます。公開先でIPやホストが匿名化されているかを確認し、個人環境のパス、メール、機器名、管理者画面は含めません。証拠ファイルをGitに追加する前に `git diff --cached` で実際の変更内容を見ます。

## 7. JSON差分比較ツールの追加検証（800周改訂版）

追加の `test_report_diff.py` は35件のテストで構成されます。次のIDはそのうちの代表例です。各結果は実行日時・Pythonバージョン・コミットSHAとセットで記録してください。

| ID | 操作 | 期待結果 | 方法 |
|---|---|---|---|
| D01 | 正常な2ポートのJSONを読む | 2ポートの辞書が得られる | 一時JSONファイル |
| D02 | `results` に同じportを2行 | 重複を拒否 | 一時JSONファイル |
| D03 | `state` を `filtered` や配列へ変更 | 受理しない | 一時JSONファイル |
| D04 | 重複JSONキー | 読込を拒否 | object_pairs_hook |
| D05 | IPv4を数値に変更 | 文字列以外を拒否 | 一時JSONファイル |
| D06 | UTCオフセット欠落 | タイムゾーン必須 | 一時JSONファイル |
| D07 | NaNまたは1MiB超の入力 | 不正として拒否 | 一時JSONファイル |
| D08 | `open → refused` | 変化したポートがstate_changesに入る | 2レポート辞書 |
| D09 | 対象IP・scope・ポート集合が異なる | 差分計算を中止 | 2レポート辞書 |
| D10 | 前後日時の逆転 | 比較を拒否 | 2レポート辞書 |
| D11 | 同じ --output を2回実行 | 2回目は終了コード2、元の内容は維持 | CLI subprocess |
| D12 | 同一ファイルを前後に指定 | 比較を拒否 | CLI subprocess |

**試験の意味を限定すること：** D01〜D12が通過しても、過去のJSONが改ざんされていないことや、TCPの応答が現実のネットワーク全体で一致することは証明されません。


## 8. 比較可能性の追加回帰テスト（800周改訂版）

| ID | 試験名 | 期待結果 | 理由 |
|---|---|---|---|
| S12 | `test_noncanonical_cidr_returns_valueerror` | `192.168.56.3/24` 形式を入力エラーとして返す | `IPv4Network(..., strict=True)` は通常のValueErrorも送出する |
| D13 | `test_non_utc_offset_is_rejected` | `timestamp_utc` の `+09:00` を拒否 | キー名のUTC契約に一致させる |
| D14 | `test_loopback_scope_cannot_claim_private_host` | loopback範囲と192.168.56.7の矛盾を拒否 | JSONの宣言scopeをそのまま信頼しない |
| D15 | `test_rejects_public_or_noncanonical_lab_scope` | 公開/24とホスト部付きCIDRを拒否 | 原典の許可範囲と入力形式を揃える |
| D16 | `test_accepts_declared_private_lab_scope` | 正規のプライベート/24を受理 | 正常なラボ入力を壊していないことを確認 |
| D17 | `test_mismatched_timeout_is_rejected` | `0.5`秒と`3.0`秒を比較させない | 同一条件の測定ではないため |
| D18 | `test_comparison_preserves_conditions` | 比較JSONにscopeとtimeout値が残る | 検査前提を後で追跡できるようにする |

試験名は付属の`tests/`に実在するメソッドに対応しています。**表の試験ID数とunittestのメソッド総数は異なります**。実際の49件の内訳はscanner14件、report_diff30件です。

## 9. 800周改訂版：入力状態とerrnoの一致（3件の追加テスト）

| ID | 実在するテスト名 | 期待結果 |
|---|---|---|
| D19 | `test_open_with_nonzero_errno_is_rejected` | `state=open` と `errno=111` の組を拒否 |
| D20 | `test_non_open_with_zero_errno_is_rejected` | `state=refused` と `errno=0` の組を拒否 |
| D21 | `test_nonzero_unknown_errno_is_retained` | `state=error_or_unknown` と非ゼロ値999を保持 |

各テストは一時JSONを使用し、ネットワークアクセスなしで検査します。レポートの値を人為的に編集したテストであり、実際に観測された通信の正しさは証明しません。スキャナ14件、比較ツール30件、合計49件。
