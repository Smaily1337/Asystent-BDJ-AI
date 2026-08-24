"""Język sesji czatu (PL / EN / DE) — bez zmiany logiki katalogu SKU."""

from __future__ import annotations

from contextvars import ContextVar

_lang: ContextVar[str] = ContextVar("bdj_lang", default="pl")

ENGLISH_QUERY_PREFIX = (
    "[LANGUAGE: English] Reply in English. Keep SKU codes, machine model names "
    "(BDJ NEXT, etc.) and UI tags like [MACHINE_CARDS: …], [PRODUCT_CARD: …], "
    "[GET_REQUEST: …] unchanged. Translate table headers to: SKU | Part name | "
    "BOM qty | Machine model. Do not invent SKUs.\n\n"
)

GERMAN_QUERY_PREFIX = (
    "[LANGUAGE: German / Deutsch] Antworte auf Deutsch. Behalte SKU-Codes, Maschinennamen "
    "(BDJ NEXT usw.) und UI-Tags wie [MACHINE_CARDS: …], [PRODUCT_CARD: …], "
    "[GET_REQUEST: …] unverändert bei. Übersetze Tabellenüberschriften: SKU | Artikelname | "
    "Menge | Maschinenmodell. Erfinde keine SKUs.\n\n"
)


def normalize_lang(value: str | None) -> str:
    v = (value or "").strip().lower()
    if v.startswith("de"):
        return "de"
    if v.startswith("en"):
        return "en"
    return "pl"


def set_lang(value: str | None) -> str:
    lang = normalize_lang(value)
    _lang.set(lang)
    return lang


def get_lang() -> str:
    return _lang.get()


def loc(pl: str, en: str, de: str | None = None) -> str:
    lang = get_lang()
    if lang == "de":
        return de if de is not None else en
    if lang == "en":
        return en
    return pl
