"""下書きの「中身」を機械で確かめる（品質管理部の 15 事実確認AI・16 表現チェックAI を自動化したもの）。

tools/th_queue.py の validate（--check・PR のチェック・投稿の前）から呼ばれる。
  - check_expressions：NG 表現（残り人数・一律・出会いの連想・ガチ感・AIっぽい言い回し）と参加費の書き方  … T-20
  - check_facts：日付・曜日・時間・会場・種目を「イベント状況」の控え CSV と照らす（中止・満員の告知も止める）… T-21
  - アクセスが分からない会場に駅名を書いていないか、分かっている会場のアクセスが CLAUDE.md と同じか        … T-22

決まりを足すときは、このファイルの表（NG・VENUE_ACCESS・SPORTS）を直す。CLAUDE.md「2.」「5.」と食い違わないこと。
"""

import csv
import datetime
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVENTS_CSV = ROOT / "docs" / "handover" / "大元の配信先_イベント状況.csv"
FEE = 1500  # 参加費（当日、現金またはPayPay）

# (正規表現, 理由)。CLAUDE.md「2. 絶対ルール」と表現チェックAI（No.16）の NG
NG = [
    (r"残り\s*[0-9０-９一二三四五六七八九十]+\s*(名|人|枠|席)", "残り人数は書かない（「まだ参加枠あります」と書く）"),
    (r"あと\s*[0-9０-９一二三四五六七八九十]+\s*(名|人|枠|席)", "残り人数は書かない（「まだ参加枠あります」と書く）"),
    (r"残りわずか|残り僅か|残りあと|満員間近|ラスト\s*[0-9０-９]+\s*(名|人|枠)", "残り人数・あおりは書かない"),
    (r"一律", "「一律」とは書かない"),
    (r"出会い|出会え|ナンパ|恋活|婚活|合コン|恋人|異性|男女比|マッチング|彼氏|彼女募集", "出会い・ナンパを連想させる書き方はしない"),
    (r"ガチ|経験者限定|経験者のみ|上級者向け|初心者お断り|初心者不可|初心者NG|レベルが高い|レベルの高い", "ガチ感・初心者お断りに見える表現は使わない"),
    (r"の世界へようこそ|革命的|いかがでしたか|圧倒的な|唯一無二|魅力をたっぷり|心に響く|ワクワクが止まらない",
     "AIっぽい言い回しは使わない"),
    (r"初心者\s*[0-9０-９]+\s*割(?!・経験者)", "参加者像は「初心者7割・経験者3割くらい」の表記どおりに書く"),
    (r"[0-9０-９]+\s*割が?\s*(1人|一人|ひとり|おひとり)", "1人参加は「ほとんどが1人参加」と書く（割合は書かない）"),
]

# CLAUDE.md「5. 日程」のアクセス。None＝不明（駅名・徒歩分数を書いてはいけない）
VENUE_ACCESS = {
    "まもり山テラス": None,
    "代々木の杜": "JR代々木駅から徒歩5分",
    "中野区中部コミュニティプラザ": None,
    "芝公園": None,
    "大久保プラザ": "大久保駅・新大久保駅すぐ",
    "渋谷区本町コミュニティ": None,
    "巣鴨体育館": "JR巣鴨駅・大塚駅から徒歩約10分",
    "目黒区民センター": "JR・東急 目黒駅から徒歩10分",
}
SPORTS = {"バドミントン": "バドミントン", "バド": "バドミントン", "バレーボール": "バレーボール", "バレー": "バレーボール",
          "卓球": "卓球", "野球": "野球"}
WEEKDAYS = "月火水木金土日"
DATE_RE = re.compile(r"(?<![0-9])(?:(1[0-2]|0?[1-9])/)?([12][0-9]|3[01]|0?[1-9])\s*[(（]([月火水木金土日])")
MD_RE = re.compile(r"(?<![0-9/])(1[0-2]|0?[1-9])/([12][0-9]|3[01]|0?[1-9])(?![0-9])")
RANGE_RE = re.compile(r"([0-2]?[0-9]):([0-5][0-9])\s*[-〜～~ー]\s*([0-2]?[0-9]):([0-5][0-9])")
START_RE = re.compile(r"([0-2]?[0-9]):([0-5][0-9])\s*(から|〜(?!\s*[0-2]?[0-9]:)|～(?!\s*[0-2]?[0-9]:)|スタート|開始)")
FEE_RE = re.compile(r"参加費[^0-9０-９\n]{0,6}([0-9０-９][0-9０-９,，]*)\s*円")


