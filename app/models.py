"""Modele Pydantic — kontrakty API."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = "sess_default"
    machine: Optional[str] = None
    lang: Optional[str] = "pl"


class ResetRequest(BaseModel):
    session_id: Optional[str] = "sess_default"


class OfferRequest(BaseModel):
    company: str
    email: str
    phone: str
    items: List[List[str]] = Field(default_factory=list)
    machine: Optional[str] = ""
    # "oferta" - wycena przygotowana na podstawie wybranych SKU
    # "zapytanie" - klient prosi o kontakt, bo bot nie dobrał jednoznacznie części
    request_type: Optional[str] = "oferta"
    message: Optional[str] = ""
