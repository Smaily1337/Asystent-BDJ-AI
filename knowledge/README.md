# Baza wiedzy — maszyny BDJ

Katalogi części pochodzą **1:1 z plików Excel BOM** (bez cen), z opcjonalnym dziedziczeniem rodzin głowicy.

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
3. stosuje dziedziczenie głowicy (`BOM_INHERITS`, np. Dual Head ← Extended head-family)
4. zapisuje `bom.md` + `czesci.md` per maszyna
5. kopiuje źródła do `knowledge/source_excel/`

Runtime (`app/rag/catalog.py`) ponownie scala `MACHINE_BOM_INHERITS` przy ładowaniu katalogu.

DragonAir: brak Excela → stub bez SKU (zakaz podawania kodów).

## Dziedziczenie BOM (głowica)

| Dziecko | Rodzic | Co jest mergowane |
|---|---|---|
| `max_dual_head` | `extended` | rodzina głowicy (UM-/UGD/UK-/GLO-/tuleje…) |

Konfiguracja: `MACHINE_BOM_INHERITS` w `app/rag/machines.py` (+ mirror w skrypcie importu).

## Maszyny

| Folder | Źródło Excel |
|---|---|
| budget | BUDGET.XLS |
| budget_easy_set | BUDGET EASY SET.XLS |
| budget_plus | BUDGET PLUS.XLS |
| budget_plus_easy_set | BUDGET PLUS EASY SET.XLS |
| mini_c_plus | MINI C PLUS.XLS |
| next | NEXT.XLS |
| extended | EXTENDED.XLS |
| max | MAX.XLS |
| max_dual_head | MAX DH.XLS ∪ Extended head-family |
| hydro_chain_cable | HYDRO BELT CABLE.XLS |
| hydro_chain_multi_tube | HYDROCHAIN MULTITUBE.XLS |
| dragonair | (brak XLS) |
