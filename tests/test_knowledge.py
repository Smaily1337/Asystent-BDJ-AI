"""Testy regresji: słowniczek, tagowanie maszyn, obecność SKU w knowledge/."""

from __future__ import annotations

from pathlib import Path

from app.rag.machines import detect_machine_from_query, get_machine_tag_from_path
from app.rag.query_rewrite import is_price_query, rewrite_query

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / "knowledge" / "maszyny"


def test_rewrite_gumka_to_uszczelka():
    out = rewrite_query("potrzebuję gumkę 7mm na next")
    assert "uszczelka" in out.lower()
    assert "gumk" in out.lower()


def test_rewrite_pasek():
    out = rewrite_query("ile kosztuje pasek do mini")
    assert "pas" in out.lower()
    assert "PNE-PAS" in out or "pas napędowy" in out.lower()
    assert is_price_query("ile kosztuje pasek do mini")


def test_rewrite_pasek_extended():
    out = rewrite_query("potrzebuję pasek czerwony do extended")
    assert "pas" in out.lower()
    assert "PNE-PAS" in out
    assert "extended" in out.lower() or "BDJ EXTENDED" in out


def test_rewrite_zegar_manometr():
    out = rewrite_query("zegar ciśnienia nie działa")
    assert "manometr" in out.lower()


def test_detect_machines():
    assert detect_machine_from_query("uszczelka do BDJ Nexta") == "bdj next"
    assert detect_machine_from_query("budget plus easy set") == "bdj budget plus easy set"
    assert detect_machine_from_query("budget easy set") == "bdj budget easy set"
    assert detect_machine_from_query("budget plus") == "bdj budget plus"
    assert detect_machine_from_query("bdj budget") == "bdj budget"
    assert detect_machine_from_query("max dual head") == "bdj max dual head"
    assert detect_machine_from_query("hydro chain multi tube") == "bdj hydro chain multi tube"
    assert detect_machine_from_query("mini c plus") == "bdj mini c plus"
    assert detect_machine_from_query("mini counter") == "bdj mini c plus"


def test_resolve_machine_budget_chip_but_extended_in_text():
    from app.rag.machines import resolve_machine_from_query

    q = "Mam maszynę BDJ Budget. mam extended"
    assert resolve_machine_from_query(q, chip_machine="BDJ Budget") == "bdj extended"

    q2 = "Mam maszynę BDJ Budget. chce do bdj extended"
    assert resolve_machine_from_query(q2, chip_machine="BDJ Budget") == "bdj extended"


def test_path_tags_new_structure():
    assert get_machine_tag_from_path(str(KB / "next" / "czesci.md")) == "BDJ NEXT"
    assert get_machine_tag_from_path(str(KB / "budget_easy_set" / "czesci.md")) == "BDJ BUDGET EASY SET"
    assert get_machine_tag_from_path(str(KB / "budget" / "czesci.md")) == "BDJ BUDGET"
    assert get_machine_tag_from_path(str(KB / "budget_plus" / "czesci.md")) == "BDJ BUDGET PLUS"
    assert get_machine_tag_from_path(str(KB / "max_dual_head" / "czesci.md")) == "BDJ MAX DUAL HEAD"
    assert get_machine_tag_from_path(str(KB / "mini_c_plus" / "czesci.md")) == "BDJ MINI C PLUS"


def test_each_machine_has_czesci():
    expected = [
        "budget",
        "budget_easy_set",
        "budget_plus",
        "budget_plus_easy_set",
        "mini_c_plus",
        "next",
        "extended",
        "max",
        "max_dual_head",
        "hydro_chain_cable",
        "hydro_chain_multi_tube",
        "dragonair",
    ]
    for slug in expected:
        path = KB / slug / "czesci.md"
        assert path.exists(), f"Brak {path}"
        assert path.stat().st_size > 50, f"Pusty plik {path}"


def test_critical_skus_present():
    """Kluczowe SKU muszą być w katalogu części (nie tylko w BOM)."""
    checks = {
        "mini_c_plus": ["MINI-OPONKI-60", "GLO-POW-", "UK-D25X5-7"],
        "next": ["PNE-PAS-DOL", "UK-D25X5-"],
        "budget_easy_set": ["BUD-GUM-", "BUD-ROL"],
        "budget": ["BUD-"],
        "max": ["GLO-DUZ-", "PNE-PAS-DOL"],
        "hydro_chain_cable": ["GLO-DUZ-"],
        "extended": ["GLO-POW-", "PNE-PAS-DOL"],
    }
    for slug, needles in checks.items():
        text = (KB / slug / "czesci.md").read_text(encoding="utf-8")
        for needle in needles:
            assert needle in text, f"{slug}/czesci.md nie zawiera {needle}"


