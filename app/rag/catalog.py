"""Strukturalny katalog części z knowledge/maszyny/*/czesci.md."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.config import ROOT_DIR
from app.rag.bom_inherit import merge_inherited_parts
from app.rag.machines import FOLDER_TO_TAG, TAG_TO_DISPLAY, _chip_to_tag

_ROW_RE = re.compile(
    r"^\|\s*(?P<sku>[A-Z0-9][A-Z0-9\-/\.,]*)\s*\|\s*(?P<name>[^|]+?)\s*\|\s*(?P<qty>[^|]*?)\s*\|\s*(?P<machine>[^|]*?)\s*\|?\s*$"
)
_FI_RE = re.compile(r"(?:fi|ø|⌀)\s*([0-9]+(?:[.,][0-9]+)?)", re.I)
_SIZE_TAIL_RE = re.compile(r"(?:^|[\s\-_/])([0-9]+(?:[.,][0-9]+)?)(?:\s*mm)?\s*$", re.I)
_SKU_SIZE_RE = re.compile(r"(?:-|_)(\d+(?:[.,]\d+)?)(?:\s*$)", re.I)
# Append "(N mm)" after fi diameter. Skip if mm or "(… mm)" already follows the number.
# (?!\d)(?![.,]\d) blocks backtracking that would split "fi 3,5 mm" into "fi 3 …".
_FI_NORMALIZE_RE = re.compile(
    r"(?i)\bfi\s*(\d+(?:[.,]\d+)?)(?!\d)(?![.,]\d)(?!\s*mm\b)(?!\s*\(\s*\d+(?:[.,]\d+)?\s*mm\s*\))"
)


@dataclass(frozen=True)
class PartRow:
    sku: str
    name: str
    qty: str
    machine: str
    machine_tag: str
    section: str
    fi_mm: float | None
    kind: str  # uszczelka | tuleja | pas | oponka | inne


def _parse_mm(raw: str) -> float | None:
    try:
        return float(raw.replace(",", "."))
    except ValueError:
        return None


def _extract_fi(sku: str, name: str) -> float | None:
    for src in (name, sku):
        m = _FI_RE.search(src)
        if m:
            return _parse_mm(m.group(1))
    # UGD-D22X5-6.5 / UK-D25X5-7 / UM-D35X5-6,5
    m = re.search(r"(?:UGD|UM|UK|USZ)[^0-9]*[0-9Xx]+(?:X[0-9]+)?-([0-9]+(?:[.,][0-9]+)?)\b", sku, re.I)
    if m:
        return _parse_mm(m.group(1))
    m = _SKU_SIZE_RE.search(sku)
    if m:
        return _parse_mm(m.group(1))
    m = _SIZE_TAIL_RE.search(name.strip())
    if m:
        return _parse_mm(m.group(1))
    return None


def _classify_kind(sku: str, name: str, section: str) -> str:
    blob = f"{sku} {name} {section}".lower()
    if any(x in blob for x in ("oponka", "oponki", "gumka na koło", "gumka na kolo")):
        return "oponka"
    if re.search(r"\b(pas|pasek)\b", blob) or sku.upper().startswith(("PNE-PAS", "MOD-PAS")):
        if "śrub" in blob or "srub" in blob or sku.upper().startswith("SRU"):
            return "inne"
        return "pas"
    if "uszczel" in blob or sku.upper().startswith(("UGD", "UM-", "UK-", "USZ", "GLO-M-USZ", "GLO-POW-USZ")):
        return "uszczelka"
    if any(x in blob for x in ("tulej", "tuleja", "wstawka", "mocująca", "mocujaca")):
        return "tuleja"
    return "inne"


def _tag_from_folder(slug: str) -> str:
    return FOLDER_TO_TAG.get(slug, "").lower()


def _parse_czesci_file(path: Path, machine_tag: str) -> list[PartRow]:
    rows: list[PartRow] = []
    section = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
            continue
        if not line.startswith("|"):
            continue
        if re.match(r"^\|\s*[-:]+", line) or "Kod SKU" in line:
            continue
        m = _ROW_RE.match(line)
        if not m:
            continue
        sku = m.group("sku").strip()
        name = m.group("name").strip()
        qty = m.group("qty").strip()
        machine = m.group("machine").strip() or TAG_TO_DISPLAY.get(machine_tag, machine_tag)
        rows.append(
            PartRow(
                sku=sku,
                name=name,
                qty=qty,
                machine=machine,
                machine_tag=machine_tag,
                section=section,
                fi_mm=_extract_fi(sku, name),
                kind=_classify_kind(sku, name, section),
            )
        )
    return rows


@lru_cache(maxsize=1)
def load_catalog() -> dict[str, list[PartRow]]:
    """machine_tag (lower) → lista części (+ MACHINE_BOM_INHERITS / UNION_PAIRS)."""
    root = ROOT_DIR / "knowledge" / "maszyny"
    out: dict[str, list[PartRow]] = {}
    if not root.exists():
        return out
    for folder in sorted(root.iterdir()):
        if not folder.is_dir():
            continue
        tag = _tag_from_folder(folder.name)
        if not tag:
            continue
        path = folder / "czesci.md"
        if not path.exists():
            continue
        out[tag] = _parse_czesci_file(path, tag)
    return merge_inherited_parts(out)


def parts_for_machine(machine_tag: str | None) -> list[PartRow]:
    """Tylko katalog wybranej maszyny — bez substring soft-match (max ≠ max dual head)."""
    if not machine_tag:
        return []
    cat = load_catalog()
    key = machine_tag.lower().strip()
    if key in cat:
        return cat[key]
    resolved = _chip_to_tag(machine_tag)
    if resolved and resolved in cat:
        return cat[resolved]
    return []


def normalize_fi_mm_in_name(name: str) -> str:
    """
    Append mm equivalent next to fi diameter in part names (source + display).
    Keeps the original `fi …` token so pastes still substring-match.
    Idempotent: skips when `mm` or `(… mm)` already follows the number.
    """
    if not name:
        return name

    def _repl(m: re.Match[str]) -> str:
        num = m.group(1)
        return f"{m.group(0)} ({num} mm)"

    return _FI_NORMALIZE_RE.sub(_repl, name)


# Alias — safety-net for UI / markdown formatting of any leftover raw names.
format_part_name_display = normalize_fi_mm_in_name


def format_parts_markdown(parts: list[PartRow], intro: str, machine_display: str) -> str:
    lines = [
        intro.strip(),
        "",
        "| Kod SKU | Nazwa elementu | Ilość w BOM | Model maszyny |",
        "| :--- | :--- | :---: | :--- |",
    ]
    for p in parts:
        display_name = format_part_name_display(p.name)
        lines.append(f"| {p.sku} | {display_name} | {p.qty} | {p.machine or machine_display} |")
    lines.append("")
    lines.append(f"[GET_QUOTE: {machine_display}]")
    return "\n".join(lines)
