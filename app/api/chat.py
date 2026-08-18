"""Endpointy czatu."""

from __future__ import annotations

import re

from fastapi import APIRouter, Request

from app.i18n import loc, set_lang
from app.models import ChatRequest, ResetRequest
from app.services.logging_store import log_customer_question
from app.rag.machines import resolve_machine_from_query

router = APIRouter(tags=["chat"])

chat_manager = None  # type: ignore

# 3-strike rule per session: po 3 nieudanych próbach doboru części
# pokazujemy przycisk kontaktu z obsługą (ten sam formularz co oferta).
HANDOFF_FAILURE_THRESHOLD = 3
_handoff_failures: dict[str, int] = {}

_SUPPORT_CONTACT_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bsupport\b", re.I),
    re.compile(r"skontaktow", re.I),
    re.compile(r"\bchc[eę]\s+(si[eę]\s+)?(skontakt|kontakt|porozmaw)", re.I),
    re.compile(r"kontakt\s+z\s+(obsług|obslug|support|zespo|handlow|serwis)", re.I),
    re.compile(r"(obsług|obslug)[aą]\s+(klient|technicz|handlow)", re.I),
    re.compile(r"dzia[lł]\s+(handlow|serwis)", re.I),
    re.compile(r"\bkonsultant", re.I),
    re.compile(r"porozmawia[ćc]\s+z\s+(cz[lł]owiekiem|kim[sś])", re.I),
    re.compile(r"formularz\s+kontakt", re.I),
    re.compile(r"dane\s+kontaktowe", re.I),
    re.compile(r"(numer|telefon|mail|e-mail|email)\s+kontakt", re.I),
    re.compile(r"jak\s+(si[eę]\s+)?skontakt", re.I),
    re.compile(r"gdzie\s+(si[eę]\s+)?skontakt", re.I),
]


def _is_unclear_response(answer: str) -> bool:
    if not answer:
        return True
    a = answer.lower()
    # Jeśli bot już podał tag do "zapytanie", nie liczymy tego jako kolejny nieudany krok
    if "[get_request:" in a:
        return False

    unclear_markers = [
        "podaj proszę model maszyny",
        "podaj proszę model",
        "wybierz **model maszyny**",
        "żeby dobrać część",
        "żeby wypisać listę uszczelek",
        "właściwy kod sku z katalogu",
        "napisz tylko średnicę",
        "dobiorę sam z katalogu",
        "kabel** czy na **mikrorurkę",
        "aby precyzyjnie dobrać część",
        "przepraszam, ale w mojej bazie nie mam przypisanej",
        "nie mam przypisanej tej części",
        "nie znalazłem",
        "nie znaleziono elementu",
        "click the photo of your machine",
        "to quote a spare part",
        "which machine is the product card",
        "write only the diameter",
        "i couldn't find",
        "sorry, this part is not assigned",
    ]
    return any(m in a for m in unclear_markers)


def _machine_for_handoff(req: ChatRequest) -> str:
    tag = resolve_machine_from_query(req.question or "", chip_machine=req.machine)
    if tag:
        from app.rag.machines import machine_display_name
        return machine_display_name(tag).strip().upper()
    if req.machine:
        return req.machine.strip().upper()
    return "ZAPYTANIE"


def _wants_support_contact(question: str) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    return any(p.search(q) for p in _SUPPORT_CONTACT_PATTERNS)


def _append_handoff_button(response: str, req: ChatRequest) -> str:
    if "[GET_REQUEST:" in response:
        return response
    cleaned = re.sub(r"\[GET_QUOTE:\s*.*?\]", "", response, flags=re.IGNORECASE).strip()
    return cleaned + f"\n\n[GET_REQUEST: {_machine_for_handoff(req)}]"


def bind_chat_manager(manager) -> None:
    global chat_manager
    chat_manager = manager


@router.post("/chat")
def handle_chat(request: ChatRequest, req: Request):
    client_ip = req.headers.get(
        "x-forwarded-for",
        req.client.host if req.client else "127.0.0.1",
    ).split(",")[0]
    session_id = request.session_id or "sess_default"
    set_lang(request.lang)

    try:
        response = chat_manager.chat(session_id, request.question, machine=request.machine)

        if _wants_support_contact(request.question or ""):
            _handoff_failures[session_id] = 0
            response = _append_handoff_button(response, request)
        elif _is_unclear_response(response):
            _handoff_failures[session_id] = _handoff_failures.get(session_id, 0) + 1
            if _handoff_failures.get(session_id, 0) >= HANDOFF_FAILURE_THRESHOLD:
                response = _append_handoff_button(response, request)
        else:
            _handoff_failures[session_id] = 0

        log_customer_question(request.question, response, client_ip, session_id)
        return {"answer": response}
    except Exception as e:
        print(f"⚠️ Błąd podczas generowania odpowiedzi chat: {e}")
        err_resp = loc(
            "Przepraszam, wystąpił problem z przetworzeniem pytania. "
            "Wyczyść czat i spróbuj ponownie.",
            "Sorry, there was a problem processing your question. "
            "Clear the chat and try again.",
        )
        log_customer_question(request.question, err_resp, client_ip, session_id)
        return {"answer": err_resp}


@router.post("/reset")
def reset_chat(body: ResetRequest = ResetRequest()):
    session_id = body.session_id or "sess_default"
    try:
        chat_manager.reset(session_id)
        _handoff_failures.pop(session_id, None)
        return {"status": "reset_success", "session_id": session_id}
    except Exception as e:
        return {"status": "error", "message": str(e)}
