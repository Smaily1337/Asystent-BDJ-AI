# Baza wiedzy — maszyny BDJ

Katalogi części pochodzą **1:1 z plików Excel BOM** (bez cen), z opcjonalnym dziedziczeniem / unionem.

**Hybryda asystenta:** LLM (lub reguły) myśli o intencji / slotach (`app/rag/intent.py`), katalog o SKU (`part_lookup` / `catalog`). Kodów SKU nigdy nie wymyśla model — tylko wiersze z BOM + `sku_validate`.

## Regeneracja

```bash
python3 scripts/import_bom_from_excel.py ~/Downloads
# albo z kopii w repo:
python3 scripts/import_bom_from_excel.py knowledge/source_excel
```

Skrypt:
1. usuwa stare `knowledge/maszyny/*`
2. czyta XLS z podanego folderu (fallback: `knowledge/source_excel/`)
3. stosuje dziedziczenie głowicy (`BOM_INHERITS`) i pełny union par Easy Set (`BOM_UNION_PAIRS`)
4. zapisuje `bom.md` + `czesci.md` per maszyna
5. kopiuje źródła do `knowledge/source_excel/`

Runtime (`app/rag/catalog.py`) ponownie scala `MACHINE_BOM_INHERITS` + `MACHINE_BOM_UNION_PAIRS` przy ładowaniu katalogu.

DragonAir: brak Excela → stub bez SKU (zakaz podawania kodów).

## Dziedziczenie BOM (głowica)

| Dziecko | Rodzic | Co jest mergowane |
|---|---|---|
| `max_dual_head` | `extended` | rodzina głowicy (UM-/UGD/UK-/GLO-/tuleje…) |

Konfiguracja: `MACHINE_BOM_INHERITS` w `app/rag/machines.py` (+ mirror w skrypcie importu).

## Union BOM (Easy Set ≡ baza)

Easy Set i baza to **te same części** — pełny union obu Exceli (obie chipy widzą ten sam zestaw SKU).

| Para | Źródła |
|---|---|
| `budget` ↔ `budget_easy_set` | BUDGET.XLS ∪ BUDGET EASY SET.XLS |
| `budget_plus` ↔ `budget_plus_easy_set` | BUDGET PLUS.XLS ∪ BUDGET PLUS EASY SET.XLS |

**Uszczelki na kabel (UK-*):** w Excelach są tylko w **BUDGET EASY SET** (`UK-D25X5-*`). Po unionie Budget i Budget Easy Set je widzą. **Budget Plus / Plus Easy Set — brak UK-* w obu Excelach** (tylko UGD + tulejka `BUD-GLO-DZI-TUL-WPR-KAB`); asystent nie wymyśla SKU.

Konfiguracja: `MACHINE_BOM_UNION_PAIRS` w `app/rag/machines.py`.

## Maszyny

| Folder | Źródło Excel |
|---|---|
| budget | BUDGET.XLS ∪ BUDGET EASY SET.XLS |
| budget_easy_set | BUDGET.XLS ∪ BUDGET EASY SET.XLS |
| budget_plus | BUDGET PLUS.XLS ∪ BUDGET PLUS EASY SET.XLS |
| budget_plus_easy_set | BUDGET PLUS.XLS ∪ BUDGET PLUS EASY SET.XLS |
| mini_c_plus | MINI C PLUS.XLS |
| next | NEXT.XLS |
| extended | EXTENDED.XLS |
| max | MAX.XLS |
| max_dual_head | MAX DH.XLS ∪ Extended head-family |
| hydro_chain_cable | HYDRO BELT CABLE.XLS |
| hydro_chain_multi_tube | HYDROCHAIN MULTITUBE.XLS |
| dragonair | (brak XLS) |
