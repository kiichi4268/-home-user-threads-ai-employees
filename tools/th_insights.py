#!/usr/bin/env python3
"""Threads の数字（インサイト）を毎晩取り、data/insights/threads_*.csv に残す。あわせて鍵が生きているか・期限を確かめる。

GitHub Actions（.github/workflows/th_insights.yml）から毎晩 23:50 に動く。Instagram 運用会社の ig_insights.py と同じ考え方
（Claude のコネクタは使わず、投稿と同じ GitHub Secrets の鍵で Threads の公式APIを直接呼ぶ）。

使い方:
  python3 tools/th_insights.py                 # 直近3日分のアカウントの数字と、直近14日の投稿の数字を取る
  python3 tools/th_insights.py --days 7        # アカウントの数字を7日分取り直す
  python3 tools/th_insights.py --token-only    # 鍵の確認だけ
  python3 tools/th_insights.py --self-test     # 通信なしの動作確認

出力（同じ日・同じ投稿の行は上書き。空欄では上書きしない）:
  data/insights/threads_account_daily.csv  日付ごと：閲覧・いいね・返信・再投稿・引用・リンクのクリック・フォロワー数
  data/insights/threads_media.csv          投稿ごと：投稿日時・閲覧・いいね・返信・再投稿・引用・シェア

鍵（環境変数・GitHub Secrets）: THREADS_ACCESS_TOKEN（必須。threads_manage_insights の権限が要る）、CHATWORK_API_TOKEN（通知）
鍵の期限: Threads の鍵は60日で切れる。Variables の THREADS_TOKEN_EXPIRES（例 2027-01-06。get_tokens.py threads が表示する）を
  入れておくと、14日前から毎晩 ChatWork に延長の手順を知らせる。
DRY_RUN=1 のときは ChatWork に送らず、CSV も書かない（画面に出すだけ）。
"""

import argparse
import datetime
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import common as q  # noqa: E402

JST = q.JST
OUT = ROOT / "data" / "insights"
# clicks（本文のリンクのクリック）は、取れないアカウント・時期があるため、取れなければ空欄になるだけで止まらない
ACCOUNT_METRICS = ["views", "likes", "replies", "reposts", "quotes", "clicks"]
MEDIA_METRICS = ["views", "likes", "replies", "reposts", "quotes", "shares"]
ACCOUNT_COLS = ["date", "followers"] + ACCOUNT_METRICS + ["fetched_at"]
MEDIA_COLS = ["id", "posted_at", "permalink", "text_head"] + MEDIA_METRICS + ["fetched_at"]
WARN_DAYS = 14
FIX_STEPS = ("延長のしかた（3分）：Mac で `python3 tools/get_tokens.py threads-refresh` ➔ 表示された THREADS_ACCESS_TOKEN を "
             "GitHub の Secrets で上書き、THREADS_TOKEN_EXPIRES を Variables で上書き（チャットには貼らない）。"
             "期限が切れてしまったら `python3 tools/get_tokens.py threads` で取り直す。")


def api(path, **params):
    params["access_token"] = q.need("THREADS_ACCESS_TOKEN")
    return q.http("GET", f"{q.THREADS_API}/{path}", params=params)


tell = q.tell


def check_token(now):
    """戻り値：(ok, 知らせる文 or None, 画面用の文, ユーザーID)"""
    try:
        me = api("me", fields="id,username")
    except q.ApiError as err:
        if err.code == "missing_token":
            return False, None, f"✗ 鍵が未登録: {err.message}", None
        bad = err.code == "190" or err.http_status in (400, 401)
        head = "鍵が使えなくなっています" if bad else "Threads に接続できませんでした"
        return False, (f"[info][title]【Threads】{head}（自動投稿・数字の取得が止まります）[/title]"
                       f"{err}\n{FIX_STEPS if bad else '一時的な障害の可能性。次の回で自動的に再確認します。'}[/info]"), f"✗ {head}: {err}", None
    line = f"✓ 鍵 OK（@{me.get('username', '?')}）"
    expires = os.environ.get("THREADS_TOKEN_EXPIRES", "").strip()
    if not expires:
        return True, None, line + "（期限の見張りは Variables に THREADS_TOKEN_EXPIRES を入れると有効）", me.get("id")
    try:
        day = datetime.date.fromisoformat(expires)
    except ValueError:
        return True, None, line + f"（THREADS_TOKEN_EXPIRES={expires} が 2027-01-06 の形ではない）", me.get("id")
    left = (day - now.astimezone(JST).date()).days
    line += f"／鍵の期限: あと{left}日（{day:%m/%d}）"
    msg = None
    if left <= WARN_DAYS:
        msg = f"[info][title]【Threads】鍵の期限まで あと{left}日（{day:%m/%d}）[/title]{FIX_STEPS}[/info]"
    return True, msg, line, me.get("id")


