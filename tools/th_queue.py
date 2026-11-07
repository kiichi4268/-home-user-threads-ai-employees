#!/usr/bin/env python3
"""Threads の承認制投稿キュー（GitHub Actions から1時間ごとに実行する）。Instagram 運用会社（-ai_employees-）の ig_queue.py と同じ流れ。

流れ:
  1. Claude が content/threads/posts/*.json（下書き）を作り、PR を出す
  2. 人が GitHub で PR を「Merge」する ＝ 承認
  3. main に入った下書きを、予定時刻に GitHub Actions が Threads に投稿し、ChatWork に結果を知らせる

使い方:
  python3 tools/th_queue.py --check                  # 下書きの形を確かめる（PR で自動実行。何も送らない）
  python3 tools/th_queue.py                          # 予定時刻を過ぎた下書きを投稿する（DRY_RUN=1 なら送らない）
  python3 tools/th_queue.py --now 2026-11-10T12:05   # その時刻として動かす（確認用）
  python3 tools/th_queue.py --self-test              # 通信なしの動作確認

下書き（1投稿1ファイル）:
  {"id": "2026-11-10-th-01", "scheduled_at": "2026-11-10T12:00:00+09:00",
   "text": "1投稿目の本文（500字以内・URLは公式LINEだけ・タグは1つまで）",
   "thread": ["2投稿目（1投稿目への自分の返信としてつなげる）", "..."],
   "media": ["2026-11-09_carousel_01.jpg"], "note": "企画メモ（投稿されない）"}
  - media は1投稿目に付ける写真（JPG）0〜10枚。0枚＝文章だけ、1枚＝画像、2枚以上＝カルーセル。
    写真は content/threads/media/ に置く（Instagram 運用会社の完成品をコピーして使ってよい。顔は隠したものだけ）。
  - 動画は未対応（Threads は公開URLで受け取るが、置き場が決まっていないため）。
  - thread は省略可。

同じ投稿を2回出さないよう、投稿前に Threads 側の最近の投稿を見て、同じ本文があれば送らない。
予定時刻から WINDOW を過ぎた下書きは送らずに ChatWork に知らせる。
鍵は環境変数（GitHub Secrets）: THREADS_ACCESS_TOKEN・WORDPRESS_TOKEN（写真の公開URL用。文章だけなら不要）・CHATWORK_API_TOKEN
"""

import argparse
import datetime
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import common as q  # noqa: E402

JST = q.JST
POSTS = ROOT / "content" / "threads" / "posts"
MEDIA_DIRS = [ROOT / "content" / "threads" / "media"]
WINDOW = datetime.timedelta(hours=2)
TEXT_LIMIT = 500          # Threads の1投稿の上限
TAG_LIMIT = 1             # Threads のトピック（#）は1投稿に1つ
MEDIA_LIMIT = 10          # Threads のカルーセルは20枚までだが、Instagram に合わせて10枚まで
THREAD_LIMIT = 5          # つなげる投稿（返信）の数の上限（読み切れる長さに抑える）
IMAGE_EXT = {".jpg", ".jpeg"}
ALLOWED_URLS = {"https://lin.ee/WIbLPFV"}  # 本文に書いてよいURL（公式LINE）。増やすときは CLAUDE.md と合わせる
URL_RE = re.compile(r"https?://[^\s）)」』、。]+")


def media_path(name):
    for d in MEDIA_DIRS:
        if (d / name).exists():
            return d / name
    return None


def load():
    return sorted((json.loads(p.read_text(encoding="utf-8")) | {"_file": p.name} for p in POSTS.glob("*.json")),
                  key=lambda p: (p.get("scheduled_at", ""), p.get("id", "")))


def texts(p):
    return [p.get("text", "")] + list(p.get("thread") or [])


