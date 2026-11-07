# 🧵 Macachette Sports × 沢田流SNS自動化AI組織 Threads 運用会社（28人体制）

リポジトリ：[kiichi4268/-home-user-threads-ai-employees](https://github.com/kiichi4268/-home-user-threads-ai-employees)
姉妹リポジトリ（Instagram 運用会社）：[kiichi4268/-ai_employees-](https://github.com/kiichi4268/-ai_employees-)

> 🔰 **最初に1回だけの設定（鍵の準備・テスト）は [THREADS.md](THREADS.md) の「2.」を上から順に。** はじめての人向けに書いてあります。
> 🧵 **毎週の運用（承認制の自動投稿）も [THREADS.md](THREADS.md)。** 新しいチャットでは「`CLAUDE.md` と `THREADS.md` を読んで、続きをお願い」と伝えるだけで続きができます。
> ✅ **足りないタスクの一覧は [TASKS.md](TASKS.md)。** 1つずつ埋めていく。
> 📐 設計書（フロア図・28人）：https://claude.ai/artifact/8kPw5m7mFmE25CB8qqmuMG （控え [docs/設計書_Threads運用会社.md](docs/設計書_Threads運用会社.md)）

「フロント拡散（**Threads**）」で毎日の会話から認知を取り、「クローズド教育（公式LINE ➔ 予約）」へ直接つなぐための、28人のAI社員の指示書と実行手順書です。
Instagram 運用会社と同じ「下書き → PR → Merge（＝承認）→ GitHub Actions が自動投稿 → 毎晩の数字 → PDCA」の流れで回します。

---

## 1. 前提（全AI社員の共通の決まりに組み込み済み）

### コンセプト
| 項目 | 内容 |
|---|---|
| 商材 | 社会人スポーツ・交流イベント（Macachette Sports）／公式LINE経由のイベント参加 |
| 誰が | BARマカシェットが運営する「Macachette Sports」（と、SNS自動化を統括するAI社員組織） |
| 誰に | 20〜40代の社会人が中心（特に初心者・運動不足に悩む1人参加の人） |
| 提供価値 | ほとんどが1人参加・「初心者7割・経験者3割くらい」・バドミントンと卓球はラケット貸出あり、という「1人でも浮かない」スポーツの場 |
| ゴール | 運動不足や休日の居場所のなさを解消し、新しい仲間とリフレッシュできる習慣へ（公式LINEから予約・継続参加） |

数字や言い方は `CLAUDE.md`「2. 絶対ルール」が正しい（「8割」「20〜30代」などの古い表記は使わない）。

### 実運用リンク（CTAで使うのはこの表だけ）
| 名称 | URL | 使いどころ |
|---|---|---|
| 公式LINE | https://lin.ee/WIbLPFV | **すべての投稿の最終CTA。Threads は本文にそのまま書いてよい**（ほかのURLは書かない） |
| リンク一覧 | https://fanme.link/@0966712221a41fa899c2 | プロフィール欄だけ（本文には書かない） |
| Instagram | https://www.instagram.com/macachette_sports | プロフィール欄だけ（雰囲気を見たい人向け） |

### 連携先（自動投稿・通知の接続先。投稿本文のCTAには使わない）
| 連携先 | URL・API | メモ |
|---|---|---|
| Threads API | `https://graph.threads.net/v1.0` | 投稿・数字の取得。鍵は `THREADS_ACCESS_TOKEN`（60日） |
| WordPress.com（画像の置き場） | https://sportsbackstage1.wordpress.com | 写真付きの投稿のときだけ。Threads は写真を公開URLで受け取るため |
| ChatWork（通知先） | https://www.chatwork.com/#!rid363171715 | `POST https://api.chatwork.com/v2/rooms/363171715/messages`。ルームIDは `CHATWORK_ROOM_ID` で上書き可 |
| スプレッドシート「大元の配信先」 | ID `19jGf5YypvpJOV8AtEpByoL6u5mPDGetQpLM-n6Kl53A` | Instagram 運用会社と共有。「イベント状況」「加藤からの修正・決定」「改善ログ」 |

鍵（APIトークン・パスワード）はリポジトリ・チャット・下書きに書かない。Mac の `.env`（`.env.example` をコピー。git には入らない）と GitHub Secrets にだけ置く。

---

## 2. ファネル

```
【集客】Threads：1日1〜2本。問いかけ型の1行目で会話（返信）を生む
   │  CTA：本文の「申し込みは公式LINEから👇 https://lin.ee/WIbLPFV」（1投稿に1つだけ）
   ▼
【クローズド教育・販売】公式LINE ➔ メニュー「イベントカレンダーから予約」➔ 参加フォーム ➔ 合言葉 ➔ 参加受付証
   │
   ▼
【継続参加・ファン化】次回の案内・返信での会話（返信の本文・名前はリポジトリに残さない）

（雰囲気を見たい人は、プロフィールから Instagram へ。Instagram 運用会社が「オープン教育」を担当）
```

Instagram は本文のURLが押せないので「プロフィールのリンクから」と案内するが、**Threads は本文に公式LINEのURLを直接置ける**。ここが Instagram 運用会社との一番の違い。

---

## 3. フォルダ構造とAI社員一覧

```
.
├── README.md                          # 本手順書
├── CLAUDE.md                          # 投稿の中身のルール・日程（Claude が毎回読む）
├── THREADS.md                         # 運用ガイド（最初に1回だけの設定・毎週の流れ・下書きの決まり）
├── .env.example                       # 鍵の置き場の見本（.env にコピーして使う）
├── .github/workflows/
│   ├── threads.yml                    # 承認制の自動投稿（毎時）と、PR での形チェック
│   └── th_insights.yml                # 毎晩23:50の数字の取得と、鍵の期限の見張り
├── tools/
│   ├── th_queue.py                    # 下書きの形チェックと、Threads への投稿
│   ├── th_insights.py                 # 数字を data/insights/ に保存・ChatWork に「今日の数字」
│   ├── get_tokens.py                  # 鍵を取る（Mac で実行。threads／threads-refresh／wordpress）
│   ├── build_ai_employees.py          # 28人分の指示書・CARDS.md を作る（元データはここ）
│   ├── content_rules.py               # 中身の自動チェック（NG表現・参加費・日付・曜日・時間・会場・種目・アクセス）
│   ├── week_notes.py                  # 週の作業ノート（だれが何を出したか）を作る・確かめる
│   └── common.py                      # 共通部品（通信・ChatWork・CSV）
├── content/threads/
│   ├── posts/                         # 下書き（1投稿1ファイル：<日付>-th-<番号>.json）
│   └── media/                         # 写真（JPG。顔を隠した完成品だけ）
├── reports/<年>-W<週>/                # 週の作業ノート（AI社員ごとの「出した物」）
├── data/insights/                     # 毎晩の数字（threads_account_daily.csv・threads_media.csv）
├── docs/
│   ├── 設計書_Threads運用会社.md       # 設計書の控え
│   ├── reference.md                   # 伸びた書き出し・参考の型の記録
│   └── handover/                      # 「大元の配信先」の控え（2026-11-04 時点）
└── ai_employees/                      # 28人のAI社員（tools/build_ai_employees.py が作る。手で直さない）
    ├── CARDS.md                       # 28人の要約（まずこれを読む）
    ├── PIPELINE.md                    # 制作の流れ
    ├── PDCA.md                        # 改善の回し方
    ├── 01_research/                   # 【リサーチ部】
    │   ├── market_research.md         # 1. 市場調査AI
    │   ├── competitor_research.md     # 2. 競合調査AI
    │   ├── post_collection.md         # 3. 投稿収集AI
    │   ├── trend_research.md          # 4. トレンド調査AI
    │   └── audience_analysis.md       # 5. 視聴者分析AI
    ├── 02_planning/                   # 【企画部】
    │   ├── idea_generation.md         # 6. 企画立案AI
    │   ├── theme_selection.md         # 7. テーマ選定AI
    │   ├── structure_design.md        # 8. 構成設計AI
    │   └── funnel_architect.md        # 9. CTA・導線設計AI
    ├── 03_content_creation/           # 【制作部】
    │   ├── hook_creator.md            # 10. フック作成AI
    │   ├── script_writer.md           # 11. 台本作成AI
    │   ├── title_writer.md            # 12. タイトル作成AI
    │   └── caption_writer.md          # 13. キャプション作成AI
    ├── 04_review_quality/             # 【品質管理部】
    │   ├── script_reviewer.md         # 14. 台本レビューAI
    │   ├── fact_checker.md            # 15. 事実確認AI
    │   ├── expression_checker.md      # 16. 表現チェックAI
    │   └── quality_controller.md      # 17. 品質確認AI
    ├── 05_visual_production/          # 【撮影・編集スタジオ】
    │   ├── material_collector.md      # 18. 素材収集AI
    │   ├── image_generator.md         # 19. 画像生成AI
    │   ├── infographic_creator.md     # 20. 図解作成AI
    │   ├── subtitle_creator.md        # 21. 字幕作成AI
    │   ├── video_editor.md            # 22. 動画編集AI
    │   └── audio_adjuster.md          # 23. 音声調整AI
    └── 06_operations_analytics/       # 【運用・分析部】
        ├── posting_manager.md         # 24. 投稿管理AI
        ├── progress_manager.md        # 25. 進行管理AI
        ├── comment_analyzer.md        # 26. コメント分析AI
        ├── numeric_analyst.md         # 27. 数値分析AI
        └── improvement_proposal.md    # 28. 改善提案AI
```

### 28人の状態（設計書のフロア図より）
| 状態 | 人数 | だれ |
|---|---|---|
| そのまま使える（Instagram と同じ仕事） | 11人 | 01・03・06・07・14・15・16・18・19・20・25 |
| 少し直す（文章中心・URLが書けるなど） | 14人 | 02・04・05・08・09・10・11・12・13・21・22・23・26・28 |
| 作成済み（Threads 用に新しく作った） | 3人 | 17 品質確認（形チェック）・24 投稿管理（自動投稿）・27 数値分析（毎晩の数字） |

各人の「本来の仕事／Threads でしていること／次にすること／3点セット（参考・NG・見る数字）」は [ai_employees/CARDS.md](ai_employees/CARDS.md)。
指示書を直すときは `tools/build_ai_employees.py` の `ROOMS`・`KITS` を直してから `python3 tools/build_ai_employees.py` を実行する（md を手で直すと次の実行で消える）。

---

## 4. 毎日の運用フロー

### 4-1. 1本の投稿が流れる順番（詳しくは [ai_employees/PIPELINE.md](ai_employees/PIPELINE.md)）
```
［リサーチ］トレンド調査・投稿収集・視聴者分析（週1でまとめて）
   ▼
［企画］企画立案 ➔ テーマ選定（案3つ → 1つ）➔ 構成設計（問いかけ → 答え3つ → 次の開催 → LINE）＋ CTA・導線設計
   ▼
［制作］フック作成（1行目）➔ タイトル作成 ➔ キャプション作成（各500字以内・タグ1つ）
   ▼
［品質］台本レビュー（弱い所を3つ直す）➔ 表現チェック ➔ 事実確認（「イベント状況」と1文字も違えない）
   ▼
［ビジュアル］写真を付けるときだけ：素材収集 ➔ 画像生成／図解作成（顔を隠した JPG）
   ▼
［最終ゲート］品質確認：python3 tools/th_queue.py --check が OK
   ▼
［運用］投稿管理：PR ➔ 加藤さんが Merge ➔ 予定時刻に自動投稿 ➔ ChatWork に結果
   ▼
［分析］毎晩23:50に数字を保存 ➔ 数値分析・コメント分析 ➔ 改善提案 ➔ 企画へ戻る
                   全工程を 進行管理AI が見る
```

### 4-2. 1週間のリズム
| いつ | だれ | すること |
|---|---|---|
| 週1回（Instagram の下書きと同じ日） | Claude（06〜17・24） | 7日分の下書き ➔ PR（GitHub への push はまとめて1回） |
| PR が届いたら | 加藤さん | 中身を見て Merge（＝承認）。直したいところは PR にコメントか Claude に伝える |
| 毎時5分（日本時間 8:05〜23:05） | GitHub Actions | 予定時刻を過ぎた下書きを投稿 |
| 毎晩23:50 | GitHub Actions | 数字を保存・ChatWork に「今日の数字」・鍵の期限の確認 |
| 毎晩（数字のあと） | Claude（27） | 日次PDCA：「一番落ちている段」と「明日の改善1つ」 |
| 日曜 | Claude（27・28ほか） | 週次PDCA（[ai_employees/PDCA.md](ai_employees/PDCA.md)） |

---

## 5. 月間イベントスケジュールの運用（毎月25日〜末日）

毎日の投稿とイベント告知を途切れさせないために、翌月の日程を毎月25日〜末日にまとめて反映します。

1. **日程を確かめる**：スプレッドシート「大元の配信先」の「イベント状況」タブ（人が入力し、AIは読むだけ）。
2. **CLAUDE.md を直す**：「5. 日程」の表を翌月分に書き換える（会場のアクセスが分からないものは「不明」のまま。推測で書かない）。曜日は必ずカレンダーで確かめる。
3. **企画立案AIに渡す**：次の形で翌月の日程を貼る。企画立案AIが、開催日から逆算して「どの週に・何を出すか」を割り振る。
   ```
   【翌月イベントスケジュール】{年}年{月}月
   ・{月}/{日}({曜}) {開始}-{終了} {絵文字}{種目}＠{会場}（{アクセス or 不明}）
   ・…（翌月の開催分をすべて）
   【共通情報】参加費：1,500円（当日、現金またはPayPay）／持ち物：着替え・体育館シューズ・飲み物／貸出：バド・卓球はラケット
   【今月の重点】（例：初参加の女性を増やしたい、バレーの集客が弱い）
   ```
4. **7日分ずつ下書きにする**：毎週、`content/threads/posts/` に下書きを作って PR。

**逆算のルール（Threads 版）**：月初に1か月の日程まとめ ➔ 14〜8日前に種目別の問いかけ・Q&A ➔ 7日前に告知 ➔ 3日前にリマインド（**残り人数は書かない**。「まだ参加枠あります」）➔ 前日に最終案内 ➔ 当日の朝に募集 ➔ 翌日以降に次回の案内（見ていないこと＝参加人数・盛り上がりは書かない）。
1日1〜2本に収まらないときは、開催日が近いものを優先し、同じ週の告知は1本にまとめる。

---

## 6. PDCAサイクル（日次・週次・月次）

改善は「大元の配信先」の「改善ログ」タブに「媒体：Threads」で書く（Instagram 運用会社と同じ表）。決まりの全文は [ai_employees/PDCA.md](ai_employees/PDCA.md)。

### 毎晩（数字のあと）
- 数値分析AI（27）：`data/insights/threads_account_daily.csv` を読み、「一番落ちている段」と「明日の改善1つ」を書く。

### 毎週（日曜）
| 順 | だれ | すること |
|---|---|---|
| 1 | 数値分析AI（27） | 直近7日の `threads_media.csv` から、返信・再投稿が多い投稿トップ3と少ない3つ |
| 2 | 視聴者分析AI（05） | 時刻別（朝・昼）・型別（問いかけ・Q&A・告知）の違いを1行ずつ |
| 3 | トレンド調査AI（04）・競合調査AI（02） | 伸びた書き出しを `docs/reference.md` に1行（他人の投稿はAPIで集めない） |
| 4 | コメント分析AI（26） | 返信の数だけ見る。よくある質問は次の投稿のネタに（本文・名前は残さない） |
| 5 | 改善提案AI（28） | 翌週に入れる改善を **1つだけ** 決める（同時に動かすのは2つまで） |
| 6 | 企画立案AI（06）➔ テーマ選定AI（07） | 改善を入れた翌週の企画 ➔ 下書き |

### 毎月（月末）
- 市場調査AI（01）・投稿収集AI（03）：翌月の方向を1行で。
- CTA・導線設計AI（09）：プロフィール文・公式LINEへの案内を数字に合わせて見直す。
- 25日〜末日：翌月の日程を反映（「5.」）。
- 共通の決まり（参加者像・参加費など）が変わったら `CLAUDE.md` と `tools/build_ai_employees.py` を直して作り直す。

---

## 7. KPI（数値分析AIに伝える項目）

| ファネル | 指標 | 出どころ | 見るポイント |
|---|---|---|---|
| 集客 | 閲覧（views） | `threads_account_daily.csv`・`threads_media.csv` | 1行目（フック）が効いているか |
| 集客 | 返信（replies）・再投稿（reposts）・引用（quotes） | 同上 | 会話が生まれているか（Threads で一番伸びる要素） |
| 集客 | いいね（likes）・フォロワー数 | 同上 | 続けて見てもらえているか |
| クローズド教育 | **公式LINEのリンクのクリック（clicks）** | `threads_account_daily.csv` | **一番大事な数字（案）**。取れないときは空欄になる（※このアカウントで取れるかは未確認） |
| クローズド教育 | LINE友だち追加 | 加藤さんから聞く（Threads の数字にはない） | クリックから友だちになっているか |
| 販売 | 申込・新規参加 | 加藤さんから聞く | 公式LINEの案内の分かりやすさ |

目標値は加藤さんと決める（未定）。最初の2〜4週間で今の数字を測り、改善提案AIが「前の週よりどれだけ上げるか」を合格ラインとして決める。見ていない数字・推測では判定しない（「不明」と書く）。

---

## 8. 運用ルール（必ず守ること。全文は CLAUDE.md「2.」）

- **事実の正しさ**：日時・会場・参加費は「イベント状況」と1文字も違えない。会場のアクセスが分からないものは書かない。参加人数・盛り上がりなど見ていないことは書かない。事実確認AIを通さない下書きは PR にしない。
- **リンクの正しさ**：本文のURLは公式LINE（https://lin.ee/WIbLPFV）だけ（`th_queue.py --check` がほかのURLをエラーにする）。
- **顔を隠す**：写真は顔にモザイク。ぼかす前の写真・動画はコミットしない（公開リポジトリ）。
- **返信の扱い**：返信の本文・返信した人の名前はリポジトリに残さない（数だけ）。返信に答えるときも NG 表現を守り、個人の連絡先は聞かない・書かない。
- **AIっぽさの排除**：表現チェックAIを必ず通す。ガチ感・初心者お断り・出会い／ナンパの連想・残り人数・「一律」は NG。
- **推測の扱い**：推測を含む表現を使ったら、下書きの `note` に「※推測」と書き、Merge 前に加藤さんに確かめてもらう。
- **承認**：公開は PR の Merge（＝加藤さんの承認）のあとだけ。出したくない下書きは PR から外す。
- **形を崩さない**：下書きの JSON のキー（`id`・`scheduled_at`・`text`・`thread`・`media`・`note`）は変えない。
- **GitHub アクセス**：Instagram 運用会社と合わせて普段は1日3回まで、困ったときだけ4回目。

---

## 9. 投稿失敗時の ChatWork 通知

`tools/th_queue.py` が投稿に失敗すると、`tools/common.py` の `failure_message` が原因の目安と直し方を付けて、ChatWork（ルーム 363171715）に送ります。

| 状況 | 例 | 直し方（通知に書かれる内容） |
|---|---|---|
| 鍵 | HTTP 401 | 鍵が切れているか貼り間違い。THREADS.md「5.」の手順で取り直す |
| 権限 | HTTP 403 | 許可の画面ですべての権限を許可して鍵を取り直す |
| 送りすぎ | HTTP 429 | Threads は24時間で250投稿まで。次の回で自動的にやり直す |
| それ以外 | 400（文字数・URL・写真など）・5xx・タイムアウト | 下書きの中身を確かめる。分からなければ Claude に「Threads の投稿が失敗した」と伝える |

ほかにも次のときに知らせます。
- 下書きの形がおかしい（その回は1件も送らない）
- 予定時刻を2時間以上過ぎて送らなかった（1回だけ）
- 鍵が使えない・期限まで14日を切った（毎晩の `th_insights.py`）

守ること
- ChatWork の鍵は `CHATWORK_API_TOKEN`（GitHub Secrets／`.env`）だけで渡す。エラー文に混ざった鍵は自動で伏せ字（****）にする。
- 失敗した下書きは、予定時刻から2時間以内なら次の回（毎時）にもう一度送ろうとする。投稿前に Threads 側に同じ本文がないかを確かめるので、2回出ることはない。そのため、同じ失敗の通知が2回以上届くことがある。

---

## 10. 予定時刻を過ぎた投稿の扱い

| 状況 | 仕組みの動き |
|---|---|
| 予定時刻から2時間以内 | そのまま投稿する（GitHub Actions の遅れを見込んだ幅） |
| 2時間を超えた | 送らずに ChatWork に「予定時刻を過ぎたため送りませんでした」を1回だけ知らせる |

期限切れになった下書きの判断（投稿管理AI・加藤さん）
| 状況 | 対応 |
|---|---|
| その日のうちで、本文がまだ正しい（「今日」「明日」が今でも合う） | 手動でカバー：下書きの `text` をコピーして Threads のアプリで投稿する |
| 翌日以降も中身が正しく、開催より前に出せる | 繰り延べ：`scheduled_at` を空いている時間に変えて PR ➔ Merge |
| 日付に依存していて、もう合わない／開催が終わった | 見送り：投稿しない。下書きのファイルを消すか `note` に「見送り」と理由 |

---

## 11. 動き出すまでのチェックリスト

### A. 事前準備
- [ ] Threads のプロフィールに公式LINE（https://lin.ee/WIbLPFV）を置く
- [ ] `.env.example` を `.env` にコピーし、`THREADS_APP_ID`・`THREADS_APP_SECRET`・`CHATWORK_API_TOKEN` を入れる

### B. 鍵（THREADS.md「2.」）
- [ ] Meta のアプリに戻り先URL（例 `https://sportsbackstage1.wordpress.com/`）と3つの権限（`threads_basic`・`threads_content_publish`・`threads_manage_insights`）を登録
- [ ] Mac で `python3 tools/get_tokens.py threads`
- [ ] GitHub Secrets：`THREADS_ACCESS_TOKEN`・`CHATWORK_API_TOKEN`（写真付きの投稿をするなら `WORDPRESS_TOKEN`）
- [ ] GitHub Variables：`THREADS_TOKEN_EXPIRES`・`TH_INSIGHTS_ENABLED=true`

### C. テスト
- [ ] Actions ➔ threads ➔ Run workflow（dry_run=1）で「✓ 鍵 Threads: OK」
- [ ] Actions ➔ th_insights ➔ Run workflow（dry_run=1）で「✓ 鍵 OK」と数字
- [ ] 下書きの PR を Merge する

### D. 本番
- [ ] Variables に `TH_ENABLED=true`（これで毎時の自動投稿が始まる。止めたいときは消す）
- [ ] 最初の予定時刻のあと、ChatWork に「【Threads】投稿しました」が届くか確かめる

---

## 12. GitHub Actions で自動投稿する（費用0円）

| ワークフロー | いつ | すること | 必要な鍵（Secrets） | スイッチ（Variables） |
|---|---|---|---|---|
| `threads.yml`（check） | PR のたび | テストと下書きの形チェック（何も投稿しない） | なし | なし |
| `threads.yml`（post） | 毎時5分（日本時間 8:05〜23:05） | 予定時刻を過ぎた下書きを投稿 | `THREADS_ACCESS_TOKEN`・`CHATWORK_API_TOKEN`（写真付きなら `WORDPRESS_TOKEN`） | `TH_ENABLED=true` |
| `th_insights.yml` | 毎晩23:50 | 数字を `data/insights/` に保存して main に push・鍵の期限の確認 | `THREADS_ACCESS_TOKEN`・`CHATWORK_API_TOKEN` | `TH_INSIGHTS_ENABLED=true`・`THREADS_TOKEN_EXPIRES` |

- 手で動かすとき：Actions ➔ ワークフローを選ぶ ➔ Run workflow。`dry_run=1` なら何も送らない（鍵の確認と、送る予定の表示だけ）。
- 費用：公開リポジトリなら Actions は無料。非公開にしても、使う時間の目安は月500分ほど（**見積もり**）で、無料枠（月2,000分）に収まる。
- 公開リポジトリのままだと、`data/insights/` の数字も誰でも見られる。気になるなら非公開（Private）にする。
- 鍵の期限：Threads の鍵は60日で切れる。14日前から毎晩 ChatWork に延長の手順が届く（`python3 tools/get_tokens.py threads-refresh` ➔ Secrets と Variables を上書き）。

### Instagram 運用会社との違い（仕組み）
| | Instagram 運用会社 | Threads 運用会社 |
|---|---|---|
| 投稿の仕組み | `ig_queue.py`・`instagram.yml` | `th_queue.py`・`threads.yml` |
| 数字 | `ig_insights.py`（`account_daily.csv`・`media.csv`） | `th_insights.py`（`threads_*.csv`） |
| 本文のURL | エラー（書かない） | 公式LINEだけ OK |
| 文字数・タグ | 2,200字・30個 | 500字・1つ |
| 動画 | あり（リール・ストーリー） | 未対応（文章・写真のみ） |
| 鍵の期限 | なし | 60日（見張りあり） |

---

## 13. 手元での確認（通信なし）

```
python3 tools/th_queue.py --self-test          # 投稿の仕組みのテスト
python3 tools/th_queue.py --check              # 下書きの形チェック
python3 tools/th_insights.py --self-test       # 数字の取得のテスト
python3 tools/build_ai_employees.py --check    # 指示書が最新か
python3 tools/th_queue.py --now 2026-11-11T12:05   # その時刻として動かす（DRY_RUN=1 が既定。送らない）
```
標準ライブラリだけで動きます（追加のインストールは不要）。

---

## 14. わかっていないこと（CLAUDE.md「7.」と同じ）
- 一部の会場（まもり山テラス・中野区中部コミュニティプラザ・芝公園・渋谷区本町コミュニティ）の最寄り駅と徒歩分数
- 公式LINEのURL：Instagram 運用会社の README は `lin.ee/VwtzoAm`、CLAUDE.md は `lin.ee/WIbLPFV`。新しいほうの CLAUDE.md に合わせて `WIbLPFV` を使っている（どちらが正しいか要確認）
- Threads のリンクのクリック数（clicks）がこのアカウントで取れるか
- 一番大事な数字の目標値
