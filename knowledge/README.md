# Baza wiedzy BDJ AI (jedna struktura)

```
knowledge/
  maszyny/<model>/
    czesci.md   # katalog części (SKU) — główne źródło dla chatbota, pogrupowane tematycznie
    bom.md      # pełna lista produkcyjna z Excel (źródło prawdy)
  wspolne/      # specyfikacje, FAQ, cenniki, słowniczek
  karty_produktow/PL/  # PDF
  data/         # logi JSON (nie commitować treści klientów)
```

## Maszyny (źródło: Excel Comarch / checklisty)

| Folder | Model | Plik źródłowy |
|---|---|---|
| `budget` | BDJ BUDGET | BUDGET.XLS |
| `budget_easy_set` | BDJ BUDGET EASY SET | BUDGET EASY SET.XLS |
| `budget_plus` | BDJ BUDGET PLUS | BUDGET PLUS.XLS |
| `budget_plus_easy_set` | BDJ BUDGET PLUS EASY SET | BUDGET PLUS EASY SET.XLS |
| `mini_c_plus` | BDJ MINI C PLUS | MINI C PLUS.XLS |
| `next` | BDJ NEXT | NEXT.XLS |
| `extended` | BDJ EXTENDED | EXTENDED.XLS |
| `max` | BDJ MAX | MAX.XLS |
| `max_dual_head` | BDJ MAX DUAL HEAD | MAX DH.XLS |
| `hydro_chain_cable` | BDJ HYDRO CHAIN CABLE | HYDRO BELT CABLE.XLS |
| `hydro_chain_multi_tube` | BDJ HYDRO CHAIN MULTI TUBE | HYDROCHAIN MULTITUBE.XLS |
| `dragonair` | BDJ DRAGONAIR | (bez nowego Excela) |

## Zasady dla AI

1. Jedna maszyna = jeden folder.
2. **czesci.md wygrywa** przy doborze części eksploatacyjnych.
3. Wolno podawać **tylko SKU obecne w tabelach** danej maszyny — bez zmyślania kodów.
4. Ceny z Exceli BOM **nie są** kopiowane do katalogu części (cenniki osobno w `wspolne/cenniki/`).
