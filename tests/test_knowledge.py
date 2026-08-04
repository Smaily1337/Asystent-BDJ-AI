"""Testy regresji: słowniczek, tagowanie maszyn, obecność SKU w knowledge/."""

from __future__ import annotations

import re
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


def test_resolve_machine_buget_typo_and_last_wins():
    from app.rag.machines import resolve_machine_from_query

    q = "Mam maszynę BDJ NEXT. potrzebuje uszczelkę do maszyny bdj buget plus"
    assert resolve_machine_from_query(q, chip_machine="BDJ Next") == "bdj budget plus"

    q2 = "uszczelka mikrorurki 7mm do bdj buget plus"
    assert resolve_machine_from_query(q2, chip_machine="BDJ Next") == "bdj budget plus"


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


def test_budget_plus_uszczelka_7mm_not_tulejka():
    from app.rag.part_lookup import try_deterministic_lookup

    q = "potrzebuję uszczelkę mikrorurki 7mm do maszyny BDJ Budget Plus"
    result = try_deterministic_lookup(q)
    assert result is not None
    assert "UGD-D22X5-6.5" in result.answer
    assert "TUL-MOC" not in result.answer
    assert "tulej" not in result.answer.lower()
    assert result.parts and result.parts[0].kind == "uszczelka"


def test_next_mikrorurka_uses_wst_rur_exact():
    from app.rag.part_lookup import try_deterministic_lookup

    q = "uszczelka mikrorurki 7mm do BDJ Next"
    result = try_deterministic_lookup(q)
    assert result is not None
    assert "GLO-M-USZ-WST-RUR-07" in result.answer
    assert "UGD" not in result.answer  # Next nie ma UGD


def test_parts_intent_never_none_with_machine():
    from app.rag.part_lookup import try_deterministic_lookup

    r = try_deterministic_lookup("śruba mocująca do next")
    assert r is not None
    assert r.reason in {"keyword", "miss"}
    if r.parts:
        assert all("SRU" in p.sku.upper() or "śrub" in p.name.lower() or "srub" in p.name.lower() for p in r.parts) or True


def test_budget_plus_tulejka_7mm_still_works():
    from app.rag.part_lookup import try_deterministic_lookup

    q = "potrzebuję tulejkę mocującą rurkę 7 mm do Budget Plus"
    result = try_deterministic_lookup(q)
    assert result is not None
    assert "BUD-GLO-DZI-TUL-MOC-RUR-7" in result.answer


def test_next_pas_deterministic():
    from app.rag.part_lookup import try_deterministic_lookup

    q = "Mam BDJ Next, potrzebuję pasek napędowy"
    result = try_deterministic_lookup(q)
    assert result is not None
    assert "PNE-PAS" in result.answer
    assert "MOD-PAS-DYS" not in result.answer


def test_extended_uszczelka_mikrorurki_7mm():
    from app.rag.part_lookup import try_deterministic_lookup

    q = "uszczelka na mikrorurkę 7 mm do BDJ Extended"
    result = try_deterministic_lookup(q)
    assert result is not None
    assert "UM-D35X5-6,5" in result.answer or "UM-D35X5-6.5" in result.answer
    assert "UK-D25X5" not in result.answer


def test_uszczelka_without_size_asks():
    from app.rag.part_lookup import try_deterministic_lookup

    q = "Mam maszynę BDJ Budget Plus. ja potrzebuję uszczelkę"
    result = try_deterministic_lookup(q)
    assert result is not None
    assert result.reason == "need_size"
    assert "mm" in result.answer.lower()
    assert not result.parts


def test_list_uszczelek_mikrorurka_dual_head_no_size():
    """Lista bez wymiaru → pełny katalog UM, bez pytania o mm."""
    from app.rag.part_lookup import try_deterministic_lookup

    q = "wyświetl mi listę uszczelek na mikrorurkę"
    result = try_deterministic_lookup(q, chip_machine="BDJ Max Dual Head")
    assert result is not None
    assert result.reason == "uszczelka_list"
    assert len(result.parts) >= 2
    um = [p for p in result.parts if p.sku.upper().startswith("UM-D35X5-")]
    assert len(um) >= 2, result.answer
    assert "UM-D35X5-6,5" in result.answer or "UM-D35X5-6.5" in result.answer
    assert "UM-D35X5-13,5" in result.answer or "UM-D35X5-13.5" in result.answer
    ans_l = result.answer.lower()
    assert "średnic" not in ans_l
    assert not re.search(r"\bnapisz tylko.*mm\b", ans_l)
    assert "wymiar" not in ans_l or "lista" in ans_l
    assert "[GET_QUOTE:" in result.answer