def load_events(path=EVENTS_CSV):
    """イベント状況の控え CSV を読む：[{date, start, end, sport, venue, state}]"""
    out = []
    with path.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            try:
                day = datetime.datetime.strptime(r["日付"].strip(), "%Y/%m/%d").date()
            except (KeyError, ValueError):
                continue
            venue = r.get("会場", "").strip()
            out.append({"date": day, "start": norm_time(r.get("開始", "")), "end": norm_time(r.get("終了", "")),
                        "sport": r.get("種目", "").strip(), "venue": venue, "base_venue": re.sub(r"[（(].*", "", venue),
                        "state": (r.get("手動の切り替え") or r.get("状態（自動）") or "").strip()})
    return out


def norm_time(s):
    m = re.match(r"\s*([0-2]?[0-9]):([0-5][0-9])", s or "")
    return f"{int(m.group(1)):02d}:{m.group(2)}" if m else ""


def z2h(s):
    return s.translate(str.maketrans("０１２３４５６７８９，", "0123456789,"))


# ---------------------------------------------------------------------------
# T-20：NG 表現と参加費
# ---------------------------------------------------------------------------
def check_expressions(text):
    errors = []
    for pattern, why in NG:
        m = re.search(pattern, text)
        if m:
            errors.append(f"NG表現「{m.group(0)}」：{why}")
    for m in FEE_RE.finditer(text):
        amount = int(z2h(m.group(1)).replace(",", ""))
        if amount != FEE:
            errors.append(f"参加費「{m.group(0)}」：参加費は1,500円（当日、現金またはPayPay）")
        elif "1,500" not in z2h(m.group(0)):
            errors.append(f"参加費「{m.group(0)}」：表記は「1,500円」にする")
    return errors


# ---------------------------------------------------------------------------
# T-21・T-22：日付・曜日・時間・会場・種目・アクセス
# ---------------------------------------------------------------------------
def year_for(month, base):
    return base.year + 1 if month < base.month - 6 else base.year - 1 if month > base.month + 6 else base.year


def dates_in(line, base):
    """行に書かれた日付（曜日つき・曜日なし）と、曜日の間違いを返す。"""
    found, errors, month = {}, [], None
    for m in DATE_RE.finditer(line):
        month = int(m.group(1)) if m.group(1) else month
        if month is None:
            continue
        try:
            day = datetime.date(year_for(month, base), month, int(m.group(2)))
        except ValueError:
            errors.append(f"日付「{m.group(0)}」がない日")
            continue
        found[day] = True
        if WEEKDAYS[day.weekday()] != m.group(3):
            errors.append(f"曜日「{m.group(0)})」：{day:%m/%d} は {WEEKDAYS[day.weekday()]}曜日")
    for m in MD_RE.finditer(line):
        try:
            found.setdefault(datetime.date(year_for(int(m.group(1)), base), int(m.group(1)), int(m.group(2))), True)
        except ValueError:
            errors.append(f"日付「{m.group(0)}」がない日")
    return list(found), errors


def relative_dates(line, base):
    out = []
    if "今日" in line or "本日" in line:
        out.append(base)
    if "明日" in line:
        out.append(base + datetime.timedelta(days=1))
    if "あさって" in line or "明後日" in line:
        out.append(base + datetime.timedelta(days=2))
    return out


