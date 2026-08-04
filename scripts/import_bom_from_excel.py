#!/usr/bin/env python3
"""Import BOM z plików Excel → knowledge/maszyny/*/bom.md + czesci.md (bez cen)."""

from __future__ import annotations

import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path

import xlrd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "knowledge" / "maszyny"
SRC_COPY = ROOT / "knowledge" / "source_excel"

# (plik w Downloads, slug folderu, tag wyświetlany, aliasy)
MAPPING: list[tuple[str, str, str, list[str]]] = [
    ("BUDGET.XLS", "budget", "BDJ BUDGET", ["BDJ BUDGET", "BUDGET"]),
    ("BUDGET EASY SET.XLS", "budget_easy_set", "BDJ BUDGET EASY SET", ["BDJ BUDGET EASY SET", "BUDGET EASY SET"]),
    ("BUDGET PLUS.XLS", "budget_plus", "BDJ BUDGET PLUS", ["BDJ BUDGET PLUS", "BUDGET PLUS"]),
    (
        "BUDGET PLUS EASY SET.XLS",
        "budget_plus_easy_set",
        "BDJ BUDGET PLUS EASY SET",
        ["BDJ BUDGET PLUS EASY SET", "BUDGET PLUS EASY SET"],
    ),
    ("MINI C PLUS.XLS", "mini_c_plus", "BDJ MINI C PLUS", ["BDJ MINI C PLUS", "MINI C PLUS", "MINIe", "MINI COUNTER"]),
    ("NEXT.XLS", "next", "BDJ NEXT", ["BDJ NEXT", "NEXT", "NEXTA"]),
    ("EXTENDED.XLS", "extended", "BDJ EXTENDED", ["BDJ EXTENDED", "EXTENDED"]),
    ("MAX.XLS", "max", "BDJ MAX", ["BDJ MAX", "MAX"]),
    ("MAX DH.XLS", "max_dual_head", "BDJ MAX DUAL HEAD", ["BDJ MAX DUAL HEAD", "MAX DH", "MAX DUAL HEAD"]),
    ("HYDRO BELT CABLE.XLS", "hydro_chain_cable", "BDJ HYDRO CHAIN CABLE", ["BDJ HYDRO CHAIN CABLE", "HYDRO BELT", "HYDRO CHAIN"]),
    (
        "HYDROCHAIN MULTITUBE.XLS",
        "hydro_chain_multi_tube",
        "BDJ HYDRO CHAIN MULTI TUBE",
        ["BDJ HYDRO CHAIN MULTI TUBE", "HYDROCHAIN MULTITUBE", "MULTI TUBE"],
    ),
]

SECTION_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("Oponki / gumki na rolkę", re.compile(r"opon|gumka na ko[lł]|gumk.*rowk|MINI-OPONKI", re.I)),
    ("Pasy napędowe / koła pasowe", re.compile(r"\bpas\b|PNE-PAS|MOD-PAS|KOL-PAS|PAS-ZEB|PAS-KLI", re.I)),
    ("Uszczelki na kabel", re.compile(r"^UK-|uszczelk.*kabel|na kabel", re.I)),
    ("Uszczelki na rurkę / mikrorurkę", re.compile(r"^UGD|^UM-|uszczelk.*rurk|uszczelk.*mikro|USZ-WST-RUR|na mikrorurk", re.I)),
    ("Uszczelki (inne)", re.compile(r"uszczelk|USZ-|oring|o-ring", re.I)),
    ("Tuleje / wstawki / mocowania głowicy", re.compile(r"tulej|wstawk|TUL-|WST-|mocowan", re.I)),
    ("Głowica — korpusy i elementy", re.compile(r"g[lł]owic|GLO-", re.I)),
    ("Rolki / wałki", re.compile(r"rolk|wa[lł]ek|WAL-|BUD-ROL|BUD-WAL", re.I)),
    ("Łożyska", re.compile(r"[lł]o[zż]ysk|KUL-LOZ", re.I)),
    ("Elektronika / pomiar", re.compile(r"ELE-|pomiar|licznik|brain|elektron", re.I)),
    ("Pneumatyka / szybkozłącza", re.compile(r"PNE-|kr[oó]ciec|szybkoz|zaw[oó]r|manometr", re.I)),
    ("Skrzynka / organizer / akcesoria", re.compile(r"skrzyn|organizer|pianka|prelube|p[lł]yn|za[sś]lepk|n[oó][zż]|obcin", re.I)),
]


