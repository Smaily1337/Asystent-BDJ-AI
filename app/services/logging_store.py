"""Trwałe logi JSON (pytania klientów + oferty) z prostym lockiem."""

from __future__ import annotations

import datetime
import json
import threading
import uuid
from pathlib import Path
from typing import Any

from app.config import settings
from app.rag.machines import detect_machine_for_log
from app.services.geo import get_country_details

_file_lock = threading.Lock()


def _read_json_list(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def _write_json_list(path: Path, data: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_question_history() -> list[dict[str, Any]]:
    with _file_lock:
        return _read_json_list(settings.questions_log_path)


def log_customer_question(
    question_text: str,
    bot_answer: str,
    client_ip: str = "127.0.0.1",
    session_id: str = "sess_default",
) -> None:
    try:
        q_lower = question_text.lower()
        ans_lower = bot_answer.lower()

        has_contact_info = any(
            term in bot_answer
            for term in [
                "48 91 483 50 11",
                "48 604 474 444",
                "info@bluedragonjet.com",
                "info@gamm-bud.pl",
            ]
        )
        is_success = not (
            "przepraszam, wystąpił problem" in ans_lower or "wystąpił błąd" in ans_lower
        )

        category = "OGÓLNE"
        if any(w in q_lower for w in ["cena", "koszt", "ile kosztuje", "cennik", "euro", "eur"]):
            category = "CENNIK"
        elif any(w in q_lower for w in ["dystrybutor", "zagranic", "niemcy", "czechy", "kupic", "gdzie kupic"]):
            category = "DYSTRYBUCJA"
        elif any(w in q_lower for w in ["szkoleni", "kurs", "certyfikat"]):
            category = "SZKOLENIA"
        elif any(w in q_lower for w in ["uszczelk", "pasek", "tulejk", "wstawk", "część", "sku", "części"]):
            category = "DOBÓR_CZĘŚCI"
        elif any(w in q_lower for w in ["zasięg", "parametr", "rurka", "kabel", "hdpe", "specyfikacj"]):
            category = "PARAMETRY_TECHNICZNE"

        geo_info = get_country_details(client_ip, question_text)
        now_dt = datetime.datetime.now()

        with _file_lock:
            history = _read_json_list(settings.questions_log_path)
            entry = {
                "id": len(history) + 1,
                "session_id": session_id,
                "timestamp": now_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "timestamp_epoch": now_dt.timestamp(),
                "question": question_text,
                "category": category,
                "detected_machine": detect_machine_for_log(question_text),
                "country_code": geo_info["code"],
                "country_name": geo_info["name"],
                "flag": geo_info["flag"],
                "city": geo_info["city"],
                "lat": geo_info["lat"],
                "lon": geo_info["lon"],
                "client_ip": client_ip,
                "has_contact_info": has_contact_info,
                "is_success": is_success,
                "answer_snippet": bot_answer[:300] + ("..." if len(bot_answer) > 300 else ""),
                "full_answer": bot_answer,
            }
            history.append(entry)
            _write_json_list(settings.questions_log_path, history)
    except Exception as e:
        print(f"⚠️ Błąd logowania pytania klienta: {e}")


def log_offer(
    company: str,
    email: str,
    phone: str,
    machine: str = "",
    items: list | None = None,
    request_type: str = "oferta",
    message: str = "",
) -> dict[str, Any]:
    entry = {
        "id": str(uuid.uuid4())[:8],
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "company": company,
        "email": email,
        "phone": phone,
        "machine": machine or "",
        "items": items or [],
        "request_type": request_type,
        "message": (message or "").strip(),
    }
    try:
        with _file_lock:
            history = _read_json_list(settings.offers_log_path)
            history.append(entry)
            _write_json_list(settings.offers_log_path, history)
    except Exception as err_log:
        print(f"⚠️ Błąd zapisu oferty do pliku JSON: {err_log}")
    return entry


def build_analytics_summary(history: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    history = history if history is not None else load_question_history()
    categories: dict[str, int] = {}
    machines: dict[str, int] = {}
    countries: dict[str, int] = {}
    for item in history:
        cat = item.get("category", "OGÓLNE")
        mac = item.get("detected_machine", "BRAK")
        c_name = f"{item.get('flag', '🌐')} {item.get('country_name', 'Nieznany')}"
        categories[cat] = categories.get(cat, 0) + 1
        machines[mac] = machines.get(mac, 0) + 1
        countries[c_name] = countries.get(c_name, 0) + 1
    return {
        "total_questions": len(history),
        "categories": categories,
        "machines": machines,
        "countries": countries,
        "recent_questions": history[-20:],
    }
