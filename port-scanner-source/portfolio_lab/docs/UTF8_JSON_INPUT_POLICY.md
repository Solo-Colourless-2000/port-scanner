# JSON入力形式の検証とポートフォリオ用の証拠化

## 何を修正したか

前回は `raw = stream.read(...)` の後に `json.loads(raw)` を呼んでいました。PythonのJSONパーサーは **bytesを渡した場合にUTF-8以外の文字コードを自動判定する** ことがあります。このため、UTF-8と書いたマニュアルに反してUTF-16、UTF-32、BOM付きUTF-8も通過していました。

現在は `text = raw.decode("utf-8")` で明示的に文字列へ変換し、続く `json.loads(text, ...)` で構文を解析します。`text`にBOMが残っていればJSONデコーダーが構文エラーにします。読込みサイズ上限1MiBは文字数ではなく **バイト数** の制限です。

`bytes` は生データの並び、`str` はUnicode文字列です。`decode()` は符号化されたバイトを文字へ、`encode()` は文字をバイトへ変換します。`UnicodeDecodeError` はUTF-8への変換失敗、`JSONDecodeError` はJSON文法不一致を表します。コードではこれらを利用者向けの `ValueError` に変換します。

## 実行して確認する

ZIP展開後、 `portfolio_lab/` に移動します。既存のテストファイルやJSONを上書きせず、まず次のコマンドを実行します。

```sh
cd portfolio_lab
python3 --version
python3 -m unittest discover -s tests -v
python3 report_diff.py --help
```

51件のテストが成功することを確認します。テストのうち `test_reports_reject_non_utf8_encodings` は、UTF-16、UTF-32、UTF-8 BOM付き入力をそれぞれ作り、全て拒否されることを確認します。`test_reports_reject_invalid_utf8_bytes` は復号不能なバイト列を使います。実際のテスト結果はOS・Pythonバージョンとともに記録してください。

個別のレポートを検査する場合は、次のコマンドです。これはネットワーク通信しません。

```sh
python3 report_diff.py --validate before.json
```

`VALID` は現在のスキーマ・文字コード検査を通過した意味で、現実にTCP接続が行われたことの証拠ではありません。エラー時の終了コードは `argparse` によって2になります。

## 転職用ポートフォリオにまとめる

1. **再現**：旧コードで非UTF-8のJSONが受理される失敗ケースを作る。原典とは別の自分の検証用リポジトリで行う。
2. **原因**：`json.loads` がbytesを受け取る場合の自動判定と、`decode("utf-8")` の違いを技術資料に記す。
3. **修正**：入力のバイト列をUTF-8へ明示的に変換してからパースする。
4. **回帰テスト**：UTF-16、UTF-32、BOM付きUTF-8、不正バイト列、正常なUTF-8を対象に、期待結果と実測結果を保存する。
5. **証拠**：GitコミットSHA、Pythonバージョン、コマンド、終了コード、テストログ、変更差分を記録する。機密情報・実ネットワークの識別子は公開しない。
6. **限界**：文字コード検査は暗号学的な完全性や観測の真正性を保証しない。JSONのフィールド検査も同様。

新しいコードを自分で書いた範囲と、このZIPに付属するAI生成の見本を区別してください。
