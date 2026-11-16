from pathlib import Path
R=Path(__file__).parent
html='portscanner_pentest_development_manual_v960_20261117.html'
zipname='portscanner_pentest_manual_v960_20261117.zip'
paths=[R/'README_最初に読む.md',R/'README.txt',R/'portfolio_lab/README.md',*(R/'portfolio_lab/docs').glob('*.md')]
for p in paths:
    if p.name=='VALIDATION_AND_PORTFOLIO_EVIDENCE_V960.md':continue
    s=p.read_text()
    s=s.replace('portscanner_pentest_development_manual_v880_20261117.html',html)
    s=s.replace('portscanner_pentest_manual_v880_20261117.zip',zipname)
    s=s.replace('880周記録','960周記録').replace('880周改訂版','960周改訂版').replace('累計880周','累計960周')
    s=s.replace('全44件','全49件').replace('44件','49件').replace('411行','497行')
    s=s.replace('30件の','35件の').replace('30テスト','35テスト')
    if p.name=='README_最初に読む.md':
        s=s.replace('今回の追加80周は、直前の800周版に対する**801〜840周（修正前40周）**と、改訂後の最終HTMLに対する**841〜880周（修正後40周）**です。', '今回の追加80周は、提供された880周版に対する**881〜920周（修正前40周）**と、今回の最終HTMLに対する**921〜960周（修正後40周）**です。')
        s+='''\n## 10. 960周改訂：JSON 1件を単独検証する方法\n\n`portfolio_lab/` へ移動し、`python3 report_diff.py --validate before.json` を実行します。形式に問題がなければ `VALID: before.json (target=127.0.0.1, ports=2)` のような表示と終了コード0が得られます。不正な入力は終了コード2です。`--validate` と `--before` / `--after` / `--output` は組み合わせられません。\n\n新版はJSONの最上位に5キー、各結果行に3キーの**完全一致**を要求します。余分なフィールドを拒否し、不足しているフィールドも具体的に報告します。これは入力の妥当性検査であり、データが未改変・実測済みだという保証ではありません。\n\n**詳しい実行手順、エラー調査、転職用証拠の作り方**は `portfolio_lab/docs/VALIDATION_AND_PORTFOLIO_EVIDENCE_V960.md` を参照してください。原典43ファイル・946行・107工程は変更していません。スキャナの独立見本237行・19工程も維持し、レポート比較見本497行・10工程へ更新しました。Pythonテストは49件です。\n\n追加監査ログは `audit/REVIEW_ROUNDS_881_920.jsonl` と `audit/REVIEW_ROUNDS_921_960.jsonl`、確認には `python3 tests/verify_review_logs_960.py` を使用します。全体の精査・制限事項は `REVIEW_REPORT.txt` に記載しています。\n'''
    if p.name=='PORTFOLIO_OPERATOR_MANUAL.md':
        s+='''\n\n## 960周版：単独検証コマンドと成果物の証拠化\n\n比較前に `python3 report_diff.py --validate before.json` と `python3 report_diff.py --validate after.json` を実行してください。実行したディレクトリ、終了コード、標準出力・標準エラーを記録します。出力が `VALID` でも実測を証明するわけではなく、JSONが現在のプログラムの受理条件を満たすだけです。複数引数モードは `--before ... --after ...`、単独検証モードは `--validate ...` で、混用できません。\n\n再現試験の入力異常（未知キー・欠落キー）、異常系テスト、GitHubへの公開前確認については `VALIDATION_AND_PORTFOLIO_EVIDENCE_V960.md` を読み、サンプルの見本から自分が改良した差分を残してください。\n'''
    p.write_text(s)

# Maintain changelog chronology: prepend actual work, no invented outcome.
cp=R/'CHANGELOG.md';prior=cp.read_text()
cp.write_text('''# ポートスキャナ教材 v960 改訂履歴（2026-11-17）\n\n- 一次資料：提供された直前版 v880 のZIPと内部の原典ZIP。原典ソースは変更しない。\n- 機械的な40周の事前監査を実行し、内容の実地精読でJSONの余分なキーを受け付ける問題を確認。\n- `portfolio_lab/report_diff.py` にレポート5フィールド・各結果行3フィールドの完全一致検査を追加。\n- `--validate` モードを新設し、既存の2ファイル比較モードと混用した場合のエラー処理を実装。\n- 対応するテスト5件を追加し、49件を実行。\n- HTML内の新規・変更コード84行について個別に文法と意図を解説。10段階の編集手順とソースのバイト一致を維持。\n- 使用ガイド、異常入力の安全な再現方法、転職用ポートフォリオの改良・検証・公開手順を追記。\n- 各周複数項目で修正後40周を再監査。自動反復周回は全文の人間による精読回数を意味しない。\n- ファイル名はポートスキャナ教材の題材に沿って統一。別プロジェクト名を含めない。\n\n---\n\n'''+prior)

p=R/'tests/verify_portfolio.py';s=p.read_text().replace('44 tests','49 tests').replace('44 total','49 total').replace('30 report comparison','35 report comparison');p.write_text(s)
p=R/'tests/verify_report_diff_lesson.py';s=p.read_text().replace('411-line','497-line').replace('==411','==497').replace('Ran 44 tests','Ran 49 tests').replace('411 byte-matched','497 byte-matched').replace('411 annotations','497 annotations').replace('44 test methods','49 test methods');s=s.replace("'--output','127.0.0.1'","'--output','--validate','127.0.0.1'");s=s.replace("and '--before' in help_run.stdout","and '--before' in help_run.stdout and '--validate' in help_run.stdout");p.write_text(s)

# Historical logs must not be overwritten. Verify the new period explicitly.
p=R/'tests/verify_review_logs_960.py'
p.write_text('''#!/usr/bin/env python3\n"""Verify additional 80 machine-audit records and distinct before/after SHA-256 hashes."""\nfrom pathlib import Path\nimport json,hashlib\nR=Path(__file__).resolve().parents[1]\nsha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()\ncurrent=R/'portscanner_pentest_development_manual_v960_20261117.html'\nold=R/'audit/BASELINE_880_MANUAL.html'\nassert sha(current)!=sha(old)\nfor phase,first,expected in [('pre',881,sha(old)),('post',921,sha(current))]:\n    rows=[json.loads(x) for x in (R/'audit'/f'REVIEW_ROUNDS_{first}_{first+39}.jsonl').read_text().splitlines()]\n    assert len(rows)==40\n    assert [r['round'] for r in rows]==list(range(first,first+40))\n    assert all(r['phase']==phase and r['html_sha256']==expected and r['result']=='PASS' for r in rows)\n    assert all(len(r['checks'])==19 and all(r['checks'].values()) for r in rows)\n    assert all(r['original_lines']==946 and r['portfolio_lines']==237 for r in rows)\n    assert all(r['diff_lines']==(411 if phase=='pre' else 497) for r in rows)\n    assert all(len(r['source_samples'])==24 for r in rows)\nprint('PASS: 40 baseline checks plus 40 final-version checks, 19 checks per pass, correct hashes.')\nprint('These are repeated automated checks, not 80 independent semantic full readings.')\n''')
print('doc updated',len(paths),'verify scripts updated')