def _parse_qty(cell) -> str:
    if isinstance(cell, float):
        return str(int(cell)) if cell == int(cell) else str(cell)
    s = str(cell).replace("\xa0", " ").strip()
    m = re.search(r"(\d+(?:[.,]\d+)?)", s)
    if not m:
        return "1"
    v = m.group(1).replace(",", ".")
    try:
        f = float(v)
        return str(int(f)) if f == int(f) else str(f)
    except ValueError:
        return "1"


def read_excel(path: Path) -> list[tuple[str, str, str]]:
    book = xlrd.open_workbook(str(path))
    sh = book.sheet_by_index(0)
    rows: list[tuple[str, str, str]] = []
    for r in range(1, sh.nrows):
        sku = str(sh.cell_value(r, 1)).strip()
        name = str(sh.cell_value(r, 3)).strip()
        if not sku or sku.lower() in {"kod towaru", "nan"}:
            continue
        if not re.match(r"^[A-Za-z0-9]", sku):
            continue
        # qty: w tych XLS często w kolumnie 7 (nie w nagłówku „Ilość”=8)
        qty_raw = sh.cell_value(r, 7)
        if qty_raw in ("", None) or (isinstance(qty_raw, str) and not re.search(r"\d", qty_raw)):
            qty_raw = sh.cell_value(r, 8)
        qty = _parse_qty(qty_raw)
        name = re.sub(r"\s+", " ", name).strip()
        rows.append((sku, name, qty))
    return rows


def section_for(sku: str, name: str) -> str:
    blob = f"{sku} {name}"
    for title, pat in SECTION_RULES:
        if pat.search(blob):
            return title
    return "Pozostałe części"


def write_bom(path: Path, tag: str, source_name: str, rows: list[tuple[str, str, str]]) -> None:
    lines = [
        f"[MODEL MASZYNY: {tag}]",
        f"[BOM PRODUKCYJNY DLA {tag}]",
        f"[ŹRÓDŁO: {source_name} — import 1:1, bez cen]",
        f"[ZASADA ANTY-HALUCYNACJA: Wolno przepisywać WYŁĄCZNIE wiersze z tej tabeli. Zakaz wymyślania SKU.]",
        "",
        f"# BOM — {tag}",
        "",
        f"Pełna lista pozycji z pliku **{source_name}** ({len(rows)} SKU).",
        "",
        "| Lp | Kod SKU | Nazwa | Ilość |",
        "| :---: | :--- | :--- | :---: |",
    ]
    for i, (sku, name, qty) in enumerate(rows, 1):
        lines.append(f"| {i} | {sku} | {name} | {qty} |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_czesci(
    path: Path,
    tag: str,
    source_name: str,
    aliases: list[str],
    rows: list[tuple[str, str, str]],
) -> None:
    grouped: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for sku, name, qty in rows:
        grouped[section_for(sku, name)].append((sku, name, qty))

    # ustalona kolejność sekcji
    order = [t for t, _ in SECTION_RULES] + ["Pozostałe części"]
    alias_line = " / ".join(aliases)

    lines = [
        f"[MODEL MASZYNY: {tag}]",
        f"[KATALOG CZĘŚCI EKSPLOATACYJNYCH — GŁÓWNE ŹRÓDŁO SKU DLA {tag}]",
        "[ZASADA ANTY-HALUCYNACJA: Wolno przepisywać WYŁĄCZNIE wiersze z poniższych tabel. Zakaz wymyślania SKU.]",
        f"[ALIAZY MODELU: {alias_line}]",
        f"[ŹRÓDŁO DANYCH: {source_name} | pełny BOM: bom.md | BEZ CEN]",
        "",
        f"# Części zamienne — {tag}",
        "",
        f"Ten katalog dotyczy wyłącznie maszyny **{tag}**. Nie mieszaj części z innych modeli.",
        f"Dane zaimportowane 1:1 z **{source_name}** ({len(rows)} pozycji).",
        "",
    ]

    n = 0
    for title in order:
        items = grouped.get(title) or []
        if not items:
            continue
        n += 1
        lines.append(f"## {n}. {title}")
        lines.append(f"[MODEL MASZYNY: {tag}]")
        lines.append("")
        lines.append("| Kod SKU | Nazwa elementu | Ilość w BOM | Model maszyny |")
        lines.append("| :--- | :--- | :---: | :--- |")
        for sku, name, qty in items:
            lines.append(f"| {sku} | {name} | {qty} | {tag} |")
        lines.append("")
        lines.append("---")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def write_dragonair_stub() -> None:
    """Brak Excela — nie zostawiamy starych/wymuszonych SKU."""
    d = OUT / "dragonair"
    d.mkdir(parents=True, exist_ok=True)
    note = (
        "[MODEL MASZYNY: BDJ DRAGONAIR]\n"
        "[BRAK BOM EXCEL — nie generować SKU]\n\n"
        "# BDJ DRAGONAIR\n\n"
        "Brak pliku Excel BOM dla DragonAir w tym imporcie. "
        "Asystent NIE może podawać kodów części dla tej maszyny.\n"
    )
    (d / "bom.md").write_text(note, encoding="utf-8")
    (d / "czesci.md").write_text(note, encoding="utf-8")


