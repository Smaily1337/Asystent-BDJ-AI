"""Polskie nazwy części z BOM → angielski display (UI / tabele czatu)."""

from __future__ import annotations

import re

from app.i18n import get_lang

# Dokładne SKU → EN (najpewniejsze dla powtarzalnych pozycji)
_SKU_EN: dict[str, str] = {
    "PNE-PAS-DOL": "Drive belt with 5 mm red overlay, central groove, for PNEUMATIC",
    "PNE-PAS-GOR": "Drive belt with 5 mm flat red overlay, for PNEUMATIC",
}

# Dłuższe frazy pierwsze
_PL_PHRASE_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bpas\s+z\s+nakładką\s+5mm\s+czerwony\s+z\s+frezem\s+centralnym\s+do\s+pneumatic\b", re.I), "Drive belt with 5 mm red overlay, central groove, for PNEUMATIC"),
    (re.compile(r"\bpas\s+z\s+nakładką\s+5mm\s+czerwony\s+płaski\s+do\s+pneumatic\b", re.I), "Drive belt with 5 mm flat red overlay, for PNEUMATIC"),
    (re.compile(r"\buszczelka\s+na\s+kabel\b", re.I), "Cable gasket"),
    (re.compile(r"\buszczelka\s+na\s+mikrorurk[ęe]\b", re.I), "Microduct gasket"),
    (re.compile(r"\buszczelka\s+na\s+rurk[ęe]\b", re.I), "Tube gasket"),
    (re.compile(r"\buszczelka\s+wstawki\s+rurki\b", re.I), "Tube-insert gasket"),
    (re.compile(r"\buszczelka\s+wstawki\s+kabla\b", re.I), "Cable-insert gasket"),
    (re.compile(r"\buszczelka\s+korpusu\b", re.I), "Body gasket"),
    (re.compile(r"\btulejka\s+mocująca\s+rurk[ęe]\b", re.I), "Tube mounting sleeve"),
    (re.compile(r"\btuleja\s+kabla\b", re.I), "Cable sleeve"),
    (re.compile(r"\btuleja\s+mikrorurki\b", re.I), "Microduct sleeve"),
    (re.compile(r"\bwstawka\s+rurki\b", re.I), "Tube insert"),
    (re.compile(r"\bwstawka\s+kabla\b", re.I), "Cable insert"),
    (re.compile(r"\bmoduł\s+pasowy\b", re.I), "Belt module"),
    (re.compile(r"\bkoło\s+pasowe\s+silników\b", re.I), "Motor belt pulley"),
    (re.compile(r"\bkoło\s+pasowe\s+duże\b", re.I), "Large belt pulley"),
    (re.compile(r"\bkoło\s+pasowe\s+małe\b", re.I), "Small belt pulley"),
    (re.compile(r"\bkoło\s+pasowe\b", re.I), "Belt pulley"),
    (re.compile(r"\bdystans\s+koła\s+dużego\b", re.I), "Large pulley spacer"),
    (re.compile(r"\bdystans\s+koła\s+małego\b", re.I), "Small pulley spacer"),
    (re.compile(r"\bśruba\s+pasowana\b", re.I), "Shoulder bolt"),
    (re.compile(r"\bzłączka\s+kątowa\s+wtykowa\b", re.I), "Angled push-in fitting"),
    (re.compile(r"\bgłowica\s+m\b", re.I), "M head"),
    (re.compile(r"\bgłowica\s+p\b", re.I), "P head"),
    (re.compile(r"\bbez\s+otworu\b", re.I), "without hole"),
    (re.compile(r"\bz\s+frezem\s+centralnym\b", re.I), "with central groove"),
    (re.compile(r"\bdo\s+pneumatic\b", re.I), "for PNEUMATIC"),
    (re.compile(r"\bocynkowana\b", re.I), "zinc-plated"),
    (re.compile(r"\bnierdzewna\b", re.I), "stainless steel"),
    (re.compile(r"\boponka\s+płaska\b", re.I), "flat drive-wheel tyre"),
    (re.compile(r"\boponka\b", re.I), "drive-wheel tyre"),
    (re.compile(r"\bmanometr\b", re.I), "pressure gauge"),
    (re.compile(r"\bpas\s+napędowy\b", re.I), "drive belt"),
    (re.compile(r"\bpas\s+z\s+nakładką\b", re.I), "belt with overlay"),
]

_PL_WORD_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\buszczelk\w*\b", re.I), "gasket"),
    (re.compile(r"\btulej\w*\b", re.I), "sleeve"),
    (re.compile(r"\bwstawk\w*\b", re.I), "insert"),
    (re.compile(r"\bpas\b", re.I), "belt"),
    (re.compile(r"\bpasek\b", re.I), "belt"),
    (re.compile(r"\bśrub\w*\b", re.I), "bolt"),
    (re.compile(r"\bsrub\w*\b", re.I), "bolt"),
    (re.compile(r"\boring\b", re.I), "O-ring"),
    (re.compile(r"\bzłączk\w*\b", re.I), "fitting"),
    (re.compile(r"\brurk\w*\b", re.I), "tube"),
    (re.compile(r"\bmikrorur\w*\b", re.I), "microduct"),
    (re.compile(r"\bkabl\w*\b", re.I), "cable"),
    (re.compile(r"\bgłowic\w*\b", re.I), "head"),
    (re.compile(r"\bmoduł\b", re.I), "module"),
    (re.compile(r"\bkoło\b", re.I), "wheel"),
    (re.compile(r"\bkolo\b", re.I), "wheel"),
    (re.compile(r"\bnapędow\w*\b", re.I), "drive"),
    (re.compile(r"\bnapedow\w*\b", re.I), "drive"),
    (re.compile(r"\bmocując\w*\b", re.I), "mounting"),
    (re.compile(r"\bmocujac\w*\b", re.I), "mounting"),
    (re.compile(r"\bczerwon\w*\b", re.I), "red"),
    (re.compile(r"\bpłask\w*\b", re.I), "flat"),
    (re.compile(r"\bplask\w*\b", re.I), "flat"),
    (re.compile(r"\bnakładk\w*\b", re.I), "overlay"),
    (re.compile(r"\bnakladk\w*\b", re.I), "overlay"),
    (re.compile(r"\bsilikon\b", re.I), "silicone"),
    (re.compile(r"\bklej\b", re.I), "adhesive"),
    (re.compile(r"\bduż\w*\b", re.I), "large"),
    (re.compile(r"\bduz\w*\b", re.I), "large"),
    (re.compile(r"\bmał\w*\b", re.I), "small"),
    (re.compile(r"\bmal\w*\b", re.I), "small"),
    (re.compile(r"\bna\b", re.I), "for"),
    (re.compile(r"\bdo\b", re.I), "for"),
    (re.compile(r"\bz\b", re.I), "with"),
]


def translate_part_name_en(name: str, sku: str | None = None) -> str:
    """Tłumaczy nazwę części z BOM na angielski (display only)."""
    text = (name or "").strip()
    if not text or get_lang() != "en":
        return text

    key = (sku or "").strip().upper()
    if key and key in _SKU_EN:
        return _SKU_EN[key]

    out = text
    for pattern, replacement in _PL_PHRASE_RULES:
        out = pattern.sub(replacement, out)
    for pattern, replacement in _PL_WORD_RULES:
        out = pattern.sub(replacement, out)

    # Sentence case first letter after cleanup
    out = re.sub(r"\s+", " ", out).strip()
    if out and out[0].islower():
        out = out[0].upper() + out[1:]
    return out
