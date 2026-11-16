# Git管理とGitHub公開の具体的な手順

## 0. 権利と自作範囲を先に整理する

本フォルダは教材として用意された見本です。そのままコピーして「自作した」と称して応募してはいけません。独自に行った要件・設計・実装・試験・文書修正を差分として残してください。原典サンプルをコピーする場合は `original_source.zip` 内の公式README「サンプルコード」を確認し、転載・配布条件を守ってください。

## 1. 自分の作業場所を準備する

```sh
cd /path/to/extracted/portfolio_lab
python3 --version
python3 -m unittest discover -s tests -v
python3 scanner.py --help
```

`/path/to/extracted/portfolio_lab` は自分が展開した実際の場所へ置き換えます。**テストは `portfolio_lab/` 直下から実行**します。ZIPルートから実行すると `ModuleNotFoundError: No module named 'scanner'` が発生し得ます。

## 2. 自分の仕様変更とテストを先に決める

例：前後のJSONレポートを読み、`open` → `refused` の変化を比較する機能を新規実装する。実装前に「比較対象の形式」「無効JSON」「違う対象IP」「保存エラー」をテスト設計書に書きます。*この例は提案であり、既に実装済みの機能ではありません。*

## 3. Gitを初期化してレビューする

```sh
git init
git status --short
cat .gitignore
git add scanner.py tests/test_scanner.py .github/workflows/tests.yml README.md .gitignore docs
# サンプルから独立して作成した成果と説明・証拠の内容を自分で確認
git diff --cached --stat
git diff --cached
```

`git diff --cached` に認証情報、内部ネットワークの情報、未許可ログや転載できない資料がないか確認します。`evidence/` 内のファイルは個別に精査してから必要なものだけ `git add` してください。

```sh
git commit -m "Document scope, verification and provenance"
git log --oneline -5
```

`git commit` の前に必要に応じて `git config user.name` と `git config user.email` を設定します。実際に自分が改良した機能は、テスト変更と実装変更を追える独立コミットにします。ここまでのコマンドはローカル操作のみで、外部へ公開しません。

## 4. GitHubへ公開する前の判断

`docs/PUBLICATION_CHECKLIST.md` の項目をすべて読み、公開対象と権利・機密性・組織ルールを確認してから、本人がGitHubでリポジトリを作成します。必要なら最初はprivateで管理します。リモートを作成・公開する操作は、この教材に含まれず、実行していません。CIのActionバージョン・権限も公開時点で再確認してください。

## 5. 採用担当者が再現できるREADMEにする

READMEには目的、動作条件、使用方法、安全な対象範囲、結果の意味、テスト手順、設計上の選択、未対応事項を載せます。「原典教材で学んだこと」「支援・生成物として提供されたサンプル」「自分が考えて実装した差分」を分けて記載します。再現できる成果のみ「検証済み」と書きます。
