"""Deterministyczny dobór części z katalogu — omija halucynacje BM25/LLM.

SKU wyłącznie z katalogu. Intencja/sloty (app.rag.intent) mogą wzbogacić pytanie,
ale nigdy nie generują kodów.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Any

from app.i18n import loc
from app.rag.catalog import (
    PartRow,
    format_part_name_display,
    format_parts_markdown,
    load_catalog,
    parts_for_machine,
)
from app.rag.intent import PartSlots, slots_to_lookup_question
from app.rag.machines import (
    is_machine_unknown_message,
    machine_display_name,
    resolve_machine_for_parts_lookup,
    resolve_machine_from_query,
)
from app.rag.machine_web import (
    format_machine_card_tag,
    format_machine_cards_tag,
    format_product_card_tag,
    machine_web_info,
)
from app.rag.query_rewrite import apply_colloquial_aliases

_EXPLICIT_MM_RE = re.compile(r"\b([0-9]+(?:[.,][0-9]+)?)\s*mm\b", re.I)
_FI_RE = re.compile(r"\bfi\s*([0-9]+(?:[.,][0-9]+)?)\b", re.I)
_SKU_RE = re.compile(r"\b([A-Z]{1,5}-[A-Z0-9]{2,}(?:-[A-Z0-9.,]+)+)\b", re.I)
_DIM_TOKEN_RE = re.compile(r"\bd\d+x\d+\b", re.I)

# uszczelka / uszczelki / uszczelek (D.lm) / uszczelkę …
_USZCZELKA_RE = re.compile(r"\b(uszczel\w*|gumk\w*|o-?ring|oring|gasket|seals?)\b", re.I)
_TULEJA_RE = re.compile(r"\b(tulejk\w*|tulej\w*|wstawk\w*|sleeve|insert)\b", re.I)
_PAS_RE = re.compile(
    r"\b(pasek|paski|pas\s+nap\w*|pas\s+czerw\w*|pas(?:y|ów|ow)?|ta[sś]m\w*|drive\s*belt|belts?)\b",
    re.I,
)
_OPONKA_RE = re.compile(
    r"\b("
    r"oponk\w*"
    r"|gumk\w*\s+(?:jezdn|na\s+(?:rolk|ko))"
    r"|ko[łl]o\s+nap\w*"
    r"|gumk\w*\s+na\s+ko[łl]o\s+nap\w*"
    r"|drive\s*wheel|tyre|tire"
    r")\b",
    re.I,
)
# mikrorurka / mikrorur / mikro rur / do mikrorur / na mikrorurk*
_MIKRORURKA_RE = re.compile(
    r"\b("
    r"mikrorur\w*"
    r"|mikro\s*rur\w*"
    r"|rurk\w*"
    r"|rurce"
    r"|microduct"
    r"|micro[-\s]?tube"
    r")\b",
    re.I,
)
_KABEL_RE = re.compile(r"\b(kabel|kabla|kablu|kable|światłowod\w*|swiatlowod\w*|cable|fiber|fibre)\b", re.I)
_WSTAWKA_USZ_RE = re.compile(r"uszczelk\w*.{0,24}wstawk\w*|wstawk\w*.{0,24}uszczelk\w*", re.I)
_MANOMETR_RE = re.compile(r"\b(manometr\w*|zegar|wska[zź]nik\s+ci[sś]nieni|pressure\s*gauge|gauge)\b", re.I)
# lista / wszystkie / pokaż / wyświetl / wybiorę sam …
_LIST_INTENT_RE = re.compile(
    r"\b("
    r"lista|list[eę]|listy|"
    r"wszystkie|wszystkich|"
    r"poka[zż]|wy[sś]wietl|"
    r"jakie\s+macie|jakie\s+s[aą]|"
    r"dost[eę]pne|"
    r"wybior[eę]\s+sam|wybior[eę]\s+sobie|"
    r"wybiorę\s+sam|wybiorę\s+sobie|"
    r"list\s+of|show\s+all|all\s+gaskets"
    r")\b",
    re.I,
)
# gołe „wyświetl listę / wybiorę sam” bez słowa uszczelka — follow-up po flow uszczelki
_BARE_LIST_FOLLOWUP_RE = re.compile(
    r"\b("
    r"(?:wy[sś]wietl|poka[zż]).{0,40}list\w*"
    r"|list\w*.{0,24}(?:wybior|wybier)"
    r"|wybior[eę]\s+sam"
    r"|wybiorę\s+sam"
    r")\b",
    re.I,
)
_GASKET_PRIOR_REASONS = frozenset({
    "uszczelka",
    "uszczelka_list",
    "need_size",
    "need_gasket_context",
})

_MACHINE_SHOWCASE_RE = re.compile(
    r"\b("
    r"co to|czym jest|opisz|poka[zż]|informacj\w+ o|charakterystyk|"
    r"parametr|specyfik|zasi[eę]g|jakie kable|jakie rur|"
    r"do czego|jak dzia[lł]a|model maszyn|"
    r"what is|what's|tell me about|specifications?|"
    r"how does|which cables|which ducts|product info"
    r")\b",
    re.I,
)

_PRODUCT_CARD_RE = re.compile(
    r"(?:"
    r"kart[aęe]\s+produkt\w*|"
    r"produktow\w*\s+kart\w*|"
    r"chc[eę]\s+kart\w*|"
    r"poka[zż]\s+kart\w*|"
    r"wy[sś]lij\s+kart\w*|"
    r"\bpdf\b|"
    r"bro[sś]ur\w*|"
    r"ulotk\w*|"
    r"product\s+card|"
    r"datasheet|data\s*sheet|"
    r"spec\s*sheet|brochure"
    r")",
    re.I,
)

# Samo «mam BDJ NEXT» / «I have Budget Easy Set» — deklaracja modelu, nie prośba o opis
_BARE_MACHINE_DECLARE_RE = re.compile(
    r"^\s*(?:mam|posiadam|i\s+have|i['']ve\s+got|my\s+machine\s+is)\s+"
    r"(?:maszyn[ęe]\s+)?(?:bdj\s+)?[\w\s+\-/]+$",
    re.I,
)

# Pytanie o dobór części → NIGDY nie puszczamy do LLM (halucynuje SKU)
_PARTS_INTENT_RE = re.compile(
    r"\b("
    r"uszczel\w*|gumk\w*|o-?ring|oring|"
    r"tulejk\w*|tulej\w*|wstawk\w*|"
    # «pas napędowy»: \w* zjada ę; bare «pas» / «pasy» — nie «pasowana» (brak \b po pas)
    r"pasek|paski|pas\s+nap\w*|pas\s+czerw\w*|pas(?:y|ów|ow)?|ta[sś]m\w*|"
    r"oponk\w*|ko[łl]o\s+nap\w*|"
    r"śrub\w*|srub\w*|"
    r"rolk\w*|kółk\w*|kolk\w*|"
    r"wałek|wałki|ośka|"
    r"manometr\w*|zegar|"
    r"łożysk\w*|lozysk\w*|"
    r"częś[cć]\w*|czesci|sku|katalog\w*|bom|"
    r"gasket|seals?|sleeve|spare\s*parts?|drive\s*belt|"
    r"bullet\w*|spadochron\w*|t[lł]oczek|"
    r"króciec|krolec|szybkoz[lł][aą]cz|"
    r"za[sś]lepk\w*|organizer|prelube|p[lł]yn\s+po[sś]lizg"
    r")\b",
    re.I,
)

_STOPWORDS = {
    "mam", "maszyne", "maszynę", "maszyna", "bdj", "do", "na", "dla", "potrzebuje",
    "potrzebuję", "prosze", "proszę", "jaka", "jaki", "jakie", "o", "i", "w", "z",
    "mm", "model", "plus", "easy", "set", "next", "mini", "budget", "max", "extended",
}


@dataclass(frozen=True)
class LookupResult:
    answer: str
    parts: tuple[PartRow, ...]
    reason: str


def is_parts_intent(question: str) -> bool:
    return bool(_PARTS_INTENT_RE.search(question or ""))


def _parse_mm(raw: str) -> float | None:
    try:
        return float(raw.replace(",", "."))
    except ValueError:
        return None


def _extract_size_mm(question: str) -> float | None:
    q = question or ""
    matches = list(_EXPLICIT_MM_RE.finditer(q))
    if matches:
        return _parse_mm(matches[-1].group(1))
    matches = list(_FI_RE.finditer(q))
    if matches:
        return _parse_mm(matches[-1].group(1))
    return None


def _almost_eq(a: float, b: float, tol: float = 0.05) -> bool:
    return abs(a - b) <= tol


def _fmt_mm(val: float) -> str:
    s = f"{val:.1f}".rstrip("0").rstrip(".")
    return s.replace(".", ",")


def is_machine_showcase_intent(question: str) -> bool:
    """Pytanie o maszynę (nie o konkretną część) — prezentacja modelu."""
    q = question or ""
    if is_parts_intent(q):
        return False
    if is_product_card_intent(q):
        return False
    return bool(_MACHINE_SHOWCASE_RE.search(q))


def is_product_card_intent(question: str) -> bool:
    """Klient prosi o kartę produktu (PDF)."""
    q = question or ""
    if is_parts_intent(q):
        return False
    return bool(_PRODUCT_CARD_RE.search(q))


def try_product_card(
    question: str,
    chip_machine: str | None = None,
) -> LookupResult | None:
    """Karta produktu PDF — duży przycisk w UI."""
    if not is_product_card_intent(question):
        return None

    tag = resolve_machine_for_parts_lookup(question or "", chip_machine=chip_machine)
    if tag:
        info = machine_web_info(tag)
        if not info:
            return None
        pdf_tag = format_product_card_tag(tag)
        if pdf_tag:
            intro = loc(
                f"Oto **karta produktu {info.display}** — PDF z parametrami "
                f"i zdjęciami maszyny:",
                f"Here is the **{info.display} product card** — a PDF with specs "
                f"and photos of the machine:",
            )
            return LookupResult(
                answer=f"{intro}\n\n{pdf_tag}",
                parts=(),
                reason="product_card",
            )
        intro = loc(
            f"Dla **{info.display}** nie mamy jeszcze karty PDF. "
            f"Szczegóły techniczne znajdziesz na stronie produktu:",
            f"We don’t have a PDF product card for **{info.display}** yet. "
            f"Technical details are on the product page:",
        )
        card = format_machine_card_tag(tag)
        return LookupResult(
            answer=f"{intro}\n\n{card}" if card else intro,
            parts=(),
            reason="product_card",
        )

    cards = format_machine_cards_tag(["all"])
    return LookupResult(
        answer=(
            loc(
                "Której maszyny dotyczy **karta produktu**? "
                "**Kliknij model** poniżej — pokażę przycisk do PDF.",
                "Which machine should the **product card** be for? "
                "**Click a model** below — I’ll show the PDF button.",
            )
            + (f"\n\n{cards}" if cards else "")
        ),
        parts=(),
        reason="product_card",
    )


def try_machine_showcase(
    question: str,
    chip_machine: str | None = None,
) -> LookupResult | None:
    """Krótka prezentacja modelu + zdjęcie/link ze strony BDJ."""
    from app.rag.machine_web import machine_web_info

    tag = resolve_machine_for_parts_lookup(question or "", chip_machine=chip_machine)
    if not tag:
        return None
    info = machine_web_info(tag)
    if not info:
        return None

    q = (question or "").strip()
    mentioned = resolve_machine_from_query(q, chip_machine=None) is not None
    short_query = len(q) < 45 and mentioned
    if _BARE_MACHINE_DECLARE_RE.match(q) and not is_machine_showcase_intent(q):
        return None
    if not is_machine_showcase_intent(q) and not short_query:
        return None

    tagline = loc(info.tagline, info.tagline_en or info.tagline)
    intro = loc(
        f"**{info.display}** — {tagline}\n\n"
        f"Szczegóły techniczne i zdjęcia maszyny znajdziesz na stronie produktu. "
        f"Do doboru **części zamiennej** napisz np.: "
        f"«Mam {info.label}, potrzebuję uszczelkę mikrorurki 7 mm».",
        f"**{info.display}** — {tagline}\n\n"
        f"You’ll find specs and photos on the product page. "
        f"To pick a **spare part**, write e.g.: "
        f"«I have {info.label}, I need a 7 mm microduct gasket».",
    )
    card = format_machine_card_tag(tag)
    return LookupResult(
        answer=f"{intro}\n\n{card}" if card else intro,
        parts=(),
        reason="machine_showcase",
    )


def ask_machine_message() -> str:
    """Publiczny komunikat need_machine (z kartami maszyn)."""
    return _ask_machine().answer


def _ask_machine() -> LookupResult:
    cards = format_machine_cards_tag(["all"])
    return LookupResult(
        answer=(
            loc(
                "Żeby dobrać część, **kliknij zdjęcie swojej maszyny** poniżej "
                "(albo wybierz model u góry czatu). "
                "Potem dopisz czego potrzebujesz i wymiar — **kod SKU podam ja**, "
                "a Ty klikasz «Zapytaj o wycenę».",
                "To quote a spare part, **click the photo of your machine** below "
                "(or pick the model at the top of the chat). "
                "Then tell me what you need and the size — **I’ll provide the SKU**, "
                "and you tap «Ask for a quote».",
            )
            + (f"\n\n{cards}" if cards else "")
        ),
        parts=(),
        reason="need_machine",
    )


def _ask_machine_for_list() -> LookupResult:
    cards = format_machine_cards_tag(["all"])
    return LookupResult(
        answer=(
            loc(
                "Żeby wypisać listę uszczelek na rurkę/mikrorurkę, **kliknij zdjęcie maszyny** "
                "poniżej (albo wybierz model u góry). "
                "Potem napisz ponownie «lista uszczelek na mikrorurkę» — pokażę pełny katalog "
                "dla tego modelu, bez dopytywania o rozmiar rurki.",
                "To list tube/microduct gaskets, **click the machine photo** below "
                "(or pick the model at the top). "
                "Then write again «list of microduct gaskets» — I’ll show the full catalog "
                "for that model, without asking for the tube size.",
            )
            + (f"\n\n{cards}" if cards else "")
        ),
        parts=(),
        reason="need_machine",
    )


def _ask_gasket_context(display: str) -> LookupResult:
    return LookupResult(
        answer=loc(
            f"Dla modelu **{display}** doprecyzuj proszę: uszczelka na **kabel** "
            f"czy na **mikrorurkę/rurkę**? (np. «na kabel 7 mm» albo «mikrorurka 7 mm»). "
            f"**Kod SKU dobiorę sam z katalogu** — potem kliknij «Zapytaj o wycenę».",
            f"For **{display}**, please specify: gasket for **cable** or for "
            f"**microduct/tube**? (e.g. «cable 7 mm» or «microduct 7 mm»). "
            f"**I’ll pick the SKU from the catalog** — then tap «Ask for a quote».",
        ),
        parts=(),
        reason="need_gasket_context",
    )


def _ask_diameter(display: str, part_label: str) -> LookupResult:
    return LookupResult(
        answer=loc(
            f"Dla modelu **{display}** napisz tylko średnicę w mm "
            f"(np. «7 mm» albo «10 mm») — chodzi o {part_label}. "
            f"**Kod SKU dobiorę sam z katalogu** — potem możesz od razu "
            f"kliknąć «Zapytaj o wycenę». Nie musisz znać numeru części.",
            f"For **{display}**, just write the diameter in mm "
            f"(e.g. «7 mm» or «10 mm») — this is about the {part_label}. "
            f"**I’ll pick the SKU from the catalog** — then you can tap "
            f"«Ask for a quote». You don’t need the part number.",
        ),
        parts=(),
        reason="need_size",
    )


def _has_gasket_list_topic(question: str) -> bool:
    """Uszczelka i/lub (mikro)rurka — wystarczy jedno (kolokwialne „lista uszczelek” / „do mikrorur”)."""
    q = question or ""
    return bool(_USZCZELKA_RE.search(q) or _MIKRORURKA_RE.search(q))


def _is_list_intent(question: str, *, prior_reason: str | None = None) -> bool:
    """
    Lista/wszystkie/pokaż uszczelek na (mikro)rurkę — bez konkretnego wymiaru.
    Follow-up typu «wyświetl listę wybiorę sam» po flow uszczelki też łapie.
    """
    q = question or ""
    if not _LIST_INTENT_RE.search(q):
        return False
    if _has_gasket_list_topic(q):
        return True
    # goły follow-up po uszczelce / pytaniu o średnicę
    if prior_reason in _GASKET_PRIOR_REASONS and _BARE_LIST_FOLLOWUP_RE.search(q):
        return True
    return False


def is_gasket_list_followup(question: str, prior_reason: str | None = None) -> bool:
    """True gdy goła lista bez słowa uszczelka, ale sesja była w flow uszczelki."""
    q = (question or "").strip()
    if not q:
        return False
    if is_parts_intent(q):
        return False
    return _is_list_intent(q, prior_reason=prior_reason)


def _name_mentions_tube(name_l: str) -> bool:
    """rurka / rurek / mikrorurka — «rurek» nie zawiera podciągu «rurk»."""
    return bool(
        re.search(r"mikro\s*rur|mikrorur|rurk|rurek|rurce|\brur\b", name_l, re.I)
    )


def _list_tube_gaskets(parts: list[PartRow]) -> list[PartRow]:
    """Wszystkie uszczelki na rurkę/mikrorurkę (UM/UGD/WST-RUR + Hydro) — bez UK."""
    gaskets = [p for p in parts if p.kind == "uszczelka" and not _is_cable_gasket_sku(p)]
    tube: list[PartRow] = []
    for p in gaskets:
        name_l = p.name.lower()
        sku_u = p.sku.upper()
        if (
            _is_ugd_um(p)
            or _is_wst_rur_gasket(p)
            or "mikrorurk" in name_l
            or "na rurk" in name_l
            or (_name_mentions_tube(name_l) and "wstaw" in name_l)
            # Hydro Multi Tube: GLO-*-USZ-*, USZ-*-RUR*, sznur silikonowy
            or (sku_u.startswith("GLO-") and "USZ" in sku_u)
            or (sku_u.startswith("USZ") and ("RUR" in sku_u or "SIL" in sku_u or "GUM" in sku_u))
        ):
            tube.append(p)
    # Katalogi bez UM/UGD (np. Multi Tube) — pokaż wszystkie nie-UK uszczelki
    if not tube and gaskets:
        tube = list(gaskets)
    out: list[PartRow] = []
    seen: set[str] = set()
    for p in sorted(tube, key=lambda x: (x.sku.upper(), x.name)):
        key = p.sku.upper()
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def _ask_clarify_after_reject() -> LookupResult:
    return LookupResult(
        answer=loc(
            "OK — pomijam poprzednią propozycję (to nie to). "
            "Napisz proszę **czego dokładnie potrzebujesz**, np.:\n"
            "• «uszczelka mikrorurki 7 mm do Extended»\n"
            "• «uszczelka na kabel 10 mm do Next»\n"
            "• «pasek do Next»\n\n"
            "Ja **podam kod SKU z katalogu**, a Ty klikasz **«Zapytaj o wycenę»**. "
            "Nie proszę Cię o numer SKU.",
            "OK — I’ll skip the previous suggestion (that’s not it). "
            "Please write **exactly what you need**, e.g.:\n"
            "• «7 mm microduct gasket for Extended»\n"
            "• «10 mm cable gasket for Next»\n"
            "• «drive belt for Next»\n\n"
            "I’ll **quote the catalog SKU**, and you tap **«Ask for a quote»**. "
            "You don’t need the SKU number.",
        ),
        parts=(),
        reason="reject_clarify",
    )


_REJECT_RE = re.compile(
    r"("
    r"po\s+chuj|po\s+co\s+mi|nie\s+chc[eę]|nie\s+potrzebuj|"
    r"źle|zły|zła|nie\s+to|to\s+nie\s+(ta|to|tulej|uszczel)|"
    r"wy[sś]wietla|pokazujesz|pokazuj|dajesz\s+mi|"
    r"odpierdal|kurw|bez\s+sensu|po\s+co\s+tu"
    r")",
    re.I,
)


def _is_rejection(question: str) -> bool:
    return bool(_REJECT_RE.search(question or ""))


def _wants_tuleja_positive(question: str) -> bool:
    """True tylko przy realnym zapytaniu o tuleję — nie przy skardze na tuleję."""
    q = question or ""
    if _is_rejection(q):
        return False
    if re.search(r"nie\s+(chc[eę]|potrzebuj)\w*.{0,20}tulej", q, re.I):
        return False
    if re.search(r"(wy[sś]wietl|pokazuj|dajesz).{0,30}tulej", q, re.I):
        return False
    if re.search(r"\btulejk\w*\s+mocuj", q, re.I):
        return True
    if re.search(r"(potrzebuj|chc[eę]|szukam|dobierz|daj|mam).{0,24}tulej", q, re.I):
        return True
    if re.search(r"\btulej\w*.{0,20}\d+(?:[.,]\d+)?\s*mm", q, re.I):
        return True
    return False



def _miss(display: str, detail: str) -> LookupResult:
    return LookupResult(
        answer=loc(
            f"Przepraszam, ale w katalogu modelu **{display}** "
            f"nie znalazłem pozycji: {detail}. "
            f"Podaj dokładniejszą nazwę części / wymiar albo skorzystaj z kontaktu z obsługą.",
            f"Sorry, I couldn’t find this item in the **{display}** catalog: {detail}. "
            f"Please give a more precise part name / size, or contact support.",
        ),
        parts=(),
        reason="miss",
    )


def _normalize_text(s: str) -> str:
    """lower, bez polskich znaków, przecinek↔kropka, zbite spacje."""
    text = (s or "").lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = text.replace(",", ".")
    text = re.sub(r"\s+", " ", text)
    return text


def _has_explicit_fi(question: str) -> bool:
    """True gdy użytkownik podał jawne «fi 13,5» / «fi 13.5» (nie reguła −0,5)."""
    return bool(_FI_RE.search(question or ""))


def _looks_like_catalog_title(question: str) -> bool:
    """Wklejona pełna nazwa katalogowa / SKU — najpierw exact match, nie fuzzy size."""
    q = (question or "").strip()
    if not q:
        return False
    n = _normalize_text(q)
    if _SKU_RE.search(q):
        return True
    if _DIM_TOKEN_RE.search(n):  # D35x5, D22x5…
        return True
    if _has_explicit_fi(q) and len(n) >= 20:
        return True
    # długa nazwa typu „Uszczelka na mikrorurkę …”
    if len(n) >= 28 and is_parts_intent(q):
        return True
    return False


def _distinctive_tokens(norm: str) -> set[str]:
    tokens: set[str] = set()
    for m in _DIM_TOKEN_RE.finditer(norm):
        tokens.add(m.group(0))
    for m in _FI_RE.finditer(norm):
        val = m.group(1).replace(",", ".")
        tokens.add(f"fi{val}")
        tokens.add(val)
    # „50mm” / „50 mm” ≡ fi 50 — żeby search mm trafiał w nazwy z fi (i odwrotnie)
    for m in _EXPLICIT_MM_RE.finditer(norm):
        val = m.group(1).replace(",", ".")
        tokens.add(f"fi{val}")
        tokens.add(val)
    for m in re.finditer(r"\bmikrorurk\w*", norm):
        tokens.add("mikrorurk")
    for m in re.finditer(r"\bkabel\w*", norm):
        tokens.add("kabel")
    for t in re.findall(r"[a-z0-9][a-z0-9.\-]{2,}", norm):
        if t in _STOPWORDS or t in {"uszczelka", "uszczelke", "na", "do"}:
            continue
        if re.fullmatch(r"\d+(?:\.\d+)?", t):
            continue
        tokens.add(t)
    return tokens


def _query_wants_gasket(query_norm: str) -> bool:
    return bool(re.search(r"\buszczel", query_norm))


def _query_wants_cable(query_norm: str) -> bool:
    return bool(re.search(r"\bkabel", query_norm))


def _part_is_gasket(part: PartRow) -> bool:
    sku = (part.sku or "").upper()
    name = (part.name or "").lower()
    if sku.startswith(("UK-", "UM-", "UGD", "USZ-")) or "USZ" in sku:
        return True
    return "uszczel" in name or part.kind == "uszczelka"


def _part_is_cable_gasket(part: PartRow) -> bool:
    sku = (part.sku or "").upper()
    name = (part.name or "").lower()
    return sku.startswith("UK-") or "na kabel" in name or ("uszczel" in name and "kabel" in name)


def _name_match_score(query_norm: str, part: PartRow) -> float:
    name_n = _normalize_text(part.name)
    sku_n = _normalize_text(part.sku)
    if not query_norm or not name_n:
        return 0.0

    # „uszczelka kabla 7mm” NIE może trafić w kulkę/zaślepkę tylko po wspólnym „7mm”
    if _query_wants_gasket(query_norm) and not _part_is_gasket(part):
        return 0.0
    if _query_wants_cable(query_norm) and not _part_is_cable_gasket(part):
        return 0.0

    if query_norm == name_n or query_norm == sku_n:
        return 1.0
    # pełna nazwa zawarta w zapytaniu (lub odwrotnie) — najwyższy priorytet
    if name_n in query_norm or (len(query_norm) >= 18 and query_norm in name_n):
        return 0.95
    if sku_n and (sku_n in query_norm or query_norm.replace(" ", "") == sku_n.replace(" ", "")):
        return 0.92

    # jawne fi / mm w query → wymagaj tego samego wymiaru w części
    q_fi = _FI_RE.search(query_norm)
    q_mm = _EXPLICIT_MM_RE.search(query_norm)
    q_size_raw = None
    if q_fi:
        q_size_raw = q_fi.group(1)
    elif q_mm:
        q_size_raw = q_mm.group(1)
    if q_size_raw is not None:
        q_size_val = _parse_mm(q_size_raw)
        if q_size_val is not None and part.fi_mm is not None and not _almost_eq(part.fi_mm, q_size_val):
            return 0.0
        # nazwa bez fi/mm vs query bez fi/mm — jeśli reszta nazwy się zgadza (wklejony tytuł)
        name_core = _FI_RE.sub(" ", name_n)
        name_core = _EXPLICIT_MM_RE.sub(" ", name_core)
        name_core = re.sub(r"[()]", " ", name_core)
        query_core = _FI_RE.sub(" ", query_norm)
        query_core = _EXPLICIT_MM_RE.sub(" ", query_core)
        name_core = re.sub(r"\s+", " ", name_core).strip()
        query_core = re.sub(r"\s+", " ", query_core).strip()
        if name_core and len(name_core) >= 12 and (
            name_core in query_core or (len(query_core) >= 12 and query_core in name_core)
        ):
            return 0.9

    q_tok = _distinctive_tokens(query_norm)
    p_tok = _distinctive_tokens(f"{name_n} {sku_n}")
    if not q_tok or not p_tok:
        return 0.0
    distinctive = {
        t for t in q_tok
        if _DIM_TOKEN_RE.fullmatch(t) or t.startswith("fi") or ("-" in t and len(t) > 5)
    }
    if distinctive and not (distinctive & p_tok):
        return 0.0
    # przy D35x5 + fi wymagaj obu
    has_dim = any(_DIM_TOKEN_RE.fullmatch(t) for t in q_tok)
    has_fi = any(t.startswith("fi") for t in q_tok)
    if has_dim and has_fi:
        if not any(_DIM_TOKEN_RE.fullmatch(t) for t in (q_tok & p_tok)):
            return 0.0
        if not any(t.startswith("fi") for t in (q_tok & p_tok)):
            return 0.0
        return 0.88

    overlap = q_tok & p_tok
    if not overlap:
        return 0.0
    # sam wymiar (fi/7) bez wspólnego typu części — za słabe na exact
    non_size = {
        t for t in overlap
        if not t.startswith("fi") and not re.fullmatch(r"\d+(?:\.\d+)?", t)
    }
    if not non_size:
        return 0.0
    ratio = len(overlap) / max(len(q_tok), 1)
    strong = bool(
        any(_DIM_TOKEN_RE.fullmatch(t) for t in overlap)
        or any(t.startswith("fi") for t in overlap)
        or "mikrorurk" in overlap
        or "kabel" in overlap
        or any("-" in t and len(t) > 5 for t in overlap)
    )
    if strong and ratio >= 0.55 and len(overlap) >= 3 and non_size:
        return 0.75 + 0.15 * min(ratio, 1.0)
    return 0.0


def _find_exact_name_matches(
    question: str,
    *,
    min_score: float = 0.85,
) -> list[PartRow]:
    """Exact / near-exact match nazwy lub SKU w całym katalogu."""
    q_norm = _normalize_text(question)
    # usuń szum typu „do BDJ MAX / potrzebuję”
    q_norm = re.sub(
        r"\b(potrzebuj\w*|prosze|proszę|mam|maszyn\w*|bdj|"
        r"budget|plus|easy|set|next|mini|max|extended|dual|head|"
        r"hydro|chain|dragonair|do|dla)\b",
        " ",
        q_norm,
    )
    q_norm = re.sub(r"\s+", " ", q_norm).strip()
    if len(q_norm) < 6:
        return []

    scored: list[tuple[float, PartRow]] = []
    for rows in load_catalog().values():
        for p in rows:
            score = _name_match_score(q_norm, p)
            if score >= min_score:
                scored.append((score, p))
    if not scored:
        return []

    # zostaw tylko najlepszy score (±0.02) — uniknij mieszania fi 11,5 z 13,5
    best = max(s for s, _ in scored)
    scored = [(s, p) for s, p in scored if s >= best - 0.02]
    scored.sort(key=lambda x: (-x[0], x[1].sku, x[1].machine_tag))

    # jeśli jest exact/containment trafienie na konkretne fi — filtruj do tego SKU
    top_sku = scored[0][1].sku.upper()
    # gdy top score >= 0.9, trzymaj tylko ten sam SKU (różne maszyny OK)
    if scored[0][0] >= 0.9:
        scored = [(s, p) for s, p in scored if p.sku.upper() == top_sku]

    out: list[PartRow] = []
    seen: set[tuple[str, str]] = set()
    for score, p in scored:
        key = (p.sku.upper(), p.machine_tag)
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def _found_elsewhere(display: str, hits: list[PartRow]) -> LookupResult:
    """Część istnieje w innych modelach — nie udawaj dostępności na wybranej maszynie."""
    by_sku: dict[str, list[PartRow]] = {}
    for p in hits:
        by_sku.setdefault(p.sku.upper(), []).append(p)

    blocks: list[str] = []
    for sku_u, rows in by_sku.items():
        name = format_part_name_display(rows[0].name, sku=rows[0].sku)
        sku = rows[0].sku
        machines = sorted({machine_display_name(r.machine_tag) or r.machine for r in rows})
        machines_str = ", ".join(f"**{m}**" for m in machines)
        blocks.append(f"• `{sku}` — {name} → {machines_str}")

    listing = "\n".join(blocks)
    return LookupResult(
        answer=(
            loc(
                f"Ta dokładna pozycja **nie występuje** w katalogu modelu **{display}**.\n\n"
                f"Natomiast jest w katalogu innych maszyn:\n{listing}\n\n"
                f"Czy chodziło Ci o jedną z tych maszyn? Jeśli tak — przełącz model na liście "
                f"i napisz ponownie (wtedy możesz od razu kliknąć **«Zapytaj o wycenę»**), "
                f"albo skorzystaj z kontaktu z obsługą.",
                f"This exact item is **not in** the **{display}** catalog.\n\n"
                f"It is listed for other machines:\n{listing}\n\n"
                f"Did you mean one of those models? If so — switch the machine in the list "
                f"and write again (then you can tap **«Ask for a quote»**), "
                f"or contact support.",
            )
        ),
        parts=(),
        reason="found_elsewhere",
    )


def _try_exact_or_elsewhere(
    question: str,
    machine: str,
    display: str,
    local_parts: list[PartRow],
) -> LookupResult | None:
    """
    Exact/near-exact nazwa lub SKU.
    Trafienie na wybranej maszynie → sukces.
    Tylko na innych → komunikat found_elsewhere.
    """
    hits = _find_exact_name_matches(question)
    if not hits:
        return None

    local_skus = {p.sku.upper() for p in local_parts}
    on_selected = [p for p in hits if p.machine_tag == machine or p.sku.upper() in local_skus]
    # preferuj wiersze z wybranej maszyny
    on_selected_local = [p for p in local_parts if p.sku.upper() in {h.sku.upper() for h in hits}]
    if on_selected_local:
        intro = loc(
            f"Na podstawie katalogu części dla maszyny **{display}**, "
            f"oto dopasowana pozycja (po dokładnej nazwie/SKU): "
            f"Zaznacz część i kliknij **«Zapytaj o wycenę»** — nie musisz znać kodu SKU.",
            f"From the spare-parts catalog for **{display}**, "
            f"here is the matching item (exact name/SKU): "
            f"Select the part and tap **«Ask for a quote»** — you don’t need the SKU code.",
        )
        # jedna pozycja na SKU
        uniq: list[PartRow] = []
        seen: set[str] = set()
        for p in on_selected_local:
            if p.sku.upper() in seen:
                continue
            seen.add(p.sku.upper())
            uniq.append(p)
        return LookupResult(
            answer=format_parts_markdown(uniq[:4], intro, display),
            parts=tuple(uniq[:4]),
            reason="exact_name",
        )

    elsewhere = [p for p in hits if p.machine_tag != machine]
    if elsewhere and not on_selected:
        return _found_elsewhere(display, elsewhere)
    if elsewhere:
        return _found_elsewhere(display, elsewhere)
    return None


def _is_ugd_um(p: PartRow) -> bool:
    return p.sku.upper().startswith(("UGD", "UM-"))


def _is_wst_rur_gasket(p: PartRow) -> bool:
    """USZ-WST-RUR… oraz Hydro USZ-…-WST-…-RUR… / WST-PRO-RUR."""
    u = p.sku.upper()
    if "USZ-WST-RUR" in u or "WST-RUR" in u:
        return True
    if "WST" in u and "RUR" in u and (
        u.startswith("USZ") or "USZ" in u or "GLO" in u
    ):
        return True
    return False


def _is_cable_gasket_sku(p: PartRow) -> bool:
    return p.sku.upper().startswith("UK-") or "na kabel" in p.name.lower()


def _filter_tube_gaskets(
    parts: list[PartRow],
    asked_mm: float,
    wstawka_context: bool,
    *,
    exact_fi: bool = False,
) -> list[PartRow]:
    """
    UGD/UM → reguła −0,5 mm (chyba że użytkownik podał jawne fi).
    GLO-*-USZ-WST-RUR → wymiar exact (bez −0,5), wg promptu.
    Nigdy UK.
    """
    gaskets = [p for p in parts if p.kind == "uszczelka" and not _is_cable_gasket_sku(p)]
    if wstawka_context:
        wst = [p for p in gaskets if _is_wst_rur_gasket(p) or "wstaw" in p.name.lower()]
        if wst:
            gaskets = wst

    half = round(asked_mm - 0.5, 2)

    if exact_fi:
        # jawne «fi 13,5» → exact, bez −0,5
        ugd_ex = [p for p in gaskets if _is_ugd_um(p) and p.fi_mm is not None and _almost_eq(p.fi_mm, asked_mm)]
        if ugd_ex:
            return ugd_ex[:1]
        wst = [
            p for p in gaskets
            if _is_wst_rur_gasket(p) and p.fi_mm is not None and _almost_eq(p.fi_mm, asked_mm)
        ]
        if wst:
            return wst[:1]
        other = [
            p for p in gaskets
            if p.fi_mm is not None
            and _almost_eq(p.fi_mm, asked_mm)
            and (
                _name_mentions_tube(p.name.lower())
                or "mikro" in p.name.lower()
                or _name_mentions_tube(p.section.lower())
                or _is_wst_rur_gasket(p)
            )
        ]
        return other[:1]

    # 1) UGD/UM fi = asked−0.5
    ugd = [p for p in gaskets if _is_ugd_um(p) and p.fi_mm is not None and _almost_eq(p.fi_mm, half)]
    if ugd:
        return ugd[:1]

    # 2) UGD/UM exact (gdy ktoś podał już fi 6,5)
    ugd_ex = [p for p in gaskets if _is_ugd_um(p) and p.fi_mm is not None and _almost_eq(p.fi_mm, asked_mm)]
    if ugd_ex:
        return ugd_ex[:1]

    # 3) Uszczelka wstawki rurki — exact size
    wst = [
        p for p in gaskets
        if _is_wst_rur_gasket(p) and p.fi_mm is not None and _almost_eq(p.fi_mm, asked_mm)
    ]
    if wst:
        return wst[:1]

    # 4) Inne uszczelki „na rurkę/mikro” / Hydro GLO-USZ z exact fi
    other = [
        p for p in gaskets
        if p.fi_mm is not None
        and _almost_eq(p.fi_mm, asked_mm)
        and (
            _name_mentions_tube(p.name.lower())
            or "mikro" in p.name.lower()
            or _name_mentions_tube(p.section.lower())
            or (p.sku.upper().startswith("GLO-") and "USZ" in p.sku.upper())
            or p.sku.upper().startswith("USZ")
        )
    ]
    return other[:1]


def _filter_cable_gaskets(parts: list[PartRow], asked_mm: float) -> list[PartRow]:
    gaskets = [p for p in parts if p.kind == "uszczelka" and _is_cable_gasket_sku(p)]
    exact = [p for p in gaskets if p.fi_mm is not None and _almost_eq(p.fi_mm, asked_mm)]
    return exact[:1]


def _filter_by_kind_and_size(parts: list[PartRow], kind: str, asked_mm: float) -> list[PartRow]:
    pool = [p for p in parts if p.kind == kind]
    return [p for p in pool if p.fi_mm is not None and _almost_eq(p.fi_mm, asked_mm)]


def _filter_pas(parts: list[PartRow]) -> list[PartRow]:
    pas = [p for p in parts if p.kind == "pas"]
    prefer = [p for p in pas if p.sku.upper().startswith("PNE-PAS-")]
    if prefer:
        order = {"PNE-PAS-DOL": 0, "PNE-PAS-GOR": 1}
        prefer.sort(key=lambda p: order.get(p.sku.upper(), 9))
        return prefer[:4]
    return pas[:4]


def _keyword_tokens(question: str) -> list[str]:
    q = (question or "").lower()
    q = re.sub(r"[^\wąćęłńóśźż\s\-]", " ", q, flags=re.I)
    tokens = []
    for t in q.split():
        t = t.strip("-")
        if len(t) < 3 or t in _STOPWORDS:
            continue
        if re.fullmatch(r"\d+(?:[.,]\d+)?", t):
            continue
        tokens.append(t)
    return tokens


def _keyword_search(parts: list[PartRow], question: str, limit: int = 6) -> list[PartRow]:
    """Proste wyszukiwanie po nazwie/SKU — tylko istniejące wiersze."""
    tokens = _keyword_tokens(question)
    if not tokens:
        return []
    scored: list[tuple[int, PartRow]] = []
    for p in parts:
        blob = f"{p.sku} {p.name} {p.section}".lower()
        hits = sum(1 for t in tokens if t in blob)
        if hits <= 0:
            continue
        # wymagaj przynajmniej jednego „mocnego” tokenu części (nie tylko „maszyna”)
        scored.append((hits, p))
    scored.sort(key=lambda x: (-x[0], x[1].sku))
    out: list[PartRow] = []
    seen: set[str] = set()
    for _, p in scored:
        if p.sku in seen:
            continue
        seen.add(p.sku)
        out.append(p)
        if len(out) >= limit:
            break
    # odrzuć zbyt słabe (1 trafienie na ogólne słowo)
    if out and scored and scored[0][0] < 1:
        return []
    return out


def _candidates_short_list(
    parts: list[PartRow],
    display: str,
    *,
    intro: str | None = None,
    limit: int = 5,
) -> LookupResult:
    """Krótka lista kandydatów z katalogu — bez wolnego LLM i bez dumpa całego BOM."""
    uniq: list[PartRow] = []
    seen: set[str] = set()
    for p in parts:
        key = p.sku.upper()
        if key in seen:
            continue
        seen.add(key)
        uniq.append(p)
        if len(uniq) >= limit:
            break
    text = intro or loc(
        f"W katalogu maszyny **{display}** znalazłem kilka pasujących pozycji "
        f"— wybierz właściwą (albo doprecyzuj wymiar / nazwę). "
        f"Zaznacz część i kliknij **«Zapytaj o wycenę»**.",
        f"In the **{display}** catalog I found several matching items "
        f"— pick the right one (or specify size / name). "
        f"Select the part and tap **«Ask for a quote»**.",
    )
    return LookupResult(
        answer=format_parts_markdown(uniq, text, display),
        parts=tuple(uniq),
        reason="candidates",
    )


def _llm_pick_candidate_index(
    question: str,
    candidates: list[PartRow],
    llm: Any,
) -> int | None:
    """
    LLM wybiera indeks spośród podanych kandydatów katalogowych albo None (= dopytaj).
    Nie może wymyślić SKU poza listą.
    """
    if llm is None or len(candidates) < 2:
        return None
    lines = [
        f"{i}: {p.sku} | {p.name}"
        for i, p in enumerate(candidates[:5])
    ]
    prompt = (
        "Wybierz JEDNĄ pozycję z listy kandydatów katalogowych najlepiej pasującą "
        "do pytania użytkownika. Odpowiedz WYŁĄCZNIE JSON: "
        '{"index": <int|null>, "ask": <bool>}. '
        "Jeśli niepewne — index=null, ask=true. NIGDY nie wymyślaj SKU.\n"
        f"Pytanie: {question}\n"
        f"Kandydaci:\n" + "\n".join(lines)
    )
    try:
        if hasattr(llm, "complete"):
            resp = llm.complete(prompt)
            text = str(getattr(resp, "text", None) or resp)
        else:
            return None
    except Exception:
        return None
    m = re.search(r"\{[\s\S]*\}", text or "")
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    if data.get("ask") is True:
        return None
    idx = data.get("index")
    if isinstance(idx, int) and 0 <= idx < min(5, len(candidates)):
        return idx
    return None


def maybe_refine_with_candidates(
    result: LookupResult,
    *,
    question: str,
    llm: Any = None,
) -> LookupResult:
    """
    Gdy keyword zwróci 2–5 trafień — LLM może wskazać jedną z listy katalogowej
    albo zostawiamy krótką listę (nigdy nie wymyśla SKU).
    """
    if result.reason != "keyword" or len(result.parts) < 2:
        return result
    parts = list(result.parts)[:5]
    if len(parts) == 1:
        return result
    display = machine_display_name(parts[0].machine_tag) or parts[0].machine
    # Twardy próg keyword — słabe trafienia → lista, bez LLM auto-pick
    tokens = _keyword_tokens(question)
    if tokens:
        scored: list[tuple[int, PartRow]] = []
        for p in parts:
            blob = f"{p.sku} {p.name} {p.section}".lower()
            hits = sum(1 for t in tokens if t in blob)
            if hits > 0:
                scored.append((hits, p))
        scored.sort(key=lambda x: (-x[0], x[1].sku))
        if scored and scored[0][0] >= 2 and (
            len(scored) == 1 or scored[0][0] > scored[1][0]
        ):
            chosen = scored[0][1]
            intro = loc(
                f"Na podstawie katalogu części dla maszyny **{display}**, "
                f"oto najlepiej pasująca pozycja: "
                f"Zaznacz część i kliknij **«Zapytaj o wycenę»**.",
                f"From the spare-parts catalog for **{display}**, "
                f"here is the best match: "
                f"Select the part and tap **«Ask for a quote»**.",
            )
            return LookupResult(
                answer=format_parts_markdown([chosen], intro, display),
                parts=(chosen,),
                reason="candidate_pick",
            )
        if not scored or scored[0][0] < 2:
            return _candidates_short_list(parts, display, limit=5)
    picked = _llm_pick_candidate_index(question, parts, llm)
    if picked is not None:
        chosen = parts[picked]
        intro = loc(
            f"Na podstawie katalogu części dla maszyny **{display}**, "
            f"oto najlepiej pasująca pozycja spośród kandydatów: "
            f"Zaznacz część i kliknij **«Zapytaj o wycenę»** — nie musisz znać kodu SKU.",
            f"From the spare-parts catalog for **{display}**, "
            f"here is the best match among candidates: "
            f"Select the part and tap **«Ask for a quote»** — you don’t need the SKU code.",
        )
        return LookupResult(
            answer=format_parts_markdown([chosen], intro, display),
            parts=(chosen,),
            reason="candidate_pick",
        )
    # bez pewnego wyboru — krótka lista zamiast dumpa
    if len(parts) > 1:
        return _candidates_short_list(parts, display, limit=5)
    return result


def lookup_from_slots(
    slots: PartSlots,
    original_question: str,
    *,
    chip_machine: str | None = None,
    prior_reason: str | None = None,
    llm: Any = None,
    history: list[tuple[str, str]] | None = None,
) -> LookupResult | None:
    """
    Hybryda: sloty → wzbogacone pytanie → wyłącznie katalog.
    Soft inference (historia/kind/size) siedzi w slotach; SKU tylko z BOM.
    """
    q_orig = apply_colloquial_aliases((original_question or "").strip())
    if is_machine_unknown_message(q_orig):
        return _ask_machine()
    chip = chip_machine
    resolved = resolve_machine_for_parts_lookup(
        original_question or "",
        chip_machine=chip,
        history=history,
        prior_reason=prior_reason,
    )
    if slots.needs_clarify == "machine" and not resolved:
        return _ask_machine_for_list() if slots.list_all else _ask_machine()

    if _OPONKA_RE.search(q_orig):
        # Nowa intencja oponki — nie ciągnij flow uszczelki z sesji
        direct = try_deterministic_lookup(
            original_question,
            chip_machine=chip,
            prior_reason=None,
            machine_source=original_question,
            history=None,
        )
        if direct is not None and direct.reason not in ("need_machine",):
            return direct

    enriched = slots_to_lookup_question(
        slots, original_question, chip_machine=chip
    )
    result = try_deterministic_lookup(
        enriched,
        chip_machine=chip,
        prior_reason=prior_reason,
        machine_source=original_question,
        history=history,
    )
    if result is None and enriched != (original_question or "").strip():
        result = try_deterministic_lookup(
            original_question,
            chip_machine=chip,
            prior_reason=prior_reason,
            machine_source=original_question,
            history=history,
        )
    if result is None:
        return None

    # Smarter clarify: jedno pytanie naraz wg slotów
    if result.reason == "need_machine" and slots.needs_clarify == "machine":
        return result
    if result.reason == "need_size" and slots.needs_clarify in {"size", "none"}:
        return result

    if result.reason == "keyword" and result.parts:
        return maybe_refine_with_candidates(
            result, question=original_question or enriched, llm=llm
        )

    # miss + keyword na oryginale → krótka lista kandydatów zamiast pustki
    if result.reason == "miss" and chip and resolved:
        machine = resolved
        if machine:
            local = parts_for_machine(machine)
            display = machine_display_name(machine)
            cands = _keyword_search(local, apply_colloquial_aliases(original_question or enriched), limit=5)
            if not cands and slots.part_kind.startswith("uszczelka"):
                cands = _list_tube_gaskets(local)[:5] if slots.list_all else []
            if cands:
                return maybe_refine_with_candidates(
                    _candidates_short_list(cands, display),
                    question=original_question or enriched,
                    llm=llm,
                )
    return result


def try_deterministic_lookup(
    question: str,
    chip_machine: str | None = None,
    *,
    prior_reason: str | None = None,
    machine_source: str | None = None,
    history: list[tuple[str, str]] | None = None,
) -> LookupResult | None:
    """
    Dobór części wyłącznie z katalogu.
    Dla pytań o części ZAWSZE zwraca LookupResult (trafienie / dopytanie / miss) —
    caller nie powinien iść do LLM po SKU.
    prior_reason: ostatni reason z sesji (np. need_size / uszczelka) — follow-up listy.
    """
    q = apply_colloquial_aliases((question or "").strip())
    if not q or len(q) < 3:
        return None

    if is_machine_unknown_message(q) or is_machine_unknown_message(question or ""):
        return _ask_machine()

    list_intent = (
        _is_list_intent(q, prior_reason=prior_reason)
        or _is_list_intent(question or "", prior_reason=prior_reason)
    )
    if _OPONKA_RE.search(q) or _OPONKA_RE.search(question or ""):
        list_intent = False
    parts_q = is_parts_intent(q) or is_parts_intent(question or "")
    if not parts_q and not list_intent:
        return None

    # Skarga na złą część (np. „po chuj tuleje”) — NIE traktuj jako zamówienie tulei
    if _is_rejection(q) or _is_rejection(question or ""):
        return _ask_clarify_after_reject()

    machine = resolve_machine_for_parts_lookup(
        machine_source if machine_source is not None else question,
        chip_machine=chip_machine,
        history=history,
        prior_reason=prior_reason,
    )
    if not machine:
        if list_intent:
            return _ask_machine_for_list()
        return _ask_machine()

    parts = parts_for_machine(machine)
    if not parts:
        return _miss(machine_display_name(machine), loc("brak katalogu części", "no parts catalog"))

    display = machine_display_name(machine)
    size = _extract_size_mm(q)

    # Lista rodziny bez wymiaru → pełna tabela (nie pytaj o mm, nie idź w exact title / LLM)
    if list_intent and size is None:
        matched = _list_tube_gaskets(parts)
        if not matched:
            return _miss(display, loc("uszczelki na rurkę/mikrorurkę", "tube/microduct gaskets"))
        intro = loc(
            f"Oto **lista uszczelek na rurkę/mikrorurkę** w katalogu maszyny **{display}** "
            f"({len(matched)} pozycji). "
            f"Zaznacz wybraną pozycję i kliknij **«Zapytaj o wycenę»** — nie musisz znać kodu SKU.",
            f"Here is the **tube/microduct gasket list** in the **{display}** catalog "
            f"({len(matched)} items). "
            f"Select an item and tap **«Ask for a quote»** — you don’t need the SKU code.",
        )
        return LookupResult(
            answer=format_parts_markdown(matched, intro, display),
            parts=tuple(matched),
            reason="uszczelka_list",
        )

    # Pełna nazwa katalogowa / SKU → najpierw exact, zanim fuzzy size (−0,5 itd.)
    # Exact match też na oryginalnym tekście (wklejona nazwa bez synonimów)
    if _looks_like_catalog_title(q) or _looks_like_catalog_title(question or ""):
        exact = _try_exact_or_elsewhere(question or q, machine, display, parts)
        if exact is None and q != (question or "").strip():
            exact = _try_exact_or_elsewhere(q, machine, display, parts)
        if exact is not None:
            return exact

    explicit_fi = _has_explicit_fi(q) or _has_explicit_fi(question or "")
    tube_ctx = bool(_MIKRORURKA_RE.search(q))
    kabel_ctx = bool(_KABEL_RE.search(q))
    wstawka_usz = bool(_WSTAWKA_USZ_RE.search(q))

    wants_uszczelka = bool(_USZCZELKA_RE.search(q))
    wants_tuleja = _wants_tuleja_positive(q) and not wants_uszczelka
    if wants_uszczelka and re.search(r"zaproponowan\w*\s+tulej", q, re.I):
        wants_tuleja = False
    wants_pas = bool(_PAS_RE.search(q))
    wants_oponka = bool(_OPONKA_RE.search(q))
    wants_manometr = bool(_MANOMETR_RE.search(q)) and not wants_uszczelka

    matched: list[PartRow] = []
    reason = ""
    size_note = ""

    def _miss_or_elsewhere(detail: str) -> LookupResult:
        """Po lokalnym miss — sprawdź czy exact nazwa jest na innych maszynach."""
        # Tylko przy wklejonej pełnej nazwie katalogowej — nie promuj kulki po „7mm”
        if not (
            _looks_like_catalog_title(q) or _looks_like_catalog_title(question or "")
        ):
            return _miss(display, detail)
        cross = _try_exact_or_elsewhere(question or q, machine, display, parts)
        if cross is not None and cross.reason == "found_elsewhere":
            return cross
        if cross is not None and cross.parts:
            return cross
        return _miss(display, detail)

    if wants_uszczelka:
        if size is None:
            return _ask_diameter(display, loc("uszczelkę", "gasket"))
        if tube_ctx and not kabel_ctx:
            matched = _filter_tube_gaskets(parts, size, wstawka_usz, exact_fi=explicit_fi)
            if (
                matched
                and not explicit_fi
                and _is_ugd_um(matched[0])
                and matched[0].fi_mm is not None
            ):
                if abs(matched[0].fi_mm - (size - 0.5)) < 0.06:
                    size_note = loc(
                        f" Dla rurki/mikrorurki {_fmt_mm(size)} mm "
                        f"dobieram uszczelkę fi {_fmt_mm(matched[0].fi_mm)} mm (reguła −0,5 mm).",
                        f" For a {_fmt_mm(size)} mm tube/microduct "
                        f"I quote a fi {_fmt_mm(matched[0].fi_mm)} mm gasket (−0.5 mm rule).",
                    )
        elif kabel_ctx and not tube_ctx:
            matched = _filter_cable_gaskets(parts, size)
        elif tube_ctx and kabel_ctx:
            matched = _filter_cable_gaskets(parts, size)
            if not matched:
                matched = _filter_tube_gaskets(parts, size, wstawka_usz, exact_fi=explicit_fi)
        else:
            cable_hits = _filter_cable_gaskets(parts, size)
            tube_hits = _filter_tube_gaskets(parts, size, wstawka_usz, exact_fi=explicit_fi)
            if cable_hits and tube_hits:
                return _ask_gasket_context(display)
            matched = cable_hits or tube_hits
            if not matched:
                matched = _filter_by_kind_and_size(parts, "uszczelka", size)[:3]
            if (
                matched
                and not explicit_fi
                and tube_hits
                and not cable_hits
                and _is_ugd_um(matched[0])
                and matched[0].fi_mm is not None
            ):
                if abs(matched[0].fi_mm - (size - 0.5)) < 0.06:
                    size_note = loc(
                        f" Dla rurki {_fmt_mm(size)} mm "
                        f"dobieram uszczelkę fi {_fmt_mm(matched[0].fi_mm)} mm (reguła −0,5 mm).",
                        f" For a {_fmt_mm(size)} mm tube "
                        f"I quote a fi {_fmt_mm(matched[0].fi_mm)} mm gasket (−0.5 mm rule).",
                    )
        reason = "uszczelka"
        if not matched:
            return _miss_or_elsewhere(loc(f"uszczelka {_fmt_mm(size)} mm", f"{_fmt_mm(size)} mm gasket"))

    elif wants_tuleja:
        if size is None:
            return _ask_diameter(display, loc("tulejkę", "sleeve"))
        matched = _filter_by_kind_and_size(parts, "tuleja", size)[:2]
        if not matched:
            # BOM często nazywa „uszczelka … tuleja fi N” → kind=uszczelka
            matched = [
                p
                for p in parts
                if p.fi_mm is not None
                and _almost_eq(p.fi_mm, size)
                and "tulej" in p.name.lower()
            ][:2]
        reason = "tuleja"
        if not matched:
            return _miss_or_elsewhere(loc(f"tulejka {_fmt_mm(size)} mm", f"{_fmt_mm(size)} mm sleeve"))

    elif wants_pas:
        matched = _filter_pas(parts)
        reason = "pas"
        if not matched:
            return _miss_or_elsewhere(loc("pas napędowy (PNE-PAS)", "drive belt (PNE-PAS)"))

    elif wants_oponka:
        if size is None:
            matched = [p for p in parts if p.kind == "oponka"][:12]
            if matched:
                intro = loc(
                    f"Oto **oponki / gumki na koło napędowe** w katalogu maszyny **{display}** "
                    f"({len(matched)} pozycji). "
                    f"Zaznacz wybraną pozycję i kliknij **«Zapytaj o wycenę»** — nie musisz znać kodu SKU.",
                    f"Here are the **drive-wheel tyres / rubber rings** in the **{display}** catalog "
                    f"({len(matched)} items). "
                    f"Select an item and tap **«Ask for a quote»** — you don’t need the SKU code.",
                )
                return LookupResult(
                    answer=format_parts_markdown(matched, intro, display),
                    parts=tuple(matched),
                    reason="oponka_list",
                )
        else:
            matched = _filter_by_kind_and_size(parts, "oponka", size)[:4]
        reason = "oponka"
        if not matched:
            return _miss_or_elsewhere(loc("oponka", "drive-wheel tyre"))

    elif wants_manometr:
        matched = [
            p for p in parts
            if "manometr" in p.name.lower() or p.sku.upper().startswith("MAN-")
        ][:4]
        reason = "manometr"
        if not matched:
            return _miss_or_elsewhere(loc("manometr", "pressure gauge"))

    else:
        # ogólne pytanie o część (śruba, rolka, …) — tylko keyword po katalogu
        matched = _keyword_search(parts, q, limit=6)
        reason = "keyword"
        if not matched:
            detail = " ".join(_keyword_tokens(q)[:6]) or "podana nazwa"
            return _miss_or_elsewhere(detail)

    if reason == "uszczelka":
        # Nie myl z tulejką mocującą (TUL-MOC), ale zostaw „uszczelka … tuleja fi N”.
        matched = [
            p
            for p in matched
            if p.kind == "uszczelka"
            and "tul-moc" not in p.sku.lower()
            and not re.search(r"tulejk?\w*\s+mocuj", p.name, re.I)
        ]
        if not matched:
            return _miss_or_elsewhere(loc("uszczelka", "gasket"))

    intro = loc(
        f"Na podstawie katalogu części dla maszyny **{display}**, "
        f"oto dopasowana pozycja:{size_note} "
        f"Zaznacz część i kliknij **«Zapytaj o wycenę»** — nie musisz znać kodu SKU.",
        f"From the spare-parts catalog for **{display}**, "
        f"here is the matching item:{size_note} "
        f"Select the part and tap **«Ask for a quote»** — you don’t need the SKU code.",
    )
    return LookupResult(
        answer=format_parts_markdown(matched, intro, display),
        parts=tuple(matched),
        reason=reason,
    )
