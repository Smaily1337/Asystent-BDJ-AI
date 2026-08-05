"""Współdzielone katalogi BOM: dziedziczenie rodziny głowicy + pełny union par Easy Set."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from app.rag.machines import (
    FOLDER_TO_TAG,
    MACHINE_BOM_INHERITS,
    MACHINE_BOM_UNION_PAIRS,
    TAG_TO_DISPLAY,
)

if TYPE_CHECKING:
    from app.rag.catalog import PartRow

# Prefiksy / wzorce części głowicy (uszczelki UM/UGD/UK, korpusy GLO, tuleje głowicy).
_HEAD_SKU_RE = re.compile(
    r"^(UM-|UGD|UK-|GLO-|USZ-WST|BUD-GLO|TUL-|WST-)",
    re.I,
)
_HEAD_SECTION_RE = re.compile(
    r"g[lł]owic|uszczelk|tulej|wstawk",
    re.I,
)


def is_head_family_part(sku: str, name: str = "", section: str = "") -> bool:
    """Czy pozycja należy do rodziny głowicy (do dziedziczenia między maszynami)."""
    if _HEAD_SKU_RE.match((sku or "").strip()):
        return True
    blob = f"{name} {section}"
    return bool(_HEAD_SECTION_RE.search(blob)) and bool(
        re.search(r"uszczelk|tulej|g[lł]owic|wstawk|mikro|kabel", blob, re.I)
    )


def tag_for_slug(slug: str) -> str:
    return FOLDER_TO_TAG.get(slug, "").lower()


def _append_missing_parts(
    child_rows: list[PartRow],
    donor_rows: list[PartRow],
    child_tag: str,
    *,
    head_family_only: bool,
) -> list[PartRow]:
    from app.rag.catalog import PartRow  # lokalny import — unika cyklu

    have = {p.sku.upper() for p in child_rows}
    display = TAG_TO_DISPLAY.get(child_tag, child_tag.upper())
    out = list(child_rows)
    for p in donor_rows:
        if p.sku.upper() in have:
            continue
        if head_family_only and not is_head_family_part(p.sku, p.name, p.section):
            continue
        out.append(
            PartRow(
                sku=p.sku,
                name=p.name,
                qty=p.qty,
                machine=display,
                machine_tag=child_tag,
                section=p.section,
                fi_mm=p.fi_mm,
                kind=p.kind,
            )
        )
        have.add(p.sku.upper())
    return out


def merge_inherited_parts(
    catalog: dict[str, list[PartRow]],
) -> dict[str, list[PartRow]]:
    """
    1) MACHINE_BOM_INHERITS — dołącz head-family z rodziców (dedupe po SKU).
    2) MACHINE_BOM_UNION_PAIRS — pełny union katalogów (Easy Set ≡ baza).
    """
    for child_slug, parent_slugs in MACHINE_BOM_INHERITS.items():
        child_tag = tag_for_slug(child_slug)
        if not child_tag:
            continue
        child_rows = list(catalog.get(child_tag, []))
        for parent_slug in parent_slugs:
            parent_tag = tag_for_slug(parent_slug)
            if not parent_tag:
                continue
            child_rows = _append_missing_parts(
                child_rows,
                catalog.get(parent_tag, []),
                child_tag,
                head_family_only=True,
            )
        catalog[child_tag] = child_rows

    for left_slug, right_slug in MACHINE_BOM_UNION_PAIRS:
        left_tag = tag_for_slug(left_slug)
        right_tag = tag_for_slug(right_slug)
        if not left_tag or not right_tag:
            continue
        left_rows = list(catalog.get(left_tag, []))
        right_rows = list(catalog.get(right_tag, []))
        catalog[left_tag] = _append_missing_parts(
            left_rows, right_rows, left_tag, head_family_only=False
        )
        catalog[right_tag] = _append_missing_parts(
            right_rows, left_rows, right_tag, head_family_only=False
        )

    return catalog


def merge_excel_rows(
    child_rows: list[tuple[str, str, str]],
    parent_rows: list[tuple[str, str, str]],
) -> list[tuple[str, str, str]]:
    """Import-time: child Excel ∪ parent head-family (sku, name, qty)."""
    have = {sku.upper() for sku, _, _ in child_rows}
    out = list(child_rows)
    for sku, name, qty in parent_rows:
        if sku.upper() in have:
            continue
        if not is_head_family_part(sku, name):
            continue
        out.append((sku, name, qty))
        have.add(sku.upper())
    return out


def merge_excel_rows_full(
    a_rows: list[tuple[str, str, str]],
    b_rows: list[tuple[str, str, str]],
) -> list[tuple[str, str, str]]:
    """Import-time: pełny union dwóch BOM (sku, name, qty), dedupe po SKU."""
    have = {sku.upper() for sku, _, _ in a_rows}
    out = list(a_rows)
    for sku, name, qty in b_rows:
        if sku.upper() in have:
            continue
        out.append((sku, name, qty))
        have.add(sku.upper())
    return out