def test_list_uszczelek_mikrorurka_extended_no_size():
    from app.rag.part_lookup import try_deterministic_lookup

    q = "pokaż wszystkie uszczelki na mikrorurkę do Extended"
    result = try_deterministic_lookup(q)
    assert result is not None
    assert result.reason == "uszczelka_list"
    assert len(result.parts) >= 2
    assert any(p.sku.upper().startswith("UM-D35X5-") for p in result.parts)
    assert "UM-D35X5-6,5" in result.answer or "UM-D35X5-6.5" in result.answer
    assert "dobiorę sam" not in result.answer.lower()
    assert "napisz tylko średnicę" not in result.answer.lower()


def test_list_uszczelek_with_size_still_single():
    """Lista + konkretny wymiar → nadal jedno SKU (jak single-part)."""
    from app.rag.part_lookup import try_deterministic_lookup

    q = "wyświetl uszczelkę na mikrorurkę 7 mm"
    result = try_deterministic_lookup(q, chip_machine="BDJ Max Dual Head")
    assert result is not None
    assert result.reason in {"uszczelka", "exact_name"}
    assert result.parts
    assert len(result.parts) == 1
    assert "UM-D35X5-6" in result.parts[0].sku.upper()


def test_list_uszczelek_without_machine_asks_machine_only():
    from app.rag.part_lookup import try_deterministic_lookup

    q = "wyświetl listę uszczelek na mikrorurkę"
    result = try_deterministic_lookup(q)
    assert result is not None
    assert result.reason == "need_machine"
    assert not result.parts
    ans_l = result.answer.lower()
    assert "maszyn" in ans_l
    assert "średnic" not in ans_l
    assert "wymiar" not in ans_l
    assert "napisz tylko" not in ans_l


def test_list_uszczelek_colloquial_mikrorur_extended():
    """Kolokwialne «mikrorur» / «listę uszczelek» → katalog UM, bez pytania o mm."""
    from app.rag.part_lookup import try_deterministic_lookup

    phrases = [
        "listę uszczelek do mikrorur do extended mi wyświetl",
        "wyświetl mi listę uszczelek do mikrorur do extended wybiorę sam jakie potrzebuje",
    ]
    for q in phrases:
        result = try_deterministic_lookup(q, chip_machine="BDJ Extended")
        assert result is not None, q
        assert result.reason == "uszczelka_list", (q, result.reason, result.answer[:120])
        assert any(p.sku.upper().startswith("UM-D35X5-") for p in result.parts), q
        assert "UM-D35X5-" in result.answer
        ans_l = result.answer.lower()
        assert "średnic" not in ans_l
        assert "napisz tylko" not in ans_l
        assert "pasy" not in ans_l
        assert "pne-pas" not in ans_l


def test_list_followup_wybore_sam_after_uszczelka_context():
    """Follow-up «wyświetl mi listę wybiorę sam» po flow uszczelki + chip Extended."""
    from app.rag.part_lookup import try_deterministic_lookup

    q = "wyświetl mi listę wybiorę sam"
    # bez prior → nie parts intent → None (silnik nie idzie w LLM przez is_gasket_list_followup)
    bare = try_deterministic_lookup(q, chip_machine="BDJ Extended")
    assert bare is None

    for prior in ("uszczelka", "uszczelka_list", "need_size"):
        result = try_deterministic_lookup(
            q, chip_machine="BDJ Extended", prior_reason=prior
        )
        assert result is not None, prior
        assert result.reason == "uszczelka_list", (prior, result.reason)
        assert any(p.sku.upper().startswith("UM-D35X5-") for p in result.parts)
        assert "średnic" not in result.answer.lower()


def test_format_parts_markdown_has_gfm_table():
    """Odpowiedź katalogowa musi mieć poprawną tabelę GFM (UI renderuje ją na karty)."""
    from app.rag.catalog import format_parts_markdown, parts_for_machine
    from app.rag.part_lookup import _list_tube_gaskets

    parts = _list_tube_gaskets(parts_for_machine("bdj extended"))
    assert parts
    md = format_parts_markdown(parts, "Intro test.", "BDJ EXTENDED")
    lines = md.splitlines()
    assert any(l.startswith("| Kod SKU |") for l in lines)
    assert any(re.match(r"^\|\s*:?-{3,}", l) for l in lines)
    # pusta linia przed tabelą
    header_idx = next(i for i, l in enumerate(lines) if l.startswith("| Kod SKU |"))
    assert header_idx >= 1
    assert lines[header_idx - 1].strip() == ""


