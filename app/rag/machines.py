"""Rozpoznawanie modeli maszyn BDJ z ścieżek i zapytań."""

from __future__ import annotations

import re

# slug folderu w knowledge/maszyny/ → tag (dłuższe slugi pierwsze przy matchu ścieżki)
FOLDER_TO_TAG = {
    "budget_plus_easy_set": "BDJ BUDGET PLUS EASY SET",
    "budget_easy_set": "BDJ BUDGET EASY SET",
    "budget_plus": "BDJ BUDGET PLUS",
    "budget": "BDJ BUDGET",
    "mini_c_plus": "BDJ MINI C PLUS",
    "next": "BDJ NEXT",
    "extended": "BDJ EXTENDED",
    "max_dual_head": "BDJ MAX DUAL HEAD",
    "max": "BDJ MAX",
    "hydro_chain_multi_tube": "BDJ HYDRO CHAIN MULTI TUBE",
    "hydro_chain_cable": "BDJ HYDRO CHAIN CABLE",
    "dragonair": "BDJ DRAGONAIR",
}

TAG_TO_DISPLAY = {
    "bdj dragonair": "BDJ DRAGONAIR",
    "bdj max dual head": "BDJ MAX DUAL HEAD",
    "bdj next": "BDJ NEXT",
    "bdj mini c plus": "BDJ MINI C PLUS",
    "bdj mini counter": "BDJ MINI C PLUS",  # alias legacy
    "bdj budget plus easy set": "BDJ BUDGET PLUS EASY SET",
    "bdj budget easy set": "BDJ BUDGET EASY SET",
    "bdj budget plus": "BDJ BUDGET PLUS",
    "bdj budget": "BDJ BUDGET",
    "bdj extended": "BDJ EXTENDED",
    "bdj hydro chain multi tube": "BDJ HYDRO CHAIN MULTI TUBE",
    "bdj hydro chain cable": "BDJ HYDRO CHAIN CABLE",
    "bdj max": "BDJ MAX",
}

# Najbardziej specyficzne wzorce pierwsze
_MACHINE_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("bdj dragonair", re.compile(r"\b(bdj\s*)?dragonair\b", re.I)),
    ("bdj max dual head", re.compile(r"\b(bdj\s*)?max\s*dual(?:\s*head)?\b", re.I)),
    ("bdj hydro chain multi tube", re.compile(r"\b(bdj\s*)?(hydro\s*chain\s*)?multi\s*tube\b", re.I)),
    ("bdj hydro chain cable", re.compile(r"\b(bdj\s*)?hydro\s*(?:chain|belt)\b", re.I)),
    ("bdj budget plus easy set", re.compile(r"\b(bdj\s*)?budget\s*plus\s*easy\s*set\b", re.I)),
    ("bdj budget easy set", re.compile(r"\b(bdj\s*)?budget\s*easy\s*set\b", re.I)),
    ("bdj budget plus", re.compile(r"\b(bdj\s*)?budget\s*plus\b(?!\s*easy)", re.I)),
    ("bdj mini c plus", re.compile(r"\b(bdj\s*)?mini\s*c\s*\+?\s*plus\b|\b(bdj\s*)?mini\s*c\+\b", re.I)),
    ("bdj mini c plus", re.compile(r"\b(bdj\s*)?(mini(?:e)?|counter)\b", re.I)),
    ("bdj next", re.compile(r"\b(bdj\s*)?nexta?\b", re.I)),
    ("bdj extended", re.compile(r"\b(bdj\s*)?extended\b", re.I)),
    ("bdj max", re.compile(r"\b(bdj\s*)?max\b(?!\s*dual)", re.I)),
    ("bdj budget", re.compile(r"\b(bdj\s*)?budget\b(?!\s*(?:plus|easy))", re.I)),
]

