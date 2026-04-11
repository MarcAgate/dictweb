from typing import Any, Dict, List, Optional

import pyewts
from tibetan_sort.tibetan_sort import TibetanSort

from app.db import get_connection

converter = pyewts.pyewts()
sorter = TibetanSort()


def contains_tibetan(text: str) -> bool:
    return any("\u0F00" <= ch <= "\u0FFF" for ch in (text or ""))


def normalize_search_term(term: str) -> str:
    term = (term or "").strip()
    if not term:
        return ""

    if contains_tibetan(term):
        return converter.toWylie(term).strip()

    return term


def build_wylie_condition(normalized: str, match_mode: str):
    if match_mode == "exact":
        return "wylie = ?", [normalized]

    if match_mode == "starts_with":
        return "wylie LIKE ?", [f"{normalized}%"]

    return "wylie LIKE ?", [f"%{normalized}%"]


def get_sort_tibetan_key(entry: Dict[str, Any]) -> str:
    tib = (entry.get("tib") or "").strip()
    wylie = (entry.get("wylie") or "").strip()

    if tib:
        return tib

    if wylie:
        try:
            return converter.toUnicode(wylie)
        except Exception:
            return wylie

    return ""


def sort_entries_by_tibetan(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not entries:
        return []

    decorated = []
    for idx, entry in enumerate(entries):
        tib_key = get_sort_tibetan_key(entry)
        decorated.append((idx, tib_key, entry))

    tib_keys = [item[1] for item in decorated]

    try:
        sorted_keys = sorter.sort_list(tib_keys)
    except Exception:
        return entries

    key_positions: Dict[str, List[int]] = {}
    for pos, key in enumerate(sorted_keys):
        key_positions.setdefault(key, []).append(pos)

    used_count: Dict[str, int] = {}

    def ranking(item):
        original_idx, tib_key, _entry = item
        positions = key_positions.get(tib_key, [999999])
        n = used_count.get(tib_key, 0)
        used_count[tib_key] = n + 1
        position = positions[min(n, len(positions) - 1)]
        return (position, original_idx)

    decorated_sorted = sorted(decorated, key=ranking)
    return [item[2] for item in decorated_sorted]


def fetch_search_rows(
    term: str,
    match_mode: str = "contains",
    sources: Optional[List[str]] = None,
    lang: str = "",
    contexte: str = "",
):
    normalized = normalize_search_term(term)

    query = """
    SELECT
        id,
        tib,
        wylie,
        source,
        contexte,
        lang,
        def,
        defWeb
    FROM dict
    WHERE 1=1
    """
    params: List[Any] = []

    if normalized:
        condition, condition_params = build_wylie_condition(normalized, match_mode)
        query += f" AND {condition}"
        params.extend(condition_params)

    clean_sources = [src.strip() for src in (sources or []) if src and src.strip()]
    if clean_sources:
        placeholders = ",".join("?" for _ in clean_sources)
        query += f" AND source IN ({placeholders})"
        params.extend(clean_sources)

    if lang.strip():
        query += " AND lang = ?"
        params.append(lang.strip())

    if contexte.strip():
        query += " AND contexte LIKE ?"
        params.append(f"%{contexte.strip()}%")

    query += " ORDER BY wylie ASC, source ASC, contexte ASC, lang ASC"

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        return cur.fetchall()
    finally:
        conn.close()


def build_entries_from_rows(rows) -> List[Dict[str, Any]]:
    by_wylie: Dict[str, Dict[str, Any]] = {}

    for row in rows:
        wylie = (row["wylie"] or "").strip()
        tib = (row["tib"] or "").strip()

        if not wylie:
            continue

        if wylie not in by_wylie:
            by_wylie[wylie] = {
                "key": wylie,
                "wylie": wylie,
                "tib": tib,
            }

        if not by_wylie[wylie]["tib"] and tib:
            by_wylie[wylie]["tib"] = tib

    entries = list(by_wylie.values())
    return sort_entries_by_tibetan(entries)


def build_tabs_for_wylie(rows, selected_wylie: str) -> Dict[str, List[Dict[str, Any]]]:
    tabs: Dict[str, List[Dict[str, Any]]] = {
        "fr": [],
        "eng": [],
        "tib": [],
    }

    for row in rows:
        row_wylie = (row["wylie"] or "").strip()
        if row_wylie != selected_wylie:
            continue

        lang_value = (row["lang"] or "").strip().upper()

        item = {
            "source": row["source"] or "",
            "contexte": row["contexte"] or "",
            "definition": row["defWeb"] or "",
            "lang": lang_value,
            "tib": row["tib"] or "",
            "wylie": row["wylie"] or "",
        }

        if lang_value == "FR":
            tabs["fr"].append(item)
        elif lang_value == "ENG":
            tabs["eng"].append(item)
        elif lang_value == "TIB":
            tabs["tib"].append(item)

    return tabs


def prepare_search_view_data(
    term: str,
    match_mode: str = "contains",
    sources: Optional[List[str]] = None,
    lang: str = "",
    contexte: str = "",
    selected_key: str = "",
) -> Dict[str, Any]:
    rows = fetch_search_rows(
        term=term,
        match_mode=match_mode,
        sources=sources,
        lang=lang,
        contexte=contexte,
    )

    entries = build_entries_from_rows(rows)

    selected_entry = None
    selected_wylie = ""

    if entries:
        if selected_key:
            selected_entry = next(
                (entry for entry in entries if entry["key"] == selected_key),
                None,
            )

        if selected_entry is None:
            selected_entry = entries[0]

        selected_wylie = selected_entry["wylie"]
        selected_entry = {
            **selected_entry,
            "tabs": build_tabs_for_wylie(rows, selected_wylie),
        }

    return {
        "entries": entries,
        "selected_entry": selected_entry,
        "selected_key": selected_wylie,
        "result_count": len(entries),
    }


def fetch_sources_grouped() -> Dict[str, List[Dict[str, Any]]]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT code, label, family, sort_order
            FROM sources
            ORDER BY family ASC, sort_order ASC, code ASC
            """
        )
        rows = cur.fetchall()

        grouped: Dict[str, List[Dict[str, Any]]] = {
            "FR": [],
            "EN": [],
            "TIB": [],
        }

        for row in rows:
            code = (row["code"] or "").strip()
            label = (row["label"] or "").strip()
            family = (row["family"] or "").strip().upper()
            sort_order = row["sort_order"]

            if family not in grouped:
                continue

            grouped[family].append(
                {
                    "code": code,
                    "label": label,
                    "display_label": f"({code}) {label}",
                    "family": family,
                    "sort_order": sort_order,
                }
            )

        return grouped
    finally:
        conn.close()