def parse(res):
    """total_value の数字と、日ごとの values（閲覧）の合計の両方を読む。"""
    out = {}
    for d in res.get("data", []):
        if "total_value" in d:
            out[d.get("name")] = (d["total_value"] or {}).get("value", "")
        elif d.get("values"):
            out[d.get("name")] = sum(int(v.get("value") or 0) for v in d["values"])
    return out


def ask(path, metrics, **params):
    """まとめて1回で聞き、だめなら1つずつ聞く。取れないものは ''。"""
    try:
        got = parse(api(path, metric=",".join(metrics), **params))
        return {m: got.get(m, "") for m in metrics}
    except q.ApiError:
        pass
    out = {}
    for m in metrics:
        try:
            out[m] = parse(api(path, metric=m, **params)).get(m, "")
        except q.ApiError as err:
            print(f"  - {m}: 取れず（{err.message[:80]}）")
            out[m] = ""
    return out


def account_rows(uid, now, days):
    today = now.astimezone(JST).date()
    followers = ask(f"{uid}/threads_insights", ["followers_count"]).get("followers_count", "")
    rows = []
    for i in range(days):
        day = today - datetime.timedelta(days=i)
        since = datetime.datetime.combine(day, datetime.time(0, 0), JST)
        until = min(since + datetime.timedelta(days=1), now)
        row = {"date": day.isoformat(), "followers": followers if i == 0 else None, "fetched_at": f"{now:%Y-%m-%d %H:%M}"}
        row.update(ask(f"{uid}/threads_insights", ACCOUNT_METRICS, since=int(since.timestamp()), until=int(until.timestamp())))
        rows.append(row)
    return rows


def media_rows(now, recent_days=14):
    rows = []
    for x in api("me/threads", fields="id,text,timestamp,permalink", limit=30).get("data", []):
        posted = q_time(x["timestamp"])
        if now - posted > datetime.timedelta(days=recent_days):
            continue
        row = {"id": x["id"], "posted_at": f"{posted.astimezone(JST):%Y-%m-%d %H:%M}", "permalink": x.get("permalink", ""),
               "text_head": (x.get("text") or "").replace("\n", " ")[:30], "fetched_at": f"{now:%Y-%m-%d %H:%M}"}
        row.update(ask(f"{x['id']}/insights", MEDIA_METRICS))
        rows.append(row)
    return rows


def q_time(ts):
    return datetime.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S%z")