_CORRECTION_PATTERN = re.compile(
    r"\b(?:mam|posiadam|jednak|chodzi\s+o|to\s+jest|chce\s+(?:do|dla)?|potrzebuj[eę]\s+(?:do|dla)?|"
    r"do\s+maszyny|dla\s+maszyny)"
    r"\s+(?:bdj\s+)?"
    r"(dragonair|max\s*dual(?:\s*head)?|multi\s*tube|hydro\s*(?:chain|belt)|"
    r"budget\s*plus\s*easy\s*set|budget\s*easy\s*set|budget\s*plus|budget|"
    r"mini\s*c\s*\+?\s*plus|mini(?:e)?|counter|nexta?|extended|max)\b",
    re.I,
)

_TOKEN_TO_TAG = {
    "dragonair": "bdj dragonair",
    "max dual": "bdj max dual head",
    "max dual head": "bdj max dual head",
    "multi tube": "bdj hydro chain multi tube",
    "hydro chain": "bdj hydro chain cable",
    "hydro belt": "bdj hydro chain cable",
    "budget plus easy set": "bdj budget plus easy set",
    "budget easy set": "bdj budget easy set",
    "budget plus": "bdj budget plus",
    "budget": "bdj budget",
    "mini c plus": "bdj mini c plus",
    "mini c+ plus": "bdj mini c plus",
    "mini c+": "bdj mini c plus",
    "mini": "bdj mini c plus",
    "minie": "bdj mini c plus",
    "counter": "bdj mini c plus",
    "next": "bdj next",
    "nexta": "bdj next",
    "extended": "bdj extended",
    "max": "bdj max",
}

def _build_chip_to_tag() -> dict[str, str]:
    """Display name, short label, folder slug, underscore/space variants → canonical tag."""
    out: dict[str, str] = {}

    def _add(alias: str, tag: str) -> None:
        key = re.sub(r"\s+", " ", (alias or "").lower().strip())
        if not key:
            return
        out[key] = tag
        out[key.replace(" ", "_")] = tag
        out[key.replace("_", " ")] = tag
        out[key.replace("-", " ")] = tag
        out[key.replace("-", "_")] = tag

    for slug, display in FOLDER_TO_TAG.items():
        tag = display.lower()
        _add(display, tag)
        _add(slug, tag)
        # bez prefiksu BDJ
        short = re.sub(r"^bdj\s+", "", display, flags=re.I).strip()
        _add(short, tag)
        # slug ze spacjami (max dual head)
        _add(slug.replace("_", " "), tag)

    # Aliasy UI / legacy
    extras = {
        "dragonair": "bdj dragonair",
        "max dual": "bdj max dual head",
        "max dh": "bdj max dual head",
        "hydro chain": "bdj hydro chain cable",
        "bdj hydro chain": "bdj hydro chain cable",
        "hydro belt": "bdj hydro chain cable",
        "hydro chain cable": "bdj hydro chain cable",
        "hydro multi tube": "bdj hydro chain multi tube",
        "multi tube": "bdj hydro chain multi tube",
        "bdj mini": "bdj mini c plus",
        "bdj mini counter": "bdj mini c plus",
        "mini counter": "bdj mini c plus",
        "mini": "bdj mini c plus",
        "minie": "bdj mini c plus",
        "counter": "bdj mini c plus",
    }
    for alias, tag in extras.items():
        _add(alias, tag)

    return out


_CHIP_TO_TAG = _build_chip_to_tag()

# Child slug → parent slug(s) whose head-family parts are unioned into the child catalog.
# Dual Head shares Extended's head assembly — config, not per-SKU hacks.
# Budget Plus Excel nie ma UK-* (uszczelki na kabel); linia Budget je ma — dziedziczymy
# rodzinę głowicy/uszczelki z Budget, bo Plus Easy Set ≡ ta sama głowica zużycia.
MACHINE_BOM_INHERITS: dict[str, list[str]] = {
    "max_dual_head": ["extended"],
    "budget_plus": ["budget"],
    "budget_plus_easy_set": ["budget"],
}

