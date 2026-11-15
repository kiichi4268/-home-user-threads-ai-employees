# NOTE.md — note 運用ガイド（受け渡し・公開・数字）

中身のルールは `CLAUDE.md`。ここは「どう渡して、どう公開するか」。

## 1. 1本の記事が公開されるまで

```
① Claude Code が記事を作る（content/note/<id>/：meta.json・free.txt・paid.txt・images/）
② python3 tools/note_check.py --check が OK
③ Claude Code が Drive「他のSNS用」に記事フォルダを作って入れる（00_投稿メモ・01_note本文・画像）。meta.json に Drive のリンク
④ PR（paid.txt は入らない。PR の説明に「直した弱い所3つ」と Drive のリンク）
⑤ 加藤さんが PR と Drive の本文（有料エリアはこちらで読む）を読んで Merge（＝承認）
⑥ 加藤さんがフォルダの共有リンクを Muse のチャットに貼る（Merge の前には渡さない）
⑦ Muse が note のエディタで下書きに組み立てる（投稿メモのとおり）
⑧ 加藤さんが下書きを最終確認 → Muse が公開
⑨ meta.json の status・published_url を更新（次の push にまとめる）
```

## 2. 記事フォルダの形（`content/note/<id>/`）

| ファイル | 中身 | リポジトリ |
|---|---|---|
| `meta.json` | タイトル・種類（free / paid）・価格の段階・ハッシュタグ・画像・状態・Drive のリンク | 入れる |
| `free.txt` | 無料記事の本文、または有料記事の無料エリア（最後の行が「ここから有料」） | 入れる |
| `paid.txt` | 有料エリアの本文 | **入れない（Drive だけ）** |
| `images/` | 見出し画像 `01_header.png`（1280×720）と本文画像 | 入れる |

本文の決まり
- 「■」で始まる行は見出し（Muse が見出しにする）
- 本文画像を入れる場所に「［画像：ファイル名］」の行を置く（Muse が画像に差し替える）

## 3. Muse が受け取る形（Drive のフォルダ）

| Drive のファイル | 元 |
|---|---|
| 00_投稿メモ（Muse向け） | 組み立て手順・有料ラインの位置・価格・初回の確認事項 |
| 01_note本文（タイトル・本文・ハッシュタグ） | meta.json のタイトル＋free.txt＋paid.txt＋ハッシュタグ |
| 01_header.png ほか | images/ |

- 参加費「1,500円（当日、現金またはPayPay）」は本文に入ったまま渡す
- Muse は文章を考えない・足さない・変えない

## 4. 有料noteの価格の変え方

- 価格の段階は本文の冒頭に書いておく（例：先着10部500円 → 980円 → 30部で1,980円）
- 販売数が条件に届いたら、**価格の設定だけ** 変える（文章は変えない）
- 変えた日と部数を meta.json の `note` と `data/note_weekly.csv` に書く

## 5. 1週間の流れ（案）

| 曜日・時刻 | だれ | すること | push |
|---|---|---|---|
| 月 8:00 | Claude Code（03 数値分析） | 先週の数字を `data/note_weekly.csv` に記録、今週の記事を決める | 1回目 |
| 水 21:00 | Claude Code（04〜12） | 今週の記事を制作 → チェック → Drive に入れる → PR | 2回目 |
| 木 | 加藤さん | PR と Drive の本文を読んで Merge → 共有リンクを Muse に | ― |
| 金 | 加藤さん・Muse | 下書きを最終確認 → 公開 | ― |
| 日 21:00 | Claude Code（03・02・01） | 週の振り返り（`ai_employees/PDCA.md`） | ― |

数字は note のダッシュボードで見る（自動では取れない）。Muse か加藤さんが、月曜朝までに先週のビュー・スキ・販売部数をチャットに貼る（どちらが担当するか要確認）。

## 6. 手元での確認（通信なし）

```
python3 tools/note_check.py --self-test
python3 tools/note_check.py --check
python3 tools/content_rules.py
```
標準ライブラリだけで動く（画像を作る `tools/make_images_note01.py` だけ Pillow が必要）。PR のたびに GitHub Actions（`.github/workflows/note_check.yml`）でも同じチェックが動く。何も投稿しない。
