"""Heurystyki geo + opcjonalne ip-api.com."""

from __future__ import annotations

import json
import urllib.request


def get_country_details(ip: str, question_text: str) -> dict:
    q_lower = question_text.lower()
    keyword_map = [
        (["niemc", "germany", "deutschland", "berlin", "monachium"],
         {"code": "DE", "name": "Niemcy", "flag": "🇩🇪", "city": "Niemcy", "lat": 51.1657, "lon": 10.4515}),
        (["włoch", "italy", "italia", "rzym", "mediolan"],
         {"code": "IT", "name": "Włochy", "flag": "🇮🇹", "city": "Włochy", "lat": 41.8719, "lon": 12.5674}),
        (["norweg", "norway", "oslo"],
         {"code": "NO", "name": "Norwegia", "flag": "🇳🇴", "city": "Norwegia", "lat": 60.4720, "lon": 8.4689}),
        (["hiszpan", "spain", "madrid", "espana"],
         {"code": "ES", "name": "Hiszpania", "flag": "🇪🇸", "city": "Hiszpania", "lat": 40.4637, "lon": -3.7492}),
        (["angli", "uk", "britain", "london", "wielka brytania"],
         {"code": "GB", "name": "Wielka Brytania", "flag": "🇬🇧", "city": "Wielka Brytania", "lat": 55.3781, "lon": -3.4360}),
        (["dubai", "uae", "emiraty"],
         {"code": "AE", "name": "ZJE", "flag": "🇦🇪", "city": "Dubaj", "lat": 23.4241, "lon": 53.8478}),
        (["czech", "praga"],
         {"code": "CZ", "name": "Czechy", "flag": "🇨🇿", "city": "Czechy", "lat": 49.8175, "lon": 15.4730}),
        (["finland", "finlandia"],
         {"code": "FI", "name": "Finlandia", "flag": "🇫🇮", "city": "Finlandia", "lat": 61.9241, "lon": 25.7482}),
    ]
    for words, info in keyword_map:
        if any(w in q_lower for w in words):
            return info

    if ip and ip not in ["127.0.0.1", "localhost", "::1"]:
        try:
            url = f"http://ip-api.com/json/{ip}?fields=status,country,countryCode,city,lat,lon"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=2) as resp:
                data = json.loads(resp.read().decode())
                if data.get("status") == "success":
                    cc = data.get("countryCode", "PL")
                    return {
                        "code": cc,
                        "name": data.get("country", "Polska"),
                        "flag": f"🌐 {cc}",
                        "city": data.get("city", "Nieznane"),
                        "lat": data.get("lat", 52.2297),
                        "lon": data.get("lon", 21.0122),
                    }
        except Exception:
            pass

    return {
        "code": "PL",
        "name": "Polska",
        "flag": "🇵🇱",
        "city": "Polska",
        "lat": 52.2297,
        "lon": 21.0122,
    }
