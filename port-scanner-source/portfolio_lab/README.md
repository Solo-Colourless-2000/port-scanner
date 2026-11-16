# Scope-limited TCP Connect Audit (portfolio learning example)

このフォルダは、ユーザーから提供された『ポートスキャナ自作ではじめるペネトレーションテスト』の学習テーマを踏まえ、新規に作成した**別実装の見本**です。原典のコードを改変・転載した完成作品ではありません。採用応募時に、**この見本を自分が設計・実装したものと偽って提出しない**でください。自分で要件を決め、機能を追加し、失敗事例と検証記録を作るための出発点です。

## 目的と範囲

* 対象はTCPの「接続を試す」手法です。SYNスキャンでも脆弱性診断でもありません。
* 初期設定は **127.0.0.0/8（loopback）限定**、最大32ポート、1回の通信タイムアウト0.1〜3秒、直列実行です。
* `--scope-cidr` と `--authorized` の両方を指定した場合だけ、/24またはそれより狭いRFC1918ネットワーク内のIPv4を検査できます。この2つのオプションは許可を自動取得するものではありません。利用前に**対象の所有者・管理者から具体的な許可**を得てください。
* `refused` はTCP接続拒否、`timeout` は時間切れ、`unreachable` は到達不能などのOSエラーです。「filtered」や「脆弱」と自動断定しません。
* レポートの結果には実行時のOSのerrnoが入ります。値はOSや条件に依存するため、固定の数字だと決めつけないでください。

## 必要な環境

Python 3.11以降、標準ライブラリのみ。Arch LinuxまたはLinux MintなどのLinuxを想定しています。外部ライブラリは不要です。

```sh
python3 --version
cd portfolio_lab
python3 -m unittest discover -s tests -v
```

## ローカル実演（ターミナル2枚）

**ターミナルA**：自分のPCのloopback上だけでHTTPサーバーを起動します。

```sh
python3 -m http.server 8765 --bind 127.0.0.1
```

**ターミナルB**：検査します。

```sh
python3 scanner.py --target 127.0.0.1 --ports 8765,8766 --timeout 0.5
python3 scanner.py --target 127.0.0.1 --ports 8765,8766 --output report-local.json
```

8765が待受中なら通常 `open`、8766にリスナーがなければ通常 `refused` です。他のプロセスが8766を使用している場合、結果は変わります。ターミナルAで `Ctrl+C` を押して終了し、再度スキャンして前後の差を確認してください。`report-local.json` が既にある場合は、誤上書きを避けるため保存に失敗します。別名にするか、内容を確認してから削除してください。

**事前に許可された隔離ラボのみ**で使う追加例：

```sh
python3 scanner.py --target 192.168.56.10 --ports 22,80 --scope-cidr 192.168.56.0/24 --authorized
```

IPアドレスやCIDRを自分の許可済みラボの値へ置き換えてください。外部公開サーバーや第三者ネットワークには使用しないでください。

## ソース構成

- `scanner.py`：入力検証、許可スコープの制限、TCP Connect結果の分類、JSONレポート出力。
- `tests/test_scanner.py`：ポート入力、スコープ逸脱拒否、実際のloopback待受／拒否のテスト。
- `.github/workflows/tests.yml`：push・PRでPython unittestを実行する例。導入時は使用するActionsのバージョン・権限を自分で再点検してください。
- `docs/`: 設計判断、リスク整理、検査証拠、公開・応募前チェックリスト。
- `evidence/`: 個人が実施した検査結果を保存する場所。サンプルには個人情報を含めないでください。

## 想定される改善課題（自分の成果として取り組む）

1. 入力の境界値・例外処理をさらにテストする。
2. 結果のJSON Schemaまたは検証規約を定義する。
3. 結果の差分比較やCSV出力を独立モジュールとして追加する。
4. OSごとのerrnoに起因する差を試験し、断定的な表示を避ける。
5. 最小権限と対象制御の設計意図を図にする。
6. 導入・再現・終了が第三者にもできるREADMEへ更新する。

**出典・区別：** 学習テーマおよび比較対象は、ユーザー提供のオライリー・ジャパン公式サンプルZIP。`scanner.py` はこのマニュアル作成用の新規サンプルです。書籍サポートリポジトリREADMEにはコードの利用条件があるため、サンプルを大量転載する場合は必ず原文を確認してください。外部サービスの利用規約・提出先の守秘義務も別途確認してください。