def validate(posts):
    errors, ids = [], set()
    for p in posts:
        where = p.get("_file", "?")
        if p.get("id") in ids:
            errors.append(f"{where}: id {p.get('id')} が重複している")
        ids.add(p.get("id"))
        try:
            at = datetime.datetime.fromisoformat(p["scheduled_at"])
            if at.tzinfo is None:
                errors.append(f"{where}: scheduled_at に +09:00 を付ける")
        except (KeyError, ValueError):
            errors.append(f"{where}: scheduled_at が 2026-11-10T12:00:00+09:00 の形ではない")
        if not isinstance(p.get("thread", []), list):
            errors.append(f"{where}: thread は文字列のリストにする")
            continue
        if len(p.get("thread") or []) > THREAD_LIMIT:
            errors.append(f"{where}: thread は {THREAD_LIMIT} 個まで")
        for i, t in enumerate(texts(p)):
            label = "text" if i == 0 else f"thread[{i - 1}]"
            if not str(t).strip():
                errors.append(f"{where}: {label} が空")
            if len(t) > TEXT_LIMIT:
                errors.append(f"{where}: {label} が {len(t)}/{TEXT_LIMIT} 字")
            if len(re.findall(r"#\S+", t)) > TAG_LIMIT:
                errors.append(f"{where}: {label} のタグ（#）は{TAG_LIMIT}つまで（Threads はトピック1つ）")
            for url in URL_RE.findall(t):
                if url not in ALLOWED_URLS:
                    errors.append(f"{where}: {label} のURL {url} は書かない（書いてよいのは公式LINE {sorted(ALLOWED_URLS)[0]} だけ）")
        media = p.get("media") or []
        if len(media) > MEDIA_LIMIT:
            errors.append(f"{where}: media は {MEDIA_LIMIT} 枚まで")
        for name in media:
            if Path(name).suffix.lower() not in IMAGE_EXT:
                errors.append(f"{where}: {name} は JPG にする（動画は未対応）")
            if media_path(name) is None:
                errors.append(f"{where}: {name} が content/threads/media/ にない")
    return errors


# ---------------------------------------------------------------------------
# Threads への送信（q.http を使うのでテストで差し替えられる）
# ---------------------------------------------------------------------------
def api(method, path, **params):
    params["access_token"] = q.need("THREADS_ACCESS_TOKEN")
    return q.http(method, f"{q.THREADS_API}/{path}", params=params)


def wait(cid):
    """画像のコンテナは処理が終わってから公開する（終わる前に公開すると失敗するため）。"""
    for _ in range(30):
        state = api("GET", cid, fields="status,error_message")
        if state.get("status") in (None, "FINISHED", "PUBLISHED"):
            return cid
        if state.get("status") in ("ERROR", "EXPIRED"):
            raise q.ApiError(400, f"Threads の画像の処理に失敗（{state.get('error_message', '')}）", "media")
        time.sleep(wait.poll_sec)
    raise q.ApiError(504, "Threads の処理が時間内に終わらない（timeout）", "media")


wait.poll_sec = 10


def first_container(p):
    paths = [media_path(n) for n in p.get("media") or []]
    if not paths:
        return api("POST", "me/threads", media_type="TEXT", text=p["text"])["id"]
    if len(paths) == 1:
        return wait(api("POST", "me/threads", media_type="IMAGE", image_url=q.wordpress_media_url(paths[0]),
                        text=p["text"])["id"])
    children = [wait(api("POST", "me/threads", media_type="IMAGE", is_carousel_item="true",
                         image_url=q.wordpress_media_url(x))["id"]) for x in paths]
    return wait(api("POST", "me/threads", media_type="CAROUSEL", children=",".join(children), text=p["text"])["id"])


def publish(p):
    first = api("POST", "me/threads_publish", creation_id=first_container(p))["id"]
    reply_to = first
    for t in p.get("thread") or []:
        cid = api("POST", "me/threads", media_type="TEXT", text=t, reply_to_id=reply_to)["id"]
        reply_to = api("POST", "me/threads_publish", creation_id=cid)["id"]
    return api("GET", first, fields="permalink").get("permalink", first)


def already_posted(p):
    """同じ本文の投稿が、最近の Threads にもうあるか。"""
    items = api("GET", "me/threads", fields="text", limit=25)
    return any((x.get("text") or "").strip() == p["text"].strip() for x in items.get("data", []))


tell = q.tell


CHECKS = [
    ("Threads", "THREADS_ACCESS_TOKEN", lambda: api("GET", "me", fields="username").get("username")),
    ("WordPress", "WORDPRESS_TOKEN", lambda: q.http("GET", f"{q.WORDPRESS_SITE_API}/users/me", headers={
        "Authorization": f"Bearer {os.environ['WORDPRESS_TOKEN']}"}).get("name")),
    ("ChatWork", "CHATWORK_API_TOKEN", lambda: q.http("GET", "https://api.chatwork.com/v2/me", headers={
        "X-ChatWorkToken": os.environ["CHATWORK_API_TOKEN"]}).get("name")),
]


