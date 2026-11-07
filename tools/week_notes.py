#!/usr/bin/env python3
"""週の作業ノート（TASKS.md T-30）：AI社員ごとの「出す物」を reports/<年>-W<週>/ に1ファイルずつ残す。

だれが本当に働いたかを、ファイルで見えるようにするための仕組み。出す物とタイミングは tools/build_ai_employees.py の OUTPUTS。

使い方:
  python3 tools/week_notes.py new 2026-11-25              # その日を含む週（月〜日）のひな形を作る
  python3 tools/week_notes.py new 2026-11-25 --image      # 画像付きの投稿を出す週（18・19・20 も入れる）
  python3 tools/week_notes.py status                      # 週ごとに「書いた人／まだの人」を表示する
  python3 tools/week_notes.py status 2026-W48             # その週だけ
  python3 tools/week_notes.py --self-test

ひな形の「（ここに書く）」が残っているファイルは「まだ」と数える。出番のない週の人はファイルを作らない。
"""

import argparse
import datetime
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import build_ai_employees as staff  # noqa: E402

REPORTS = ROOT / "reports"
TODO = "（ここに書く）"


def people():
    for room, dirname, members in staff.ROOMS:
        for no, name, fname, *_ in members:
            yield no, name, fname, room, dirname


def week_of(day):
    y, w, _ = day.isocalendar()
    monday = day - datetime.timedelta(days=day.weekday())
    return f"{y}-W{w:02d}", monday


def is_month_end_week(monday):
    sunday = monday + datetime.timedelta(days=6)
    return (sunday + datetime.timedelta(days=7)).month != sunday.month  # 次の週の日曜が翌月＝この週が月末の週


def due(cadence, monday, image):
    return {"weekly": True, "sunday": True, "monthly": is_month_end_week(monday), "image": image,
            "video": False, "auto": False}[cadence]


def new(day, image=False, out=None):
    out = out or REPORTS
    key, monday = week_of(day)
    folder = out / key
    folder.mkdir(parents=True, exist_ok=True)
    made, skipped = [], []
    for no, name, fname, room, dirname in people():
        cadence, what = staff.OUTPUTS[no]
        if not due(cadence, monday, image):
            skipped.append(f"No.{no:02d} {name}（{staff.CADENCE[cadence]}）")
            continue
        path = folder / f"{no:02d}_{fname}.md"
        if path.exists():
            continue  # 書きかけを消さない
        path.write_text(f"""# No.{no:02d} {name}（{room}）— {key}（{monday:%m/%d}〜{monday + datetime.timedelta(days=6):%m/%d}）

- いつ：{staff.CADENCE[cadence]}
- 出す物：{what}
- 指示書：`ai_employees/{dirname}/{fname}.md`

## 出した物
{TODO}

## 使った材料（ファイル名・数字の出どころ）
{TODO}

## 次の人へ（1行。なければ「なし」）
{TODO}
""", encoding="utf-8")
        made.append(path.name)
    sunday = monday + datetime.timedelta(days=6)
    (folder / "README.md").write_text(f"""# 週の作業ノート {key}（{monday:%m/%d}〜{sunday:%m/%d}）

- この週に出番のある AI社員のファイルがある。書いたら「{TODO}」を消す。
- 確かめ方：`python3 tools/week_notes.py status {key}`
- 返信の本文・返信した人の名前・鍵の値は書かない（公開リポジトリ）。推測は「推測」と書く。
- 月末の週：{"はい（01 市場調査・11 台本作成も出番）" if is_month_end_week(monday) else "いいえ"}／画像付きの週：{"はい" if image else "いいえ"}

出番のない人：{"、".join(skipped) or "なし"}
""", encoding="utf-8")
    return folder, made


def status(only=None, out=None):
    out = out or REPORTS
    lines = []
    for folder in sorted(out.glob("*-W*")):
        if only and folder.name != only:
            continue
        files = sorted(f for f in folder.glob("[0-9][0-9]_*.md"))
        done = [f for f in files if TODO not in f.read_text(encoding="utf-8")]
        todo = [f for f in files if f not in done]
        names = {f"{no:02d}": name for no, name, *_ in people()}
        lines.append(f"{folder.name}：書いた {len(done)}人／まだ {len(todo)}人")
        if done:
            lines.append("  書いた：" + "、".join(names[f.name[:2]] for f in done))
        if todo:
            lines.append("  まだ　：" + "、".join(names[f.name[:2]] for f in todo))
    return "\n".join(lines) or "週の作業ノートはまだない（python3 tools/week_notes.py new <日付>）"


def self_test():
    tmp = Path(tempfile.mkdtemp())
    folder, made = new(datetime.date(2026, 11, 25), out=tmp)  # 11/23〜11/29 は月末の週
    assert folder.name == "2026-W48", folder
    nos = {int(m[:2]) for m in made}
    assert {6, 7, 14, 15, 27, 28, 1, 11}.issubset(nos) and not nos & {18, 19, 20, 22, 23, 24}, nos
    folder2, made2 = new(datetime.date(2026, 11, 11), image=True, out=tmp)  # 11/9〜11/15：月末ではない・画像あり
    nos2 = {int(m[:2]) for m in made2}
    assert {18, 19, 20}.issubset(nos2) and not nos2 & {1, 11}, nos2
    f = folder / "07_theme_selection.md"
    f.write_text(f.read_text(encoding="utf-8").replace(TODO, "案A・案B・案C → 案B（理由）"), encoding="utf-8")
    st = status("2026-W48", out=tmp)
    assert "書いた 1人" in st and "テーマ選定AI" in st.splitlines()[1], st
    new(datetime.date(2026, 11, 25), out=tmp)
    assert TODO not in f.read_text(encoding="utf-8")  # 書きかけは上書きしない
    print("week_notes self-test OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", nargs="?", choices=["new", "status"])
    ap.add_argument("arg", nargs="?")
    ap.add_argument("--image", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.cmd == "new":
        day = datetime.date.fromisoformat(a.arg) if a.arg else datetime.date.today()
        folder, made = new(day, a.image)
        print(f"{folder.relative_to(ROOT)}：ひな形 {len(made)}件を作りました")
    elif a.cmd == "status":
        if a.arg and not re.fullmatch(r"\d{4}-W\d{2}", a.arg):
            sys.exit("週は 2026-W48 の形で")
        print(status(a.arg))
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
