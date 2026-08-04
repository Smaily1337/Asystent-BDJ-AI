"""Per-session ContextChatEngine — izolacja pamięci między użytkownikami."""

from __future__ import annotations

import threading
from typing import Any

from llama_index.core.chat_engine import ContextChatEngine
from llama_index.core.memory import ChatMemoryBuffer

from app.config import settings
from app.prompts import SYSTEM_PROMPT
from app.rag.machines import machine_display_name, resolve_machine_from_query
from app.rag.part_lookup import (
    is_gasket_list_followup,
    is_parts_intent,
    try_deterministic_lookup,
)
from app.rag.query_rewrite import rewrite_query
from app.rag.sku_validate import sanitize_answer_skus


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

            engine = self._make_engine()
            self._engines[sid] = engine
            self._order.append(sid)
            return engine

    def chat(self, session_id: str, question: str, machine: str | None = None) -> str:
        sid = session_id or "sess_default"
        resolved = resolve_machine_from_query(question, chip_machine=machine)
        q = question
        if resolved:
            display = machine_display_name(resolved)
            if display and display.lower() not in question.lower():
                q = f"Mam maszynę {display}. {question}"
        elif machine and machine.lower() not in question.lower():
            q = f"Mam maszynę {machine}. {question}"

        prior_reason = self._last_part_reason.get(sid)

        # Dobór części: WYŁĄCZNIE katalog — LLM tu nie ma prawa wymyślać SKU
        # + follow-up „wyświetl listę wybiorę sam” po flow uszczelki
        wants_parts = (
            is_parts_intent(q)
            or is_parts_intent(question)
            or is_gasket_list_followup(question, prior_reason)
            or is_gasket_list_followup(q, prior_reason)
        )
        if wants_parts:
            deterministic = try_deterministic_lookup(
                q, chip_machine=machine, prior_reason=prior_reason
            )
            if deterministic is None:
                deterministic = try_deterministic_lookup(
                    question, chip_machine=machine, prior_reason=prior_reason
                )
            if deterministic is not None:
                self._last_part_reason[sid] = deterministic.reason
                return deterministic.answer
            # nie powinno się zdarzyć — is_parts_intent ⇒ lookup zawsze coś zwraca
            return (
                "Podaj proszę model maszyny oraz nazwę / wymiar części "
                "(np. uszczelka mikrorurki 7 mm do Budget Plus)."
            )

        query = rewrite_query(q, chip_machine=machine)
        engine = self.get_engine(sid)
        try:
            raw = str(engine.chat(query))
        except Exception:
            self.reset(sid)
            engine = self.get_engine(sid)
            raw = str(engine.chat(query))
        return sanitize_answer_skus(raw, q, chip_machine=machine)

    def reset(self, session_id: str) -> None:
        sid = session_id or "sess_default"
        with self._lock:
            engine = self._engines.pop(sid, None)
            self._last_part_reason.pop(sid, None)
            if sid in self._order:
                self._order.remove(sid)
            if engine is not None:
                try:
                    engine.reset()
                except Exception:
                    pass