def check_keys():
    """鍵が GitHub Secrets に入っていて、本物として通るかを読み取りだけで確かめる（何も投稿しない）。"""
    ng = 0
    for label, name, probe in CHECKS:
        if not os.environ.get(name):
            ng += label == "Threads"  # WordPress は写真付きのときだけ、ChatWork は通知だけに要る
            print(f"{'✗' if label == 'Threads' else '－'} 鍵 {label}: 未登録（{name}）")
            continue
        try:
            print(f"✓ 鍵 {label}: OK（{probe()}）")
        except q.ApiError as err:
            ng += 1
            print(f"✗ 鍵 {label}: NG {q.mask(err)}（401・190 なら貼り間違いか期限切れ）")
    return ng


def run(now, dry):
    posts = load()
    errors = validate(posts)
    if errors:
        print("\n".join(errors))
        tell("[info][title]【Threads】下書きの形がおかしいため、今回は送りませんでした[/title]" + "\n".join(errors[:10]) + "[/info]", dry)
        return {"failed": list(errors)}
    summary = {"sent": [], "failed": [], "skipped": [], "expired": [], "planned": []}
    for p in posts:
        at = datetime.datetime.fromisoformat(p["scheduled_at"])
        if at > now:
            continue
        if now - at > WINDOW:
            if now - at <= WINDOW + datetime.timedelta(hours=1):  # 期限切れの知らせは1回だけ
                summary["expired"].append(p["id"])
                tell(f"[info][title]【Threads】予定時刻を過ぎたため送りませんでした[/title]{p['id']}（予定 {at:%m/%d %H:%M}）[/info]", dry)
            continue
        if dry:
            summary["planned"].append(p["id"])
            print(f"○ {p['id']}: DRY_RUN のため送らない（本番なら {1 + len(p.get('thread') or [])} 投稿・写真 {len(p.get('media') or [])} 枚）")
            continue
        try:
            if already_posted(p):
                summary["skipped"].append(p["id"])
                print(f"- {p['id']}: もう投稿されているので送らない")
                continue
            url = publish(p)
            summary["sent"].append(p["id"])
            print(f"✓ {p['id']}: 投稿しました {url}")
            tell(f"[info][title]【Threads】投稿しました[/title]{p['id']}\n{url}[/info]", dry)
        except q.ApiError as err:
            summary["failed"].append(p["id"])
            print(f"✗ {p['id']}: 失敗 {err}")
            tell(q.failure_message(p["id"], p["scheduled_at"], err, p["text"]), dry)
    return summary


