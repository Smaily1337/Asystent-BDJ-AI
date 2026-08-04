"""Współdzielone rodziny BOM między maszynami (np. Dual Head ← Extended head)."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from app.rag.machines import FOLDER_TO_TAG, MACHINE_BOM_INHERITS, TAG_TO_DISPLAY

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


def merge_inherited_parts(
    catalog: dict[str, list[PartRow]],
) -> dict[str, list[PartRow]]:
    """
    Dla każdego wpisu MACHINE_BOM_INHERITS dołącz head-family z rodziców
    (dedupe po SKU). Wiersze dziedziczone dostają tag/display dziecka.
    """
    from app.rag.catalog import PartRow  # lokalny import — unika cyklu

    for child_slug, parent_slugs in MACHINE_BOM_INHERITS.items():
        child_tag = tag_for_slug(child_slug)
        if not child_tag:
            continue
        child_rows = list(catalog.get(child_tag, []))
        have = {p.sku.upper() for p in child_rows}
        display = TAG_TO_DISPLAY.get(child_tag, child_tag.upper())

        for parent_slug in parent_slugs:
            parent_tag = tag_for_slug(parent_slug)
            if not parent_tag:
                continue
            for p in catalog.get(parent_tag, []):
                if p.sku.upper() in have:
                    continue
                if not is_head_family_part(p.sku, p.name, p.section):
                    continue
                child_rows.append(
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

        catalog[child_tag] = child_rows

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
