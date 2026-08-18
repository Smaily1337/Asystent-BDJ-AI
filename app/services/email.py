"""Wysyłka maili ofertowych — Resend API (Render) lub SMTP (lokalnie)."""

from __future__ import annotations

import smtplib
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

import httpx

from app.config import settings


@dataclass(frozen=True)
class EmailResult:
    sent: bool
    provider: str
    error: str = ""


def _build_body(
    company: str,
    email: str,
    phone: str,
    machine: Optional[str],
    items: Optional[List[List[str]]],
    request_type: str,
    message: str,
) -> tuple[str, str]:
    subject_type = "zapytanie" if request_type == "zapytanie" else "zapytanie ofertowe"
    subject = f"Nowe {subject_type} z Bota AI - {company}"

    if request_type == "zapytanie":
        body = "Nowe zapytanie (kontakt) z Chatbota BDJ!\n\n"
    else:
        body = "Nowe zapytanie ofertowe z Chatbota BDJ!\n\n"
    body += f"🏢 Firma: {company}\n"
    body += f"📧 E-mail: {email}\n"
    body += f"📞 Telefon: {phone}\n\n"

    if machine:
        if request_type == "zapytanie":
            body += f"🎯 Dotyczy maszyny / tematu: {machine}\n\n"
        else:
            body += f"🎯 Klient prosi o wycenę maszyny / tematu: {machine}\n\n"

    if items:
        body += "🔧 Wybrane części zamienne / akcesoria:\n"
        for item in items:
            line = " | ".join(item) if isinstance(item, list) else str(item)
            body += f"  • {line}\n"
        body += "\n"

    if message and message.strip():
        body += f"💬 Wiadomość od klienta:\n{message.strip()}\n"

    return subject, body


def _send_via_resend(subject: str, body: str, recipients: list[str], reply_to: str) -> EmailResult:
    try:
        payload: dict = {
            "from": settings.resend_from,
            "to": recipients,
            "subject": subject,
            "text": body,
        }
        if reply_to:
            payload["reply_to"] = reply_to
        response = httpx.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.resend_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=15.0,
        )
        if response.status_code in (200, 201):
            print(f"✅ E-mail wysłany przez Resend na {recipients}")
            return EmailResult(sent=True, provider="resend")
        err = response.text[:500]
        print(f"❌ Resend HTTP {response.status_code}: {err}")
        return EmailResult(sent=False, provider="resend", error=err)
    except Exception as e:
        print(f"❌ Błąd wysyłki Resend: {e}")
        return EmailResult(sent=False, provider="resend", error=str(e))


def _send_via_smtp(subject: str, body: str, recipients: list[str], reply_to: str) -> EmailResult:
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_login
    msg["To"] = ", ".join(recipients)
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        print(f"Wysyłanie e-maila przez Gmail SSL (port {settings.smtp_port_ssl})...")
        server = smtplib.SMTP_SSL(settings.smtp_server, settings.smtp_port_ssl, timeout=10)
        server.login(settings.smtp_login, settings.smtp_password)
        server.send_message(msg)
        server.quit()
        print(f"✅ E-mail wysłany na {recipients} przez SSL!")
        return EmailResult(sent=True, provider="smtp")
    except Exception as e_ssl:
        print(f"⚠️ SSL nie powiódł się ({e_ssl}). Próba TLS {settings.smtp_port_tls}...")
        try:
            server = smtplib.SMTP(settings.smtp_server, settings.smtp_port_tls, timeout=10)
            server.starttls()
            server.login(settings.smtp_login, settings.smtp_password)
            server.send_message(msg)
            server.quit()
            print(f"✅ E-mail wysłany na {recipients} przez TLS!")
            return EmailResult(sent=True, provider="smtp")
        except Exception as e_tls:
            print(f"❌ Błąd wysyłki e-mail SMTP: {e_tls}")
            return EmailResult(sent=False, provider="smtp", error=str(e_tls))


def send_offer_email(
    company: str,
    email: str,
    phone: str,
    machine: Optional[str] = "",
    items: Optional[List[List[str]]] = None,
    request_type: str = "oferta",
    message: str = "",
) -> EmailResult:
    recipients = list(settings.offer_recipients)
    subject, body = _build_body(company, email, phone, machine, items, request_type, message)
    reply_to = email.strip() if email else ""

    if settings.resend_api_key:
        result = _send_via_resend(subject, body, recipients, reply_to)
        if result.sent:
            return result
        if settings.smtp_login and settings.smtp_password:
            smtp_result = _send_via_smtp(subject, body, recipients, reply_to)
            if smtp_result.sent:
                return smtp_result
            return EmailResult(
                sent=False,
                provider="resend+smtp",
                error=result.error or smtp_result.error,
            )
        return result

    if settings.smtp_login and settings.smtp_password:
        return _send_via_smtp(subject, body, recipients, reply_to)

    return EmailResult(
        sent=False,
        provider="none",
        error="Brak RESEND_API_KEY ani SMTP_LOGIN / SMTP_PASSWORD",
    )