def check_facts(text, scheduled, events=None):
    """scheduled：投稿する日（date）。text の各行を、その行の日付（なければ「今日・明日」）の開催と照らす。"""
    events = load_events() if events is None else events
    by_day = {}
    for e in events:
        by_day.setdefault(e["date"], []).append(e)
    errors = []
    venues = sorted(VENUE_ACCESS, key=len, reverse=True)
    for line in text.splitlines():
        days, errs = dates_in(line, scheduled)
        errors += errs
        days = days or relative_dates(line, scheduled)
        cands = [e for d in days for e in by_day.get(d, [])]
        for d in days:
            if d not in by_day and (DATE_RE.search(line) or MD_RE.search(line) or relative_dates(line, scheduled)):
                if any(s in line for s in SPORTS) or any(v in line for v in venues) or RANGE_RE.search(line):
                    errors.append(f"{d:%m/%d} に開催はない（イベント状況）：「{line.strip()[:40]}」")
            for e in by_day.get(d, []):
                if re.search(r"中止|満員", e["state"]) and d >= scheduled:
                    errors.append(f"{d:%m/%d} {e['sport']} は「{e['state']}」なので告知しない")
        # 時間
        for m in RANGE_RE.finditer(line):
            span = (f"{int(m.group(1)):02d}:{m.group(2)}", f"{int(m.group(3)):02d}:{m.group(4)}")
            pool = cands or events
            if not any((e["start"], e["end"]) == span for e in pool):
                where = "その日の開催" if cands else "どの開催"
                errors.append(f"時間「{m.group(0)}」が{where}とも合わない（イベント状況）")
        for m in START_RE.finditer(line):
            start = f"{int(m.group(1)):02d}:{m.group(2)}"
            if cands and not any(e["start"] == start for e in cands):
                errors.append(f"開始「{m.group(0)}」がその日の開催と合わない（イベント状況）")
        # 会場・アクセス
        for v in venues:
            if v not in line:
                continue
            if cands and not any(e["base_venue"] == v for e in cands):
                errors.append(f"会場「{v}」がその日の開催と合わない（イベント状況）")
            after = line.split(v, 1)[1]
            paren = re.match(r"\s*[（(]([^）)]*)[）)]", after)
            access = VENUE_ACCESS[v]
            if access is None and (paren and "駅" in paren.group(1) or re.match(r"[^。\n]{0,8}駅", after)):
                errors.append(f"会場「{v}」のアクセスは不明なので、駅名・徒歩分数を書かない")
            elif access and paren and "駅" in paren.group(1) and paren.group(1) != access:
                errors.append(f"会場「{v}」のアクセスは「{access}」と書く（いまは「{paren.group(1)}」）")
        # 種目（日付のある行だけ）
        if cands and DATE_RE.search(line) or cands and relative_dates(line, scheduled):
            named = {SPORTS[s] for s in SPORTS if s in line}
            have = {e["sport"] for e in cands}
            for s in named - have:
                errors.append(f"種目「{s}」がその日の開催にない（イベント状況：{'・'.join(sorted(have))}）")
    return list(dict.fromkeys(errors))  # 同じ指摘は1回だけ


def check_post(p, events=None):
    """1つの下書きの本文すべて（text と thread）を確かめる。戻り値は「どこ：何が」のリスト。"""
    try:
        scheduled = datetime.datetime.fromisoformat(p["scheduled_at"]).date()
    except (KeyError, ValueError):
        return []
    out = []
    for i, t in enumerate([p.get("text", "")] + list(p.get("thread") or [])):
        label = "text" if i == 0 else f"thread[{i - 1}]"
        out += [f"{label} の{e}" for e in check_expressions(t) + check_facts(t, scheduled, events)]
    return out


def self_test():
    ev = [{"date": datetime.date(2026, 11, 14), "start": "15:00", "end": "17:00", "sport": "バドミントン", "venue": "まもり山テラス",
           "base_venue": "まもり山テラス", "state": "不明"},
          {"date": datetime.date(2026, 11, 15), "start": "13:00", "end": "15:00", "sport": "バドミントン", "venue": "代々木の杜",
           "base_venue": "代々木の杜", "state": "不明"},
          {"date": datetime.date(2026, 11, 22), "start": "17:00", "end": "19:00", "sport": "野球", "venue": "芝公園",
           "base_venue": "芝公園", "state": "中止"}]
    d = datetime.date(2026, 11, 13)
    ok = "11/14(土) バド 15:00-17:00 まもり山テラス\n11/15(日) 13:00-15:00 代々木の杜（JR代々木駅から徒歩5分）\n参加費1,500円（当日、現金またはPayPay）"
    assert check_expressions(ok) == [] and check_facts(ok, d, ev) == [], check_facts(ok, d, ev)
    assert check_facts("今日15:00から、まもり山テラスでバドミントンです", datetime.date(2026, 11, 14), ev) == []
    cases = {
        "残り3名です": "残り人数", "参加費は一律です": "一律", "素敵な出会いがあるかも": "出会い", "ガチ勢歓迎": "ガチ",
        "参加費2,000円": "1,500円", "参加費1500円": "表記",
    }
    for text, word in cases.items():
        assert any(word in e for e in check_expressions(text)), (text, check_expressions(text))
    bad = {
        "11/14(日) バド": "曜日", "11/14(土) 16:00-18:00": "時間", "11/14(土) 代々木の杜": "会場",
        "11/14(土) 卓球": "種目", "まもり山テラス（〇〇駅から徒歩3分）": "アクセスは不明",
        "代々木の杜（代々木駅から徒歩8分）": "JR代々木駅から徒歩5分", "11/16(月) バド 13:00-15:00": "開催はない",
        "11/22(日) 野球": "中止", "明日16:00から、まもり山テラス": "開始",
    }
    for text, word in bad.items():
        errs = check_facts(text, d, ev)
        assert any(word in e for e in errs), (text, errs)
    print("content_rules self-test OK")


if __name__ == "__main__":
    self_test()
