"""Linki i zdjęcia maszyn BDJ ze strony bluedragonjet.com — karty w czacie."""

from __future__ import annotations

from dataclasses import dataclass

CATALOG_URL = "https://bluedragonjet.com/c/wdmuchiwarki-pl/"

PDF_BASE = "https://bluedragonjet.com/wp-content/uploads/2026/08/"


# Kanoniczny tag (jak w machines.py) → dane produktu na stronie.
@dataclass(frozen=True)
class MachineWebInfo:
    tag: str
    display: str
    label: str
    url: str
    image: str
    tagline: str
    product_card_url: str = ""


MACHINE_WEB: dict[str, MachineWebInfo] = {
    "bdj mini c plus": MachineWebInfo(
        tag="bdj mini c plus",
        display="BDJ MINI C PLUS",
        label="Mini C Plus",
        url="https://bluedragonjet.com/p/bdj-minie/",
        image="https://bluedragonjet.com/wp-content/uploads/2026/05/IMG_3796-1024x768.png",
        tagline="Kompaktowa wdmuchiwarka — kable 2,5–10 mm, zasięg do 1000 m",
        product_card_url=PDF_BASE + "MINIe.pdf",
    ),
    "bdj next": MachineWebInfo(
        tag="bdj next",
        display="BDJ NEXT",
        label="Next",
        url="https://bluedragonjet.com/p/wdmuchiwarka-bdj-next/",
        image="https://bluedragonjet.com/wp-content/uploads/2025/03/001-scaled.jpg",
        tagline="Wszechstronna wdmuchiwarka — kable 2,5–12 mm, zasięg do 3500 m",
        product_card_url=PDF_BASE + "NEXT.pdf",
    ),
    "bdj budget": MachineWebInfo(
        tag="bdj budget",
        display="BDJ BUDGET",
        label="Budget",
        url="https://bluedragonjet.com/p/wdmuchiwarka-bdj-budget/",
        image="https://bluedragonjet.com/wp-content/uploads/2022/12/Budget-8-scaled.jpg",
        tagline="Mikrowdmuchiwarka FTTH — kable 0,7–6 mm, rurki 7–16 mm",
    ),
    "bdj budget easy set": MachineWebInfo(
        tag="bdj budget easy set",
        display="BDJ BUDGET EASY SET",
        label="Budget Easy Set",
        url="https://bluedragonjet.com/p/bdj-budget-easy-set/",
        image="https://bluedragonjet.com/wp-content/uploads/2022/12/Budget-EasySet-3-scaled.jpg",
        tagline="Budget ze zintegrowanym napędem — kable 0,7–6 mm",
        product_card_url=PDF_BASE + "BUDGET-EASY-SET-2.pdf",
    ),
    "bdj budget plus": MachineWebInfo(
        tag="bdj budget plus",
        display="BDJ BUDGET PLUS",
        label="Budget Plus",
        url="https://bluedragonjet.com/p/wdmuchiwarka-bdj-budget-plus/",
        image="https://bluedragonjet.com/wp-content/uploads/2022/12/Budget-Plus-1-scaled.jpg",
        tagline="Dzielona głowica — kable 0,7–6 mm, rurki 7 i 10 mm",
    ),
    "bdj budget plus easy set": MachineWebInfo(
        tag="bdj budget plus easy set",
        display="BDJ BUDGET PLUS EASY SET",
        label="Budget Plus Easy Set",
        url="https://bluedragonjet.com/p/bdj-budget-plus-easy-set/",
        image="https://bluedragonjet.com/wp-content/uploads/2022/12/Budget-Plus-EasySet-1-scaled.jpg",
        tagline="Budget Plus ze zintegrowanym napędem i dzieloną głowicą",
        product_card_url=PDF_BASE + "BUDGET-PLUS-EASY-SET.pdf",
    ),
    "bdj extended": MachineWebInfo(
        tag="bdj extended",
        display="BDJ EXTENDED",
        label="Extended",
        url="https://bluedragonjet.com/p/wdmuchiwarka-bdj-extended/",
        image="https://bluedragonjet.com/wp-content/uploads/2022/12/Extended-1-scaled.jpg",
        tagline="Mikrokable — kable 2,5–12 mm, rurki 5–18 mm, zasięg do 3000 m",
    ),
    "bdj max": MachineWebInfo(
        tag="bdj max",
        display="BDJ MAX",
        label="Max",
        url="https://bluedragonjet.com/p/wdmuchiwarka-bdj-max/",
        image="https://bluedragonjet.com/wp-content/uploads/2022/12/MAX-1-scaled.jpg",
        tagline="Duże średnice — kable 6–15 mm, rury HDPE 32–50 mm",
        product_card_url=PDF_BASE + "MAX-.pdf",
    ),
    "bdj max dual head": MachineWebInfo(
        tag="bdj max dual head",
        display="BDJ MAX DUAL HEAD",
        label="Max Dual Head",
        url="https://bluedragonjet.com/p/bdj-max-dual-head/",
        image="https://bluedragonjet.com/wp-content/uploads/2023/02/BDJ-Max-Dual-Head-3.jpg",
        tagline="Wymienna głowica — dobór części według zamontowanej głowicy",
        product_card_url=PDF_BASE + "MAX-DUAL-HEAD.pdf",
    ),
    "bdj hydro chain cable": MachineWebInfo(
        tag="bdj hydro chain cable",
        display="BDJ HYDRO CHAIN CABLE",
        label="Hydro Chain Cable",
        url="https://bluedragonjet.com/p/wdmuchiwarka-bdj-hydro-chain/",
        image="https://bluedragonjet.com/wp-content/uploads/2022/12/Hydrochain-1-scaled.jpg",
        tagline="Łańcuchowa do kabli — kable 6–20 mm, silniki hydrauliczne",
        product_card_url=PDF_BASE + "HYDRO-CHAIN-CABLE.pdf",
    ),
    "bdj hydro chain multi tube": MachineWebInfo(
        tag="bdj hydro chain multi tube",
        display="BDJ HYDRO CHAIN MULTI TUBE",
        label="Hydro Multi Tube",
        url="https://bluedragonjet.com/p/bdj-hydro-chain-multi-tube/",
        image="https://bluedragonjet.com/wp-content/uploads/2022/12/BDJ-Hydro-Chain-Multi-Tube-1-scaled.jpg",
        tagline="Pakiety mikrorurek — rury HDPE 32–50 mm, zasięg do 1500 m",
        product_card_url=PDF_BASE + "HYDRO-CHAIN-MULTI-TUBE.pdf",
    ),
    "bdj dragonair": MachineWebInfo(
        tag="bdj dragonair",
        display="BDJ DRAGONAIR",
        label="DragonAir",
        url="https://bluedragonjet.com/p/mobilny-kompresor-dragonair/",
        image="https://bluedragonjet.com/wp-content/uploads/2026/04/IMG_7918899856072071461-1024x768.png",
        tagline="Mobilny kompresor spalinowy do zasilania wdmuchiwarek BDJ",
        product_card_url=PDF_BASE + "Dragon-Air.pdf",
    ),
    "bdj brain v3": MachineWebInfo(
        tag="bdj brain v3",
        display="BDJ BRAIN V3",
        label="Brain V3",
        url=CATALOG_URL,
        image="",
        tagline="Sterownik pomiarowy BDJ — osobny produkt (nie wdmuchiwarka)",
        product_card_url=PDF_BASE + "BRAIN-V3.pdf",
    ),
}

