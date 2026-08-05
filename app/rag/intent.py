"""Lekka ekstrakcja intencji/slotów części — LLM myśli o intencji, katalog o SKU.

Nigdy nie wymyśla kodów SKU. Wypełnia wyłącznie sloty z tekstu użytkownika
(+ krótka historia). Fallback: reguły/regex gdy LLM niedostępny lub padnie.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, replace
from typing import Any, Literal

from app.rag.query_rewrite import apply_colloquial_aliases

PartKind = Literal[
    "uszczelka_mikrorurka",
    "uszczelka_kabel",
    "tuleja",
    "pas",
    "manometr",
    "other",
    "unknown",
]
ClarifyNeed = Literal["machine", "size", "kind", "none"]

_VALID_KINDS = frozenset({
    "uszczelka_mikrorurka",
    "uszczelka_kabel",
    "tuleja",
    "pas",
    "manometr",
    "other",
    "unknown",
})
_VALID_CLARIFY = frozenset({"machine", "size", "kind", "none"})

_EXPLICIT_MM_RE = re.compile(r"\b([0-9]+(?:[.,][0-9]+)?)\s*mm\b", re.I)
_FI_RE = re.compile(r"\bfi\s*([0-9]+(?:[.,][0-9]+)?)\b", re.I)
_BARE_SIZE_RE = re.compile(
    r"^\s*(?:fi\s*)?([0-9]+(?:[.,][0-9]+)?)\s*(?:mm)?\s*$",
    re.I,
)
_USZCZELKA_RE = re.compile(r"\b(uszczel\w*|gumk\w*|o-?ring|oring)\b", re.I)
_MIKRORURKA_RE = re.compile(
    r"\b(mikrorur\w*|mikro\s*rur\w*|rurk\w*|rurce)\b",
    re.I,
)
_KABEL_RE = re.compile(r"\b(kabel|kabla|kablu|kable|światłowod\w*|swiatlowod\w*)\b", re.I)
_TULEJA_RE = re.compile(r"\b(tulejk\w*|tulej\w*|wstawk\w*)\b", re.I)
_PAS_RE = re.compile(
    r"\b(pasek|paski|pas\s+nap\w*|pas\s+czerw\w*|pas(?:y|ów|ow)?|ta[sś]m\w*)\b",
    re.I,
)
_MANOMETR_RE = re.compile(r"\b(manometr\w*|zegar|wska[zź]nik\s+ci[sś]nieni)\b", re.I)
_LIST_RE = re.compile(
    r"\b("
    r"lista|list[eę]|listy|wszystkie|wszystkich|"
    r"poka[zż]|wy[sś]wietl|jakie\s+macie|dost[eę]pne|"
    r"wybior[eę]\s+sam|wybiorę\s+sam"
    r")\b",
    re.I,
)
_SAME_BUT_RE = re.compile(
    r"\b("
    r"to\s+samo|"
    r"tak\s+samo|"
    r"to\s+samo\s+ale|"
    r"a\s+na\s+(?:kabel|mikrorur|rurk)|"
    r"ale\s+na\s+(?:kabel|mikrorur|rurk)|"
    r"tylko\s+na\s+(?:kabel|mikrorur|rurk)|"
    r"zamian\w*\s+na"
    r")\b",
    re.I,
)
_PARTS_HINT_RE = re.compile(
    r"\b("
    r"uszczel\w*|gumk\w*|o-?ring|tulej\w*|wstawk\w*|"
    r"pasek|paski|pas\s+nap|pas\s+czerw|pas(?:y|ów|ow)?|ta[sś]m\w*|manometr|zegar|rolk\w*|śrub\w*|"
    r"częś[cć]\w*|sku|katalog|bom|oponk\w*|fi\s*\d|"
    r"kabel|mikrorur|rurk"
    r")\b",
    re.I,
)

_KIND_TO_PHRASE: dict[str, str] = {
    "uszczelka_mikrorurka": "uszczelka mikrorurki",
    "uszczelka_kabel": "uszczelka na kabel",
    "tuleja": "tulejka",
    "pas": "pas napędowy",
    "manometr": "manometr",
}

_INTENT_SYSTEM = """Jesteś ekstraktorem slotów do doboru części zamiennych BDJ.
Zwróć WYŁĄCZNIE jeden obiekt JSON (bez markdown, bez komentarzy).
NIGDY nie wymyślaj kodów SKU / numerów katalogowych — tylko sloty z tekstu.

