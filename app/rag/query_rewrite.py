"""Przepisanie potocznego pytania klienta na fachowe terminy (przed BM25)."""

from __future__ import annotations

import re

from app.rag.machines import machine_display_name, resolve_machine_from_query

# (wzorce w pytaniu) → oficjalna nazwa z instrukcji
_SYNONYM_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(o-?ring|oring|gumk\w*|uszczelk\w*)\b", re.I), "uszczelka"),
    (re.compile(r"\b(pasek|paski|pas\s+nap|pas\s+czerw|ta[sś]m\w*\s+nap|ta[sś]m\w*)\b", re.I), "pas napędowy"),
    (re.compile(r"\b(nak[lł]adk\w*\s+pas\w*|pas\s+z\s+nak[lł]adk\w*)\b", re.I), "pas napędowy PNE-PAS"),
    (re.compile(r"\b(tulejk\w*\s+kabl\w*|wstawk\w*\s+kabl\w*|prowadzen\w*\s+kabl\w*)\b", re.I), "tuleja kabla"),
    (re.compile(r"\b(tulejk\w*\s+mikro\w*|wstawk\w*\s+mikro\w*|wstawk\w*\s+rurk\w*|uchwyt\w*\s+mikro\w*)\b", re.I), "tuleja mikrorurki"),
    (re.compile(r"\b(oponk\w*|gumk\w*\s+na\s+(rolk\w*|ko[łl]\w*)|gumk\w*\s+jezdn\w*)\b", re.I), "oponka MINI-OPONKI"),
    (re.compile(r"\b(zegar|wska[zź]nik\s+ci[sś]nieni\w*|ci[sś]?nieniomierz|cinieniomierz)\b", re.I), "manometr"),
    (re.compile(r"\b(wałek|wałki|ośka|ośki)\b", re.I), "wałek"),
    (re.compile(r"\b(kółk\w*|kolk\w*|koło|kola|koła)\b", re.I), "rolka"),
    (re.compile(r"\b(t[lł]umik\w*)\b", re.I), "tłumik"),
    (re.compile(r"\b(bullet\w*|ko[nń]c[oó]wk\w*\s+na\s+kabel)\b", re.I), "bullet końcówka kabla"),
    (re.compile(r"\b(spadochron\w*|t[lł]oczek|t[lł]oczki|piston)\b", re.I), "spadochron tłoczek"),
]

_PRICE_HINTS = re.compile(
    r"\b(cena|ceny|cennik|koszt|ile\s+kosztuje|euro|eur|€|price|pricing)\b",
    re.I,
)


def rewrite_query(question: str, chip_machine: str | None = None) -> str:
    """Wzbogaca pytanie: synonimy + jawny tag wykrytego modelu (dla BM25 i LLM)."""
    q = (question or "").strip()
    if not q:
        return q

    extras: list[str] = []
    for pattern, canonical in _SYNONYM_RULES:
        if pattern.search(q) and canonical.lower() not in q.lower():
            extras.append(canonical)

    if _PRICE_HINTS.search(q):
        extras.extend(["cennik", "cena EUR"])

    machine = resolve_machine_from_query(q, chip_machine=chip_machine)
    parts = [q]

    if machine:
        display = machine_display_name(machine)
        parts.append(
            f"[WYKRYTY MODEL MASZYNY: {display} — NIE PYTAJ PONOWNIE O MODEL. "
            f"Dobieraj części wyłącznie dla {display}.]"
        )

    if extras:
        parts.append(f"[oficjalnie: {', '.join(dict.fromkeys(extras))}]")

    # Wzmocnienie BM25 dla pytań o pas napędowy (pasek → PNE-PAS / MOD-PAS w BOM)
    if re.search(r"\b(pasek|paski|pas\s+nap|pas\s+czerw|ta[sś]m\w*)\b", q, re.I):
        parts.append(
            "[MAPOWANIE: pasek/paski/taśma = Pas napędowy. Szukaj SKU: PNE-PAS-DOL, PNE-PAS-GOR, MOD-PAS. "
            "NIE mylić z SRU-PAS (śruby) ani uszczelką.]"
        )

    return " ".join(parts) if len(parts) > 1 else q


def is_price_query(question: str) -> bool:
    return bool(_PRICE_HINTS.search(question or ""))
