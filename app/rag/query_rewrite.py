"""Przepisanie potocznego pytania klienta na fachowe terminy (przed BM25)."""

from __future__ import annotations

import re

from app.rag.machines import machine_display_name, resolve_machine_from_query

# (wzorce w pytaniu) → oficjalna nazwa z instrukcji
_SYNONYM_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(o-?ring|oring|gumk\w*|uszczelk\w*)\b", re.I), "uszczelka"),
    (re.compile(r"\b(pasek|paski|pas\s+nap\w*|pas\s+czerw\w*|ta[sś]m\w*\s+nap|ta[sś]m\w*)\b", re.I), "pas napędowy"),
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

# rurka/mikrorurka X mm → uszczelka fi (X−0.5); pomiń gdy już jest «fi …»
_TUBE_SIZE_RE = re.compile(
    r"(?:mikrorur\w*|mikro\s*rur\w*|rurk\w*|uszczelk\w*|gumk\w*).{0,40}?"
    r"(\d+(?:[.,]\d+)?)\s*mm"
    r"|"
    r"(\d+(?:[.,]\d+)?)\s*mm.{0,40}?(?:mikrorur\w*|rurk\w*|uszczelk\w*)",
    re.I,
)
_EXPLICIT_FI_RE = re.compile(r"\bfi\s*[0-9]+(?:[.,][0-9]+)?\b", re.I)


def _gasket_size_hints(question: str) -> list[str]:
    """Dla uszczelki na rurkę 7 mm dopisz fi 6,5 / UGD / UM — inaczej BM25 bierze tulejkę 7."""
    q = question or ""
    if not re.search(r"\b(uszczelk\w*|gumk\w*|o-?ring)\b", q, re.I):
        return []
    if re.search(r"\b(tulejk\w*|tulej\w*)\b", q, re.I) and not re.search(r"uszczelk\w*", q, re.I):
        return []

    hints = [
        "uszczelka UGD UM UK",
        "ZAKAZ mylenia uszczelki z tulejką mocującą TUL-MOC",
    ]
    # Jawne «fi 13,5» w nazwie katalogowej — nie dopisuj −0,5
    if _EXPLICIT_FI_RE.search(q):
        m_fi = re.search(r"\bfi\s*([0-9]+(?:[.,][0-9]+)?)\b", q, re.I)
        if m_fi:
            fi_s = m_fi.group(1).replace(".", ",")
            hints.append(f"fi {fi_s}")
            hints.append(f"UM-D35X5-{fi_s}")
            hints.append(f"UGD-D22X5-{fi_s}".replace(",", "."))
        return hints

    m = _TUBE_SIZE_RE.search(q)
    if not m:
        m2 = re.search(r"(\d+(?:[.,]\d+)?)\s*mm", q, re.I)
        if not m2:
            return hints
        raw = m2.group(1)
    else:
        raw = m.group(1) or m.group(2)
    try:
        asked = float(raw.replace(",", "."))
    except ValueError:
        return hints

    tubeish = bool(re.search(r"\b(mikrorur\w*|rurk\w*)\b", q, re.I))
    kabelish = bool(re.search(r"\b(kabel|kabla|kablu)\b", q, re.I))
    if tubeish or not kabelish:
        half = asked - 0.5
        half_s = str(half).replace(".", ",")
        if half_s.endswith(",0"):
            half_s = half_s[:-2]
        if abs(half - round(half)) > 0.01:
            half_s = f"{half:.1f}".replace(".", ",")
        hints.append(f"fi {half_s}")
        hints.append(f"UGD-D22X5-{half_s}".replace(",", "."))
        hints.append(f"UM-D35X5-{half_s}".replace(",", "."))
        hints.append(f"dla rurki {str(asked).replace('.', ',')} mm uszczelka fi {half_s}")
    if kabelish:
        hints.append(f"UK-D25X5-{str(asked).replace('.', ',')}")
        hints.append(f"uszczelka na kabel fi {str(asked).replace('.', ',')}")
    return hints