Pola JSON:
{
  "machine": string|null,          // model z tekstu/historii, np. "Extended", "Next"
  "part_kind": "uszczelka_mikrorurka"|"uszczelka_kabel"|"tuleja"|"pas"|"manometr"|"other"|"unknown",
  "size_mm": number|null,          // średnica w mm jeśli podana
  "exact_fi": bool,                // true gdy użytkownik napisał jawne "fi X"
  "list_all": bool,                // chce listę / wszystkie / wybiorę sam
  "confidence": number,            // 0..1
  "needs_clarify": "machine"|"size"|"kind"|"none"
}

Reguły:
- Uzupełniaj sloty z bieżącej wiadomości + krótkiej historii (follow-up).
- „to samo ale na kabel” → zachowaj machine/size z historii, part_kind=uszczelka_kabel.
- Gołe „7” / „7 mm” po pytaniu o uszczelkę → size_mm + kind z historii.
- „gumka/oring” → uszczelka_*; „pasek” → pas; „zegar” → manometr.
- Gdy brak modelu a potrzeba części → needs_clarify=machine.
- Gdy uszczelka/tuleja bez rozmiaru i nie list_all → needs_clarify=size.
- Nie zgaduj size_mm ani machine jeśli nie ma w tekście/historii.
"""


@dataclass(frozen=True)
class PartSlots:
    machine: str | None = None
    part_kind: PartKind = "unknown"
    size_mm: float | None = None
    exact_fi: bool = False
    list_all: bool = False
    confidence: float = 0.0
    needs_clarify: ClarifyNeed = "none"

    def is_parts_ish(self) -> bool:
        if self.list_all:
            return True
        if self.part_kind not in ("unknown",):
            return True
        if self.size_mm is not None and self.confidence >= 0.4:
            return True
        return False


def _parse_mm(raw: str) -> float | None:
    try:
        return float(raw.replace(",", "."))
    except ValueError:
        return None


def _extract_size(text: str) -> tuple[float | None, bool]:
    q = text or ""
    fi = list(_FI_RE.finditer(q))
    if fi:
        return _parse_mm(fi[-1].group(1)), True
    mm = list(_EXPLICIT_MM_RE.finditer(q))
    if mm:
        return _parse_mm(mm[-1].group(1)), False
    bare = _BARE_SIZE_RE.match(q.strip())
    if bare:
        return _parse_mm(bare.group(1)), bool(re.match(r"^\s*fi\b", q.strip(), re.I))
    return None, False


def _detect_kind(text: str) -> PartKind:
    q = apply_colloquial_aliases(text or "")
    has_usz = bool(_USZCZELKA_RE.search(q))
    tube = bool(_MIKRORURKA_RE.search(q))
    kabel = bool(_KABEL_RE.search(q))
    if has_usz or tube or kabel:
        if kabel and not tube:
            return "uszczelka_kabel"
        if tube:
            return "uszczelka_mikrorurka"
        if has_usz and kabel:
            return "uszczelka_kabel"
        if has_usz:
            # goła uszczelka — domyślnie ścieżka rurki (katalog i tak dopyta / spróbuje UK)
            return "uszczelka_mikrorurka"
        if kabel:
            return "uszczelka_kabel"
    if _TULEJA_RE.search(q) and not has_usz:
        return "tuleja"
    if _PAS_RE.search(q):
        return "pas"
    if _MANOMETR_RE.search(q):
        return "manometr"
    if _PARTS_HINT_RE.search(q):
        return "other"
    return "unknown"


def _history_blob(history: list[tuple[str, str]] | None) -> str:
    if not history:
        return ""
    chunks: list[str] = []
    for role, text in history[-4:]:
        t = (text or "").strip()
        if not t:
            continue
        # skróć długie odpowiedzi katalogowe — zostaw intro + SKU hints
        if role == "assistant" and len(t) > 400:
            t = t[:400]
        chunks.append(f"{role}: {t}")
    return "\n".join(chunks)


def _slots_from_rules(
    message: str,
    *,
    history: list[tuple[str, str]] | None = None,
    chip_machine: str | None = None,
    prior_reason: str | None = None,
) -> PartSlots:
    q = apply_colloquial_aliases((message or "").strip())
    hist = _history_blob(history)
    combined_for_machine = f"{hist}\n{q}" if hist else q

    size, exact_fi = _extract_size(q)
    kind = _detect_kind(q)
    list_all = bool(_LIST_RE.search(q))
    same_but = bool(_SAME_BUT_RE.search(q))

    # Inferencja z historii (follow-up)
    hist_kind: PartKind = "unknown"
    hist_size: float | None = None
    hist_exact = False
    hist_machine: str | None = None
    if history:
        # ostatnie wiadomości user — kind/size/machine
        for role, text in reversed(history[-4:]):
            blob = apply_colloquial_aliases(text or "")
            if hist_kind == "unknown":
                k = _detect_kind(blob)
                if k != "unknown":
                    hist_kind = k
            if hist_size is None:
                hs, he = _extract_size(blob)
                if hs is not None:
                    hist_size, hist_exact = hs, he
            if hist_machine is None:
                # proste wyłuskanie nazwy modelu z historii
                m = re.search(
                    r"\b(budget\s+plus\s+easy\s+set|budget\s+easy\s+set|budget\s+plus|"
                    r"budget|mini\s*c\s*plus|mini|nexta?|extended|max\s+dual\s+head|"
                    r"max|hydro\s+chain(?:\s+multi\s+tube|\s+cable)?|"
                    r"multi\s*tube|dragonair)\b",
                    blob,
                    re.I,
                )
                if m:
                    hist_machine = m.group(1)

    # „to samo ale na kabel/rurkę”
    if same_but or (kind in ("uszczelka_kabel", "uszczelka_mikrorurka") and hist_kind.startswith("uszczelka")):
        if kind == "unknown" and hist_kind != "unknown":
            kind = hist_kind
        if size is None and hist_size is not None:
            size, exact_fi = hist_size, hist_exact
        # przełączenie kabel ↔ mikrorurka
        if _KABEL_RE.search(q) and not _MIKRORURKA_RE.search(q):
            kind = "uszczelka_kabel"
        elif _MIKRORURKA_RE.search(q) and not _KABEL_RE.search(q):
            kind = "uszczelka_mikrorurka"

    # goły rozmiar / krótki follow-up po need_size
    bare_size_only = bool(_BARE_SIZE_RE.match(q.strip())) or (
        size is not None and kind in ("unknown", "other") and len(q) < 24
        and not _USZCZELKA_RE.search(q)
        and not _TULEJA_RE.search(q)
        and not _PAS_RE.search(q)
        and not _MANOMETR_RE.search(q)
    )
    if bare_size_only and size is not None and (
        prior_reason in {"need_size", "uszczelka", "uszczelka_list"}
        or hist_kind != "unknown"
    ):
        kind = hist_kind if hist_kind != "unknown" else "uszczelka_mikrorurka"

    if kind in ("unknown", "other") and list_all and (
        prior_reason in {"need_size", "uszczelka", "uszczelka_list"}
        or hist_kind.startswith("uszczelka")
        or _USZCZELKA_RE.search(hist)
        or _MIKRORURKA_RE.search(hist)
    ):
        kind = "uszczelka_mikrorurka"

    # vague: historia ma uszczelkę + maszynę, user pisze ogólnikowo
    if kind == "unknown" and hist_kind != "unknown" and (
        same_but or len(q) < 40 and _PARTS_HINT_RE.search(q)
    ):
        kind = hist_kind

    machine = chip_machine
    if not machine and hist_machine:
        machine = hist_machine
    # model w bieżącej wiadomości wygrywa — resolve zrobi to w lookup;
    # tu zostawiamy surową wskazówkę jeśli chip pusty
    m_now = re.search(
        r"\b(budget\s+plus\s+easy\s+set|budget\s+easy\s+set|budget\s+plus|"
        r"budget|mini\s*c\s*plus|mini|nexta?|extended|max\s+dual\s+head|"
        r"max|hydro\s+chain(?:\s+multi\s+tube|\s+cable)?|"
        r"multi\s*tube|dragonair)\b",
        q,
        re.I,
    )
    if m_now:
        machine = m_now.group(1)

    needs: ClarifyNeed = "none"
    if kind != "unknown" or list_all or size is not None:
        if not machine and not chip_machine:
            # spróbuj jeszcze z combined
            if not re.search(
                r"\b(budget|mini|next|extended|max|hydro|multi\s*tube|dragonair)\b",
                combined_for_machine,
                re.I,
            ):
                needs = "machine"
        if needs == "none" and kind in ("uszczelka_mikrorurka", "uszczelka_kabel", "tuleja"):
            if size is None and not list_all:
                needs = "size"
        if needs == "none" and kind == "unknown" and list_all is False and size is None:
            if _PARTS_HINT_RE.search(q):
                needs = "kind"

    conf = 0.35
    if kind != "unknown":
        conf += 0.25
    if size is not None:
        conf += 0.2
    if machine or chip_machine:
        conf += 0.15
    if list_all:
        conf += 0.1
    if same_but and hist_kind != "unknown":
        conf = max(conf, 0.7)
    conf = min(conf, 0.95)

    return PartSlots(
        machine=machine,
        part_kind=kind,
        size_mm=size,
        exact_fi=exact_fi,
        list_all=list_all,
        confidence=conf,
        needs_clarify=needs,
    )


def _coerce_slots(data: dict[str, Any]) -> PartSlots | None:
    if not isinstance(data, dict):
        return None
    kind = str(data.get("part_kind") or "unknown")
    if kind not in _VALID_KINDS:
        kind = "unknown"
    clarify = str(data.get("needs_clarify") or "none")
    if clarify not in _VALID_CLARIFY:
        clarify = "none"
    size = data.get("size_mm")
    size_f: float | None
    try:
        size_f = float(size) if size is not None else None
    except (TypeError, ValueError):
        size_f = None
    try:
        conf = float(data.get("confidence") or 0.0)
    except (TypeError, ValueError):
        conf = 0.0
    machine = data.get("machine")
    if machine is not None:
        machine = str(machine).strip() or None
    return PartSlots(
        machine=machine,
        part_kind=kind,  # type: ignore[arg-type]
        size_mm=size_f,
        exact_fi=bool(data.get("exact_fi")),
        list_all=bool(data.get("list_all")),
        confidence=max(0.0, min(conf, 1.0)),
        needs_clarify=clarify,  # type: ignore[arg-type]
    )


def _llm_extract(
    message: str,
    *,
    history: list[tuple[str, str]] | None,
    chip_machine: str | None,
    llm: Any,
) -> PartSlots | None:
    if llm is None:
        return None
    hist = _history_blob(history)
    user_payload = {
        "message": message,
        "chip_machine": chip_machine,
        "history": hist or None,
    }
    prompt = (
        "Wyodrębnij sloty. Wejście JSON:\n"
        f"{json.dumps(user_payload, ensure_ascii=False)}\n"
        "Odpowiedź: wyłącznie obiekt JSON ze slotami."
    )
    try:
        # LlamaIndex OpenAILike
        if hasattr(llm, "complete"):
            resp = llm.complete(_INTENT_SYSTEM + "\n\n" + prompt)
            text = str(getattr(resp, "text", None) or resp)
        elif hasattr(llm, "chat"):
            from llama_index.core.llms import ChatMessage, MessageRole

            resp = llm.chat([
                ChatMessage(role=MessageRole.SYSTEM, content=_INTENT_SYSTEM),
                ChatMessage(role=MessageRole.USER, content=prompt),
            ])
            text = str(getattr(resp, "message", resp))
            if hasattr(resp, "message") and hasattr(resp.message, "content"):
                text = str(resp.message.content)
        else:
            return None
    except Exception:
        return None

    text = (text or "").strip()
    if not text:
        return None
    # wyciągnij JSON z ewentualnego fence
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    return _coerce_slots(data)


def _merge_slots(primary: PartSlots, fallback: PartSlots) -> PartSlots:
    """Uzupełnij dziury z LLM slotami z reguł (i odwrotnie dla machine/size)."""
    kind = primary.part_kind if primary.part_kind != "unknown" else fallback.part_kind
    size = primary.size_mm if primary.size_mm is not None else fallback.size_mm
    exact = primary.exact_fi if primary.size_mm is not None else fallback.exact_fi
    machine = primary.machine or fallback.machine
    list_all = primary.list_all or fallback.list_all
    conf = max(primary.confidence, fallback.confidence)
    # clarify: preferuj bardziej konkretne z reguł gdy LLM mówi none zbyt wcześnie
    clarify = primary.needs_clarify
    if clarify == "none" and fallback.needs_clarify != "none" and (
        (fallback.needs_clarify == "size" and size is None and not list_all)
        or (fallback.needs_clarify == "machine" and not machine)
        or fallback.needs_clarify == "kind"
    ):
        clarify = fallback.needs_clarify
    # przelicz clarify po merge
    if not machine and kind != "unknown":
        clarify = "machine"
    elif kind in ("uszczelka_mikrorurka", "uszczelka_kabel", "tuleja") and size is None and not list_all:
        clarify = "size"
    elif clarify == "kind" and kind != "unknown":
        clarify = "none"
    return PartSlots(
        machine=machine,
        part_kind=kind,  # type: ignore[arg-type]
        size_mm=size,
        exact_fi=exact,
        list_all=list_all,
        confidence=conf,
        needs_clarify=clarify,  # type: ignore[arg-type]
    )


def extract_part_slots(
    message: str,
    *,
    history: list[tuple[str, str]] | None = None,
    chip_machine: str | None = None,
    prior_reason: str | None = None,
    llm: Any = None,
    use_llm: bool = True,
) -> PartSlots:
    """
    Ekstrahuje sloty części. LLM (JSON) + merge z regułami; przy błędzie — same reguły.
    Nigdy nie zwraca SKU.
    """
    rules = _slots_from_rules(
        message,
        history=history,
        chip_machine=chip_machine,
        prior_reason=prior_reason,
    )
    if not use_llm or llm is None:
        return rules

    llm_slots = _llm_extract(
        message,
        history=history,
        chip_machine=chip_machine,
        llm=llm,
    )
    if llm_slots is None:
        return rules
    return _merge_slots(llm_slots, rules)


def slots_to_lookup_question(slots: PartSlots, original: str) -> str:
    """Składa jednoznaczne pytanie dla try_deterministic_lookup z slotów."""
    bits: list[str] = []
    if slots.machine:
        bits.append(f"Mam maszynę {slots.machine}.")
    if slots.list_all:
        bits.append("wyświetl listę")
    phrase = _KIND_TO_PHRASE.get(slots.part_kind)
    if phrase:
        bits.append(phrase)
    elif slots.part_kind == "other" and (original or "").strip():
        bits.append(apply_colloquial_aliases(original.strip()))
    if slots.size_mm is not None:
        s = f"{slots.size_mm:g}".replace(".", ",")
        if slots.exact_fi:
            bits.append(f"fi {s}")
        else:
            bits.append(f"{s} mm")
    built = " ".join(bits).strip()
    if not built:
        return apply_colloquial_aliases((original or "").strip())
    # zachowaj oryginał gdy sloty prawie puste vs bogaty tekst użytkownika
    if slots.part_kind == "unknown" and not slots.list_all and slots.size_mm is None:
        return apply_colloquial_aliases((original or "").strip())
    return built


def slots_as_dict(slots: PartSlots) -> dict[str, Any]:
    return asdict(slots)


def with_chip_machine(slots: PartSlots, chip: str | None) -> PartSlots:
    if not chip or slots.machine:
        return slots
    return replace(slots, machine=chip)
