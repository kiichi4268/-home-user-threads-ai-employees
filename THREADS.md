# 🧵 Threads 運用ガイド（引き継ぎメモ）

Threads 運用会社のリポジトリです。Instagram 運用会社（`kiichi4268/-ai_employees-`）と同じ「下書き → PR → Merge（＝承認）→ GitHub Actions が自動投稿」の流れで、Threads（@macachette_sports）を回します。
新しいチャットでは「`CLAUDE.md` と `THREADS.md` を読んで、続きをお願い」と伝えるだけで再開できます。
計画の全体図（28人のAI社員のうち、そのまま11・少し直す15・新しく作る2）：https://claude.ai/artifact/8kPw5m7mFmE25CB8qqmuMG

## 1. いまの状態（2026-11-07）
| 項目 | 状態 |
|---|---|
| 投稿の仕組み（投稿管理AI No.24） | ✅ 作成済み：`tools/th_queue.py`・`.github/workflows/threads.yml` |
| 数字の取得と鍵の見張り（数値分析AI No.27） | ✅ 作成済み：`tools/th_insights.py`・`.github/workflows/th_insights.yml` |
| 下書き | ✅ 11/11〜11/24 の14日分（`content/threads/posts/`） |
| AI社員28人の指示書 | ✅ `ai_employees/`（`tools/build_ai_employees.py` で作る） |
| Threads の鍵 | ⏳ **まだ**（下の「2.」の人の作業が必要） |
| 動き出すスイッチ | ⏳ Variables の `TH_ENABLED`・`TH_INSIGHTS_ENABLED` を入れるまで、何も投稿しない |

## 2. 最初に1回だけ（人の作業・10〜15分）
1. **Meta のアプリに Threads の戻り先URLを登録する**
   - Meta for Developers ➔ アプリ ➔ ユースケース「Threads API にアクセス」➔ 設定 ➔ 「リダイレクトコールバックURL」に、たとえば `https://sportsbackstage1.wordpress.com/` を入れて保存
   - 権限は `threads_basic`・`threads_content_publish`・`threads_manage_insights` の3つを追加しておく
   - ※以前「戻り先URLのエラー」で止まったのは、`http://localhost:8080/callback` を使ったためと考えられます（**推測**。Threads は https のURLしか登録できない、という前提）
2. **Mac で鍵を取る**（戻り先URLの既定は `https://sportsbackstage1.wordpress.com/`。1で別のURLを登録したときは、前に `OAUTH_REDIRECT_URI=そのURL ` を付けて実行する）
   先に `.env.example` を `.env` にコピーし、`THREADS_APP_ID`・`THREADS_APP_SECRET`（Meta のアプリの Threads の設定画面にある値）を入れておく。
   ```
   cd ~/Desktop/-home-user-threads-ai-employees-main && python3 tools/get_tokens.py threads
   （フォルダ名は、GitHub から ZIP で落として Desktop に展開したときのもの。違う場所なら、そのフォルダに移動する）
   ```
   ブラウザで「許可」➔ 移動した先のアドレス欄のURLを丸ごとコピーして、ターミナルに貼って Enter。`.env` に `THREADS_ACCESS_TOKEN` と `THREADS_TOKEN_EXPIRES`（期限の日付）が入ります。
3. **GitHub に登録する**（Settings ➔ Secrets and variables ➔ Actions）
   | 場所 | Name | 値 |
   |---|---|---|
   | Secrets | `THREADS_ACCESS_TOKEN` | `.env` の値（チャットには貼らない） |
| Secrets | `CHATWORK_API_TOKEN` | Instagram 運用会社と同じ値（通知用） |
| Secrets | `WORDPRESS_TOKEN` | Instagram 運用会社と同じ値（写真付きの投稿をするときだけ） |
   | Variables | `THREADS_TOKEN_EXPIRES` | 2で表示された日付（例 2027-01-06） |
   | Variables | `TH_INSIGHTS_ENABLED` | `true`（毎晩の数字取得） |
   | Variables | `TH_ENABLED` | `true`（自動投稿。**最後に**入れる） |
4. **確かめる**：Actions ➔ threads ➔ Run workflow（dry_run=1）で「✓ 鍵 Threads: OK」と出るか。th_insights も Run workflow（dry_run=1）。

## 3. 毎週の流れ（Instagram と同じ）
```
① Claude が下書きを作る（週1回・7日分。Instagram 運用会社の下書きと同じ日に。push はまとめて1回）
② 加藤さんが PR を見て「Merge」 ＝ 承認
③ 予定時刻に自動で投稿 ➔ ChatWork に「【Threads】投稿しました＋URL」
```
- 2時間以上遅れたものは送らず ChatWork に知らせる。同じ本文は2回出ない（投稿前に Threads 側を確認）。
- 毎晩23:50に数字を `data/insights/threads_account_daily.csv`・`threads_media.csv` に保存し、ChatWork に「今日の数字」を送る。
- 日曜の週次PDCAで、Threads の「一番落ちている段」と「改善1つ」も決め、改善ログに「媒体：Threads」で書く。

## 4. 下書きの決まり（`tools/th_queue.py --check` が自動で確かめる）
| 項目 | 決まり |
|---|---|
| ファイル | `content/threads/posts/<日付>-th-<番号>.json`（形は th_queue.py の説明のとおり） |
| 本文 | 1投稿500字まで。`thread` に入れた文は、1投稿目への返信として順につながる（5個まで） |
| URL | **公式LINE（https://lin.ee/WIbLPFV）だけ**書いてよい。ほかのURLはエラー |
| タグ | 1投稿に1つまで（Threads はトピック1つ） |
| 写真 | JPG 0〜10枚（1投稿目に付く）。`content/threads/media/` に置く（Instagram 運用会社の完成品をコピーしてよい。顔を隠したものだけ）。動画は未対応 |
| 本数 | 1日1〜2本（朝か昼）。型：問いかけ → 答え3つ → 次の開催 → LINE |
| 中身 | CLAUDE.md の絶対ルールはすべて同じ（参加費・残り人数を書かない・アクセス不明の会場は書かない・顔を隠す など） |

## 5. 鍵の期限（60日）
- 毎晩、鍵が使えるかを確かめ、`THREADS_TOKEN_EXPIRES` の14日前から ChatWork に延長の手順を送ります。
- 延長：`python3 tools/get_tokens.py threads-refresh` ➔ Secrets の `THREADS_ACCESS_TOKEN` と Variables の `THREADS_TOKEN_EXPIRES` を上書き。

## 6. ファイルの地図
| ファイル | 中身 |
|---|---|
| `CLAUDE.md` | 投稿の中身のルール・日程 |
| `ai_employees/` | AI社員28人（`CARDS.md`＝要約、`PIPELINE.md`＝制作の流れ、`PDCA.md`＝改善） |
| `tools/th_queue.py` | 下書きの形チェックと自動投稿 |
| `tools/th_insights.py` | 毎晩の数字と鍵の見張り |
| `tools/get_tokens.py` | 鍵を取る（Mac で実行） |
| `tools/common.py` | 共通部品（通信・ChatWork・CSV） |
| `docs/設計書_Threads運用会社.md` | 設計書（フロア図の控え） |
| `docs/handover/` | 「大元の配信先」の控え（2026-11-04） |

## 7. わかっていないこと
- `clicks`（本文のリンクのクリック数）が、このアカウントで取れるか。取れなければ空欄になるだけで止まらない。取れない場合は、公式LINE側の友だち追加の数で代わりに見る。
- 一番大事な数字の目標値（加藤さんと決める）。