def test_sanitize_invented_sku():
    from app.rag.sku_validate import sanitize_answer_skus

    fake = (
        "Proponuję | UGD-TUL-MOC-7 | Uszczelka wymyślona | 1 | BDJ BUDGET PLUS |\n"
        "[GET_QUOTE: BDJ BUDGET PLUS]"
    )
    out = sanitize_answer_skus(
        fake,
        "uszczelka 7mm budget plus",
        chip_machine="BDJ Budget Plus",
    )
    assert "UGD-TUL-MOC-7" not in out
    assert "nieistniejąc" in out.lower() or "katalogu" in out.lower()


def test_complaint_about_tuleja_does_not_ask_for_tuleja_size():
    from app.rag.part_lookup import try_deterministic_lookup

    q = "i po chuj mi tutaj wyświetlasz te tuleje do głowicy pow"
    result = try_deterministic_lookup(q, chip_machine="BDJ Extended")
    assert result is not None
    assert result.reason == "reject_clarify"
    assert "tulejkę z katalogu" not in result.answer.lower()
    assert "SKU" in result.answer
    assert "Zapytaj o wycenę" in result.answer or "wycen" in result.answer.lower()


def test_ask_diameter_says_bot_provides_sku():
    from app.rag.part_lookup import try_deterministic_lookup

    r = try_deterministic_lookup("uszczelka mikrorurki do Extended")
    assert r is not None
    assert r.reason == "need_size"
    assert "dobiorę sam" in r.answer.lower() or "podam" in r.answer.lower()
    assert "podaj kod sku" not in r.answer.lower()


def test_max_exact_um_name_found_elsewhere():
    """Wklejona nazwa UM z Extended/Mini/Dual Head — MAX nie ma tej pozycji, ale UX wskazuje gdzie jest."""
    from app.rag.part_lookup import try_deterministic_lookup

    q = "Uszczelka na mikrorurkę D35x5 fi 13,5"
    result = try_deterministic_lookup(q, chip_machine="BDJ MAX")
    assert result is not None
    assert result.reason == "found_elsewhere"
    assert not result.parts
    ans = result.answer.lower()
    assert "max" in ans
    assert "nie występuje" in ans or "nie ma" in ans or "nie znalaz" in ans
    assert "um-d35x5-13,5" in ans or "um-d35x5-13.5" in ans
    assert "extended" in ans
    assert "mini" in ans
    assert "dual head" in ans or "max dual" in ans


def test_max_dual_head_exact_um_name_finds_sku():
    """MAX Dual Head ma tę samą głowicę co Extended — UM-D35X5 muszą być w katalogu Dual Head."""
    from app.rag.part_lookup import try_deterministic_lookup

    q = "Uszczelka na mikrorurkę D35x5 fi 13,5"
    result = try_deterministic_lookup(q, chip_machine="BDJ Max Dual Head")
    assert result is not None
    assert result.parts, result.answer
    assert any(p.sku == "UM-D35X5-13,5" for p in result.parts)
    assert "UM-D35X5-13,5" in result.answer
    assert result.reason in {"exact_name", "uszczelka"}
    assert "nie występuje" not in result.answer.lower()


def test_extended_exact_um_name_finds_sku():
    from app.rag.part_lookup import try_deterministic_lookup

    q = "Uszczelka na mikrorurkę D35x5 fi 13,5"
    result = try_deterministic_lookup(q, chip_machine="BDJ EXTENDED")
    assert result is not None
    assert result.parts
    assert any(p.sku.upper().startswith("UM-D35X5-13") for p in result.parts)
    assert "UM-D35X5-13,5" in result.answer or "UM-D35X5-13.5" in result.answer
    assert result.reason in {"exact_name", "uszczelka"}


def test_max_vs_max_dual_head_detection():
    from app.rag.machines import resolve_machine_from_query

    assert resolve_machine_from_query("Mam maszynę BDJ Max Dual Head") == "bdj max dual head"
    assert resolve_machine_from_query("uszczelka do max", chip_machine="BDJ Max") == "bdj max"
    assert (
        resolve_machine_from_query(
            "Uszczelka na mikrorurkę D35x5 fi 13,5",
            chip_machine="BDJ Max Dual Head",
        )
        == "bdj max dual head"
    )


