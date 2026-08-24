"""Niemieckie zapytania klientów → polskie terminy katalogowe (przed lookup / BM25).

Katalog SKU i reguły doboru działają po polsku. Warstwa tłumaczy potoczne DE
(fuzzy) na terminy z BOM — bez zmiany samych kodów w bazie.
"""

from __future__ import annotations

import re

from app.i18n import get_lang

# Kolejność: dłuższe / bardziej specyficzne frazy pierwsze.
_DE_PHRASE_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bmikrorohr[\-\s]?dichtung(?:en)?\b", re.I), "uszczelka mikrorurki"),
    (re.compile(r"\bmikrorohr[\-\s]?abdichtung(?:en)?\b", re.I), "uszczelka mikrorurki"),
    (re.compile(r"\brohr[\-\s]?dichtung(?:en)?\b", re.I), "uszczelka mikrorurki"),
    (re.compile(r"\bdichtung(?:en)?\s+f[üu]r\s+(?:das\s+)?mikrorohr\b", re.I), "uszczelka mikrorurki"),
    (re.compile(r"\bdichtung(?:en)?\s+f[üu]r\s+(?:das\s+)?rohr\b", re.I), "uszczelka mikrorurki"),
    (re.compile(r"\bkabel[\-\s]?dichtung(?:en)?\b", re.I), "uszczelka na kabel"),
    (re.compile(r"\bglasfaser[\-\s]?dichtung(?:en)?\b", re.I), "uszczelka na kabel"),
    (re.compile(r"\blwl[\-\s]?dichtung(?:en)?\b", re.I), "uszczelka na kabel"),
    (re.compile(r"\bdichtung(?:en)?\s+f[üu]r\s+(?:das\s+)?kabel\b", re.I), "uszczelka na kabel"),
    (re.compile(r"\bdichtung(?:en)?\s+f[üu]r\s+(?:die\s+)?glasfaser\b", re.I), "uszczelka na kabel"),
    (re.compile(r"\bantriebs[\-\s]?riemen\b", re.I), "pas napędowy"),
    (re.compile(r"\bantriebs[\-\s]?band\b", re.I), "pas napędowy"),
    (re.compile(r"\bzahn[\-\s]?riemen\b", re.I), "pas napędowy"),
    (re.compile(r"\bantriebs[\-\s]?rad\b", re.I), "oponka"),
    (re.compile(r"\bantriebs[\-\s]?r[äa]der\b", re.I), "oponka"),
    (re.compile(r"\bdruck[\-\s]?anzeige(?:n)?\b", re.I), "manometr"),
    (re.compile(r"\bersatz[\-\s]?teil(?:e)?\b", re.I), "część zamienna"),
    (re.compile(r"\bprodukt[\-\s]?datenblatt\b", re.I), "karta produktu"),
    (re.compile(r"\bdaten[\-\s]?blatt\b", re.I), "karta produktu"),
    (re.compile(r"\bprodukt[\-\s]?karte\b", re.I), "karta produktu"),
    (re.compile(r"\bzeige\s+alle\b", re.I), "pokaż wszystkie"),
    (re.compile(r"\bliste\s+von\b", re.I), "lista"),
    (re.compile(r"\balle\s+dichtungen\b", re.I), "wszystkie uszczelki"),
    (re.compile(r"\bwas\s+ist\b", re.I), "co to"),
    (re.compile(r"\berkl[äa]re\s+mir\b", re.I), "opisz"),
    (re.compile(r"\bich\s+brauche(?:\s+ein|\s+eine|\s+einen)?\b", re.I), "potrzebuję"),
    (re.compile(r"\bich\s+ben[öo]tige(?:\s+ein|\s+eine|\s+einen)?\b", re.I), "potrzebuję"),
    (re.compile(r"\bich\s+suche(?:\s+ein|\s+eine|\s+einen)?\b", re.I), "potrzebuję"),
    (re.compile(r"\bich\s+habe\b", re.I), "mam"),
    (re.compile(r"\bich\s+nutze\b", re.I), "mam"),
    (re.compile(r"\bich\s+besitze\b", re.I), "mam"),
    (re.compile(r"\bmeine\s+maschine\s+ist\b", re.I), "mam maszynę"),
    (re.compile(r"\bf[üu]r\s+meine\b", re.I), "do"),
    (re.compile(r"\bf[üu]r\s+die\b", re.I), "do"),
    (re.compile(r"\bf[üu]r\s+das\b", re.I), "do"),
    (re.compile(r"\bdasselbe\s+aber\s+f[üu]r\s+(?:das\s+)?kabel\b", re.I), "to samo na kabel"),
    (re.compile(r"\bdasselbe\s+aber\s+f[üu]r\s+(?:das\s+)?rohr\b", re.I), "to samo na mikrorurkę"),
]

_DE_WORD_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bdichtungen?\b", re.I), "uszczelka"),
    (re.compile(r"\bo-?ringe?\b", re.I), "uszczelka"),
    (re.compile(r"\bh[üu]lsen?\b", re.I), "tuleja"),
    (re.compile(r"\bf[üu]hrungsh[üu]lsen?\b", re.I), "tuleja"),
    (re.compile(r"\beins[äa]tze?\b", re.I), "wstawka"),
    (re.compile(r"\briemen\b", re.I), "pas"),
    (re.compile(r"\breifen\b", re.I), "oponka"),
    (re.compile(r"\bmanometer\b", re.I), "manometr"),
    (re.compile(r"\bmikrorohre?\b", re.I), "mikrorurka"),
    (re.compile(r"\br[öo]hrchen\b", re.I), "mikrorurka"),
    (re.compile(r"\brohre?\b", re.I), "mikrorurka"),
    (re.compile(r"\bkabel\b", re.I), "kabel"),
    (re.compile(r"\bglasfaser\b", re.I), "kabel"),
    (re.compile(r"\blwl\b", re.I), "kabel"),
    (re.compile(r"\bspezifikationen?\b", re.I), "parametry"),
    (re.compile(r"\bkompressor\b", re.I), "kompresor"),
    (re.compile(r"\beinblasmaschine\b", re.I), "wdmuchiwarka"),
    (re.compile(r"\beinblasen\b", re.I), "wdmuchiwanie"),
]


def translate_de_query_for_lookup(question: str) -> str:
    """
    Mapuje niemieckie pytanie na polskie terminy katalogowe.
    No-op gdy sesja PL/EN lub brak tekstu.
    """
    q = (question or "").strip()
    if not q or get_lang() != "de":
        return q

    for pattern, replacement in _DE_PHRASE_RULES:
        q = pattern.sub(replacement, q)
    for pattern, replacement in _DE_WORD_RULES:
        q = pattern.sub(replacement, q)
    return q


def translate_de_history(
    history: list[tuple[str, str]] | None,
) -> list[tuple[str, str]] | None:
    """Tłumaczy wiadomości usera w historii."""
    if not history or get_lang() != "de":
        return history
    return [(translate_de_query_for_lookup(u), a) for u, a in history]