# Potoczne → fachowe (kolejność: bardziej specyficzne pierwsze)
_COLLOQUIAL_REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bgumk\w*\s+jezdn\w*\b", re.I), "oponka"),
    (re.compile(r"\bgumk\w*\s+na\s+(?:rolk\w*|ko[łl]\w*)\b", re.I), "oponka"),
    (re.compile(r"\b(o-?ring|oring)\b", re.I), "uszczelka"),
    (re.compile(r"\bgumk\w*\b", re.I), "uszczelka"),
    (re.compile(r"\b(pasek|paski)(?:\s+nap[eę]dow\w*)?\b", re.I), "pas napędowy"),
    (re.compile(r"\bta[sś]m\w*(?:\s+nap\w*)?\b", re.I), "pas napędowy"),
    (re.compile(r"\bpas\s+czerw\w*\b", re.I), "pas napędowy"),
    (re.compile(r"\b(zegar|wska[zź]nik\s+ci[sś]nieni\w*|ci[sś]?nieniomierz|cinieniomierz)\b", re.I), "manometr"),
    (re.compile(r"\btulejk\w*\s+kabl\w*\b", re.I), "tuleja kabla"),
    (re.compile(r"\bwstawk\w*\s+kabl\w*\b", re.I), "tuleja kabla"),
    (re.compile(r"\btulejk\w*\s+mikro\w*\b", re.I), "tuleja mikrorurki"),
    (re.compile(r"\bwstawk\w*\s+(?:mikro\w*|rurk\w*)\b", re.I), "tuleja mikrorurki"),
    (re.compile(r"\b(ośka|ośki|wał)\b", re.I), "wałek"),
    (re.compile(r"\b(kółk\w*|kolk\w*)\b", re.I), "rolka"),
]


def apply_colloquial_aliases(question: str) -> str:
    """
    Mapuje potoczne nazwy na fachowe terminy katalogowe — na ścieżce lookup
    (nie tylko LLM/BM25).
    """
    q = question or ""
    for pattern, replacement in _COLLOQUIAL_REPLACEMENTS:
        q = pattern.sub(replacement, q)
    return q


def rewrite_query(question: str, chip_machine: str | None = None) -> str:
    """Wzbogaca pytanie: synonimy + jawny tag wykrytego modelu (dla BM25 i LLM)."""
    # Zachowaj oryginał (gumka/pasek) — mapowanie doklejamy w [oficjalnie:], nie nadpisujemy.
    q = (question or "").strip()
    if not q:
        return q

    extras: list[str] = []
    for pattern, canonical in _SYNONYM_RULES:
        if pattern.search(q) and canonical.lower() not in q.lower():
            extras.append(canonical)

    if _PRICE_HINTS.search(q):
        extras.extend(["cennik", "cena EUR"])

    extras.extend(_gasket_size_hints(q))

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

    if re.search(r"\b(pasek|paski|pas\s+nap\w*|pas\s+czerw\w*|ta[sś]m\w*)\b", q, re.I):
        parts.append(
            "[MAPOWANIE: pasek/paski/taśma = Pas napędowy. Szukaj SKU: PNE-PAS-DOL, PNE-PAS-GOR, MOD-PAS. "
            "NIE mylić z SRU-PAS (śruby) ani uszczelką.]"
        )

    if re.search(r"\b(uszczelk\w*|gumk\w*)\b", q, re.I):
        parts.append(
            "[MAPOWANIE: uszczelka ≠ tulejka. Szukaj SKU UGD-/UM-/UK-/USZ-. "
            "NIE proponuj BUD-GLO-*-TUL-MOC ani tulejek mocujących.]"
        )

    return " ".join(parts) if len(parts) > 1 else q


def is_price_query(question: str) -> bool:
    return bool(_PRICE_HINTS.search(question or ""))