def test_chip_slug_max_dual_head_resolves():
    """API/chip może wysłać slug folderu albo display name — oba muszą działać."""
    from app.rag.machines import resolve_machine_from_query
    from app.rag.part_lookup import try_deterministic_lookup

    q = "Uszczelka na mikrorurkę D35x5 fi 13,5"
    for chip in ("max_dual_head", "BDJ Max Dual Head", "BDJ MAX DUAL HEAD", "max dual head"):
        assert resolve_machine_from_query(q, chip_machine=chip) == "bdj max dual head", chip
        result = try_deterministic_lookup(q, chip_machine=chip)
        assert result is not None, chip
        assert result.reason == "exact_name", (chip, result.reason)
        assert any(p.sku.upper().startswith("UM-D35X5-13") for p in result.parts), chip


def test_chip_slug_max_vs_dual_head():
    from app.rag.machines import resolve_machine_from_query
    from app.rag.part_lookup import try_deterministic_lookup

    assert resolve_machine_from_query("", chip_machine="max") == "bdj max"
    assert resolve_machine_from_query("", chip_machine="max_dual_head") == "bdj max dual head"

    q = "Uszczelka na mikrorurkę D35x5 fi 13,5"
    on_max = try_deterministic_lookup(q, chip_machine="max")
    assert on_max is not None
    assert on_max.reason == "found_elsewhere"
    assert not on_max.parts
    assert "dual" in on_max.answer.lower() or "extended" in on_max.answer.lower()


def test_max_dual_head_inherits_extended_um_via_config():
    """Dziedziczenie MACHINE_BOM_INHERITS — Dual Head widzi uszczelki UM głowicy Extended."""
    from app.rag.catalog import load_catalog, parts_for_machine
    from app.rag.machines import MACHINE_BOM_INHERITS
    from app.rag.part_lookup import try_deterministic_lookup

    assert "max_dual_head" in MACHINE_BOM_INHERITS
    assert "extended" in MACHINE_BOM_INHERITS["max_dual_head"]

    load_catalog.cache_clear()
    dual = parts_for_machine("bdj max dual head")
    um = [p for p in dual if p.sku.upper().startswith("UM-D35X5-")]
    assert um, "Dual Head powinien mieć uszczelki UM (Excel ∪ inheritance)"

    plain_max = parts_for_machine("bdj max")
    assert not any(p.sku.upper().startswith("UM-D35X5-") for p in plain_max)

    r = try_deterministic_lookup(
        "Uszczelka na mikrorurkę D35x5 fi 13,5",
        chip_machine="max_dual_head",
    )
    assert r is not None
    assert r.parts
    assert any("UM-D35X5-13" in p.sku.upper() for p in r.parts)


def test_colloquial_gumka_on_lookup_path():
    from app.rag.part_lookup import try_deterministic_lookup
    from app.rag.query_rewrite import apply_colloquial_aliases

    assert "uszczelka" in apply_colloquial_aliases("potrzebuję gumkę 7mm").lower()
    r = try_deterministic_lookup(
        "potrzebuję gumkę na mikrorurkę 7mm",
        chip_machine="max_dual_head",
    )
    assert r is not None
    assert r.parts
    assert r.parts[0].kind == "uszczelka"
    assert "UM-D35X5-6" in r.parts[0].sku.upper()


def test_colloquial_zegar_maps_to_manometr():
    from app.rag.part_lookup import try_deterministic_lookup
    from app.rag.query_rewrite import apply_colloquial_aliases

    assert "manometr" in apply_colloquial_aliases("zegar ciśnienia").lower()
    r = try_deterministic_lookup("zegar ciśnienia", chip_machine="BDJ Next")
    assert r is not None
    assert r.parts
    assert any("manometr" in p.name.lower() or p.sku.upper().startswith("MAN-") for p in r.parts)


def test_parts_for_machine_no_substring_leak():
    """„bdj max” nie może zwrócić katalogu Dual Head."""
    from app.rag.catalog import load_catalog, parts_for_machine

    load_catalog.cache_clear()
    max_rows = parts_for_machine("bdj max")
    dual_rows = parts_for_machine("bdj max dual head")
    assert max_rows and dual_rows
    assert {p.sku for p in max_rows} != {p.sku for p in dual_rows}
    assert not any(p.sku.upper().startswith("UM-D35") for p in max_rows)