def test_mini_has_official_excel_parts():
    text = (KB / "mini_c_plus" / "czesci.md").read_text(encoding="utf-8")
    assert "MINI-OPONKI-60" in text
    assert "GLO-POW-" in text  # Mini C Plus wg Excelu ma głowicę POW


def _belt_skus_from_bom(bom_text: str) -> set[str]:
    """SKU pasów z BOM — muszą być też w czesci.md (główne źródło dla bota)."""
    import re

    patterns = [
        re.compile(r"PNE-PAS-[A-Z0-9]+"),
        re.compile(r"MOD-PAS-[A-Z0-9-]+"),
        re.compile(r"PAS-KLI-[A-Z0-9-]+"),
        re.compile(r"PAS-ZEB-[A-Z0-9-]+"),
        re.compile(r"KOL-PAS-[A-Z0-9-/]+"),
        re.compile(r"MINI-OPONKI-[0-9]+"),
    ]
    skus: set[str] = set()
    for line in bom_text.splitlines():
        if "|" not in line or line.strip().startswith("| :"):
            continue
        for pat in patterns:
            for m in pat.finditer(line):
                skus.add(m.group(0))
    return skus


def test_bom_belt_parts_synced_to_czesci():
    """Regresja: pasy z bom.md muszą być w czesci.md — inaczej bot nie znajdzie „paska”."""
    for slug_dir in sorted(KB.iterdir()):
        if not slug_dir.is_dir():
            continue
        bom_path = slug_dir / "bom.md"
        czesci_path = slug_dir / "czesci.md"
        if not bom_path.exists() or not czesci_path.exists():
            continue
        bom_skus = _belt_skus_from_bom(bom_path.read_text(encoding="utf-8"))
        if not bom_skus:
            continue
        czesci_text = czesci_path.read_text(encoding="utf-8")
        missing = sorted(s for s in bom_skus if s not in czesci_text)
        assert not missing, f"{slug_dir.name}: brak w czesci.md: {missing}"


MAX_DUAL_HEAD_BELT_SKUS = [
    "PNE-PAS-DOL",
    "PNE-PAS-GOR",
]


def test_rewrite_oponki_mini():
    out = rewrite_query("potrzebuję oponki do mini counter")
    assert "oponk" in out.lower() or "MINI-OPONKI" in out
    assert "mini" in out.lower() or "BDJ MINI" in out


def test_mini_bom_exists():
    bom = KB / "mini_c_plus" / "bom.md"
    assert bom.exists(), "Brak bom.md dla mini_c_plus"
    assert bom.read_text(encoding="utf-8").count("| MINI-OPONKI-60 |") >= 1


def test_wants_support_contact():
    from app.api.chat import _wants_support_contact

    assert _wants_support_contact("chcę się skontaktować z supportem")
    assert _wants_support_contact("jak mogę skontaktować się z obsługą?")
    assert _wants_support_contact("proszę o dane kontaktowe")
    assert not _wants_support_contact("potrzebuję uszczelkę 7mm do next")


def test_max_dual_head_has_belt_parts():
    text = (KB / "max_dual_head" / "czesci.md").read_text(encoding="utf-8")
    for sku in MAX_DUAL_HEAD_BELT_SKUS:
        assert sku in text, f"max_dual_head/czesci.md nie zawiera {sku}"


def test_excel_import_row_counts():
    """Szybka kontrola, że katalogi nie są puste po imporcie Excel."""
    expected_min = {
        "budget": 60,
        "budget_easy_set": 70,
        "budget_plus": 60,
        "budget_plus_easy_set": 60,
        "extended": 120,
        "next": 130,
        "max": 100,
        "max_dual_head": 150,
        "mini_c_plus": 100,
        "hydro_chain_cable": 70,
        "hydro_chain_multi_tube": 60,
    }
    for slug, minimum in expected_min.items():
        bom = (KB / slug / "bom.md").read_text(encoding="utf-8")
        data_rows = sum(1 for line in bom.splitlines() if line.startswith("| ") and "Kod SKU" not in line and ":---" not in line)
        assert data_rows >= minimum, f"{slug}: tylko {data_rows} wierszy BOM (oczekiwano >= {minimum})"


if __name__ == "__main__":
    tests = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in tests:
        try:
            fn()
            print(f"OK  {fn.__name__}")
        except Exception as e:
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
    raise SystemExit(1 if failed else 0)