# Undirected pairs: full catalog union (Easy Set ≡ base machine — shared parts).
# Each chip stays distinct; both catalogs see the union of both Excels.
MACHINE_BOM_UNION_PAIRS: list[tuple[str, str]] = [
    ("budget", "budget_easy_set"),
    ("budget_plus", "budget_plus_easy_set"),
]


def get_machine_tag_from_path(full_path: str) -> str:
    path_lower = full_path.replace("\\", "/").lower()

    for slug, tag in FOLDER_TO_TAG.items():
        if f"/maszyny/{slug}/" in path_lower or path_lower.rstrip("/").endswith(f"/maszyny/{slug}"):
            return tag

    if "dragonair" in path_lower:
        return "BDJ DRAGONAIR"
    if "dual" in path_lower and "max" in path_lower:
        return "BDJ MAX DUAL HEAD"
    if "multitube" in path_lower or "multi_tube" in path_lower or "multi tube" in path_lower:
        return "BDJ HYDRO CHAIN MULTI TUBE"
    if "hydro_chain_cable" in path_lower or "hydro belt" in path_lower:
        return "BDJ HYDRO CHAIN CABLE"
    if "hydro chain" in path_lower or "hydro_chain" in path_lower:
        return "BDJ HYDRO CHAIN CABLE"
    if "budget_plus_easy" in path_lower or "budget plus easy" in path_lower:
        return "BDJ BUDGET PLUS EASY SET"
    if "budget_easy" in path_lower or "budget easy" in path_lower:
        return "BDJ BUDGET EASY SET"
    if "budget_plus" in path_lower or "budget plus" in path_lower:
        return "BDJ BUDGET PLUS"
    if "mini_c_plus" in path_lower or "mini c plus" in path_lower:
        return "BDJ MINI C PLUS"
    if "extended" in path_lower or "extend" in path_lower:
        return "BDJ EXTENDED"
    if re.search(r"/budget(/|$)", path_lower) or path_lower.rstrip("/").endswith("/budget"):
        return "BDJ BUDGET"
    if "mini" in path_lower or "counter" in path_lower:
        return "BDJ MINI C PLUS"
    if "next" in path_lower:
        return "BDJ NEXT"
    if "max" in path_lower:
        return "BDJ MAX"
    return ""


def _normalize_token(token: str) -> str | None:
    key = re.sub(r"\s+", " ", token.lower().strip())
    key = key.replace("c+", "c plus")
    return _TOKEN_TO_TAG.get(key)


def _chip_to_tag(chip_machine: str | None) -> str | None:
    """Akceptuje display name (BDJ MAX), slug (max_dual_head) i warianty spacji/underscore."""
    if not chip_machine:
        return None
    raw = chip_machine.lower().strip()
    if not raw:
        return None
    # normalizuj separatory
    key = re.sub(r"[\s_\-]+", " ", raw).strip()
    if key in _CHIP_TO_TAG:
        return _CHIP_TO_TAG[key]
    underscored = key.replace(" ", "_")
    if underscored in _CHIP_TO_TAG:
        return _CHIP_TO_TAG[underscored]
    # już kanoniczny tag?
    if key in TAG_TO_DISPLAY:
        return key
    return _CHIP_TO_TAG.get(raw)


def _find_machine_mentions(query: str) -> list[tuple[int, str]]:
    found: list[tuple[int, int, str, int]] = []
    for priority, (tag, pattern) in enumerate(_MACHINE_RULES):
        for match in pattern.finditer(query):
            found.append((match.start(), match.end(), tag, priority))

    found.sort(key=lambda item: (item[0], item[3]))

    mentions: list[tuple[int, str]] = []
    seen_starts: set[int] = set()
    for start, _end, tag, _priority in found:
        if start in seen_starts:
            continue
        seen_starts.add(start)
        mentions.append((start, tag))
    return mentions


