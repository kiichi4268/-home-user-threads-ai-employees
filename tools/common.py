"""Threads 運用会社の共通部品（通信・鍵・ChatWork 通知・CSV 保存）。標準ライブラリだけで動く。

鍵は環境変数（GitHub Secrets、手元では .env）だけで渡す。コード・JSON・チャットには書かない。
"""

import csv
import datetime
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JST = datetime.timezone(datetime.timedelta(hours=9))
THREADS_API = "https://graph.threads.net/v1.0"
WORDPRESS_SITE_API = "https://public-api.wordpress.com/wp/v2/sites/sportsbackstage1.wordpress.com"
CHATWORK_ROOM_ID = "363171715"
MAX_ATTEMPTS = 3
SECRET_RE = re.compile(
    r"(?i)(bearer\s+|token[\"'=:\s]+|access_token=|x-chatworktoken[\"'=:\s]+|password[\"'=:\s]+|secret[\"'=:\s]+)[^\s\"',&]+")


class ApiError(Exception):
    def __init__(self, http_status, message, code=""):
        super().__init__(f"HTTP {http_status} {message}")
        self.http_status, self.message, self.code = http_status, message, code


def mask(text):
    """エラー文に混ざった鍵を伏せ字にする。"""
    return SECRET_RE.sub(lambda m: m.group(1) + "****", str(text))


def load_env(path=ROOT / ".env"):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def need(name):
    value = os.environ.get(name)
    if not value:
        raise ApiError(401, f"{name} が設定されていません（GitHub Secrets または .env）", "missing_token")
    return value


def http(method, url, *, params=None, form=None, body=None, headers=None, raw=None):
    """通信（テストでは差し替える）。"""
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    headers = dict(headers or {})
    data = raw
    if form is not None:
        data = urllib.parse.urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            text = res.read().decode() or "{}"
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        try:
            err = json.loads(detail)
            err = err.get("error", err)
            message = (err.get("message") or err.get("error_description") or detail) if isinstance(err, dict) else str(err)
            code = str(err.get("code", "")) if isinstance(err, dict) else ""
        except ValueError:
            message, code = detail[:300], ""
        raise ApiError(e.code, mask(message), code) from None
    except (urllib.error.URLError, TimeoutError) as e:
        raise ApiError(0, f"connection error: {e}") from None
    return json.loads(text) if text.strip().startswith(("{", "[")) else {"text": text}


def wordpress_media_url(path):
    """写真を WordPress のメディアに上げて公開URLを得る（Threads は写真を公開URLで受け取るため）。"""
    ctype = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    res = http("POST", f"{WORDPRESS_SITE_API}/media", raw=path.read_bytes(), headers={
        "Authorization": f"Bearer {need('WORDPRESS_TOKEN')}", "Content-Type": ctype,
        "Content-Disposition": f'attachment; filename="{path.name}"'})
    return res["source_url"]


# ---------------------------------------------------------------------------
# ChatWork
# ---------------------------------------------------------------------------
def room_id():
    return os.environ.get("CHATWORK_ROOM_ID") or CHATWORK_ROOM_ID


def send_chatwork(body, token):
    return http("POST", f"https://api.chatwork.com/v2/rooms/{urllib.parse.quote(room_id(), safe='')}/messages",
                form={"body": body}, headers={"X-ChatWorkToken": token})


def tell(text, dry):
    """ChatWork に知らせる。DRY_RUN・鍵なし・送信失敗のときは画面に出すだけ（通知の失敗で本処理を止めない）。"""
    token = os.environ.get("CHATWORK_API_TOKEN")
    if dry or not token:
        print(f"  ChatWork（{'DRY_RUN のため送らない' if dry else '鍵がないため送らない'}）:\n{text}")
        return
    try:
        send_chatwork(text, token)
    except Exception as e:
        print(f"  ChatWork への通知に失敗: {mask(e)}")


def failure_message(post_id, scheduled_at, err, text):
    hint = {401: "鍵が切れているか貼り間違い。THREADS.md「5.」の手順で鍵を取り直す",
            403: "権限が足りない。鍵を取り直すとき、許可の画面ですべての権限を許可する",
            429: "送りすぎ（Threads は24時間で250投稿まで）。次の回で自動的にやり直す"}.get(
        err.http_status, "下書きの中身（文字数・URL・写真）を確かめる。分からなければ Claude に「Threads の投稿が失敗した」と伝える")
    return (f"[info][title]【Threads】投稿に失敗しました[/title]{post_id}（予定 {scheduled_at[:16].replace('T', ' ')}）\n"
            f"エラー：{mask(err)}\n直し方：{hint}\n本文の頭：{text[:40]}[/info]")


# ---------------------------------------------------------------------------
# CSV（同じキーの行は上書き。空欄では上書きしない）
# ---------------------------------------------------------------------------
def upsert(path, cols, key, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    old = {}
    if path.exists():
        with path.open(encoding="utf-8") as f:
            for r in csv.DictReader(f):
                old[r[key]] = r
    for r in rows:
        cur = old.get(r[key], {})
        for c in cols:
            v = r.get(c)
            if v not in (None, ""):
                cur[c] = v
        cur[key] = r[key]
        old[r[key]] = cur
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for k in sorted(old):
            w.writerow({c: old[k].get(c, "") for c in cols})
