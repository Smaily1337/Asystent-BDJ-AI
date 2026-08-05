# Asystent BDJ AI

Chatbot techniczny Blue Dragon Jet / Gamm-Bud — dobór części zamiennych (FastAPI + DeepSeek + BM25).

## Uruchomienie

```bash
pip install -r requirements.txt
cp .env.example api.env   # uzupełnij klucze
python server.py
```

- Widget: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/login
- Health: http://127.0.0.1:8000/health

## Jedna baza wiedzy

```
knowledge/
  maszyny/<model>/
    czesci.md     # katalog części eksploatacyjnych (główne źródło SKU)
    bom.md        # pełny BOM produkcyjny (opcjonalnie)
  wspolne/        # specyfikacje, FAQ, cenniki, słowniczek
  karty_produktow/PL/
  data/           # logi JSON (gitignored)
```

Jedna maszyna = jeden folder. Przy konflikcie wygrywa `czesci.md`.

Stare foldery `baza_wiedzy` / `czesci_nowe` są w `_legacy_knowledge/` (archiwum).

## Zmienne środowiskowe (lokalnie i Render)

Skopiuj `.env.example` → `api.env` lokalnie (`api.env` jest w `.gitignore` i **nigdy** nie trafia na GitHub).

Na Renderze ustaw te same klucze w **Environment** (Dashboard → serwis → Environment):

| Klucz | Wymagany | Opis |
|-------|----------|------|
| `DEEPSEEK_API_KEY` | tak | chat / RAG |
| `RESEND_API_KEY` | tak (Render) | wysyłka maili przez API (działa na Free) |
| `RESEND_FROM` | nie | domyślnie `Dragon AI <onboarding@resend.dev>` |
| `OFFER_RECIPIENTS` | nie | domyślnie `info@gamm-bud.com` |
| `SMTP_LOGIN` | lokalnie | konto SMTP (na Render Free **nie działa**) |
| `SMTP_PASSWORD` | lokalnie | hasło aplikacji Gmail |
| `ADMIN_USER` / `ADMIN_PASSWORD` | zalecane | panel `/admin` |
| `HOST` | na Renderze | `0.0.0.0` (nie `127.0.0.1`) |
| `PORT` | Render ustawia | zwykle zostaw domyślne z platformy |

Bez `RESEND_API_KEY` (produkcja) ani `SMTP_LOGIN` / `SMTP_PASSWORD` (lokalnie) endpoint `POST /offer` zwraca `{"status":"success","email_sent":false}`.

Start na Renderze (przykład): `uvicorn server:app --host 0.0.0.0 --port $PORT`

Health check w Renderze: ustaw ścieżkę **`/health`** (albo `/` — obsługujemy też `HEAD`).

## Testy

```bash
python tests/test_knowledge.py
```

## Struktura kodu

```
app/          # FastAPI, RAG, serwisy
static/       # widget HTML
knowledge/    # baza wiedzy
server.py     # python server.py
```
