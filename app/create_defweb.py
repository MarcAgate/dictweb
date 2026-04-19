import hashlib
import hmac
import os
import re
import sys
from urllib.parse import quote_plus

import pyewts

from app.db import get_connection

SEARCH_LINK_SECRET = os.getenv("DICTWEB_SEARCH_LINK_SECRET", "CHANGE-ME-SEARCH-LINK-SECRET")

converter = pyewts.pyewts()

TIBETAN_RUN_RE = re.compile(r"[\u0F00-\u0FFF]+")
BODY_RE = re.compile(r"<body\b[^>]*>(.*?)</body>", re.IGNORECASE | re.DOTALL)
HEAD_RE = re.compile(r"<head\b[^>]*>.*?</head>", re.IGNORECASE | re.DOTALL)
SCRIPT_RE = re.compile(r"<script\b[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL)
STYLE_RE = re.compile(r"<style\b[^>]*>.*?</style>", re.IGNORECASE | re.DOTALL)
HTML_TAG_RE = re.compile(r"</?(html|body|head|meta|title|link|doctype)[^>]*>", re.IGNORECASE)
TAG_RE = re.compile(r"(<[^>]+>|[^<]+)")
TRAILING_TIBETAN_PUNCTUATION = "།༎༏༐༑༔"


def sign_search_term(term: str) -> str:
    payload = (term or "").strip().encode("utf-8")
    return hmac.new(
        SEARCH_LINK_SECRET.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()


def load_known_wylie(conn) -> set[str]:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT DISTINCT wylie
        FROM dict
        WHERE wylie IS NOT NULL
          AND TRIM(wylie) <> ''
        """
    )
    return {
        (row["wylie"] or "").strip()
        for row in cur.fetchall()
        if (row["wylie"] or "").strip()
    }


def extract_definition_html(raw_html: str) -> str:
    text = raw_html or ""

    body_match = BODY_RE.search(text)
    if body_match:
        text = body_match.group(1)

    text = HEAD_RE.sub("", text)
    text = SCRIPT_RE.sub("", text)
    text = STYLE_RE.sub("", text)
    text = HTML_TAG_RE.sub("", text)

    return text.strip()


def split_tibetan_base_and_suffix(tibetan_text: str) -> tuple[str, str]:
    base = tibetan_text.rstrip(TRAILING_TIBETAN_PUNCTUATION)
    suffix = tibetan_text[len(base):]
    return base, suffix


def wrap_tibetan_plain(text: str) -> str:
    return (
        f'<span class="tibetan tibetan-plain" lang="bo" '
        f'data-script="tibetan">{text}</span>'
    )


def wrap_tibetan_link(text: str, href: str) -> str:
    return (
        f'<a href="{href}" class="def-term-link tibetan" '
        f'lang="bo" data-script="tibetan">{text}</a>'
    )


def render_tibetan_segment(tibetan_text: str, known_wylie: set[str]) -> str:
    base_text, trailing_suffix = split_tibetan_base_and_suffix(tibetan_text)

    if not base_text:
        return wrap_tibetan_plain(tibetan_text)

    try:
        normalized_wylie = converter.toWylie(base_text).strip()
    except Exception:
        return wrap_tibetan_plain(tibetan_text)

    if normalized_wylie in known_wylie:
        sig = sign_search_term(base_text)
        href = f"/search?q={quote_plus(base_text)}&match_mode=exact&sig={sig}"
        linked = wrap_tibetan_link(base_text, href)
        if trailing_suffix:
            return f"{linked}{wrap_tibetan_plain(trailing_suffix)}"
        return linked

    plain = wrap_tibetan_plain(base_text)
    if trailing_suffix:
        return f"{plain}{wrap_tibetan_plain(trailing_suffix)}"
    return plain


def replace_tibetan_markup_in_text(text: str, known_wylie: set[str]) -> str:
    def replacer(match):
        tibetan_text = match.group(0)
        return render_tibetan_segment(tibetan_text, known_wylie)

    return TIBETAN_RUN_RE.sub(replacer, text or "")


def build_defweb(definition: str, known_wylie: set[str]) -> str:
    cleaned_html = extract_definition_html(definition)

    parts = []
    for chunk in TAG_RE.findall(cleaned_html):
        if chunk.startswith("<"):
            parts.append(chunk)
        else:
            parts.append(replace_tibetan_markup_in_text(chunk, known_wylie))

    return "".join(parts).strip()


def update_defweb_for_entry(conn, entry_id: int, known_wylie: set[str]) -> bool:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, def
        FROM dict
        WHERE id = ?
        """,
        (entry_id,),
    )
    row = cur.fetchone()
    if row is None:
        return False

    definition = row["def"] or ""
    defweb = build_defweb(definition, known_wylie)

    cur.execute(
        """
        UPDATE dict
        SET defWeb = ?
        WHERE id = ?
        """,
        (defweb, entry_id),
    )
    return True


def regenerate_defweb_for_entry(entry_id: int) -> bool:
    conn = get_connection()
    try:
        known_wylie = load_known_wylie(conn)
        updated = update_defweb_for_entry(conn, entry_id, known_wylie)
        conn.commit()
        return updated
    finally:
        conn.close()


def regenerate_defweb_for_all() -> int:
    conn = get_connection()
    try:
        known_wylie = load_known_wylie(conn)
        cur = conn.cursor()
        cur.execute("SELECT id, def FROM dict")
        rows = cur.fetchall()

        updates = []
        for row in rows:
            row_id = row["id"]
            definition = row["def"] or ""
            defweb = build_defweb(definition, known_wylie)
            updates.append((defweb, row_id))

        cur.executemany("UPDATE dict SET defWeb = ? WHERE id = ?", updates)
        conn.commit()
        return len(updates)
    finally:
        conn.close()


def main():
    args = sys.argv[1:]

    if args:
        try:
            entry_id = int(args[0])
        except ValueError:
            print("Usage: python -m app.create_defweb [entry_id]")
            raise SystemExit(1)

        updated = regenerate_defweb_for_entry(entry_id)
        if updated:
            print(f"Entrée {entry_id} mise à jour dans defWeb.")
        else:
            print(f"Entrée {entry_id} introuvable.")
        return

    count = regenerate_defweb_for_all()
    print(f"{count} entrées mises à jour dans defWeb.")


if __name__ == "__main__":
    main()