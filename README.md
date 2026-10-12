# ニュースダイジェスト（BBC News RSS → news.json → Yahoo!ニュース風UI）

構成: `index.html`（表示）/ `news.json`（データ）/ `scripts/fetch_news.py`（RSS取得）/ `.github/workflows/update-news.yml`（30分ごとに自動実行）

## セットアップ
1. GitHubで新しい公開(Public)リポジトリを作り、この中身をすべてアップロード。
   `.github/workflows/update-news.yml` はWeb画面の「Add file → Create new file」でパスを入力して貼り付けるのが確実です。
2. Settings → Pages → Source: Deploy from a branch → Branch: `main` / `(root)`。
3. Actions タブ → 「Update news」→ Run workflow で初回を手動実行（`news.json` が更新されます）。
4. 公開URL（https://katsuyori8.github.io/リポジトリ名/）を開く。

## 日本語訳（任意）
Settings → Secrets and variables → Actions に `ANTHROPIC_API_KEY` を登録すると、新着の見出し・概要を日本語に翻訳します（API料金がかかります）。未設定なら英語のまま表示されます。

## 注意
- BBCのRSS利用規約（出典の明示・元記事へのリンク・BBCロゴの不使用など）を必ず確認してください。本文は転載しない構成です。
- フィードのURLは `scripts/fetch_news.py` の `FEEDS` で変更できます。取得に失敗したフィードはスキップされます。
- 更新頻度は workflow の `cron` で変更できます。
