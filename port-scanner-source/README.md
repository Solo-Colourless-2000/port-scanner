# ポートスキャナ開発・ペネトレーションテスト学習教材

このZIPには、学習を進めるために必要な教材と実行用ファイルのみを収録しています。監査ログ、変更履歴、旧版の控え、画面検査画像、制作時だけ使用したスクリプトは含めていません。

## 最初に開くファイル

`portscanner_pentest_development_manual.html` をブラウザで開いてください。インターネット接続は不要です。章ごとの開発工程、各行・構成要素の説明、完成物の操作方法、転職用のポートフォリオ制作手順を収録しています。

## 何が入っているか

- `original_source.zip`：元の書籍サンプル。原典の確認用。脆弱な演習素材も含むため、そのまま公開・実行しないでください。
- `SOURCE_MANIFEST.json`：学習で入力する43ファイルのハッシュ情報。下記 `tools/` が使用します。
- `tools/`：学習用フォルダの作成・原典との照合・重複したサンプルの同期に使用する3スクリプト。
- `portfolio_lab/`：Pythonで作るTCP ConnectスキャナとJSON比較ツールの学習用見本。ソース、単体テスト、CI設定、設計・公開ガイドを収録しています。

## 1. ZIPを展開する

```sh
mkdir -p ~/Documents/portscanner-study
cd ~/Documents/portscanner-study
unzip /path/to/portscanner_pentest_project_20261117.zip
```

`/path/to/` はダウンロード先に合わせて変更してください。

## 2. 原典のコードを自分で入力する

展開先ルートで次を実行すると、原典の43ファイルが空になった学習用フォルダを作れます。**既存の作業フォルダは上書きしません。**

```sh
python3 tools/prepare_workspace.py
```

HTMLの工程を順に進め、43ファイルを入力します。完了後に次のコマンドで原典と照合します。

```sh
python3 tools/check_workspace.py
```

途中段階の `EMPTY` / `DIFFER` は正常です。全部で43件の `MATCH` になればバイト単位で一致しています。`MATCH` は安全な動作まで保証するものではありません。

## 3. ポートフォリオ用プログラムを確認する

**自分の端末の `127.0.0.1` でのみ試してください。** 端末Aでローカルサーバーを起動します。

```sh
cd portfolio_lab
python3 -m http.server 8765 --bind 127.0.0.1
```

別の端末Bで同じ `portfolio_lab/` に移動し、次のように操作します。

```sh
python3 scanner.py --help
python3 report_diff.py --help
python3 scanner.py --target 127.0.0.1 --ports 8765,8766 --timeout 0.5 --output before.json
```

端末Aで `Ctrl+C` を押してサーバーを止めた後、端末Bで続けます。

```sh
python3 scanner.py --target 127.0.0.1 --ports 8765,8766 --timeout 0.5 --output after.json
python3 report_diff.py --validate before.json
python3 report_diff.py --before before.json --after after.json --output difference.json
python3 -m json.tool difference.json
```

JSONは既存ファイルへ上書き保存できません。以前のファイルが残っている場合は**別の出力名**を使ってください。ポート8765・8766の状態は、ほかのプロセスやOSによって変わることがあります。

## 4. テストと学習資料

`portfolio_lab/` をカレントディレクトリにして実行してください。

```sh
python3 -m unittest discover -s tests -v
```

Python 3.11以降、標準ライブラリのみで実行できます。同梱の単体テストは現在51件です。より詳しい手順は `portfolio_lab/README.md`、`portfolio_lab/docs/PORTFOLIO_OPERATOR_MANUAL.md`、`portfolio_lab/docs/PORTFOLIO_BUILD_GUIDE.md`、`portfolio_lab/docs/REPORT_DIFF_BUILD_GUIDE.md` にあります。

## 5. 転職用ポートフォリオとして使う際の注意

`portfolio_lab/` は完成見本であり、そのまま提出しても自分で設計した証拠にはなりません。新しい作業リポジトリで自分の要件・実装・失敗を再現するテスト・修正前後の差分・実測ログ・設計判断を作成し、実際に行った範囲だけを説明してください。原典の書籍サンプルを丸ごと公開しないよう、再利用条件と公開前チェックリストも確認してください。

意図的に脆弱な原典のDocker環境、ARP操作、実行可能メモリを扱うコードなどは、通常のPCや許可のないネットワークで実行しないでください。
