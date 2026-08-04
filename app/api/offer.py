"""Endpoint ofert / leadów."""

from __future__ import annotations

from fastapi import APIRouter

from app.models import OfferRequest
from app.services.email import send_offer_email
from app.services.logging_store import log_offer

router = APIRouter(tags=["offer"])


@router.post("/offer")
def handle_offer(request: OfferRequest):
    print("\n" + "=" * 50)
    print("📩 NOWE ZAPYTANIE Z CZATBOTA")
    print("=" * 50)
    print(f"🏢 Firma:   {request.company}")
    print(f"📧 Email:   {request.email}")
    print(f"📞 Telefon: {request.phone}")
    print(f"🧾 Typ:     {request.request_type or 'oferta'}")
    if request.machine:
        print(f"🎯 Dotyczy maszyny: {request.machine}")
    if request.message:
        print(f"💬 Wiadomość klienta: {request.message}")
    if request.items:
        print("🔧 Wybrane pozycje z tabeli:")
        for item in request.items:
            print(f"   -> {' | '.join(item) if isinstance(item, list) else item}")
    print("=" * 50 + "\n")

    log_offer(
        company=request.company,
        email=request.email,
        phone=request.phone,
        machine=request.machine or "",
        items=request.items or [],
        request_type=request.request_type or "oferta",
        message=request.message or "",
    )

    email_sent = send_offer_email(
        company=request.company,
        email=request.email,
        phone=request.phone,
        machine=request.machine or "",
        items=request.items or [],
        request_type=request.request_type or "oferta",
        message=request.message or "",
    )
    return {"status": "success", "email_sent": email_sent}
