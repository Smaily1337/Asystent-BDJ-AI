"""Wysyłka maili ofertowych przez SMTP."""

from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

from app.config import settings


def send_offer_email(
    company: str,
    email: str,
    phone: str,
    machine: Optional[str] = "",
    items: Optional[List[List[str]]] = None,
    request_type: str = "oferta",
    message: str = "",
) -> bool:
    if not settings.smtp_login or not settings.smtp_password:
        print("⚠️ Brak SMTP_LOGIN / SMTP_PASSWORD — pomijam wysyłkę e-mail.")
        return False

    recipients = list(settings.offer_recipients)
    msg = MIMEMultipart()
    subject_type = "zapytanie" if request_type == "zapytanie" else "zapytanie ofertowe"
    msg["Subject"] = f"Nowe {subject_type} z Bota AI - {company}"
    msg["From"] = settings.smtp_login
    msg["To"] = ", ".join(recipients)

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

    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        print(f"Wysyłanie e-maila przez Gmail SSL (port {settings.smtp_port_ssl})...")
        server = smtplib.SMTP_SSL(settings.smtp_server, settings.smtp_port_ssl, timeout=10)
        server.login(settings.smtp_login, settings.smtp_password)
        server.send_message(msg)
        server.quit()
        print(f"✅ E-mail wysłany na {recipients} przez SSL!")
        return True
    except Exception as e_ssl:
        print(f"⚠️ SSL nie powiódł się ({e_ssl}). Próba TLS {settings.smtp_port_tls}...")
        try:
            server = smtplib.SMTP(settings.smtp_server, settings.smtp_port_tls, timeout=10)
            server.starttls()
            server.login(settings.smtp_login, settings.smtp_password)
            server.send_message(msg)
            server.quit()
            print(f"✅ E-mail wysłany na {recipients} przez TLS!")
            return True
        except Exception as e_tls:
            print(f"❌ Błąd wysyłki e-mail: {e_tls}")
            return False
