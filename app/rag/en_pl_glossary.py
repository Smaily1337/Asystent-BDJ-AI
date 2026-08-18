"""Angielskie zapytania klientów → polskie terminy katalogowe (przed lookup / BM25).

Katalog SKU i reguły doboru działają po polsku. Warstwa tłumaczy potoczne EN
(fuzzy) na terminy z BOM — bez zmiany samych kodów w bazie.
"""

from __future__ import annotations

import re

from app.i18n import get_lang

# Kolejność: dłuższe / bardziej specyficzne frazy pierwsze.
_EN_PHRASE_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bmicro[\-\s]?duct\s+gasket(?:s)?\b", re.I), "uszczelka mikrorurki"),
    (re.compile(r"\bmicro[\-\s]?duct\s+seal(?:s)?\b", re.I), "uszczelka mikrorurki"),
    (re.compile(r"\bmicro[\-\s]?tube\s+gasket(?:s)?\b", re.I), "uszczelka mikrorurki"),
    (re.compile(r"\bmicro[\-\s]?tube\s+seal(?:s)?\b", re.I), "uszczelka mikrorurki"),
    (re.compile(r"\bpipe\s+seal(?:s)?\b", re.I), "uszczelka mikrorurki"),
    (re.compile(r"\bduct\s+seal(?:s)?\b", re.I), "uszczelka mikrorurki"),
    (re.compile(r"\btube\s+seal(?:s)?\b", re.I), "uszczelka mikrorurki"),
    (re.compile(r"\bpipe\s+gasket(?:s)?\b", re.I), "uszczelka mikrorurki"),
    (re.compile(r"\bduct\s+gasket(?:s)?\b", re.I), "uszczelka mikrorurki"),
    (re.compile(r"\btube\s+gasket(?:s)?\b", re.I), "uszczelka mikrorurki"),
    (re.compile(r"\bcable\s+gasket(?:s)?\b", re.I), "uszczelka na kabel"),
    (re.compile(r"\bcable\s+seal(?:s)?\b", re.I), "uszczelka na kabel"),
    (re.compile(r"\bfibre\s+seal(?:s)?\b", re.I), "uszczelka na kabel"),
    (re.compile(r"\bfiber\s+seal(?:s)?\b", re.I), "uszczelka na kabel"),
    (re.compile(r"\bfibre\s+gasket(?:s)?\b", re.I), "uszczelka na kabel"),
    (re.compile(r"\bfiber\s+gasket(?:s)?\b", re.I), "uszczelka na kabel"),
    (re.compile(r"\bdrive\s+belt(?:s)?\b", re.I), "pas napędowy"),
    (re.compile(r"\bdrive\s+wheel(?:s)?\b", re.I), "oponka"),
    (re.compile(r"\bpressure\s+gauge(?:s)?\b", re.I), "manometr"),
    (re.compile(r"\bspare\s+part(?:s)?\b", re.I), "część zamienna"),
    (re.compile(r"\bshow\s+all\b", re.I), "pokaż wszystkie"),
    (re.compile(r"\blist\s+of\b", re.I), "lista"),
    (re.compile(r"\ball\s+gaskets\b", re.I), "wszystkie uszczelki"),
    (re.compile(r"\bproduct\s+card\b", re.I), "karta produktu"),
    (re.compile(r"\bdata\s*sheet\b", re.I), "karta produktu"),
    (re.compile(r"\bspec\s*sheet\b", re.I), "karta produktu"),
    (re.compile(r"\bwhat\s+is\b", re.I), "co to"),
    (re.compile(r"\btell\s+me\s+about\b", re.I), "opisz"),
    (re.compile(r"\bi\s+need(?:\s+a|\s+an)?\b", re.I), "potrzebuję"),
    (re.compile(r"\bi\s+want(?:\s+a|\s+an)?\b", re.I), "potrzebuję"),
    (re.compile(r"\bi['']ve\s+got\b", re.I), "mam"),
    (re.compile(r"\bi\s+have\b", re.I), "mam"),
    (re.compile(r"\bmy\s+machine\s+is\b", re.I), "mam maszynę"),
    (re.compile(r"\bfor\s+my\b", re.I), "do"),
    (re.compile(r"\bsame\s+but\s+(?:for\s+)?(?:the\s+)?cable\b", re.I), "to samo na kabel"),
    (re.compile(r"\bsame\s+but\s+(?:for\s+)?(?:the\s+)?(?:tube|duct|pipe|microduct)\b", re.I), "to samo na mikrorurkę"),
]

_EN_WORD_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bgaskets?\b", re.I), "uszczelka"),
    (re.compile(r"\bseals?\b", re.I), "uszczelka"),
    (re.compile(r"\bo-?rings?\b", re.I), "uszczelka"),
    (re.compile(r"\bsleeves?\b", re.I), "tuleja"),
    (re.compile(r"\binserts?\b", re.I), "wstawka"),
    (re.compile(r"\bbelts?\b", re.I), "pas"),
    (re.compile(r"\btyres?\b", re.I), "oponka"),
    (re.compile(r"\btires?\b", re.I), "oponka"),
    (re.compile(r"\bgauges?\b", re.I), "manometr"),
    (re.compile(r"\bmicro[\-\s]?ducts?\b", re.I), "mikrorurka"),
    (re.compile(r"\bmicro[\-\s]?tubes?\b", re.I), "mikrorurka"),
    (re.compile(r"\bducts?\b", re.I), "mikrorurka"),
    (re.compile(r"\bpipes?\b", re.I), "mikrorurka"),
    (re.compile(r"\btubes?\b", re.I), "rurka"),
    (re.compile(r"\bcables?\b", re.I), "kabel"),
    (re.compile(r"\bfibres?\b", re.I), "kabel"),
    (re.compile(r"\bfibers?\b", re.I), "kabel"),
    (re.compile(r"\bspecifications?\b", re.I), "parametry"),
    (re.compile(r"\bbrochure\b", re.I), "karta produktu"),
]


def translate_en_query_for_lookup(question: str) -> str:
    """
    Mapuje angielskie pytanie na polskie terminy katalogowe.
    No-op gdy sesja PL lub brak tekstu.
    """
    q = (question or "").strip()
    if not q or get_lang() != "en":
        return q

    for pattern, replacement in _EN_PHRASE_RULES:
        q = pattern.sub(replacement, q)
    for pattern, replacement in _EN_WORD_RULES:
        q = pattern.sub(replacement, q)
    return q


def translate_en_history(
    history: list[tuple[str, str]] | None,
) -> list[tuple[str, str]] | None:
    """Tłumaczy wiadomości usera w historii (asystent zostaje EN/PL jak było)."""
    if not history or get_lang() != "en":
        return history
    return [(translate_en_query_for_lookup(u), a) for u, a in history]