def summary_text(now, acc, media):
    today = acc[0] if acc else {}
    best = sorted([m for m in media if str(m.get("replies", "")).isdigit()], key=lambda m: -int(m["replies"]))[:3]
    lines = [f"閲覧 {today.get('views', '?')}／返信 {today.get('replies', '?')}／再投稿 {today.get('reposts', '?')}"
             f"／リンクのクリック {today.get('clicks') or '?'}／フォロワー {today.get('followers', '?')}"]
    if best:
        lines.append("返信が多い投稿（14日）：" + "、".join(f"{b['text_head'][:12]}… {b['replies']}" for b in best))
    lines.append("※数字は遅れて確定することがあります（毎晩3日分を取り直します）")
    return f"[info][title]【Threads】今日の数字 {now:%m/%d}[/title]" + "\n".join(lines) + "[/info]"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=3)
    ap.add_argument("--token-only", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--now")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    dry = os.environ.get("DRY_RUN", "0") != "0"
    now = datetime.datetime.fromisoformat(args.now) if args.now else datetime.datetime.now(JST)
    now = now if now.tzinfo else now.replace(tzinfo=JST)
    ok, alert, line, uid = check_token(now)
    print(line)
    if alert:
        tell(alert, dry)
    if not ok:
        sys.exit(1)
    if args.token_only:
        return
    acc = account_rows(uid, now, args.days)
    media = media_rows(now)
    print(f"アカウント {len(acc)}日分・投稿 {len(media)}件")
    if acc and all(acc[0].get(m) in ("", None) for m in ACCOUNT_METRICS):
        tell("[info][title]【Threads】数字が1つも取れませんでした[/title]鍵に threads_manage_insights の権限が無い可能性があります。"
             "`python3 tools/get_tokens.py threads` で取り直し（許可の画面で数字の権限も許可）➔ GitHub Secrets を上書きしてください。[/info]", dry)
    if not dry:
        q.upsert(OUT / "threads_account_daily.csv", ACCOUNT_COLS, "date", acc)
        q.upsert(OUT / "threads_media.csv", MEDIA_COLS, "id", media)
    tell(summary_text(now, acc, media), dry)


# ---------------------------------------------------------------------------
# 通信なしの動作確認
# ---------------------------------------------------------------------------
def self_test():
    import csv
    import tempfile
    global OUT
    real = (OUT, q.http)
    OUT = Path(tempfile.mkdtemp())
    os.environ["THREADS_ACCESS_TOKEN"] = os.environ.get("THREADS_ACCESS_TOKEN") or "test"
    now = datetime.datetime(2026, 11, 10, 23, 50, tzinfo=JST)

    def fake(method, url, params=None, **kw):
        if url.endswith("/me"):
            return {"id": "u1", "username": "macachette_sports"}
        if url.endswith("/u1/threads_insights"):
            ms = params["metric"].split(",")
            if "clicks" in ms and len(ms) > 1:
                raise q.ApiError(400, "not supported", "100")  # まとめて聞くと失敗 ➔ 1つずつ
            if ms == ["clicks"]:
                raise q.ApiError(400, "not supported", "100")
            return {"data": [{"name": "views", "values": [{"value": 3}, {"value": 4}]} if m == "views"
                             else {"name": m, "total_value": {"value": 9}} for m in ms]}
        if url.endswith("/me/threads"):
            return {"data": [{"id": "t1", "text": "社会人になって、1人でスポーツ始めた人いる？", "timestamp": "2026-11-10T03:00:00+0000"},
                             {"id": "old", "text": "前の", "timestamp": "2026-10-01T03:00:00+0000"}]}
        if url.endswith("/insights"):
            return {"data": [{"name": m, "values": [{"value": 2}]} for m in params["metric"].split(",")]}
        raise AssertionError(url)
    q.http = fake
    try:
        ok, alert, line, uid = check_token(now)
        assert ok and uid == "u1" and alert is None, line
        os.environ["THREADS_TOKEN_EXPIRES"] = "2026-11-20"
        ok, alert, line, uid = check_token(now)
        assert alert and "あと10日" in alert and "threads-refresh" in alert, alert
        os.environ.pop("THREADS_TOKEN_EXPIRES")
        acc = account_rows("u1", now, 2)
        assert acc[0]["views"] == 7 and acc[0]["replies"] == 9 and acc[0]["clicks"] == "" and acc[0]["followers"] == 9, acc[0]
        media = media_rows(now)
        assert [m["id"] for m in media] == ["t1"] and media[0]["replies"] == 2, media
        q.upsert(OUT / "t.csv", ACCOUNT_COLS, "date", acc)
        rows = list(csv.DictReader((OUT / "t.csv").open(encoding="utf-8")))
        assert len(rows) == 2 and "返信が多い" in summary_text(now, acc, media)

        def broken(method, url, params=None, **kw):
            raise q.ApiError(400, "Error validating access token", "190")
        q.http = broken
        ok, alert, line, uid = check_token(now)
        assert not ok and "鍵が使えなくなっています" in alert and "get_tokens.py threads" in alert
        print("self-test OK")
    finally:
        OUT, q.http = real
        os.environ.pop("THREADS_TOKEN_EXPIRES", None)


if __name__ == "__main__":
    main()
