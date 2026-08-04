"""Walidacja SKU w odpowiedziach — zakaz zmyślonych / sklejanych kodów."""

from __future__ import annotations

import re

from app.rag.catalog import parts_for_machine
from app.rag.machines import machine_display_name, resolve_machine_from_query

# Typowy SKU BDJ: LITERY-SEGMENTY (min. 1 myślnik, 2+ segmenty)
_SKU_RE = re.compile(r"\b([A-Z]{2,}(?:-[A-Z0-9][A-Z0-9\.,/]*)+)\b")

# Fałszywe pozytywy z markdown / tagów
_SKU_DENY = {
    "GET-QUOTE",
    "GET-REQUEST",
    "BDJ-NEXT",
    "BDJ-MAX",
    "BDJ-BUDGET",
    "BDJ-EXTENDED",
}


def extract_skus(text: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for m in _SKU_RE.finditer(text or ""):
        sku = m.group(1).strip()
        key = sku.upper()
        if key in _SKU_DENY or key.startswith("BDJ-"):
            continue
        # za krótkie / nie wygląda na katalog
        if key.count("-") < 1 or len(key) < 6:
            continue
        if key not in seen:
            seen.add(key)
            found.append(sku)
    return found


def catalog_sku_set(machine_tag: str | None) -> set[str]:
    rows = parts_for_machine(machine_tag)
    return {p.sku.upper() for p in rows}


def find_invalid_skus(answer: str, machine_tag: str | None) -> list[str]:
    allowed = catalog_sku_set(machine_tag)
    if not allowed:
        # bez katalogu nie filtrujemy agresywnie (FAQ itd.)
        return []
    invalid: list[str] = []
    for sku in extract_skus(answer):
        if sku.upper() not in allowed:
            invalid.append(sku)
    return invalid


def sanitize_answer_skus(
    answer: str,
    question: str,
    chip_machine: str | None = None,
) -> str:
    """
    Usuwa z odpowiedzi SKU spoza katalogu maszyny.
    Jeśli po czyszczeniu nie zostaje żaden poprawny SKU, a były zmyślone —
    zamienia odpowiedź na bezpieczny komunikat.
    """
    machine = resolve_machine_from_query(question or "", chip_machine=chip_machine)
    if not machine:
        return answer

    allowed = catalog_sku_set(machine)
    if not allowed:
        return answer

    invalid = find_invalid_skus(answer, machine)
    if not invalid:
        return answer

    cleaned = answer
    for sku in invalid:
        cleaned = re.sub(re.escape(sku), "", cleaned)

    # posprzątaj puste komórki tabeli / podwójne spacje
    cleaned = re.sub(r"\|\s*\|", "| — |", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

    remaining = [s for s in extract_skus(cleaned) if s.upper() in allowed]
    if remaining:
        note = (
            "\n\n_(Usunięto kody spoza katalogu tej maszyny — "
            "podaję wyłącznie istniejące SKU.)_"
        )
        return cleaned + note

    display = machine_display_name(machine)
    return (
        f"Przepraszam — w odpowiedzi pojawiły się nieistniejące kody części. "
        f"Dla modelu {display} mogę podać wyłącznie pozycje z oficjalnego katalogu. "
        f"Podaj proszę dokładny typ części i wymiar (np. uszczelka mikrorurki 7 mm), "
        f"a dobiorę właściwy SKU."
    )
