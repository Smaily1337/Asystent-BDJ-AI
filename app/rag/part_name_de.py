"""Polskie nazwy części z BOM → niemiecki display (UI / tabele czatu)."""

from __future__ import annotations

import re

from app.i18n import get_lang

_SKU_DE: dict[str, str] = {
    "PNE-PAS-DOL": "Antriebsriemen mit 5 mm roter Auflage, Mittelnut, für PNEUMATIC",
    "PNE-PAS-GOR": "Antriebsriemen mit 5 mm flacher roter Auflage, für PNEUMATIC",
}

_PL_DE_PHRASE_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bpas\s+z\s+nakładką\s+5mm\s+czerwony\s+z\s+frezem\s+centralnym\s+do\s+pneumatic\b", re.I), "Antriebsriemen mit 5 mm roter Auflage, Mittelnut, für PNEUMATIC"),
    (re.compile(r"\bpas\s+z\s+nakładką\s+5mm\s+czerwony\s+płaski\s+do\s+pneumatic\b", re.I), "Antriebsriemen mit 5 mm flacher roter Auflage, für PNEUMATIC"),
    (re.compile(r"\buszczelka\s+na\s+kabel\b", re.I), "Kabeldichtung"),
    (re.compile(r"\buszczelka\s+na\s+mikrorurk[ęe]\b", re.I), "Mikrorohrdichtung"),
    (re.compile(r"\buszczelka\s+na\s+rurk[ęe]\b", re.I), "Rohrdichtung"),
    (re.compile(r"\buszczelka\s+wstawki\s+rurki\b", re.I), "Rohreinsatzdichtung"),
    (re.compile(r"\buszczelka\s+wstawki\s+kabla\b", re.I), "Kabeleinsatzdichtung"),
    (re.compile(r"\buszczelka\s+korpusu\b", re.I), "Gehäusedichtung"),
    (re.compile(r"\btulejka\s+mocująca\s+rurk[ęe]\b", re.I), "Rohrbefestigungshülse"),
    (re.compile(r"\btuleja\s+kabla\b", re.I), "Kabelführungshülse"),
    (re.compile(r"\btuleja\s+mikrorurki\b", re.I), "Mikrorohrhülse"),
    (re.compile(r"\bwstawka\s+rurki\b", re.I), "Rohreinsatz"),
    (re.compile(r"\bwstawka\s+kabla\b", re.I), "Kabeleinsatz"),
    (re.compile(r"\bmoduł\s+pasowy\b", re.I), "Riemenmodul"),
    (re.compile(r"\bkoło\s+pasowe\s+silników\b", re.I), "Motor-Riemenscheibe"),
    (re.compile(r"\bkoło\s+pasowe\s+duże\b", re.I), "Große Riemenscheibe"),
    (re.compile(r"\bkoło\s+pasowe\s+małe\b", re.I), "Kleine Riemenscheibe"),
    (re.compile(r"\bkoło\s+pasowe\b", re.I), "Riemenscheibe"),
    (re.compile(r"\bdystans\s+koła\s+dużego\b", re.I), "Distanzstück für große Riemenscheibe"),
    (re.compile(r"\bdystans\s+koła\s+małego\b", re.I), "Distanzstück für kleine Riemenscheibe"),
    (re.compile(r"\bśruba\s+pasowana\b", re.I), "Passschraube"),
    (re.compile(r"\bzłączka\s+kątowa\s+wtykowa\b", re.I), "Winkelsteckverbinder"),
    (re.compile(r"\bgłowica\s+m\b", re.I), "M-Kopf"),
    (re.compile(r"\bgłowica\s+p\b", re.I), "P-Kopf"),
    (re.compile(r"\bbez\s+otworu\b", re.I), "ohne Bohrung"),
    (re.compile(r"\bz\s+frezem\s+centralnym\b", re.I), "mit Mittelnut"),
    (re.compile(r"\bdo\s+pneumatic\b", re.I), "für PNEUMATIC"),
    (re.compile(r"\bocynkowana\b", re.I), "verzinkt"),
    (re.compile(r"\bnierdzewna\b", re.I), "Edelstahl"),
    (re.compile(r"\boponka\s+płaska\b", re.I), "Flacher Antriebsradreifen"),
    (re.compile(r"\boponka\b", re.I), "Antriebsradreifen"),
    (re.compile(r"\bmanometr\b", re.I), "Manometer"),
    (re.compile(r"\bpas\s+napędowy\b", re.I), "Antriebsriemen"),
    (re.compile(r"\bpas\s+z\s+nakładką\b", re.I), "Riemen mit Auflage"),
]

