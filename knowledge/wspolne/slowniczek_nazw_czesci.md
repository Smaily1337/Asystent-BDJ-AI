# Słowniczek nazw części — język klienta ↔ nazwa z instrukcji

[SŁOWNICZEK SYNONIMÓW / SŁOWNICTWO KLIENTA]
[KEYWORDS: synonim, inne nazwy, potocznie, gumka, pasek, paski, pas, taśma, tulejka, wstawka, oring, o-ring, zegar, koło, wałek, oponka, tłumik, manometr, rolka, PNE-PAS, MOD-PAS]

Klienci często używają potocznych nazw zamiast oficjalnych z katalogu / instrukcji.
Przy doborze części ZAWSZE mapuj potoczną nazwę na **Nazwę z instrukcji**, a następnie szukaj SKU pod tą oficjalną nazwą w katalogu maszyny.

| Nazwa z instrukcji | Inne nazwy (język klienta) |
| :--- | :--- |
| **Pas** (pas napędowy) | **Pasek, paski, taśma, taśma napędowa, pas czerwony, pas do wdmuchiwarki, pasek napędowy, pasek czerwony, pasek górny, pasek dolny, napęd pasowy** |
| Uszczelka | Gumka, oring, o-ring |
| Tuleja kabla | Tulejka kabla, Wstawka kabla, Prowadzenie kabla |
| Tuleja mikrorurki | Tulejka mikrorurki, Wstawka mikrorurki, Uchwyt mikrorurki |
| Oponka | Gumka jezdna, guma jezdna, gumka na rolkę, gumka na koło (NIE mylić z pasem napędowym!) |
| Tłumik | |
| Manometr | Zegar, wskaźnik ciśnienia, ciśnieniomierz, cinieniomierz |
| Wałek | Wał, Oś, Ośka |
| Rolka | Koło, Kółko (NIE mylić z kołem pasowym MOD-PAS!) |

---

## PAS — pas napędowy (KRYTYCZNE MAPOWANIE)

Gdy klient pyta o **„pasek”**, **„paski”**, **„taśmę”**, **„pas czerwony”** itp. — **ZAWSZE** chodzi o **Pas napędowy** w katalogu/BOM, NIE o uszczelkę, oponkę ani pasek jezdny maszyny.

### Oficjalne nazwy w bazie (szukaj po słowie „Pas” w kolumnie Nazwa):

| Kod SKU | Nazwa w katalogu | Uwagi |
| :--- | :--- | :--- |
| `PNE-PAS-DOL` | **Pas** z nakładką 5mm czerwony z frezem centralnym do PNEUMATIC | Pas dolny / z frezem |
| `PNE-PAS-GOR` | **Pas** z nakładką 5mm czerwony płaski do PNEUMATIC | Pas górny / płaski |
| `MOD-PAS-KOL-PAS-DUZ-13PJ` | Moduł pasowy - Koło pasowe duże 13PJ | Koło pasowe (nie sam pas!) |
| `MOD-PAS-KOL-PAS-MAL-13PJ` | Moduł pasowy - Koło pasowe małe 13PJ | Koło pasowe małe |
| `MOD-PAS-KOL-PAS-SIL-13PJ` | Moduł pasowy - Koło pasowe silników 13PJ | Koło pasowe silnika |
| `MOD-PAS-DYS-KOL-MAL` | Moduł pasowy - Dystans koła małego | Część układu pasowego |
| `MOD-PAS-DYS-KOL-DUZ` | Moduł pasowy - Dystans koła dużego | Część układu pasowego |

**Prefiksy SKU do wyszukiwania:** `PNE-PAS-*` (same pasy), `MOD-PAS-*` (koła i moduły pasowe).

**NIE mylić z:**
- `SRU-PAS-*` — to **śruby pasowane** (ISO 7379), NIE pasek napędowy!
- Uszczelką (gumka, oring)
- Oponką jezdną

### Przykłady mapowania pytań klienta:

| Pytanie klienta | Szukaj w bazie |
| :--- | :--- |
| „potrzebuję pasek do Extended” | `PNE-PAS-DOL`, `PNE-PAS-GOR` |
| „pasek czerwony dolny” | `PNE-PAS-DOL` |
| „pasek górny płaski” | `PNE-PAS-GOR` |
| „koło pasowe małe” | `MOD-PAS-KOL-PAS-MAL-13PJ` |
| „napęd pasowy / moduł pasowy” | `MOD-PAS-*` |

---

## Reguły użycia

1. Gdy klient mówi np. „gumka”, „oring”, „o-ring” → chodzi o **Uszczelkę** (dobierz SKU uszczelki do modelu i wymiaru).
2. **Gdy klient mówi „pasek”, „paski”, „taśma”, „pas czerwony”, „pasek napędowy” → ZAWSZE chodzi o Pas napędowy (`PNE-PAS-DOL` / `PNE-PAS-GOR`). Szukaj w BOM/katalogu po słowie „Pas” i prefiksie `PNE-PAS`.**
3. Gdy klient mówi „tulejka kabla” / „wstawka kabla” / „prowadzenie kabla” → **Tuleja kabla** (wstawka kabla w katalogu).
4. Gdy klient mówi „tulejka mikrorurki” / „wstawka mikrorurki” / „uchwyt mikrorurki” → **Tuleja mikrorurki** (wstawka rurki / mikrorurki).
5. Gdy klient mówi „zegar” / „wskaźnik ciśnienia” → **Manometr**.
6. Gdy klient mówi „koło” / „kółko” (bez „pasowe”) → **Rolka**. Gdy mówi „koło pasowe” → `MOD-PAS-KOL-PAS-*`.
7. Gdy klient mówi „wał” / „oś” / „ośka” → **Wałek**.
8. „Gumka jezdna” / „oponka” / „gumka na rolkę” → **Oponka** — dla BDJ MINI / MINI COUNTER: SKU `MINI-OPONKI-60` (miękka 60 ShA) lub `MINI-OPONKI-80` (twarda 80 ShA). To NIE jest pas napędowy ani uszczelka głowicy.
9. W odpowiedzi dla klienta możesz użyć zarówno nazwy oficjalnej, jak i potocznej, ale w tabeli części podawaj oficjalną nazwę z katalogu + kod SKU.

## Uwaga

Plik będzie uzupełniany o kolejne synonimy. Nie wymyślaj mapowań spoza tej tabeli.
