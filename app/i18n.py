"""Język sesji czatu (PL / EN) — bez zmiany logiki katalogu SKU."""

from __future__ import annotations

from contextvars import ContextVar

_lang: ContextVar[str] = ContextVar("bdj_lang", default="pl")

ENGLISH_QUERY_PREFIX = (
    "[LANGUAGE: English] Reply in English. Keep SKU codes, machine model names "
    "(BDJ NEXT, etc.) and UI tags like [MACHINE_CARDS: …], [PRODUCT_CARD: …], "
    "[GET_REQUEST: …] unchanged. Translate table headers to: SKU | Part name | "
    "BOM qty | Machine model. Do not invent SKUs.\n\n"
)


def normalize_lang(value: str | None) -> str:
    v = (value or "").strip().lower()
    if v.startswith("en"):
        return "en"
    return "pl"


def set_lang(value: str | None) -> str:
    lang = normalize_lang(value)
    _lang.set(lang)
    return lang


def get_lang() -> str:
    return _lang.get()


def loc(pl: str, en: str) -> str:
    return en if get_lang() == "en" else pl