# User nie zna / pyta o model — nie dziedzicz chipa ani historii sesji.
_MACHINE_UNKNOWN_RE = re.compile(
    r"(?:"
    r"nie\s+w[iy]em\s+(?:jaki|jaka|jak[aą]|co\s+to\s+za)?(?:\s+mam)?\s*(?:model|maszyn)"
    r"|nie\s+znam\s+(?:modelu|maszyny|jak[aą]\s+(?:to\s+)?maszyn)"
    r"|nie\s+mam\s+poj[eę]cia\s+(?:jaki|jaka|jak[aą]|co\s+to\s+za)?\s*(?:model|maszyn)"
    r"|(?:jaki|jaka|jak[aą])\s+(?:to\s+)?(?:model|maszyn)\s+(?:mam|posiadam|u\s+mnie|to\s+jest)"
    r")",
    re.I,
)


def is_machine_unknown_message(text: str) -> bool:
    """True gdy user mówi, że nie zna modelu / pyta jaki ma model."""
    q = (text or "").strip()
    if not q:
        return False
    return bool(_MACHINE_UNKNOWN_RE.search(q))


# Follow-upy częściowe — wtedy można dziedziczyć model z wcześniejszych wiadomości USER.
_PARTS_SESSION_REASONS = frozenset({
    "uszczelka",
    "uszczelka_list",
    "need_size",
    "need_machine",
    "tuleja",
    "pas",
    "oponka",
    "oponka_list",
    "manometr",
    "keyword",
    "candidates",
    "candidate_pick",
    "exact_name",
    "found_elsewhere",
    "reject_clarify",
    "miss",
})


def resolve_machine_for_parts_lookup(
    message: str,
    *,
    chip_machine: str | None = None,
    history: list[tuple[str, str]] | None = None,
    prior_reason: str | None = None,
) -> str | None:
    """
    Model maszyny do katalogu części — tylko z wiarygodnych źródeł:
    (1) bieżąca wiadomość użytkownika, (2) chip UI, (3) wcześniejsze wiadomości USER
    w trwającym flow częściowym. Nigdy z odpowiedzi asystenta ani z syntetycznego
    „Mam maszynę …” wzbogaconego pytania (tam LLM często domyśla Extended).
    """
    if is_machine_unknown_message(message or ""):
        return None
    m = resolve_machine_from_query(message or "", chip_machine=None)
    if m:
        return m
    if chip_machine:
        return _chip_to_tag(chip_machine)
    if prior_reason in _PARTS_SESSION_REASONS and history:
        for role, text in reversed(history[-4:]):
            if role != "user":
                continue
            m = resolve_machine_from_query(text or "", chip_machine=None)
            if m:
                return m
    return None


def resolve_machine_from_query(query: str, chip_machine: str | None = None) -> str | None:
    """Wybiera właściwy model: korekta użytkownika > ostatnie wspomnienie > chip UI."""
    q = (query or "").strip()
    # Literówki klientów
    q = re.sub(r"\bbuget\b", "budget", q, flags=re.I)
    q = re.sub(r"\bbudzet\b", "budget", q, flags=re.I)
    if not q:
        return _chip_to_tag(chip_machine)

    if is_machine_unknown_message(q):
        return None

    correction = _CORRECTION_PATTERN.search(q)
    if correction:
        tag = _normalize_token(correction.group(1))
        if tag:
            return tag

    mentions = _find_machine_mentions(q)
    if len(mentions) >= 2:
        return mentions[-1][1]
    if len(mentions) == 1:
        return mentions[0][1]

    return _chip_to_tag(chip_machine)


def detect_machine_from_query(query: str) -> str | None:
    """Zwraca kanoniczny tag maszyny (lowercase) albo None."""
    return resolve_machine_from_query(query)


def machine_display_name(tag: str | None) -> str:
    if not tag:
        return ""
    return TAG_TO_DISPLAY.get(tag.lower(), tag.upper())


def detect_machine_for_log(question: str) -> str:
    tag = resolve_machine_from_query(question)
    if tag:
        return machine_display_name(tag)
    return "BRAK"
