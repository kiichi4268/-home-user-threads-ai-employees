"""note の記事を Muse に渡す前に、機械で確かめる（品質管理部の 10 事実確認AI・11 表現チェックAI・12 受け渡しチェックAI）。

使い方
  python3 tools/note_check.py --check       # content/note/ の全記事を確かめる（PR のたびに GitHub Actions でも動く）
  python3 tools/note_check.py --self-test   # このツール自体のテスト

確かめること
  - meta.json：タイトル64字以内・ハッシュタグ10個まで（# で始まる）・画像があり 1280×720 か
  - 本文：参加費「1,500円（当日、現金またはPayPay）」が入っているか／URLは公式LINEだけか／
          【要追記】などの埋め残しがないか／［画像：〜］が本文画像と合っているか／有料なら「ここから有料」の行があるか
  - NG表現と参加費の書き方（tools/content_rules.py の check_expressions）
  - 読みやすさ（1行の長さ・空行のない塊）は「注意」として出すだけ（止めない）

有料エリア（paid.txt）は公開リポジトリに置かない（.gitignore）。手元にあるときだけ一緒に確かめる。
標準ライブラリだけで動く。
"""

import json
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from content_rules import check_expressions, check_readability  # noqa: E402

NOTE_DIR = ROOT / "content" / "note"
FEE_TEXT = "1,500円（当日、現金またはPayPay）"
LINE_URL = "https://lin.ee/WIbLPFV"
TITLE_MAX = 64
TAGS_MAX = 10
SIZE = (1280, 720)
PAID_MARK = "ここから有料"
PLACEHOLDERS = re.compile(r"【要追記|【要更新|【要確認|TODO|TBD|XXX")
IMAGE_MARK = re.compile(r"［画像：([^］]+)］")
URL_RE = re.compile(r"https?://[^\s）)」]+")


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


def check_text(text, label):
    errors = []
    for m in URL_RE.finditer(text):
        if m.group(0) != LINE_URL:
            errors.append(f"{label}：URL「{m.group(0)}」は書かない（書いてよいのは公式LINE {LINE_URL} だけ）")
    m = PLACEHOLDERS.search(text)
    if m:
        errors.append(f"{label}：埋め残し「{m.group(0)}」がある（Muse は文章を足さないので、完成させて渡す）")
    errors += [f"{label}：{e}" for e in check_expressions(text)]
    return errors


def check_article(folder):
    errors, warns = [], []
    name = folder.name
    meta_path = folder / "meta.json"
    if not meta_path.exists():
        return [f"{name}：meta.json がない"], []
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"{name}：meta.json が読めない（{e}）"], []

    title = meta.get("title", "")
    if not title:
        errors.append(f"{name}：タイトルがない")
    elif len(title) > TITLE_MAX:
        errors.append(f"{name}：タイトルが{len(title)}字（{TITLE_MAX}字まで）")
    tags = meta.get("hashtags", [])
    if len(tags) > TAGS_MAX:
        errors.append(f"{name}：ハッシュタグが{len(tags)}個（{TAGS_MAX}個まで）")
    for t in tags:
        if not t.startswith("#") or " " in t:
            errors.append(f"{name}：ハッシュタグ「{t}」は # で始め、空白を入れない")

    images = []
    for key in ("header_image",):
        if not meta.get(key):
            errors.append(f"{name}：見出し画像（{key}）がない")
        else:
            images.append(meta[key])
    images += meta.get("body_images", [])
    for rel in images:
        p = folder / rel
        if not p.exists():
            errors.append(f"{name}：画像 {rel} がない")
            continue
        size = png_size(p)
        if size is None:
            errors.append(f"{name}：画像 {rel} は PNG にする")
        elif rel == meta.get("header_image") and size != SIZE:
            errors.append(f"{name}：見出し画像は {SIZE[0]}×{SIZE[1]}（いまは {size[0]}×{size[1]}）")

    free = folder / "free.txt"
    if not free.exists():
        return errors + [f"{name}：free.txt（無料エリア・無料記事の本文）がない"], warns
    text = free.read_text(encoding="utf-8")
    paid = folder / "paid.txt"
    paid_text = paid.read_text(encoding="utf-8") if paid.exists() else ""
    whole = text + "\n" + paid_text

    errors += check_text(text, f"{name}/free.txt")
    if paid_text:
        errors += check_text(paid_text, f"{name}/paid.txt")
    if FEE_TEXT not in whole:
        errors.append(f"{name}：参加費「{FEE_TEXT}」が本文にない")
    if meta.get("type") == "paid":
        if PAID_MARK not in text:
            errors.append(f"{name}：有料の記事なのに、free.txt の最後に「{PAID_MARK}」の行がない")
        if not meta.get("price_steps"):
            errors.append(f"{name}：有料の記事なのに price_steps（価格の段階）がない")
    marks = IMAGE_MARK.findall(whole)
    body_names = {Path(b).name for b in meta.get("body_images", [])}
    for mk in marks:
        if mk not in body_names:
            errors.append(f"{name}：本文の［画像：{mk}］が body_images にない")
    if paid_text or meta.get("type") != "paid":
        for b in body_names - set(marks):
            errors.append(f"{name}：本文画像 {b} を入れる場所（［画像：{b}］）が本文にない")
    warns += [f"{name}：{w}" for w in check_readability(whole)]
    return errors, warns


