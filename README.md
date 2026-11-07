# 🧵 Macachette Sports × Threads 運用会社（AI社員28人）

社会人スポーツサークル「マカシェットスポーツ」の **Threads（@macachette_sports）** を、28人のAI社員と GitHub Actions で回すためのリポジトリです。
Instagram 運用会社（[kiichi4268/-ai_employees-](https://github.com/kiichi4268/-ai_employees-)）と同じ流れを、Threads 向けに作り直しています。

```
① Claude が7日分の下書きを作る（content/threads/posts/*.json） → PR
② 加藤さんが PR を「Merge」 ＝ 承認
③ 予定時刻に GitHub Actions が Threads に投稿 → ChatWork に結果
④ 毎晩23:50に数字を data/insights/ に保存 → Claude が日次・週次のPDCA
```

| まず読む | 中身 |
|---|---|
| [THREADS.md](THREADS.md) | 運用ガイド（最初に1回だけの設定・毎週の流れ・下書きの決まり） |
| [CLAUDE.md](CLAUDE.md) | 投稿の中身のルール・日程（Claude が毎回読む） |
| [ai_employees/CARDS.md](ai_employees/CARDS.md) | AI社員28人の要約 |
| [docs/設計書_Threads運用会社.md](docs/設計書_Threads運用会社.md) | 設計書（フロア図・Instagram との違い） |

## 守るルール
- 費用は0円（GitHub Actions の無料枠・Threads の公式API・WordPress の画像置き場だけ）。
- 鍵はチャットに貼らない（Mac の `.env` と GitHub Secrets にだけ置く）。
- このリポジトリを公開にする場合、`data/insights/` の数字も誰でも見られる。気になるなら非公開（Private）にする。

## 動作確認（通信なし）
```
python3 tools/th_queue.py --self-test && python3 tools/th_queue.py --check
python3 tools/th_insights.py --self-test
python3 tools/build_ai_employees.py --check
```
標準ライブラリだけで動きます（追加のインストールは不要）。
