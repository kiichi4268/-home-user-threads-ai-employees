#!/usr/bin/env python3
"""Threads 運用会社の AI社員28人の指示書・カード・制作の流れを作る（ai_employees/ を書き出す）。

使い方:
  python3 tools/build_ai_employees.py          # ai_employees/ を作り直す
  python3 tools/build_ai_employees.py --check  # 書き出し済みのファイルと中身が同じかを確かめる（PR で使う）

元データは設計書「マカシェット AI社員の会社 Threads版」（https://claude.ai/artifact/8kPw5m7mFmE25CB8qqmuMG）のフロア図。
Instagram 運用会社（kiichi4268/-ai_employees-）と同じ6部門・28席で、Threads に合わせて仕事を直している。
指示書を直すときは、ここ（ROOMS・KITS）を直してから実行する。md を手で直すと、次の実行で消える。
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "ai_employees"

STATUS = {"auto": "そのまま使える", "kenmu": "少し直す", "prep": "新しく作る", "done": "作成済み"}

# (No, 名前, ファイル名, 状態, 本来の仕事, Threads でしていること, 次にすること)
ROOMS = [
    ("リサーチ部", "01_research", [
        (1, "市場調査AI", "market_research", "auto", "社会人スポーツ市場の調査。",
         "Instagram と同じ調査を使い回せる。", "月初の回で Threads 向けの話題も1行足す。"),
        (2, "競合調査AI", "competitor_research", "kenmu", "ほかのサークルとの比較。",
         "Threads で伸びている社会人サークルの文章の型を見る。", "加藤さんが見つけた投稿を送ってもらう。"),
        (3, "投稿収集AI", "post_collection", "auto", "参考になる投稿を集める。",
         "集め方は同じ（他人の投稿はAPIで集めない）。", "Threads の参考も同じ所（docs/reference.md）に残す。"),
        (4, "トレンド調査AI", "trend_research", "kenmu", "流行りの型。",
         "Threads は話題の言葉・問いかけが伸びやすい。", "週次で「伸びた書き出し」を記録する。"),
        (5, "視聴者分析AI", "audience_analysis", "kenmu", "誰が見ているか。",
         "返信してくれた人の傾向を見る（名前は残さない）。", "数字が取れるようになってから。"),
    ]),
    ("企画部", "02_planning", [
        (6, "企画立案AI", "idea_generation", "auto", "企画を出す。",
         "Instagram の週テーマをそのまま Threads にも使う。", "同じ週の企画から、文章向けの1本を選ぶ。"),
        (7, "テーマ選定AI", "theme_selection", "auto", "テーマ案3つから1つ。", "同じ。", "―"),
        (8, "構成設計AI", "structure_design", "kenmu", "並び・形を決める。",
         "画像8枚ではなく、500字の本文や連続投稿（スレッド）の形にする。", "型：問いかけ → 答え3つ → 次の開催 → LINE。"),
        (9, "CTA・導線設計AI", "funnel_architect", "kenmu", "行動のお願いを1つに。",
         "Threads は本文にURLを書ける。公式LINEのリンクをそのまま置く。", "リンクのクリックを一番大事な数字にする（案）。"),
    ]),
    ("制作部", "03_content_creation", [
        (10, "フック作成AI", "hook_creator", "kenmu", "最初の1行で止める。",
         "Threads は1行目がすべて。問いかけ型（例：「社会人になって、1人でスポーツ始めた人いる？」）。",
         "Instagram の見出し帯を文章に直す。"),
        (11, "台本作成AI", "script_writer", "kenmu", "台本。",
         "動画は未対応なので、返信への答え方の台本（よくある質問への答え方）を作る（docs/replies.md）。動画に対応したらリールの台本も。",
         "docs/replies.md を作り、月1で見直す（TASKS.md T-34）。"),
        (12, "タイトル作成AI", "title_writer", "kenmu", "表紙・タイトル。",
         "Threads にはタイトル欄がないので、1行目に役目を寄せる。", "―"),
        (13, "キャプション作成AI", "caption_writer", "kenmu", "本文。",
         "本文が主役。500字以内、ハッシュタグは1つ（トピック）。", "Instagram のキャプションから作り直す。"),
    ]),
    ("品質管理部", "04_review_quality", [
        (14, "台本レビューAI", "script_reviewer", "auto", "弱い所を直す。", "同じ。", "―"),
        (15, "事実確認AI", "fact_checker", "auto", "日時・会場・参加費の照合。",
         "同じ（イベント状況と1文字も違えない）。", "―"),
        (16, "表現チェックAI", "expression_checker", "auto", "NG表現を消す。",
         "同じ（出会い・ナンパの連想、ガチ感、残り人数はNG）。返信への答え方にも使う。", "―"),
        (17, "品質確認AI", "quality_controller", "done", "最終確認。",
         "形チェックに Threads の決まり（500字・URLは公式LINEだけ・タグ1つ）を入れた（tools/th_queue.py --check）。",
         "PR では自動で動く。新しい決まりができたら th_queue.py の validate に足す。"),
    ]),
    ("撮影・編集スタジオ", "05_visual_production", [
        (18, "素材収集AI", "material_collector", "auto", "素材を集める。", "同じ（顔は必ず隠す）。", "―"),
        (19, "画像生成AI", "image_generator", "auto", "画像。",
         "Instagram の画像をそのまま添付できる（content/threads/media/ にコピー）。", "―"),
        (20, "図解作成AI", "infographic_creator", "auto", "カード・カレンダー。", "日程カードをそのまま使う。", "―"),
        (21, "字幕作成AI", "subtitle_creator", "kenmu", "テロップ。",
         "字幕と同じ「短く切って読みやすくする」仕事として、スマホで読みやすい改行かを確かめる。",
         "改行の自動チェックを作る（TASKS.md T-35）。それまでは週の作業ノートで目で確かめる。"),
        (22, "動画編集AI", "video_editor", "kenmu", "動画。",
         "リールを Threads にも流用するときだけ（縦動画はそのまま使える。いまの仕組みは動画未対応）。", "―"),
        (23, "音声調整AI", "audio_adjuster", "kenmu", "読み上げとBGM。", "動画を流用するときだけ。", "―"),
    ]),
    ("運用・分析部", "06_operations_analytics", [
        (24, "投稿管理AI", "posting_manager", "done", "予定どおりに投稿する。",
         "承認制の自動投稿を作成済み（tools/th_queue.py・.github/workflows/threads.yml）。鍵の登録待ち。",
         "鍵ができたら Variables の TH_ENABLED=true で動かす（THREADS.md「2.」）。"),
        (25, "進行管理AI", "progress_manager", "auto", "締め切りと段取り。",
         "Instagram の予約（月・水・金・日・毎晩）に Threads の分を足すだけ。", "―"),
        (26, "コメント分析AI", "comment_analyzer", "kenmu", "返信の傾向。",
         "Threads では返信が一番の手がかり。数だけ見て、本文は公開リポジトリに残さない。", "よくある質問を次の投稿のネタにする。"),
        (27, "数値分析AI", "numeric_analyst", "done", "数字を読む。",
         "毎晩23:50に閲覧・いいね・返信・再投稿・引用・リンクのクリック・フォロワーを保存する仕組みを作成済み"
         "（tools/th_insights.py）。鍵の期限60日の見張りも。",
         "鍵ができたら Variables の TH_INSIGHTS_ENABLED=true。data/insights/threads_*.csv を読んで日次PDCAを書く。"),
        (28, "改善提案AI", "improvement_proposal", "kenmu", "改善を1つ決める。",
         "改善ログに「媒体：Threads」で書く。", "日曜の週次で一緒に決める。"),
    ]),
]

# 3点セット（参考にするもの／NG／毎回見る数字）と、受け取るもの → 渡すもの
KITS = {
    1: ("社会人スポーツ・一人参加の悩みの記事、Instagram 運用会社の市場調査メモ", "数字の出どころが書けない話", "フォロワー数の推移"),
    2: ("加藤さんが送ってくれた他サークルの Threads 投稿（本文の型だけ）", "他人の投稿をそのまま写す・APIで集める", "伸びた投稿の書き出しの型"),
    3: ("docs/reference.md", "他人の投稿の本文をリポジトリに丸ごと貼る", "参考の数（週3つまで）"),
    4: ("伸びた書き出しの記録（docs/reference.md）", "流行り言葉の使いすぎ・ネタの押し付け", "閲覧の多い投稿の1行目"),
    5: ("data/insights/threads_media.csv の返信数", "返信した人の名前・本文を残す", "返信数・フォロワーの増え方"),
    6: ("Instagram 運用会社の週テーマ、CLAUDE.md「4. 投稿の型」", "日程の分からない開催を企画にする", "週の閲覧・返信"),
    7: ("テーマ案3つ", "理由のない選択", "前の週の一番落ちている段"),
    8: ("型：問いかけ → 答え3つ → 次の開催 → LINE", "1投稿に話題を2つ以上入れる", "続きの投稿まで読まれているか（返信の位置）"),
    9: ("公式LINE https://lin.ee/WIbLPFV", "CTAを2つ以上置く・ほかのURL", "リンクのクリック（clicks）"),
    10: ("CLAUDE.md の1行目の例、伸びた書き出しの記録", "釣りの1行目・ガチ感・出会いの連想", "閲覧数"),
    11: ("加藤さんから聞いたよくある質問・CLAUDE.md の絶対ルール", "個人の連絡先を聞く・残り人数を答える・推測で答える", "返信数"),
    12: ("1行目の役目（だれに・なにを）", "タイトルだけ強くて中身と合わない", "閲覧数"),
    13: ("content/threads/posts/ の下書き", "500字超え・タグ2つ以上・URL（公式LINE以外）", "返信・再投稿"),
    14: ("右腕の4ルール「書いたら弱い所を3つ直す」", "直した所を書かない", "―"),
    15: ("「イベント状況」シート（控え docs/handover/）", "推測の会場アクセス・参加人数・盛り上がり", "―"),
    16: ("CLAUDE.md「2. 絶対ルール」の NG", "残り人数・一律・ガチ感・ナンパの連想・AIっぽい言い回し", "―"),
    17: ("python3 tools/th_queue.py --check", "チェックを通さずに PR を出す", "PR のチェックの結果"),
    18: ("Drive「Macachette素材」", "顔が分かる写真", "―"),
    19: ("Instagram 運用会社の完成画像（顔を隠したもの）", "実際の開催に見せかけた AI 画像（「※画像はイメージです」を入れる）", "画像付きと文章だけの閲覧の差"),
    20: ("日程カード", "日付・曜日のずれ", "―"),
    21: ("スマホの画面（折り返しの目安：全角20字前後。目安なので実機でも確かめる）", "改行のない長い塊・1文が長すぎる", "続きまで読まれているか"),
    22: ("縦動画のリール", "ぼかしていない動画", "―"),
    23: ("studio の読み上げとBGM（Instagram 運用会社）", "―", "―"),
    24: ("THREADS.md、tools/th_queue.py", "Merge 前に投稿する", "ChatWork の「投稿しました／失敗しました」"),
    25: ("予約の時刻（PIPELINE.md）", "GitHub アクセスの回数を守らない（1日3回、困ったときだけ4回）", "下書きの予定日と PR の日"),
    26: ("data/insights/threads_media.csv の replies", "返信の本文・名前を公開リポジトリに残す", "返信数"),
    27: ("data/insights/threads_account_daily.csv・threads_media.csv", "数字のない結論", "閲覧 → 返信 → リンクのクリック → LINE 友だち"),
    28: ("PDCA.md、改善ログ", "改善を2つ以上同時にする", "前回の改善の判定日の数字"),
}

# 週の作業ノート（T-30）：いつ動き、何を出すか。tools/week_notes.py がこの表から reports/<年>-W<週>/ のひな形を作る。
# いつ：weekly＝週1の下書きの日／sunday＝日曜の週次／monthly＝月末の週／image＝画像付きを出す週／video＝動画対応後／auto＝GitHub Actions
OUTPUTS = {
    1: ("monthly", "翌月の方向を1行（季節・連休・年末などの動き）と、その根拠"),
    2: ("sunday", "加藤さんが送った他サークルの投稿から、本文の「型」だけを1〜3行（送られていない週は「なし」）"),
    3: ("sunday", "docs/reference.md に足した参考の型（週3つまで）"),
    4: ("sunday", "伸びた書き出しの型を1行（threads_media.csv の閲覧上位から）"),
    5: ("sunday", "時刻別（朝・昼）・型別（問いかけ・Q&A・告知）の伸びの違いを1行ずつ"),
    6: ("weekly", "その週の企画（Instagram の週テーマ → 文章向けに直したもの）"),
    7: ("weekly", "テーマ案3つ → 選んだ1つ → 理由1行"),
    8: ("weekly", "7日分の構成表（日付・型・1投稿目／続きの役割）"),
    9: ("weekly", "CTA の確認（各投稿の最後が公式LINEの URL 1つになっているか）。月末はプロフィール文の見直し案も"),
    10: ("weekly", "各投稿の1行目（問いかけ型）"),
    11: ("monthly", "返信への答え方の台本（docs/replies.md）を見直した所"),
    12: ("weekly", "各投稿の1行目の A案・B案と、採用した方（不採用の案も残す）"),
    13: ("weekly", "下書きのファイル名の一覧（content/threads/posts/）"),
    14: ("weekly", "直した弱い所3つ（直す前 → 直した後）。PR の説明にも同じものを書く"),
    15: ("weekly", "照合した日付・時間・会場の一覧と、`th_queue.py --check` の結果（イベント状況の控えの日付も書く）"),
    16: ("weekly", "消した・言い換えた表現（自動チェックで止まったものも）"),
    17: ("weekly", "`th_queue.py --self-test`・`--check` の結果の最後の1行"),
    18: ("image", "選んだ素材（Drive のフォルダ名・ファイル名）と、顔を隠したかの確認"),
    19: ("image", "content/threads/media/ に入れた画像と、注記（※画像はイメージです／※写真は過去の開催時のものです）"),
    20: ("image", "日程カードを使った投稿と、日付・曜日の確認"),
    21: ("weekly", "スマホで読みやすい改行か（1行が長すぎないか・塊になっていないか）の確認結果"),
    22: ("video", "（動画対応後）流用したリールと、ぼかしの確認"),
    23: ("video", "（動画対応後）音声と BGM の確認"),
    24: ("auto", "（自動）GitHub Actions の投稿結果。ChatWork の「投稿しました／失敗しました」を見る"),
    25: ("weekly", "予定どおりか（下書きの予定日・PR の日）と、その日の GitHub アクセスの回数"),
    26: ("sunday", "返信の多い投稿トップ3（数だけ）と、加藤さんから聞いた質問 → 次のネタ"),
    27: ("sunday", "今週の数字（閲覧・返信・再投稿・クリック）と「一番落ちている段」"),
    28: ("sunday", "来週の改善1つ（仮説・やること・見る数字・判定日）。改善ログにも1行"),
}
CADENCE = {"weekly": "週1（下書きの日）", "sunday": "日曜（週次）", "monthly": "月末", "image": "画像付きを出す週",
           "video": "動画対応後", "auto": "自動（GitHub Actions）"}


def card(no, name, status, job, now, nxt):
    return (f"### No.{no:02d} {name}（{STATUS[status]}）\n- 本来の仕事：{job}\n- Threads では：{now}\n- 次にすること：{nxt}\n"
            f"- 3点セット：参考＝{KITS[no][0]}／NG＝{KITS[no][1]}／見る数字＝{KITS[no][2]}\n"
            f"- 出す物（{CADENCE[OUTPUTS[no][0]]}）：{OUTPUTS[no][1]}\n")


def person(room, dirname, no, name, fname, status, job, now, nxt):
    ref, ng, metric = KITS[no]
    return f"""# {name}（No.{no:02d}・{room}）