def check_all(root=NOTE_DIR):
    errors, warns = [], []
    folders = sorted(p for p in root.iterdir() if p.is_dir()) if root.exists() else []
    for f in folders:
        e, w = check_article(f)
        errors += e
        warns += w
    return folders, errors, warns


def self_test():
    import tempfile
    import zlib

    def png(path, w, h):
        raw = b"".join(b"\x00" + b"\x00\x00\x00" * w for _ in range(h))
        def chunk(t, d):
            return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
        path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                         + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))

    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        a = root / "note_99_test"
        (a / "images").mkdir(parents=True)
        png(a / "images" / "01_header.png", 1280, 720)
        png(a / "images" / "02_x.png", 1280, 720)
        meta = {"type": "paid", "title": "テスト", "hashtags": ["#テスト"], "header_image": "images/01_header.png",
                "body_images": ["images/02_x.png"], "price_steps": [{"price": 500}]}
        (a / "meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
        good = f"参加費は1回{FEE_TEXT}です。\n［画像：02_x.png］\n申し込みは {LINE_URL}\n――　ここから有料（500円）　――\n"
        (a / "free.txt").write_text(good, encoding="utf-8")
        _, errs, _ = check_all(root)
        assert errs == [], errs
        bad = {
            "https://example.com を見てね": "URL",
            "【要追記：人数】": "埋め残し",
            "残り3名です": "残り人数",
            "参加費2,000円": "参加費",
        }
        for t, word in bad.items():
            (a / "free.txt").write_text(good + t, encoding="utf-8")
            _, errs, _ = check_all(root)
            assert any(word in e for e in errs), (t, errs)
        (a / "free.txt").write_text(good.replace(PAID_MARK, "続き"), encoding="utf-8")
        assert any(PAID_MARK in e for e in check_all(root)[1])
        (a / "free.txt").write_text(good.replace(FEE_TEXT, "1,500円"), encoding="utf-8")
        assert any("参加費" in e for e in check_all(root)[1])
        png(a / "images" / "01_header.png", 1200, 630)
        (a / "free.txt").write_text(good, encoding="utf-8")
        assert any("1280×720" in e for e in check_all(root)[1])
        png(a / "images" / "01_header.png", 1280, 720)
        meta["title"] = "あ" * 65
        meta["hashtags"] = ["#a"] * 11
        (a / "meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
        errs = check_all(root)[1]
        assert any("タイトル" in e for e in errs) and any("ハッシュタグ" in e for e in errs), errs
    print("note_check self-test OK")


def main(argv):
    if "--self-test" in argv:
        self_test()
        return 0
    folders, errors, warns = check_all()
    for w in warns:
        print(f"注意 {w}")
    for e in errors:
        print(f"✗ {e}")
    if errors:
        print(f"NG：{len(errors)}件（{len(folders)}本の記事）")
        return 1
    print(f"OK：{len(folders)}本の記事")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
