# JSON検証から転職用ポートフォリオまで：実測と説明の手順（第960版）

本資料は `portfolio_lab/scanner.py` と `report_diff.py` に対応しています。前者は対象IPv4へTCP接続を試みます。後者は保存済みファイルを読み込み、**ネットワーク通信を行わず**形式検査と比較を行います。原典の書籍サンプルとは別に作った学習用見本です。権利者の許諾が不明な原典ファイルを、自作作品として公開しないでください。

## 1. 実行条件を用意する

Linux上でPython 3.11以降を用意します。追加のPythonパッケージは不要です。ZIPを展開した後、**`portfolio_lab/` に移動**します。

```sh
pwd
python3 --version
python3 report_diff.py --help
python3 scanner.py --help
python3 -m unittest discover -s tests -v
```

`pwd` は現在の作業ディレクトリを表示します。`--help` は実際のCLIが受理する引数を確認します。`unittest discover -s tests -v` は `tests` 内の `test_*.py` を見つけて実行します。成功したテスト数は自分の環境の出力から記録してください。

失敗時は `python3` のパスとバージョン、`pwd`、実行したコマンドと終了コードを確認します。`ModuleNotFoundError: No module named 'scanner'` と表示された場合、**ZIPのルートではなく `portfolio_lab/` にいるか**を確認します。対処のためにシステム全体へ無関係なライブラリを追加する必要はありません。

## 2. 対象を `127.0.0.1` のみにした動作試験

異なる端末Aと端末Bを用意します。端末Aで待受を開始します。

```sh
cd portfolio_lab
python3 -m http.server 8765 --bind 127.0.0.1
```

端末Bでも `portfolio_lab/` へ移動して、次を実行します。すべて**端末Bから**です。

```sh
cd portfolio_lab
python3 scanner.py --target 127.0.0.1 --ports 8765,8766 --timeout 0.5 --output before.json
python3 report_diff.py --validate before.json
python3 -m json.tool before.json
```

最初のコマンドは最大0.5秒のTCP接続を各ポートに試行し、成功なら `state: open`、接続拒否なら `state: refused` を含むJSONを作成します。ただし、その実測結果は自分のOS・ポート競合・実行タイミングに依存します。`--output` の保存先が既存ファイルなら上書きせずエラーになります。

2番目の `--validate` は**保存済みJSONを1個だけ読み取り、構文、型、必須フィールド、追加フィールドの有無、値域、スコープ、重複ポート、UTC日時などを確認**します。正常な場合は、例えば以下のような表示です。

```text
VALID: before.json (target=127.0.0.1, ports=2)
```

この `VALID` は**JSON形式と内部整合性が検査を通過した**という意味です。ネットワーク観測を再実行したという意味でも、報告書に改ざんがないことを暗号学的に証明したという意味でもありません。コマンドが成功すると通常は終了コード0、入力不正なら終了コード2です。

端末Aのサーバーを `Ctrl+C` で停止した後、端末Bで以下を実行します。

```sh
python3 scanner.py --target 127.0.0.1 --ports 8765,8766 --timeout 0.5 --output after.json
python3 report_diff.py --validate after.json
python3 report_diff.py --before before.json --after after.json --output difference.json
python3 -m json.tool difference.json
```

`--before` と `--after` は**必ず2つセット**で使います。`--validate` は単独検証モードなので、`--before`、`--after`、`--output` と混ぜられません。比較は対象IPv4、宣言したスコープ、接続タイムアウト、ポート集合、日時の前後関係が適合するときに行います。差分は「状態の変化」であり、「脆弱性」や「攻撃成功」の証拠ではありません。

## 3. 主要なCLI引数を一つずつ理解する

| 引数 | プログラム | 目的 | よくある失敗 |
|---|---|---|---|
| `--target` | `scanner.py` | IPv4アドレスを直接指定 | DNS名を渡したり許可外を指定する |
| `--ports` | `scanner.py` | 1〜32件の整数ポートをカンマ区切りで指定 | 重複・空欄・65536以上 |
| `--timeout` | `scanner.py` | 1回の接続の最大待ち時間を秒で指定（0.1〜3.0） | 極端な値、不正な文字 |
| `--scope-cidr` と `--authorized` | `scanner.py` | RFC1918の小範囲ラボを明示 | 外部IPの指定、他人の環境への無許可通信 |
| `--output` | 両方 | 新規JSONファイルへ保存 | 既存ファイルへの上書きを拒否 |
| `--validate` | `report_diff.py` | JSON 1件を**オフライン**で検証 | 比較オプションと併用 |
| `--before`、`--after` | `report_diff.py` | 先後2件の報告書を比較 | タイムアウト・ポート集合・対象の不一致 |

`scanner.py` の `--authorized` は自己申告フラグです。第三者のスキャン許可を自動で取得する仕組みではありません。初めは `127.0.0.1` だけで学んでください。

## 4. 異常なJSONを安全に確認する

実際に使う証拠は壊さず、一時作業ディレクトリで行います。比較ツールはトップレベルに `timestamp_utc`、`target`、`scope`、`timeout_seconds`、`results` の**5フィールドだけ**を認め、各 `results` 要素には `port`、`state`、`errno` の**3フィールドだけ**を認めます。入力スキーマを固定する目的で余計なキーを拒否します。

