# 📝 Macachette Sports note 運用会社（12人体制）

リポジトリ：[kiichi4268/-home-user-threads-ai-employees](https://github.com/kiichi4268/-home-user-threads-ai-employees)
姉妹リポジトリ（Instagram 運用会社）：[kiichi4268/-ai_employees-](https://github.com/kiichi4268/-ai_employees-)

> 🧭 **中身のルールは [CLAUDE.md](CLAUDE.md)、受け渡しと公開の手順は [NOTE.md](NOTE.md)。** 新しいチャットでは「`CLAUDE.md` と `NOTE.md` を読んで、続きをお願い」と伝えるだけで続きができます。
> ✅ **足りないタスクは [TASKS.md](TASKS.md)。**
> 🗺️ 運用マップ：https://claude.ai/artifact/QsTjpmQ7Q3oiLrFjBYgQqf （控え [docs/設計書_note運用会社.md](docs/設計書_note運用会社.md)）

12人のAI社員が note の記事（タイトル・本文・画像）を作り、**Muse がブラウザで投稿する** ための指示書と手順書です。**週1回**稼働します。

## 1. 前提

| 項目 | 内容 |
|---|---|
| 商材 | 社会人スポーツ・交流イベント（Macachette Sports）のノウハウ（有料note）／公式LINE経由のイベント参加 |
| 誰が | BARマカシェットが運営する「Macachette Sports」 |
| 誰に | 20〜40代の社会人（特に運動ブランク・1人参加が不安な人） |
| 目的 | 「運動ブランクの社会人が、ひとりで来て、気まずくならずに汗をかける場所」を note で知ってもらい、①有料noteで収益 ②公式LINE → 初参加 |
| 一番大事な数字 | 有料noteの販売部数（月）。ゴールは [docs/goals.md](docs/goals.md)（**案**） |

## 2. ファネル
```
【認知】note の記事（無料記事・有料記事の無料エリア）
   │
   ├─▶【収益】有料エリアの購入（先着価格 → 段階的に値上げ）
   │
   ▼
【申込】公式LINE https://lin.ee/WIbLPFV ➔ イベントカレンダーから予約 ➔ 参加フォーム ➔ 合言葉 ➔ 参加受付証
   ▼
【当日】参加受付証を見せて参加費 1,500円（当日、現金またはPayPay）
```

## 3. 1本の記事が公開されるまで
```
Claude Code が作る ➔ note_check が OK ➔ Drive「他のSNS用」に記事フォルダ ➔ PR
➔ 加藤さんが Merge（＝承認） ➔ 加藤さんが共有リンクを Muse に
➔ Muse が下書き ➔ 加藤さんが最終確認 ➔ Muse が公開
```
詳しくは [NOTE.md](NOTE.md)。

## 4. フォルダ構造
```
.
├── README.md                     # 本手順書
├── CLAUDE.md                     # 記事の中身のルール（Claude が毎回読む）
├── NOTE.md                       # 受け渡し・公開・数字の手順
├── TASKS.md                      # 足りないタスク
├── .github/workflows/note_check.yml   # PR のたびに記事を確かめる（何も投稿しない）
├── tools/
│   ├── note_check.py             # 記事のチェック（タイトル・画像・参加費・URL・埋め残し・NG表現）
│   ├── content_rules.py          # NG表現・参加費・日付と会場の照合
│   └── make_images_note01.py     # 第1弾の画像を作る（Pillow）
├── content/note/<id>/            # 記事ごと：meta.json・free.txt・images/（paid.txt は入れない）
├── data/note_weekly.csv          # 週の数字（ビュー・スキ・販売部数）
├── docs/
│   ├── goals.md                  # 目的・ゴール・会社のレベル・ラインナップ（案）
│   ├── reference.md              # 伸びた note の型
│   ├── 設計書_note運用会社.md     # 運用マップの控え
│   └── handover/                 # 「大元の配信先」の控え
└── ai_employees/
    ├── CARDS.md                  # 12人の要約（まずこれを読む）
    ├── PIPELINE.md               # 制作の流れ
    └── PDCA.md                   # 改善の回し方
```

## 5. 12人のAI社員
| 担当 | No. | AI社員 |
|---|---|---|
| 調べる | 01〜03 | 売れ筋調査・読者の声分析・数値分析 |
| 作る | 04〜09 | 企画・構成・本文・タイトル/フック・見出し画像・図解 |
| 確かめる | 10〜12 | 事実確認・表現チェック・受け渡しチェック |

各人の仕事と3点セット（参考・NG・見る数字）は [ai_employees/CARDS.md](ai_employees/CARDS.md)。

## 6. 運用ルール（全文は CLAUDE.md「2.」）
- **Muse は文章を変えない**：空欄・【要追記】を残さずに完成させて渡す。
- **有料エリアは公開リポジトリに置かない**：`paid.txt` は Drive だけ（`.gitignore`）。このリポジトリは公開。
- **参加費**「1,500円（当日、現金またはPayPay）」を本文に必ず入れる。
- **事実**：見ていないこと・確かめていない数字は書かない。
- **価格と「限定」**：書いたとおりに実行する。
- **push は1日2回まで**。

## 7. 手元での確認
```
python3 tools/note_check.py --self-test
python3 tools/note_check.py --check
python3 tools/content_rules.py
```

## 8. 週1回の稼働
稼働日（仮に水曜21:00）に、先週の数字の記録 → 振り返り → 次の記事づくり → Drive → PR をまとめて行う。push はその1回だけ。詳しくは [NOTE.md](NOTE.md)「5.」。
