# 追加ポートフォリオ教材：TCP観測結果の差分比較

## 1. 実装の位置付けと成果物

この章で扱う `report_diff.py` と `tests/test_report_diff.py` は、ユーザー提供の原典ZIPには含まれない、**今回の教材のための別実装の見本**です。原典ソースを直接変更したものではありません。また、ここに含めた実装をコピーしただけで「自分の独自開発実績」とは呼べません。自分で要件を追加し、テストの失敗・修正・再検証を記録して初めて、面接で説明できる開発経験になります。

入力は `scanner.py` が生成したJSONファイル2つ。出力は変化したTCP状態の一覧です。`report_diff.py` 自体は `socket` をimportしないので、ファイル比較の実行時に**ネットワーク接続を開始しません**。ただし、入力JSONはIPアドレスなどの情報を含むため、公開前に内容を確認してください。

## 2. 入力レポートの構造と各フィールド

`scanner.py` は次の形式でJSONを生成します。以下は**構造の例**であり、実際に観測した結果の証拠ではありません。

```json
{
  "timestamp_utc": "2026-11-16T10:00:00+00:00",
  "target": "127.0.0.1",
  "scope": "127.0.0.0/8 (loopback only)",
  "timeout_seconds": 0.5,
  "results": [
    {"port": 8765, "state": "open", "errno": 0},
    {"port": 8766, "state": "refused", "errno": 111}
  ]
}
```

`timestamp_utc` はスキャンが開始する時点で付けるUTC日時です。タイムゾーン指定のない時刻は比較できないため拒否します。`target` はIPv4リテラル文字列、`scope` は宣言された範囲の説明、`timeout_seconds` は接続の待ち時間、`results` はポートごとの観測です。`errno` の具体的な整数はOSに依存します。上の `111` をすべての環境で `ECONNREFUSED` と決めつけないでください。

`state` の `open` はTCP接続成功、`refused` は接続拒否、`timeout` は時間切れ、`unreachable` は到達不能、`error_or_unknown` はその他のOSエラー等を意味します。**どれもサービスの脆弱性判定ではありません。**

## 3. 新規開発を段階的に進める準備

展開したZIPのルートで、まず完成見本のコードを閲覧し、HTMLマニュアルの「発展実装：2回のTCP観測結果を比較する」を開きます。以下は空の自作練習用ファイルを作る例です。

```sh
mkdir -p my_report_diff/tests
cd my_report_diff
touch report_diff.py tests/test_report_diff.py
python3 --version
```

`mkdir -p` は必要な親ディレクトリを作り、`touch` は既存のファイルを削除せずに存在を確保します。`cd my_report_diff` 後は、ここがテスト実行と相対パスの基準です。HTMLの10工程に従い、1回の工程で示された行範囲だけ入力してください。先に `report_diff.py`、次に `tests/test_report_diff.py`、また `report_diff.py` と、実際の開発のように往復します。工程の途中では依存関数が未完成のためテストが失敗する場合があります。完成後にまとめて全49件のテストを実行してください。

## 4. 完成版の使用方法：ローカル環境だけを使用

`portfolio_lab/` に移動し、同じフォルダでPythonを起動します。`report_diff.py` は独立したコマンドですが、入力JSONを用意するには先にスキャナを実行します。

**端末A：ローカルHTTPサーバーを起動**

```sh
python3 -m http.server 8765 --bind 127.0.0.1
```

`-m http.server` はPython標準のHTTPサーバーモジュールを使う指定、`8765` は待ち受けポート、`--bind 127.0.0.1` は自分のPCのloopbackアドレスだけにバインドする指定です。もし8765が使用中なら、`ss -ltn` で確認し、空いているポートに変更します。`Ctrl+C` で終了できます。

**端末B：待ち受け中の結果を保存**

```sh
cd portfolio_lab
python3 scanner.py --target 127.0.0.1 --ports 8765,8766 --output before.json
```

`--target` は対象IPv4、`--ports` はカンマ区切りのTCPポート、`--output` は新規作成するJSONファイル名です。入力に応じた結果が表示されます。`before.json` が既にある場合は、既存の証拠を保護するため終了コード2で拒否します。勝手に削除する前に内容を確認してください。

**端末Aで `Ctrl+C` を押してサーバーを止め、端末Bで次を実行**

```sh
python3 scanner.py --target 127.0.0.1 --ports 8765,8766 --output after.json
python3 report_diff.py --before before.json --after after.json --output difference.json
python3 -m json.tool difference.json
```

`--before` は変更前レポートのパス、`--after` は変更後レポートのパス、`--output` は差分結果を新規保存する場所です。`-m json.tool` はJSONを読みやすく整形して表示するPython標準モジュールです。2回の測定は同じIP、同じscope、同じポート集合で、日時が前後の順になる必要があります。一般に8765が `open → refused` へ変わりますが、ほかのプロセスやOSの影響で変化しないこともあります。

出力JSONの `state_changes` は変わったポートと前後の状態、`unchanged_ports` は変化なしのポート数、`ports_checked` は比較したポート総数です。**errnoの整数が変わっただけでは状態変化には含めません**。これは比較対象をTCP状態に限定した設計判断です。