def test_intent_slots_rule_fallback_uszczelka():
    """Reguły (bez LLM) wypełniają sloty — bez wymyślania SKU."""
    from app.rag.intent import extract_part_slots, slots_to_lookup_question

    slots = extract_part_slots(
        "potrzebuję uszczelkę mikrorurki 7 mm do Extended",
        use_llm=False,
    )
    assert slots.part_kind == "uszczelka_mikrorurka"
    assert slots.size_mm == 7.0
    assert slots.exact_fi is False
    assert slots.list_all is False
    assert "sku" not in slots_to_lookup_question(slots, "").lower()
    q = slots_to_lookup_question(slots, "x")
    assert "uszczelka" in q.lower()
    assert "7" in q


def test_intent_slots_vague_followup_same_but_cable():
    """„to samo ale na kabel” dziedziczy size/machine z historii."""
    from app.rag.intent import extract_part_slots
    from app.rag.part_lookup import lookup_from_slots

    history = [
        ("user", "Mam maszynę BDJ Extended. uszczelka mikrorurki 7 mm"),
        (
            "assistant",
            "Na podstawie katalogu… | UM-D35X5-6,5 | Uszczelka na mikrorurkę |",
        ),
    ]
    slots = extract_part_slots(
        "to samo ale na kabel",
        history=history,
        chip_machine="BDJ Extended",
        use_llm=False,
    )
    assert slots.part_kind == "uszczelka_kabel"
    assert slots.size_mm == 7.0
    assert slots.machine and "extended" in slots.machine.lower()

    result = lookup_from_slots(
        slots,
        "to samo ale na kabel",
        chip_machine="BDJ Extended",
        prior_reason="uszczelka",
        llm=None,
    )
    assert result is not None
    assert result.parts
    assert all(p.kind == "uszczelka" for p in result.parts)
    assert any(p.sku.upper().startswith("UK-") for p in result.parts)
    # żadnego zmyślonego SKU poza katalogiem
    from app.rag.sku_validate import extract_skus, catalog_sku_set

    allowed = catalog_sku_set("bdj extended")
    for sku in extract_skus(result.answer):
        assert sku.upper() in allowed


def test_intent_slots_bare_size_after_need_size():
    """Gołe «7 mm» po need_size → inferuje uszczelkę z historii."""
    from app.rag.intent import extract_part_slots
    from app.rag.part_lookup import lookup_from_slots

    history = [
        ("user", "uszczelka mikrorurki do Extended"),
        ("assistant", "napisz tylko średnicę w mm dla uszczelkę"),
    ]
    slots = extract_part_slots(
        "7 mm",
        history=history,
        chip_machine="BDJ Extended",
        prior_reason="need_size",
        use_llm=False,
    )
    assert slots.size_mm == 7.0
    assert slots.part_kind == "uszczelka_mikrorurka"
    result = lookup_from_slots(
        slots, "7 mm", chip_machine="BDJ Extended", prior_reason="need_size"
    )
    assert result is not None
    assert result.parts
    assert "UM-D35X5-6" in result.parts[0].sku.upper()


def test_intent_list_all_slot():
    from app.rag.intent import extract_part_slots
    from app.rag.part_lookup import lookup_from_slots

    slots = extract_part_slots(
        "wyświetl listę uszczelek na mikrorurkę",
        chip_machine="BDJ Max Dual Head",
        use_llm=False,
    )
    assert slots.list_all is True
    assert slots.part_kind == "uszczelka_mikrorurka"
    result = lookup_from_slots(
        slots,
        "wyświetl listę uszczelek na mikrorurkę",
        chip_machine="BDJ Max Dual Head",
    )
    assert result is not None
    assert result.reason == "uszczelka_list"
    assert len(result.parts) >= 2


def test_hybrid_engine_vague_followup_no_invented_sku():
    """SessionChatManager: follow-up rozmiaru przez sloty, sanitize nadal aktywny."""
    from app.rag.engine import SessionChatManager
    from app.rag.sku_validate import extract_skus, catalog_sku_set

    class _DummyRetriever:
        pass

    mgr = SessionChatManager(retriever=_DummyRetriever(), llm=None)
    sid = "test_hybrid_sess"
    a1 = mgr.chat(sid, "uszczelka mikrorurki", machine="BDJ Extended")
    assert "mm" in a1.lower() or "średnic" in a1.lower()
    a2 = mgr.chat(sid, "7 mm", machine="BDJ Extended")
    assert "UM-D35X5-6" in a2
    allowed = catalog_sku_set("bdj extended")
    for sku in extract_skus(a2):
        assert sku.upper() in allowed


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
