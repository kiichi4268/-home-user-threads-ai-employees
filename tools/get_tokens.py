#!/usr/bin/env python3
"""自動投稿に使うアクセストークンを、ブラウザで「許可」を1回押すだけで取得して .env に保存する（ご本人のPCで実行する）。

使い方:
  python3 tools/get_tokens.py threads           # THREADS_ACCESS_TOKEN・THREADS_TOKEN_EXPIRES（60日。期限前に threads-refresh で延長）
  python3 tools/get_tokens.py threads-refresh   # 期限を延ばす（鍵を取ってから24時間たてば延長できる）
  python3 tools/get_tokens.py wordpress         # WORDPRESS_TOKEN（写真付きの投稿だけに使う。Instagram 運用会社と同じ値でよい）

流れ:
  1. 各アプリの設定画面に「リダイレクトURI」を登録しておく（既定は http://localhost:8080/callback。
     https しか登録できない媒体は、環境変数 OAUTH_REDIRECT_URI に登録したURL（例：自分のサイトのURL）を入れて実行する）
  2. 表示されたURLがブラウザで開くので、ログインして「許可」を押す
  3. localhost のときは自動で受け取る。それ以外は、許可したあとのブラウザのアドレス欄のURLを丸ごとコピーして貼り付ける
  4. トークンを .env に書き込む（画面には伏せ字で表示。チャットやリポジトリには貼らない）

必要な鍵（.env）: THREADS_APP_ID/SECRET（写真付きの投稿もするなら WORDPRESS_CLIENT_ID/SECRET）
取得したトークンは GitHub の Settings ➔ Secrets and variables ➔ Actions に、同じ名前でご自身で登録する。
"""

import http.server
import json
import os
import secrets
import sys
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV = ROOT / ".env"
# Threads は https の戻り先URLしか登録できない（と考えられる）ため、既定を WordPress のサイトにしている。
# アプリの「リダイレクトコールバックURL」に登録したものと1文字も違わないこと。
REDIRECT = os.environ.get("OAUTH_REDIRECT_URI", "https://sportsbackstage1.wordpress.com/")
WORDPRESS_SITE = "sportsbackstage1.wordpress.com"


def load_env():
    if ENV.exists():
        for line in ENV.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def need(name):
    value = os.environ.get(name)
    if not value:
        sys.exit(f"{name} が .env にありません")
    return value


def save(values):
    """.env の該当キーだけを書き換える（ほかの行はそのまま）。"""
    lines = ENV.read_text(encoding="utf-8").splitlines() if ENV.exists() else []
    done = set()
    for i, line in enumerate(lines):
        key = line.split("=", 1)[0].strip()
        if key in values:
            lines[i], done = f"{key}={values[key]}", done | {key}
    lines += [f"{k}={v}" for k, v in values.items() if k not in done]
    ENV.write_text("\n".join(lines) + "\n", encoding="utf-8")
    ENV.chmod(0o600)
    for k, v in values.items():
        print(f"  .env に保存：{k}={v[:4]}…{v[-4:]}（{len(v)}文字）")


def post(url, form):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(form).encode(),
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    return call(req)


def get(url, params):
    return call(urllib.request.Request(f"{url}?{urllib.parse.urlencode(params)}"))


def call(req):
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return json.loads(res.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"取得に失敗しました（HTTP {e.code}）：{e.read().decode(errors='replace')[:300]}")


def authorize(url, params):
    """ブラウザで許可してもらい、リダイレクト先URLの code を受け取る。"""
    state = secrets.token_urlsafe(16)
    full = f"{url}?{urllib.parse.urlencode({**params, 'state': state})}"
    print(f"\n次のURLをブラウザで開いて「許可」を押してください（自動で開かないときはコピーして開く）：\n{full}\n")
    webbrowser.open(full)
    target = urllib.parse.urlparse(REDIRECT)
    if target.hostname in ("localhost", "127.0.0.1"):
        got = {}

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                got.update(urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query))
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write("受け取りました。この画面は閉じてOKです。".encode())

            def log_message(self, *args):
                pass
        server = http.server.HTTPServer((target.hostname, target.port or 80), Handler)
        while "code" not in got and "error" not in got:
            server.handle_request()
        query = got
    else:
        pasted = input("許可したあとのブラウザのアドレス欄のURLを貼り付けて Enter：").strip()
        query = urllib.parse.parse_qs(urllib.parse.urlparse(pasted).query)
    if "error" in query:
        sys.exit(f"許可されませんでした：{query.get('error_description', query['error'])[0]}")
    if query.get("state", [""])[0] != state:
        sys.exit("state が一致しません（別のURLを貼り付けた可能性）。もう一度実行してください")
    return query["code"][0]


def wordpress():
    cid, secret = need("WORDPRESS_CLIENT_ID"), need("WORDPRESS_CLIENT_SECRET")
    code = authorize("https://public-api.wordpress.com/oauth2/authorize",
                     {"client_id": cid, "redirect_uri": REDIRECT, "response_type": "code", "blog": WORDPRESS_SITE})
    res = post("https://public-api.wordpress.com/oauth2/token", {
        "client_id": cid, "client_secret": secret, "redirect_uri": REDIRECT, "code": code,
        "grant_type": "authorization_code"})
    save({"WORDPRESS_TOKEN": res["access_token"]})




def threads():
    app_id, secret = need("THREADS_APP_ID"), need("THREADS_APP_SECRET")
    code = authorize("https://threads.net/oauth/authorize", {
        "client_id": app_id, "redirect_uri": REDIRECT, "response_type": "code",
        "scope": "threads_basic,threads_content_publish,threads_manage_insights"})
    short = post("https://graph.threads.net/oauth/access_token", {
        "client_id": app_id, "client_secret": secret, "redirect_uri": REDIRECT, "code": code.split("#")[0],
        "grant_type": "authorization_code"})["access_token"]
    long = get("https://graph.threads.net/access_token",
               {"grant_type": "th_exchange_token", "client_secret": secret, "access_token": short})
    save({"THREADS_ACCESS_TOKEN": long["access_token"]})
    threads_expiry(long.get("expires_in", 5184000))


def threads_refresh():
    res = get("https://graph.threads.net/refresh_access_token",
              {"grant_type": "th_refresh_token", "access_token": need("THREADS_ACCESS_TOKEN")})
    save({"THREADS_ACCESS_TOKEN": res["access_token"]})
    threads_expiry(res.get("expires_in", 5184000))


def threads_expiry(seconds):
    """期限の日付を .env に残し、GitHub の Variables に入れる値を表示する（th_insights.py が14日前から知らせる）。"""
    import datetime
    day = (datetime.date.today() + datetime.timedelta(seconds=int(seconds))).isoformat()
    save({"THREADS_TOKEN_EXPIRES": day})
    print(f"  有効期限：{day}（約{int(seconds) // 86400}日）。GitHub の Variables に THREADS_TOKEN_EXPIRES = {day} を登録（上書き）してください")
    print("  期限が来る前に `python3 tools/get_tokens.py threads-refresh` で延長します（鍵を取ってから24時間たてば延長できる）")


COMMANDS = {"threads": threads, "threads-refresh": threads_refresh, "wordpress": wordpress}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
        sys.exit(__doc__)
    load_env()
    print(f"リダイレクトURI：{REDIRECT}（アプリの設定画面に登録したものと1文字も違わないこと）")
    COMMANDS[sys.argv[1]]()
    print("完了。GitHub の Secrets にも同じ名前で登録してください（値はチャットに貼らない）")