## 5. エラーに遭遇したとき

| 症状・メッセージ | 主な原因 | 調べること |
|---|---|---|
| `No such file or directory` | `cd` の位置かファイル名が違う | `pwd`, `ls`, `ls -l *.json` を確認 |
| `ModuleNotFoundError: report_diff` | 別ディレクトリでテスト実行 | `portfolio_lab/` へ移動してから `python3 -m unittest discover -s tests -v` |
| `invalid UTF-8 JSON` | 入力がJSONとして不正 | `python3 -m json.tool before.json` で単独検証 |
| `duplicate JSON key` | 同一キーがJSON内に重複 | 手入力・自動生成元を調査し、報告書の出典を確認 |
| `invalid state` | 許可されない状態名や型 | `open/refused/timeout/unreachable/error_or_unknown` のいずれかを確認 |
| `target ...` | IP文字列がない、IPv6、数値、形式違い | `scanner.py` から再生成し、文字列IPv4を使う |
| `timestamp_utc ...` | 時差情報がない、不正日時 | `+00:00` 等のオフセットを含める |
| `outside scanner limits` | timeout_secondsが0.1〜3秒外 | 元スキャナがどの値で動いたかを確認 |
| `same port set` | 比較したポート集合が違う | 両スキャンで `--ports` を揃える |
| `different declared scan scopes` | 申告スコープ文字列が違う | 許可範囲・入力コマンドの履歴を確認 |
| `before must have an earlier timestamp` | ファイルが逆、同時刻 | 前後ファイルと取得時刻を見直す |
| `File exists` や上書き失敗 | difference.jsonが既に存在 | 新しい出力名へ変更、証拠を保存してから整理 |
| 変化が表示されない | 終了前後で状態が同じ、別プロセスが待受 | `ss -ltn`, `ps`, 実行日時と端末Aの停止を確認 |

## 6. テストの実行と観察

```sh
cd portfolio_lab
python3 -m unittest discover -s tests -v
python3 report_diff.py --help
```

現在の学習見本では、従来の14テストに、比較機能の35テストを追加し、合計49件です。`test_report_diff.py` はファイルを一時ディレクトリに作り、不正JSON、重複キー、重複ポート、bool型のポート、タイムゾーンなしの日時、NaN、ファイル上書き拒否を再現します。実ネットワークは使用しません。テスト結果には「Ran 49 tests / OK」のような集約結果だけでなく、テスト名と実行環境も記録してください。

## 7. 転職活動のための独立改善課題

この見本から**自分で設計する**変更案として、`errno` の変化も別一覧として報告する機能、JSONスキーマバージョン、結果のCSV出力、前後レポートを匿名化する処理、差分結果のファイル保存を一時ファイル＋安全な公開操作にする方式を考えられます。最初から全部実装する必要はありません。どれか1件について次の過程を証拠に残します。

1. 要件と不適切な入力を文章で定義する。どんな入力を拒否するか、なぜ拒否するかを書く。
2. 期待動作を示すテストを自分で書き、**実際に失敗した記録**を保存する。
3. 実装を追加し、ローカルテストと異常系テストを実行する。
4. `git diff` で変更箇所を確認し、差分が自分の設計範囲であることを示す。
5. README・設計図・脅威モデル・検査表・既知の制限を更新する。
6. GitHubへ公開する前に、原典コードや未許諾データ、実IP、秘密情報、生成したJSONを含めていないか確認する。
7. 面接では「何を観測したかったか → なぜ同一対象だけ比較するか → どんな異常入力を拒否したか → 最初に失敗したテスト → 修正 → 残る限界」を2〜5分で説明する。

## 8. このツールがしないこと

HTTPレスポンスを取得する機能、脆弱性の検出、SYNスキャン、第三者の管理者権限確認、DNS解決、パケットの盗聴はありません。`report_diff.py` は保存されたレポートを読むだけで、入力ファイルが実際に許可された対象から収集されたかを証明できません。同じ `state` でも時刻やOSが変われば意味合いは変化します。「差分がない＝安全」とは断定できません。

**参照：** 本配布物の `portfolio_lab/scanner.py`、`report_diff.py`、`tests/test_scanner.py`、`tests/test_report_diff.py`、原典ZIP内のREADMEとChapter 02のTCPスキャナ（学習テーマの一次資料）。


## 9. UTC・スコープ・待機時間の一貫性（800周改訂版）

初版の比較処理では対象・ポート・scopeが同じでも`timeout_seconds`が異なる二回の測定が比較できていました。今回の改訂では、値が違えば`reports must use the same TCP connection timeout`と明示して中止します。比較JSONにscopeとtimeoutも含めます。

`timestamp_utc`はタイムゾーン付きなら何でもよいわけではなく、UTCとのオフセットが0である必要があります。JSONに書かれたscopeは利用者による申告値なので、`target`がloopbackか、指定された正規のプライベート/24以下のCIDRに含まれるかを確認します。これはデータの整合性検査であり、実際の接続の許可・取得結果の真正性の保証ではありません。

実際の手順と試験・証拠の記録方法は`MEASUREMENT_COMPARABILITY_AND_EVIDENCE.md`を参照してください。
