"""Per-session ContextChatEngine — izolacja pamięci między użytkownikami.

Hybryda części: LLM/reguły myślą o intencji (sloty), katalog o SKU.
Odpowiedzi z częściami zawsze przechodzą przez sanitize_answer_skus.
"""

from __future__ import annotations

import threading
from typing import Any

from llama_index.core.chat_engine import ContextChatEngine
from llama_index.core.memory import ChatMemoryBuffer

from app.config import settings
from app.i18n import ENGLISH_QUERY_PREFIX, get_lang
from app.rag.en_pl_glossary import translate_en_history, translate_en_query_for_lookup
from app.prompts import SYSTEM_PROMPT
from app.rag.intent import extract_part_slots, with_chip_machine
from app.rag.machines import machine_display_name, is_machine_unknown_message, resolve_machine_from_query
from app.rag.part_lookup import (
    is_gasket_list_followup,
    is_parts_intent,
    lookup_from_slots,
    try_deterministic_lookup,
    try_machine_showcase,
    try_product_card,
)
from app.rag.query_rewrite import rewrite_query
from app.rag.sku_validate import sanitize_answer_skus

# Powody sesji uznawane za kontekst części (follow-upy)
_PARTS_REASONS = frozenset({
    "uszczelka",
    "uszczelka_list",
    "need_size",
    "need_machine",
    "need_gasket_context",
    "machine_showcase",
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


class SessionChatManager:
    """Jeden silnik czatu na session_id (z limitem LRU-like przyrostu)."""

    def __init__(
        self,
        retriever: Any,
        llm: Any,
        system_prompt: str = SYSTEM_PROMPT,
        token_limit: int | None = None,
        max_sessions: int = 200,
    ):
        self._retriever = retriever
        self._llm = llm
        self._system_prompt = system_prompt
        self._token_limit = token_limit or settings.memory_token_limit
        self._max_sessions = max_sessions
        self._engines: dict[str, ContextChatEngine] = {}
        self._order: list[str] = []
        self._last_part_reason: dict[str, str] = {}
        self._turns: dict[str, list[tuple[str, str]]] = {}
        self._lock = threading.Lock()

    def _make_engine(self) -> ContextChatEngine:
        memory = ChatMemoryBuffer.from_defaults(token_limit=self._token_limit)
        return ContextChatEngine.from_defaults(
            retriever=self._retriever,
            llm=self._llm,
            memory=memory,
            system_prompt=self._system_prompt,
            context_template="Knowledge base context:\n<context>\n{context_str}\n</context>",
        )

    def get_engine(self, session_id: str) -> ContextChatEngine:
        sid = session_id or "sess_default"
        with self._lock:
            if sid in self._engines:
                if sid in self._order:
                    self._order.remove(sid)
                self._order.append(sid)
                return self._engines[sid]

            while len(self._engines) >= self._max_sessions and self._order:
                oldest = self._order.pop(0)
                self._engines.pop(oldest, None)
                self._turns.pop(oldest, None)

            engine = self._make_engine()
            self._engines[sid] = engine
            self._order.append(sid)
            return engine

    def _recent_history(self, sid: str, n: int = 4) -> list[tuple[str, str]]:
        with self._lock:
            turns = self._turns.get(sid) or []
            return list(turns[-n:])

    def _remember(self, sid: str, role: str, text: str) -> None:
        with self._lock:
            buf = self._turns.setdefault(sid, [])
            buf.append((role, (text or "")[:800]))
            if len(buf) > 12:
                del buf[:-12]

    def chat(self, session_id: str, question: str, machine: str | None = None) -> str:
        sid = session_id or "sess_default"

        lookup_question = translate_en_query_for_lookup(question)

        if is_machine_unknown_message(lookup_question):
            from app.rag.part_lookup import ask_machine_message

            self._last_part_reason[sid] = "need_machine"
            answer = ask_machine_message()
            self._remember(sid, "user", question)
            self._remember(sid, "assistant", answer)
            return answer

        resolved = resolve_machine_from_query(lookup_question, chip_machine=machine)
        q = lookup_question
        if resolved:
            display = machine_display_name(resolved)
            if display and display.lower() not in lookup_question.lower():
                q = f"Mam maszynę {display}. {lookup_question}"
        elif machine and machine.lower() not in lookup_question.lower():
            q = f"Mam maszynę {machine}. {lookup_question}"

        prior_reason = self._last_part_reason.get(sid)
        history = translate_en_history(self._recent_history(sid, n=4))
        # Chip z UI LUB model wykryty w tekście — sloty nie mogą zgubić maszyny
        chip_for_lookup = machine or (
            machine_display_name(resolved) if resolved else None
        )

        product_card = try_product_card(lookup_question, chip_machine=chip_for_lookup)
        if product_card is not None and not (
            is_parts_intent(q)
            or is_gasket_list_followup(lookup_question, prior_reason)
        ):
            self._last_part_reason[sid] = product_card.reason
            answer = sanitize_answer_skus(
                product_card.answer, q, chip_machine=chip_for_lookup
            )
            self._remember(sid, "user", question)
            self._remember(sid, "assistant", answer)
            return answer

        showcase = try_machine_showcase(lookup_question, chip_machine=chip_for_lookup)
        if showcase is not None and not (
            is_parts_intent(q)
            or is_gasket_list_followup(lookup_question, prior_reason)
        ):
            self._last_part_reason[sid] = showcase.reason
            answer = sanitize_answer_skus(
                showcase.answer, q, chip_machine=chip_for_lookup
            )
            self._remember(sid, "user", question)
            self._remember(sid, "assistant", answer)
            return answer

        # (1) Lekka ekstrakcja intencji/slotów — LLM lub reguły; bez SKU
        slots = extract_part_slots(
            lookup_question,
            history=history,
            chip_machine=chip_for_lookup,
            prior_reason=prior_reason,
            llm=self._llm,
            use_llm=True,
        )
        slots = with_chip_machine(slots, chip_for_lookup)

        wants_parts = (
            is_parts_intent(q)
            or is_gasket_list_followup(lookup_question, prior_reason)
            or is_gasket_list_followup(q, prior_reason)
            or slots.is_parts_ish()
            or (prior_reason in _PARTS_REASONS and slots.size_mm is not None)
            or (prior_reason in _PARTS_REASONS and slots.list_all)
        )

        if wants_parts:
            # (2) ZAWSZE resolve SKU tylko przez katalog
            deterministic = lookup_from_slots(
                slots,
                q,
                chip_machine=chip_for_lookup,
                prior_reason=prior_reason,
                llm=self._llm,
                history=history,
            )
            if deterministic is None:
                deterministic = lookup_from_slots(
                    slots,
                    lookup_question,
                    chip_machine=chip_for_lookup,
                    prior_reason=prior_reason,
                    llm=self._llm,
                    history=history,
                )
            if deterministic is None:
                deterministic = try_deterministic_lookup(
                    q,
                    chip_machine=chip_for_lookup,
                    prior_reason=prior_reason,
                    machine_source=lookup_question,
                    history=history,
                )
            if deterministic is not None:
                self._last_part_reason[sid] = deterministic.reason
                # (3) Odpowiedź katalogowa — sanitize na wszelki wypadek
                answer = sanitize_answer_skus(
                    deterministic.answer, q, chip_machine=chip_for_lookup
                )
                self._remember(sid, "user", question)
                self._remember(sid, "assistant", answer)
                return answer
            self._last_part_reason[sid] = "need_clarify"
            from app.rag.part_lookup import ask_machine_message

            fallback = ask_machine_message()
            self._remember(sid, "user", question)
            self._remember(sid, "assistant", fallback)
            return fallback

        query = rewrite_query(q, chip_machine=chip_for_lookup)
        if get_lang() == "en":
            query = ENGLISH_QUERY_PREFIX + query
        engine = self.get_engine(sid)
        try:
            raw = str(engine.chat(query))
        except Exception:
            self.reset(sid)
            engine = self.get_engine(sid)
            raw = str(engine.chat(query))
        answer = sanitize_answer_skus(raw, q, chip_machine=chip_for_lookup)
        self._remember(sid, "user", question)
        self._remember(sid, "assistant", answer)
        return answer

    def reset(self, session_id: str) -> None:
        sid = session_id or "sess_default"
        with self._lock:
            engine = self._engines.pop(sid, None)
            self._last_part_reason.pop(sid, None)
            self._turns.pop(sid, None)
            if sid in self._order:
                self._order.remove(sid)
            if engine is not None:
                try:
                    engine.reset()
                except Exception:
                    pass