_PL_DE_WORD_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\buszczelk\w*\b", re.I), "Dichtung"),
    (re.compile(r"\btulej\w*\b", re.I), "Hülse"),
    (re.compile(r"\bwstawk\w*\b", re.I), "Einsatz"),
    (re.compile(r"\bpas\b", re.I), "Riemen"),
    (re.compile(r"\bpasek\b", re.I), "Riemen"),
    (re.compile(r"\bśrub\w*\b", re.I), "Schraube"),
    (re.compile(r"\bsrub\w*\b", re.I), "Schraube"),
    (re.compile(r"\boring\b", re.I), "O-Ring"),
    (re.compile(r"\bzłączk\w*\b", re.I), "Verbinder"),
    (re.compile(r"\brurk\w*\b", re.I), "Rohr"),
    (re.compile(r"\bmikrorur\w*\b", re.I), "Mikrorohr"),
    (re.compile(r"\bkabl\w*\b", re.I), "Kabel"),
    (re.compile(r"\bgłowic\w*\b", re.I), "Kopf"),
    (re.compile(r"\bmoduł\b", re.I), "Modul"),
    (re.compile(r"\bkoło\b", re.I), "Rad"),
    (re.compile(r"\bkolo\b", re.I), "Rad"),
    (re.compile(r"\bnapędow\w*\b", re.I), "Antriebs-"),
    (re.compile(r"\bnapedow\w*\b", re.I), "Antriebs-"),
    (re.compile(r"\bmocując\w*\b", re.I), "Befestigungs-"),
    (re.compile(r"\bmocujac\w*\b", re.I), "Befestigungs-"),
    (re.compile(r"\bczerwon\w*\b", re.I), "rot"),
    (re.compile(r"\bpłask\w*\b", re.I), "flach"),
    (re.compile(r"\bplask\w*\b", re.I), "flach"),
    (re.compile(r"\bnakładk\w*\b", re.I), "Auflage"),
    (re.compile(r"\bnakladk\w*\b", re.I), "Auflage"),
    (re.compile(r"\bsilikon\b", re.I), "Silikon"),
    (re.compile(r"\bklej\b", re.I), "Kleber"),
    (re.compile(r"\bduż\w*\b", re.I), "groß"),
    (re.compile(r"\bduz\w*\b", re.I), "groß"),
    (re.compile(r"\bmał\w*\b", re.I), "klein"),
    (re.compile(r"\bmal\w*\b", re.I), "klein"),
    (re.compile(r"\bna\b", re.I), "für"),
    (re.compile(r"\bdo\b", re.I), "für"),
    (re.compile(r"\bz\b", re.I), "mit"),
]


def translate_part_name_de(name: str, sku: str | None = None) -> str:
    """Tłumaczy nazwę części z BOM na niemiecki (display only)."""
    text = (name or "").strip()
    if not text or get_lang() != "de":
        return text

    key = (sku or "").strip().upper()
    if key and key in _SKU_DE:
        return _SKU_DE[key]

    for pattern, replacement in _PL_DE_PHRASE_RULES:
        text = pattern.sub(replacement, text)
    for pattern, replacement in _PL_DE_WORD_RULES:
        text = pattern.sub(replacement, text)
    return text