# Kolejność kart „wszystkie modele” w UI (Brain V3 na końcu — bez katalogu części).
MACHINE_CARD_ORDER: tuple[str, ...] = tuple(
    k for k in MACHINE_WEB if k != "bdj brain v3"
) + ("bdj brain v3",)


def machine_web_info(tag: str | None) -> MachineWebInfo | None:
    if not tag:
        return None
    key = tag.lower().strip()
    if key in MACHINE_WEB:
        return MACHINE_WEB[key]
    return None


def machines_for_api() -> dict:
    """JSON dla frontu — bez logiki biznesowej."""
    return {
        "catalog_url": CATALOG_URL,
        "machines": [
            {
                "tag": info.tag,
                "display": info.display,
                "label": info.label,
                "url": info.url,
                "image": info.image,
                "tagline": info.tagline,
                "product_card_url": info.product_card_url,
            }
            for info in (MACHINE_WEB[t] for t in MACHINE_CARD_ORDER)
        ],
    }


def format_machine_card_tag(tag: str | None) -> str:
    if not tag:
        return ""
    info = machine_web_info(tag)
    if not info:
        return ""
    return f"[MACHINE_CARD: {info.tag}]"


def format_machine_cards_tag(tags: list[str] | None = None) -> str:
    """
    Tagi dla UI — parsowane w static/index.html.
    tags=None lub ['all'] → wszystkie modele.
    """
    if not tags or (len(tags) == 1 and tags[0].lower() == "all"):
        slugs = ",".join(MACHINE_CARD_ORDER)
        return f"[MACHINE_CARDS: {slugs}]"
    resolved: list[str] = []
    for t in tags:
        info = machine_web_info(t)
        if info:
            resolved.append(info.tag)
    if not resolved:
        return ""
    return f"[MACHINE_CARDS: {','.join(resolved)}]"


def append_catalog_link(text: str) -> str:
    return (
        f"{text.rstrip()}\n\n"
        f"Pełna oferta wdmuchiwarek: [{CATALOG_URL}]({CATALOG_URL})"
    )
