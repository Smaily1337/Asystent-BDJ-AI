"""Ładowanie dokumentów Markdown i budowa BM25 + filtr maszyn."""

from __future__ import annotations

from llama_index.core import Document, Settings, SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import QueryBundle
from llama_index.llms.openai_like import OpenAILike
from llama_index.retrievers.bm25 import BM25Retriever

from app.config import Settings as AppSettings, settings
from app.rag.machines import detect_machine_from_query, resolve_machine_from_query, get_machine_tag_from_path
from app.rag.query_rewrite import is_price_query, rewrite_query


def create_llm(cfg: AppSettings | None = None) -> OpenAILike:
    cfg = cfg or settings
    if not cfg.deepseek_api_key:
        print("❌ BŁĄD: Nie znaleziono klucza DEEPSEEK_API_KEY w api.env / .env!")

    llm = OpenAILike(
        model=cfg.deepseek_model,
        api_base=cfg.deepseek_api_base,
        api_key=cfg.deepseek_api_key,
        temperature=cfg.llm_temperature,
        is_chat_model=True,
        context_window=cfg.context_window,
        max_tokens=cfg.max_tokens,
    )
    Settings.llm = llm
    Settings.context_window = cfg.context_window
    Settings.num_output = cfg.max_tokens
    Settings.chunk_size = cfg.chunk_size
    Settings.chunk_overlap = cfg.chunk_overlap
    return llm


def _enrich_document(doc: Document) -> Document:
    full_path = doc.metadata.get("file_path", "")
    prefix = ""
    machine_tag = get_machine_tag_from_path(full_path)
    path_norm = full_path.replace("\\", "/").lower()
    filename = path_norm.rsplit("/", 1)[-1]

    if machine_tag:
        prefix += f"[DOKUMENT DOTYCZY MASZYNY: {machine_tag}]\n"
        if filename == "bom.md" or "/bom.md" in path_norm:
            prefix += (
                f"[BOM PRODUKCYJNY DLA {machine_tag}]\n"
                "[PRIORYTET: Przy doborze części eksploatacyjnych (uszczelki, wstawki, tuleje, paski) "
                "preferuj plik czesci.md tej samej maszyny.]\n"
            )
        elif filename == "czesci.md" or "/czesci.md" in path_norm:
            prefix += f"[KATALOG CZĘŚCI EKSPLOATACYJNYCH — GŁÓWNE ŹRÓDŁO SKU DLA {machine_tag}]\n"
        prefix += "\n"

    if "cenniki" in path_norm:
        prefix += (
            "[DOKUMENT JEST CENNIKIEM - ZAWIERA CENY. WALUTA: WSZYSTKIE CENY W CENNIKU SĄ W EURO (EUR/€)]\n"
            "[KEYWORDS: price, cost, pricing, budget, euro, eur, cennik]\n\n"
        )

    if "/faq/" in path_norm or "pytania_inne" in path_norm:
        prefix += "[SEKCJA FAQ - CZĘSTE PYTANIA I ODPOWIEDZI.]\n\n"

    if "slowniczek" in path_norm:
        prefix += (
            "[SŁOWNICZEK SYNIMÓW NAZW CZĘŚCI — mapuj język klienta na nazwę z instrukcji, "
            "potem dobieraj SKU z katalogu maszyny.]\n"
            "[KEYWORDS: synonim, gumka, pasek, tulejka, wstawka, oring, o-ring, zegar, koło, wałek, oponka]\n\n"
        )

    if "specyfikacje" in path_norm:
        prefix += "[SPECYFIKACJE I PARAMETRY TECHNICZNE MASZYN BDJ.]\n\n"

    # Nie indeksuj README w knowledge/
    if filename == "readme.md":
        return Document(text="", metadata={**doc.metadata, "skip": True})

    return Document(text=prefix + doc.text, metadata=doc.metadata)


def load_documents(cfg: AppSettings | None = None) -> list[Document]:
    cfg = cfg or settings
    dirs = cfg.knowledge_paths()
    print(f"🚀 Ładowanie bazy wiedzy (.md) z: {[str(d) for d in dirs]}...")

    original: list[Document] = []
    for d in dirs:
        docs = SimpleDirectoryReader(
            str(d),
            recursive=True,
            required_exts=[".md", ".MD"],
            exclude=["data/*", "karty_produktow/*", "README.md"],
        ).load_data()
        original.extend(docs)

    documents = []
    for doc in original:
        enriched = _enrich_document(doc)
        if enriched.metadata.get("skip") or not enriched.text.strip():
            continue
        # dodatkowy filtr ścieżek
        fp = enriched.metadata.get("file_path", "").replace("\\", "/").lower()
        if "/data/" in fp or "/karty_produktow/" in fp:
            continue
        documents.append(enriched)

    print(f"✅ Wczytano {len(documents)} dokumentów Markdown.")
    return documents


class MachineFilteringRetriever(BaseRetriever):
    def __init__(self, bm25_retriever: BM25Retriever):
        super().__init__()
        self._bm25_retriever = bm25_retriever

    def _retrieve(self, query_bundle):
        raw = query_bundle.query_str if hasattr(query_bundle, "query_str") else str(query_bundle)
        rewritten = rewrite_query(raw)
        bundle = QueryBundle(query_str=rewritten) if rewritten != raw else query_bundle

        all_nodes = self._bm25_retriever.retrieve(bundle)
        target_machine = resolve_machine_from_query(raw) or resolve_machine_from_query(rewritten)

        # Pytania cenowe: mocniej faworyzuj cenniki + dokumenty bez maszyny
        if is_price_query(raw):
            price_first = [
                n for n in all_nodes
                if "cennik" in n.node.metadata.get("file_path", "").lower()
                or "cenniki" in n.node.metadata.get("file_path", "").lower()
            ]
            if price_first:
                rest = [n for n in all_nodes if n not in price_first]
                all_nodes = price_first + rest

        if not target_machine:
            return all_nodes

        filtered = []
        for n in all_nodes:
            fpath = n.node.metadata.get("file_path", "").lower().replace("\\", "/")
            node_machine = get_machine_tag_from_path(fpath).lower()
            if node_machine:
                if target_machine in node_machine or node_machine in target_machine:
                    filtered.append(n)
            else:
                filtered.append(n)
        return filtered if filtered else all_nodes


def build_retriever(cfg: AppSettings | None = None) -> MachineFilteringRetriever:
    cfg = cfg or settings
    documents = load_documents(cfg)
    nodes = SentenceSplitter(
        chunk_size=cfg.chunk_size,
        chunk_overlap=cfg.chunk_overlap,
    ).get_nodes_from_documents(documents)

    for node in nodes:
        full_path = node.metadata.get("file_path", "").replace("\\", "/")
        machine_tag = get_machine_tag_from_path(full_path)
        if machine_tag:
            header = f"[DOKUMENT DOTYCZY MASZYNY: {machine_tag}]\n"
            if header not in node.text:
                node.text = header + node.text

    base_bm25 = BM25Retriever.from_defaults(nodes=nodes, similarity_top_k=cfg.bm25_top_k)
    return MachineFilteringRetriever(base_bm25)
