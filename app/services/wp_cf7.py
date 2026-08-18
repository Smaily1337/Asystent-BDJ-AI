"""Przekazanie leada do formularza Contact Form 7 na stronie WordPress (backup)."""

from __future__ import annotations

from typing import List, Optional

import httpx

from app.config import settings


def _format_items(items: Optional[List[List[str]]]) -> str:
    lines: list[str] = []
    for item in items or []:
        if isinstance(item, list):
            lines.append(" | ".join(x for x in item if x))
        elif item:
            lines.append(str(item))
    return "\n".join(lines)


def forward_offer_to_wordpress(
    *,
    company: str,
    email: str,
    phone: str,
    machine: str = "",
    items: Optional[List[List[str]]] = None,
    message: str = "",
    request_type: str = "oferta",
) -> tuple[bool, str]:
    """
    Wysyła dane do CF7 (formularz ofertowy na stronie głównej).
    Działa jako backup gdy Resend/SMTP zawiedzie — wymaga WP_CF7_ENABLED=true.
    """
    if not settings.wp_cf7_enabled:
        return False, "disabled"

    form_id = settings.wp_cf7_form_id
    unit_tag = settings.wp_cf7_unit_tag
    url = f"{settings.wp_site_url.rstrip('/')}/wp-json/contact-form-7/v1/contact-forms/{form_id}/feedback"

    item_text = _format_items(items)
    details = "\n\n".join(
        x
        for x in [
            f"Źródło: Dragon AI chat ({request_type})",
            f"Firma: {company}" if company else "",
            f"Maszyna: {machine}" if machine else "",
            message.strip() if message else "",
            ("Wybrane pozycje:\n" + item_text) if item_text else "",
        ]
        if x
    )

    data = {
        "_wpcf7": str(form_id),
        "_wpcf7_version": settings.wp_cf7_version,
        "_wpcf7_locale": settings.wp_cf7_locale,
        "_wpcf7_unit_tag": unit_tag,
        "your-email": email,
        "your-phone": phone,
        "calc01": machine or company,
        "calc02": details,
        "products-list": item_text or details,
    }

    try:
        response = httpx.post(
            url,
            data=data,
            headers={
                "User-Agent": "DragonAI-Bot/1.0 (+https://bluedragonjet.com)",
                "Referer": settings.wp_site_url.rstrip("/") + "/",
            },
            timeout=20.0,
            follow_redirects=True,
        )
        payload = response.json()
        status = (payload.get("status") or "").lower()
        if status in {"mail_sent", "sent"}:
            return True, status
        return False, payload.get("message") or status or f"HTTP {response.status_code}"
    except Exception as exc:
        return False, str(exc)