> Threads 運用会社（@macachette_sports の Threads）の AI社員です。このファイルは `tools/build_ai_employees.py` が作ります（手で直さない）。
> 決まりは `CLAUDE.md` が優先。食い違ったら CLAUDE.md と「加藤からの修正・決定」シートが正しい。

## 状態：{STATUS[status]}

| | |
|---|---|
| 本来の仕事 | {job} |
| Threads でしていること | {now} |
| 次にすること | {nxt} |

## 出す物（週の作業ノート）
- **いつ**：{CADENCE[OUTPUTS[no][0]]}
- **出す物**：{OUTPUTS[no][1]}
- **書く場所**：`reports/<年>-W<週>/{no:02d}_{fname}.md`（`python3 tools/week_notes.py new` がひな形を作る）

## 3点セット（毎回この3つから始める）
- **参考にするもの**：{ref}
- **NG**：{ng}
- **毎回見る数字**：{metric}

## 共通の決まり（短く。詳しくは CLAUDE.md）
- 公開は PR の Merge（＝加藤さんの承認）のあとだけ。
- 本文は500字まで・タグ1つ・URLは公式LINE（https://lin.ee/WIbLPFV）だけ。
- 参加費は「1,500円（当日、現金またはPayPay）」。残り人数は書かない。分からないことは推測せず「不明」と書く。
- 顔は必ず隠す。出会い・ナンパを連想させる表現、ガチ感、AIっぽい言い回しはNG。
- 制作の流れの中での自分の番は `ai_employees/PIPELINE.md`。
"""


def build():
    files = {}
    cards = ["# AI社員カード（Threads 運用会社・28人の要約）\n",
             "制作の予約では、まずこのカードと PIPELINE.md だけを読む（トークン節約）。詳しく必要なときだけ各指示書を開く。\n"]
    counts = {k: 0 for k in STATUS}
    for room, dirname, people in ROOMS:
        cards.append(f"\n## {room}（`ai_employees/{dirname}/`）\n")
        for no, name, fname, status, job, now, nxt in people:
            counts[status] += 1
            files[f"{dirname}/{fname}.md"] = person(room, dirname, no, name, fname, status, job, now, nxt)
            cards.append("\n" + card(no, name, status, job, now, nxt))
    summary = "・".join(f"{STATUS[k]} {v}人" for k, v in counts.items() if v)
    cards.insert(2, f"\n内訳：{summary}（合計 {sum(counts.values())}人）\n")
    files["CARDS.md"] = "".join(cards)
    return files


def main():
    files = build()
    if "--check" in sys.argv:
        diff = [k for k, v in files.items() if not (OUT / k).exists() or (OUT / k).read_text(encoding="utf-8") != v]
        print("\n".join(diff) or f"OK: {len(files)}ファイル、最新")
        sys.exit(1 if diff else 0)
    for k, v in files.items():
        (OUT / k).parent.mkdir(parents=True, exist_ok=True)
        (OUT / k).write_text(v, encoding="utf-8")
    print(f"{len(files)}ファイルを書き出しました（ai_employees/）")


if __name__ == "__main__":
    main()