# Child slug → parent slug(s): union head-family parts at import time.
# Mirror of app.rag.machines.MACHINE_BOM_INHERITS (Dual Head shares Extended head).
BOM_INHERITS: dict[str, list[str]] = {
    "max_dual_head": ["extended"],
}


def main(downloads: Path) -> None:
    # Import lokalny — skrypt może iść bez pełnego PYTHONPATH app/
    try:
        from app.rag.bom_inherit import merge_excel_rows
    except ImportError:
        sys.path.insert(0, str(ROOT))
        from app.rag.bom_inherit import merge_excel_rows

    if OUT.exists():
        # usuń stare katalogi maszyn — pełny rebuild
        for child in list(OUT.iterdir()):
            if child.is_dir():
                shutil.rmtree(child)

    SRC_COPY.mkdir(parents=True, exist_ok=True)

    # Najpierw wczytaj wszystkie Excelle, potem dziedziczenie, potem zapis
    loaded: dict[str, tuple[str, list[str], list[tuple[str, str, str]], str]] = {}
    for filename, slug, tag, aliases in MAPPING:
        src = downloads / filename
        if not src.exists():
            # fallback: kopia w repo
            src = SRC_COPY / filename
        if not src.exists():
            raise FileNotFoundError(f"Brak pliku: {filename} (Downloads ani {SRC_COPY})")
        dest_xls = SRC_COPY / filename
        if src.resolve() != dest_xls.resolve():
            shutil.copy2(src, dest_xls)

        rows = read_excel(dest_xls if dest_xls.exists() else src)
        if not rows:
            raise RuntimeError(f"Pusty Excel: {filename}")
        loaded[slug] = (tag, aliases, rows, filename)

    total = 0
    for slug, (tag, aliases, rows, filename) in loaded.items():
        parents = BOM_INHERITS.get(slug, [])
        for parent_slug in parents:
            if parent_slug not in loaded:
                print(f"WARN  {slug}: brak rodzica {parent_slug} do dziedziczenia")
                continue
            before = len(rows)
            rows = merge_excel_rows(rows, loaded[parent_slug][2])
            added = len(rows) - before
            if added:
                print(f"INHERIT {slug} ← {parent_slug} head-family +{added} SKU")

        out_dir = OUT / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        source_note = filename
        if parents:
            source_note = f"{filename} ∪ head-family from {', '.join(parents)}"
        write_bom(out_dir / "bom.md", tag, source_note, rows)
        write_czesci(out_dir / "czesci.md", tag, source_note, aliases, rows)
        total += len(rows)
        print(f"OK  {slug:24} {len(rows):4} SKU  ← {source_note}")

    write_dragonair_stub()
    print(f"\nGotowe: {len(MAPPING)} maszyn + stub DragonAir, łącznie {total} pozycji SKU.")
    print(f"Kopie Excel: {SRC_COPY}")
    print(f"Dziedziczenie głowicy: {BOM_INHERITS}")


if __name__ == "__main__":
    dl = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Downloads"
    main(dl)