```sh
python3 - <<'PY'
import json
from pathlib import Path
report = json.loads(Path('before.json').read_text(encoding='utf-8'))
report['made_up_field'] = 'not in schema'
Path('tampered_for_test.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
PY
python3 report_diff.py --validate tampered_for_test.json
```

`report fields mismatch` を含むエラーと終了コード2が期待されます。`echo $?` は直前のコマンドの終了コードを表示します。失敗の再現を報告書へ記録した後、テスト用ファイルを片付けます。**検証するJSONの仕様が将来拡張された場合は、コード・テスト・資料を一緒に改訂する必要**があります。入力を拒否できることはデータの真正性の証明ではありません。

## 5. エラーから原因を切り分ける

| 表示・状態 | 主な意味 | 最初に確認するもの |
|---|---|---|
| `FileNotFoundError` | 指定したJSONが存在しない | `pwd`、`ls -l`、相対パス |
| `report fields mismatch` | JSON最上位の必須・余分キー | `timestamp_utc` 等5キーを確認 |
| `result fields mismatch` | 結果行の必須・余分キー | `port`・`state`・`errno` の3キー |
| `invalid UTF-8 JSON` | 破損JSONや不正なエンコーディング | ファイルをテキストで開いて先頭と末尾を確認 |
| `non-standard JSON constant` | `NaN` または `Infinity` 等 | 数値字句を置き換える |
| `same TCP connection timeout` | 比較対象の測定条件が違う | 両JSONの `timeout_seconds` |
| `before must have an earlier timestamp` | 観測日時の順序が不適切 | UTCタイムスタンプ |
| `already exists` | 上書き保護 | 既存の証拠を消さず別名を使う |
| `refused` | 相手が接続を拒否したとOSが通知 | サーバーがまだ起動しているか、対象ポート |
| `timeout` | 指定時間内に接続結果が確定しない | 通信条件、OS、プロセスとタイムアウト |
| `error_or_unknown` | その他のOSエラー番号 | `errno`、OS、実測ログ |

`refused`、`timeout`、`unreachable` は異なる観測結果です。`timeout` を勝手に「ポートが閉じている」と翻訳しないでください。`--validate` の結果が `VALID` であっても、報告書が正しい実測結果である保証はありません。

## 6. セキュリティエンジニア応募用の成果物を自分で作る

教材の見本をコピーして自作と称しても実績にはなりません。**改良の要件→失敗するテスト→修正→再テスト→実測→説明→公開前監査**まで、自分の作業履歴として残します。

1. **要件**：loopbackだけを対象にする理由、入力の上限、脅威と防御策、完成条件を `docs/REQUIREMENTS.md` に自分の言葉で書く。
2. **現状の再現**：見本のテストとローカル演習を実行し、Python・OS・実行コマンド・日付・終了コードを記録する。提供サンプルと個人の修正を明示的に区別する。
3. **課題設定**：例として「差分JSONに測定条件のハッシュを含める」「エラー分類をOSごとに比較検証する」「レポートの検証専用CLIの操作性を改善する」など、自分で1つ選び理由を書く。
4. **テスト先行**：期待する失敗を示す単体テストを作る。失敗出力も記録し、実装前の状態をコミットする。
5. **小さく実装**：入力検証と機能を分離する。例外型を区別し、異常入力で外部通信が起きないことを確認する。
6. **統合試験**：自分の `127.0.0.1` で実行し、期待値と実測を表にする。単なる単体テスト成功だけで実運用の安全を主張しない。
7. **レビュー**：公開用README、構成図、設計上の選択肢、セキュリティ上の制限、テスト方法、再現できなかった事象を明示する。
8. **公開前監査**：`git status --short`、`git diff --cached --stat`、`git diff --cached` で公開対象を確認する。IP情報、実アカウント、APIキー、原典ZIP、脆弱な演習環境を載せない。
9. **証拠の照合**：テスト結果の原本と公開する要約、Gitコミット、ハッシュ値が対応するよう記録する。SHA-256は改変の検知には使えるが、作成者や観測の真正性は証明しない。
10. **面接**：なぜ対象を制限したか、TCP Connectの仕組み、何が観測できて何は断定できないか、仕様をどうテストしたかを2分程度で説明できるよう準備する。

### 検証記録テンプレート

| 試験ID | Gitコミット | OS / Python | コマンド | 期待結果 | 実測結果 | 判定 | 証拠ファイル |
|---|---|---|---|---|---|---|---|
| V-01 | 実際のSHAを記録 | 実環境を記録 | `python3 report_diff.py --validate before.json` | `VALID` と終了コード0 | 実測後に記入 | 未実施 | `evidence/V-01.txt` |
| V-02 | 実際のSHAを記録 | 実環境を記録 | `python3 report_diff.py --validate tampered_for_test.json` | 不正キーを拒否し終了コード2 | 実測後に記入 | 未実施 | `evidence/V-02.txt` |

この表の「実測」「判定」を実行前に合格と書かないでください。もし失敗したら、その事実と調査・修正を記録します。面接では、数字の大きい監査回数よりも、**自分が見つけた欠陥と実証した修正**が説得力を持ちます。

**一次資料**：このZIPの `portfolio_lab/scanner.py`、`portfolio_lab/report_diff.py`、両テスト、`README_最初に読む.md`、原典の利用条件を記した `original_source.zip`。
