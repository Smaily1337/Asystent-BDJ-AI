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