## タイムアウト例外の修正と回帰テスト

`connect_ex()` が失敗をエラー番号で返す場合だけでなく、Pythonの `TimeoutError` が直接発生する場合もあります。`TimeoutError` は `OSError` の一種なので先に捕捉し、`errno.ETIMEDOUT` として結果に記録するようにしました。`ProbeErrorTests` にモックによる2件の回帰テストを追加し、当時の13件を実行できます。対象IPへ通信しなくても異常系が検証できます。

詳細は `docs/PROTOCOL_AND_ERROR_GUIDE.md` を参照してください。

## 就職・転職ポートフォリオとして進める

学習済みの見本をそのまま提出するのではなく、`docs/GIT_AND_PUBLICATION_STEPS.md` の手順で自分が加えた差分を記録し、`docs/INTERVIEW_GUIDE.md` で実装範囲・検査・限界の説明を準備してください。検査証拠を置く場合は `evidence/README.md` の公開ルールを確認してください。

詳細な8日間の開発手順は `docs/PORTFOLIO_BUILD_GUIDE.md`、試験IDと証拠の保存ルールは `docs/REPRODUCIBLE_TEST_PLAN.md` にまとめました。自作の追加機能とそのテストを実際に実装してから成果物として提出してください。

## 独立したオフラインJSONレポート比較

`report_diff.py` は今回の教材で追加した**新しい独立見本**です。元のスキャナから取得した２つのJSONだけを読み、異なるポート状態を見つけます。比較処理はネットワーク接続を行いません。

```sh
cd portfolio_lab
python3 -m unittest discover -s tests -v
python3 report_diff.py --help
python3 report_diff.py --before before.json --after after.json --output difference.json
```

`before.json` と `after.json` は同じ `scanner.py` から、同一IPv4・同一スコープ・同一ポート番号集合で、順に保存してください。差分ファイルは新規作成だけを許し、既存の `difference.json` は上書きしません。元のJSONをGitHubへそのままコミットしないでください。

追加教材はHTMLの「発展実装：2回のTCP観測結果を比較する」の10工程・513行、詳細操作は `docs/REPORT_DIFF_BUILD_GUIDE.md` です。既存14件と比較37件のテストで**合計51件**です。コードをコピーしただけの実績を自作と称しないでください。


## 比較条件の一貫性と証拠

`report_diff.py` はターゲット・宣言CIDR・ポート集合だけでなく `timeout_seconds` が一致するかを確認します。`timestamp_utc` はUTC、ループバックとラボCIDRの記載は対象IPv4との整合が必要です。詳細は [`docs/MEASUREMENT_COMPARABILITY_AND_EVIDENCE.md`](docs/MEASUREMENT_COMPARABILITY_AND_EVIDENCE.md) を参照してください。合計51件のテストを `python3 -m unittest discover -s tests -v` で実行できます。

## state/errno入力の矛盾を拒否する

`report_diff.py` は `open` なのに errno が0以外、`open`以外なのに errno が0である入力を拒否します。後者も含めて非ゼロの失敗番号をOS共通の定数と誤認しないよう、異常系2件と正常系1件のテストを追加しました。合計51件。運用例と転職応募用の本人実装・テスト証拠の作り方は [`docs/PORTFOLIO_OPERATOR_MANUAL.md`](docs/PORTFOLIO_OPERATOR_MANUAL.md) を参照してください。


## JSON単独検証と公開用の検証証拠（追加学習）

```sh
cd portfolio_lab
python3 report_diff.py --validate before.json
python3 report_diff.py --validate after.json
python3 report_diff.py --before before.json --after after.json --output difference.json
```

`--validate` は入力JSONの必須フィールド・余分なフィールド・型・範囲を確認します。正常なら `VALID:` と終了コード0、不正なら終了コード2です。オフライン検証であり実際にTCP通信しません。**真正性の証明ではない**点を README・面接で説明してください。詳しい作業は `docs/VALIDATION_AND_EVIDENCE.md` を参照してください。


### JSON文字コードの検証

比較ツールはUTF-8（BOMなし）だけを受理します。`json.loads(bytes)`が自動判定するUTF-16/32/BOM付き入力を、decode("utf-8")→json.loads(text)の順序により拒否します。詳細と検証方法は `docs/UTF8_JSON_INPUT_POLICY.md` を参照してください。