# ---------------------------------------------------------------------------
# 通信なしの動作確認
# ---------------------------------------------------------------------------
def self_test():
    import tempfile
    global POSTS, MEDIA_DIRS
    real = (POSTS, MEDIA_DIRS, q.http, q.send_chatwork)
    tmp = Path(tempfile.mkdtemp())
    POSTS, MEDIA_DIRS = tmp / "posts", [tmp / "media"]
    POSTS.mkdir()
    MEDIA_DIRS[0].mkdir()
    for name in ("a.jpg", "b.jpg"):
        (MEDIA_DIRS[0] / name).write_bytes(b"x")

    def write(pid, at, text, thread=None, media=None):
        (POSTS / f"{pid}.json").write_text(json.dumps(
            {"id": pid, "scheduled_at": at, "text": text, "thread": thread or [], "media": media or []}, ensure_ascii=False))

    write("text", "2026-11-10T12:00:00+09:00", "社会人になって、1人でスポーツ始めた人いる？ #社会人サークル",
          ["答え3つ", "申し込みは公式LINEから https://lin.ee/WIbLPFV"])
    write("image", "2026-11-10T12:00:00+09:00", "画像つき", media=["a.jpg"])
    write("carousel", "2026-11-10T12:00:00+09:00", "カルーセル", media=["a.jpg", "b.jpg"])
    write("later", "2026-11-10T21:00:00+09:00", "夜の投稿")
    write("old", "2026-11-10T08:00:00+09:00", "朝の投稿")
    calls, sent, state = [], [], {"posted": []}

    def fake(method, url, **kw):
        params = {k: v for k, v in (kw.get("params") or {}).items() if k != "access_token"}
        calls.append((method, url.rsplit("/", 1)[-1], params))
        if url.endswith("wordpress.com/media") or url.endswith("/media"):
            return {"source_url": "https://img/x.jpg"}
        if url.endswith("/me/threads") and method == "GET":
            return {"data": [{"text": t} for t in state["posted"]]}
        if url.endswith("/me/threads"):
            return {"id": f"C{len(calls)}"}
        if url.endswith("/threads_publish"):
            return {"id": f"P{len(calls)}"}
        if params.get("fields") == "status,error_message":
            return {"status": "FINISHED"}
        return {"permalink": "https://www.threads.net/@macachette_sports/post/x"}

    q.http = fake
    q.send_chatwork = lambda body, token: sent.append(body)
    wait.poll_sec = 0
    os.environ.update(THREADS_ACCESS_TOKEN="T", WORDPRESS_TOKEN="W", CHATWORK_API_TOKEN="c")
    try:
        assert not validate(load()), validate(load())
        s = run(datetime.datetime.fromisoformat("2026-11-10T12:05:00+09:00"), dry=True)
        assert s["planned"] == ["carousel", "image", "text"] and not calls, s

        s = run(datetime.datetime.fromisoformat("2026-11-10T12:05:00+09:00"), dry=False)
        assert s["sent"] == ["carousel", "image", "text"], s
        creates = [c[2] for c in calls if c[0] == "POST" and c[1] == "threads"]
        assert [c.get("media_type") for c in creates].count("CAROUSEL") == 1
        assert sum(1 for c in creates if c.get("is_carousel_item")) == 2
        replies = [c for c in creates if c.get("reply_to_id")]
        assert len(replies) == 2 and replies[1]["reply_to_id"] != replies[0]["reply_to_id"], replies  # 順につながる
        assert len(sent) == 3 and all("投稿しました" in b for b in sent), sent

        calls.clear()
        state["posted"] = ["社会人になって、1人でスポーツ始めた人いる？ #社会人サークル"]
        s = run(datetime.datetime.fromisoformat("2026-11-10T12:35:00+09:00"), dry=False)
        assert "text" in s["skipped"], s  # 同じ本文は2回出さない

        s = run(datetime.datetime.fromisoformat("2026-11-10T14:30:00+09:00"), dry=False)
        assert s["expired"] == ["carousel", "image", "text"], s

        write("bad", "2026-11-11T12:00", "x" * 501 + " #a #b https://example.com", media=["none.png"])
        errs = validate(load())
        for word in ("+09:00", "/500 字", "タグ", "example.com", "JPG", "ない"):
            assert any(word in e for e in errs), (word, errs)
    finally:
        POSTS, MEDIA_DIRS, q.http, q.send_chatwork = real
    print("self-test: 文章・画像・カルーセル・連続投稿・DRY_RUN・二重投稿の防止・期限切れ・下書きの形チェック すべて想定どおり")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="下書きの形だけ確かめる（何も送らない）")
    parser.add_argument("--now", help="この時刻として動かす（例 2026-11-10T12:05。日本時間）")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    posts = load()
    if args.check:
        errors = validate(posts)
        for p in posts:
            print(f"・{p['scheduled_at'][:16].replace('T', ' ')} {1 + len(p.get('thread') or [])}投稿 {p['id']}")
        print("\n".join(errors) or f"OK: 下書き {len(posts)}件、形の問題なし")
        sys.exit(1 if errors else 0)
    q.load_env()
    dry = os.environ.get("DRY_RUN", "1") != "0"
    now = datetime.datetime.fromisoformat(args.now) if args.now else datetime.datetime.now(JST)
    now = now if now.tzinfo else now.replace(tzinfo=JST)
    print(f"Threads キュー {now:%Y-%m-%d %H:%M}（{'DRY_RUN：送信しない' if dry else '本番：送信する'}）")
    bad_keys = check_keys() if dry and os.environ.get("GITHUB_ACTIONS") else 0
    summary = run(now, dry)
    print("結果: " + "、".join(f"{k} {len(v)}件" for k, v in summary.items()))
    if summary.get("failed") or bad_keys:
        sys.exit(1)


if __name__ == "__main__":
    main()
