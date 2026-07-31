from fastapi import FastAPI, Request, Form, Cookie, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from typing import List, Optional

# LlamaIndex imports
from llama_index.core import Settings, SimpleDirectoryReader, Document
from llama_index.llms.openai_like import OpenAILike
from llama_index.core.node_parser import SentenceSplitter
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.chat_engine import ContextChatEngine
from llama_index.core.memory import ChatMemoryBuffer

# ==========================================
# KONFIGURACJA POCZTY GMAIL (GAMMA-BUD)
# ==========================================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_LOGIN = "info@gamm-bud.pl"
SMTP_PASSWORD = "ohikvdeofcpwgmck"
# ==========================================

load_dotenv("api.env")
klucz_deepseek = os.getenv("DEEPSEEK_API_KEY")

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
ACTIVE_SESSIONS = set()

def require_auth(admin_session: str = Cookie(None)):
    if not admin_session or admin_session not in ACTIVE_SESSIONS:
        return False
    return True


if not klucz_deepseek:
    print("❌ BŁĄD: Nie znaleziono klucza DEEPSEEK_API_KEY w pliku api.env!")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

KARTY_DIR = "baza_wiedzy/karty_produktow/PL"
if os.path.exists(KARTY_DIR):
    app.mount("/karty", StaticFiles(directory=KARTY_DIR), name="karty")

import re

llm = OpenAILike(
    model="deepseek-chat",
    api_base="https://api.deepseek.com/v1",
    api_key=klucz_deepseek,
    temperature=0.1,
    is_chat_model=True,
    context_window=32768,
    max_tokens=2048
)

system_prompt = """Jesteś precyzyjnym i nieomylnym asystentem technicznym firmy Blue Dragon Jet. Twoim zadaniem jest wyłącznie dobór części zamiennych, uszczelek oraz podawanie parametrów technicznych wdmuchiwarek na podstawie dostarczonych plików Markdown (.md). Twoje odpowiedzi muszą być w 100% oparte na dokumentach.

ZASTOSUJ SIĘ BEZWZGLĘDNIE DO PONIŻSZYCH ZASAD:

1. KRYTYCZNA ZASADA BEZWZGLĘDNEJ PRAWDOMÓWNOŚCI I ANTY-HALUCYNACJI (ZAKAZ ZMYŚLANIA WIERSZY I SKU)
- Wolno Ci przepisać WYŁĄCZNIE i DOSŁOWNIE istniejące wiersze z tabeli zawartej w kontekście dla wybranej maszyny. ZABRANIA SIĘ tworzenia zmyślonych wierszy, wymyślania części bez SKU lub dopasowywania wymiarów na siłę!
- Jeśli w tabeli dla wybranej maszyny nie ma dokładnie szukanej części, ODPOWIEDZ WYŁĄCZNIE:
"Przepraszam, ale w mojej bazie nie mam przypisanej tej części dla wybranego modelu maszyny." (i wskaż w podsumowaniu, która maszyna z oferty posiada dany wymiar, np. BDJ NEXT dla kabla 16 mm).

2. ZROZUMIENIE SYNONIMÓW I MODELI
- Nazwy: "Mini", "MINIe", "BDJ Mini", "Blue Dragon Jet Mini" oraz "Mini Counter" oznaczają TĘ SAMĄ MASZYNĘ (seria BDJ Mini).
- Nazwy: "Budget", "Budget Plus", "Easy Set", "Nexta", "Max", "Extended", "Hydro Chain" to ZUPEŁNIE INNE maszyny. Nigdy ich nie myl.

3. KRYTYCZNA ZASADA BRAKU MODELU (DOPRECYZOWANIE)
- Jeśli użytkownik podaje wymiar (np. "uszczelka na rurkę 7mm"), ale NIE PODAJE docelowego modelu maszyny, NIE WOLNO Ci wyświetlać tabeli z częściami.
- W takiej sytuacji przerwij dobór i dopytaj: "Aby precyzyjnie dobrać część, podaj proszę model maszyny (np. BDJ Mini, BDJ Nexta, BDJ Budget)."

4. ZASADA DOBORU USZCZELEK NA RURKI (ZASADA 0,5 MM MNIEJSZA)
- Zgodnie ze sztuką technologiczną uszczelki na rurkę (mikrorurkę) muszą mieć wymiar wewnętrzny o 0,5 mm mniejszy niż nominalna średnica zewnętrzna rurki.
- Gdy użytkownik pyta o uszczelkę na rurkę o średnicy X mm (np. rurka 7 mm), ZAWSZE proponuj uszczelkę o wymiarze wewnętrznym (X - 0,5) mm (np. dla rurki 7 mm -> uszczelka 6,5 mm; dla rurki 5 mm -> uszczelka 4,5 mm; dla rurki 10 mm -> uszczelka 9,5 mm).
- Uszczelka MUSI istnieć w tabeli uszczelek na rurki dla wyznaczonej maszyny!

5. PARAMETRY TECHNICZNE I ZASIĘGI WDMUCHIWAREK
Oto oficjalne specyfikacje i ograniczenia maszyn:
- **BDJ BUDGET EASY SET**: Kable 0.7 - 6 mm (uszczelki do 8 mm) | Rurki 7 - 16 mm | Zasięg: do 700 m
- **BDJ BUDGET PLUS EASY SET**: Kable 0.7 - 6 mm | Rurki 7 i 10 mm (głowica dzielona) | Zasięg: do 700 m
- **BDJ MINI / MINIe / MINI COUNTER**: Kable 2.5 - 10 mm | Rurki 7, 10, 12 mm | Zasięg: do 1000 m (wersja Counter posiada licznik)
- **BDJ NEXT / BDJ NEXTA**: Kable 2.5 - 12 mm (uszczelki do 16 mm) | Rurki 7 - 16 mm | Zasięg: do 3500 m
- **BDJ EXTENDED**: Kable 2.5 - 12 mm | Rurki 5 - 18 mm (głowica POW) | Zasięg: do 3000 m
- **BDJ MAX**: Kable 6 - 15 mm | Rury HDPE 32, 40, 50 mm | Zasięg: do 2500 m
- **BDJ MAX DUAL HEAD**: Hybrydowa z wymiennymi głowicami | Kable i rurki od 7 mm do rur 50 mm | Zasięg: do 2500 m
- **BDJ HYDRO CHAIN CABLE**: Kable 6 - 20 mm | Rury HDPE 32, 40, 50 mm | Zasięg: do 2500 m
- **BDJ HYDRO CHAIN MULTI TUBE**: Pakiety mikrorurek (np. 3-5x10 mm) | Rury HDPE 32, 40, 50 mm | Zasięg: do 1500 m

Gdy użytkownik pyta o możliwości, zasięgi lub obsługiwane kable/rurki danej maszyny, odpowiedz precyzyjnie w oparciu o powyższe zestawienie.

6. FORMATOWANIE WYNIKU
- Wynik części przedstaw w czytelnej tabeli Markdown z kolumnami (Kod SKU, Nazwa elementu, Przeznaczenie/Wymiar, Model maszyny). Kod SKU jest WYMAGANY dla każdej części!
- Gdy odpowiadasz na pytania dotyczące części zamiennych lub specyfikacji konkretnego modelu maszyny (np. BDJ NEXT), na samym końcu wiadomości dodaj tag wyceny w formacie: [GET_QUOTE: NAZWA_MASZYNY]. Jeśli pytanie dotyczy danych kontaktowych, firmy, dystrybutorów lub gwarancji, NIE dodawaj tagu [GET_QUOTE: ...].

7. DANE KONTAKTOWE I ESKALACJA DO CZŁOWIEKA
- Jeżeli użytkownik PYTA O DANE KONTAKTOWE, adres, telefon, e-mail, lub chce się skontaktować z działem handlowym / serwisem, ZAWSZE podaj poniższe dane w sformatowanej, czytelnej formie.
- Format odpowiedzi:

---
Skontaktuj się bezpośrednio z naszym zespołem – chętnie pomożemy!

📞 **+48 91 483 50 11**
📞 **+48 604 474 444**
📧 **info@bluedragonjet.com**

---
"""
Settings.llm = llm
Settings.context_window = 32768
Settings.num_output = 2048
Settings.chunk_size = 1000
Settings.chunk_overlap = 150

Baza_Wiedzy_Path = "./baza_wiedzy"
print(f"🚀 Ładowanie bazy wiedzy (.md) z: {Baza_Wiedzy_Path}...")

if not os.path.exists(Baza_Wiedzy_Path):
    os.makedirs(Baza_Wiedzy_Path)

# Wczytujemy WYŁĄCZNIE pliki .md (odrzucamy szum z PDF-ów)
original_documents = SimpleDirectoryReader(
    Baza_Wiedzy_Path, 
    recursive=True, 
    required_exts=[".md"]
).load_data()

documents = []
for doc in original_documents:
    full_path = doc.metadata.get('file_path', '')
    normalized_path = full_path.replace('\\', '/')
    oznaczenie = ""
    
    if 'Wdmuchiwarki/' in normalized_path:
        try:
            machine_name = normalized_path.split('Wdmuchiwarki/')[1].split('/')[0]
            oznaczenie += f"[DOKUMENT DOTYCZY MASZYNY: BDJ {machine_name.upper()}]\n\n"
        except: pass
            
    if 'cenniki' in normalized_path.lower():
        oznaczenie += "[DOKUMENT JEST CENNIKIEM - ZAWIERA CENY. WALUTA: WSZYSTKIE CENY W CENNIKU SĄ W EURO (EUR/€)]\n"
        oznaczenie += "[KEYWORDS: price, cost, pricing, budget, euro, eur, cennik]\n\n"

    if 'pytania_inne' in normalized_path.lower() or 'faq' in normalized_path.lower():
        oznaczenie += "[SEKCJA FAQ - CZĘSTE PYTANIA I ODPOWIEDZI.]\n\n"

    nowy_tekst = oznaczenie + doc.text
    documents.append(Document(text=nowy_tekst, metadata=doc.metadata))

print(f"✅ Wczytano {len(documents)} czystych dokumentów Markdown.")

from llama_index.core.retrievers import BaseRetriever

nodes = SentenceSplitter(chunk_size=1000, chunk_overlap=150).get_nodes_from_documents(documents)
for node in nodes:
    full_path = node.metadata.get('file_path', '').replace('\\', '/')
    if 'Wdmuchiwarki/' in full_path:
        try:
            machine_name = full_path.split('Wdmuchiwarki/')[1].split('/')[0]
            header_prefix = f"[DOKUMENT DOTYCZY MASZYNY: BDJ {machine_name.upper()}]\n"
            if header_prefix not in node.text:
                node.text = header_prefix + node.text
        except: pass

base_bm25 = BM25Retriever.from_defaults(nodes=nodes, similarity_top_k=5)

class MachineFilteringRetriever(BaseRetriever):
    def __init__(self, bm25_retriever):
        super().__init__()
        self._bm25_retriever = bm25_retriever

    def _retrieve(self, query_bundle):
        query_str = query_bundle.query_str if hasattr(query_bundle, 'query_str') else str(query_bundle)
        query_lower = query_str.lower()
        all_nodes = self._bm25_retriever.retrieve(query_bundle)
        
        target_machine = None
        if re.search(r'\b(bdj\s*)?nexta?\b', query_lower):
            target_machine = "next"
        elif re.search(r'\b(bdj\s*)?(mini|minie|counter)\b', query_lower):
            target_machine = "mini counter"
        elif re.search(r'\b(bdj\s*)?budget\s*plus\b', query_lower):
            target_machine = "budget plus easy set"
        elif re.search(r'\b(bdj\s*)?budget\b', query_lower):
            target_machine = "budget easy set"
        elif re.search(r'\b(bdj\s*)?extended\b', query_lower):
            target_machine = "extended"
        elif re.search(r'\bmulti\s*tube\b', query_lower):
            target_machine = "hydro chain multi tube"
        elif re.search(r'\bhydro\s*chain\b', query_lower):
            target_machine = "hydro chain cable"
        elif re.search(r'\b(bdj\s*)?max\b', query_lower):
            target_machine = "max"

        if target_machine:
            filtered = []
            for n in all_nodes:
                fpath = n.node.metadata.get("file_path", "").lower().replace("\\", "/")
                if "wdmuchiwarki/" in fpath:
                    if f"wdmuchiwarki/{target_machine}/" in fpath:
                        filtered.append(n)
                else:
                    filtered.append(n)
            if filtered:
                return filtered

        return all_nodes

retriever = MachineFilteringRetriever(base_bm25)
memory = ChatMemoryBuffer.from_defaults(token_limit=3000)

chat_engine = ContextChatEngine.from_defaults(
    retriever=retriever,
    llm=llm,
    memory=memory,
    system_prompt=system_prompt,
    context_template="Knowledge base context:\n<context>\n{context_str}\n</context>"
)

class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = "sess_default"

class OfferRequest(BaseModel):
    company: str
    email: str
    phone: str
    items: List[List[str]]
    machine: Optional[str] = ""

import json
import datetime
import urllib.request
from pathlib import Path
from fastapi import Request
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse
import io
import csv

LOG_FILE_PATH = Path("baza_wiedzy/historia_pytan_klientow.json")

def get_country_details(ip: str, question_text: str):
    q_lower = question_text.lower()
    if any(w in q_lower for w in ["niemc", "germany", "deutschland", "berlin", "monachium"]):
        return {"code": "DE", "name": "Niemcy", "flag": "🇩🇪", "city": "Niemcy", "lat": 51.1657, "lon": 10.4515}
    elif any(w in q_lower for w in ["włoch", "italy", "italia", "rzym", "mediolan"]):
        return {"code": "IT", "name": "Włochy", "flag": "🇮🇹", "city": "Włochy", "lat": 41.8719, "lon": 12.5674}
    elif any(w in q_lower for w in ["norweg", "norway", "oslo"]):
        return {"code": "NO", "name": "Norwegia", "flag": "🇳🇴", "city": "Norwegia", "lat": 60.4720, "lon": 8.4689}
    elif any(w in q_lower for w in ["hiszpan", "spain", "madrid", "espana"]):
        return {"code": "ES", "name": "Hiszpania", "flag": "🇪🇸", "city": "Hiszpania", "lat": 40.4637, "lon": -3.7492}
    elif any(w in q_lower for w in ["angli", "uk", "britain", "london", "wielka brytania"]):
        return {"code": "GB", "name": "Wielka Brytania", "flag": "🇬🇧", "city": "Wielka Brytania", "lat": 55.3781, "lon": -3.4360}
    elif any(w in q_lower for w in ["dubai", "uae", "emiraty"]):
        return {"code": "AE", "name": "ZJE", "flag": "🇦🇪", "city": "Dubaj", "lat": 23.4241, "lon": 53.8478}
    elif any(w in q_lower for w in ["czech", "praga"]):
        return {"code": "CZ", "name": "Czechy", "flag": "🇨🇿", "city": "Czechy", "lat": 49.8175, "lon": 15.4730}
    elif any(w in q_lower for w in ["finland", "finlandia"]):
        return {"code": "FI", "name": "Finlandia", "flag": "🇫🇮", "city": "Finlandia", "lat": 61.9241, "lon": 25.7482}

    if ip and ip not in ["127.0.0.1", "localhost", "::1"]:
        try:
            url = f"http://ip-api.com/json/{ip}?fields=status,country,countryCode,city,lat,lon"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=2) as resp:
                data = json.loads(resp.read().decode())
                if data.get("status") == "success":
                    cc = data.get("countryCode", "PL")
                    return {
                        "code": cc,
                        "name": data.get("country", "Polska"),
                        "flag": f"🌐 {cc}",
                        "city": data.get("city", "Nieznane"),
                        "lat": data.get("lat", 52.2297),
                        "lon": data.get("lon", 21.0122)
                    }
        except Exception:
            pass

    return {"code": "PL", "name": "Polska", "flag": "🇵🇱", "city": "Polska", "lat": 52.2297, "lon": 21.0122}

def log_customer_question(question_text: str, bot_answer: str, client_ip: str = "127.0.0.1", session_id: str = "sess_default"):
    try:
        LOG_FILE_PATH.parent.mkdir(exist_ok=True)
        history = []
        if LOG_FILE_PATH.exists():
            try:
                with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                history = []

        q_lower = question_text.lower()
        ans_lower = bot_answer.lower()

        # Detekcja czy odpowiedź zawiera dane kontaktowe
        has_contact_info = any(term in bot_answer for term in ["48 91 483 50 11", "48 604 474 444", "info@bluedragonjet.com", "info@gamm-bud.pl"])
        
        # Detekcja czy odpowiedź odniosła sukces
        is_success = not ("przepraszam, wystąpił problem" in ans_lower or "wystąpił błąd" in ans_lower)

        category = "OGÓLNE"
        if any(w in q_lower for w in ["cena", "koszt", "ile kosztuje", "cennik", "euro", "eur"]):
            category = "CENNIK"
        elif any(w in q_lower for w in ["dystrybutor", "zagranic", "niemcy", "czechy", "kupic", "gdzie kupic"]):
            category = "DYSTRYBUCJA"
        elif any(w in q_lower for w in ["szkoleni", "kurs", "certyfikat"]):
            category = "SZKOLENIA"
        elif any(w in q_lower for w in ["uszczelk", "pasek", "tulejk", "wstawk", "część", "sku", "części"]):
            category = "DOBÓR_CZĘŚCI"
        elif any(w in q_lower for w in ["zasięg", "parametr", "rurka", "kabel", "hdpe", "specyfikacj"]):
            category = "PARAMETRY_TECHNICZNE"

        detected_machine = "BRAK"
        if "next" in q_lower: detected_machine = "BDJ NEXT"
        elif "mini" in q_lower or "counter" in q_lower: detected_machine = "BDJ MINI"
        elif "budget plus" in q_lower: detected_machine = "BDJ BUDGET PLUS"
        elif "budget" in q_lower: detected_machine = "BDJ BUDGET"
        elif "extended" in q_lower: detected_machine = "BDJ EXTENDED"
        elif "multi tube" in q_lower: detected_machine = "BDJ HYDRO CHAIN MULTI TUBE"
        elif "hydro chain" in q_lower: detected_machine = "BDJ HYDRO CHAIN CABLE"
        elif "max" in q_lower: detected_machine = "BDJ MAX"

        geo_info = get_country_details(client_ip, question_text)
        now_dt = datetime.datetime.now()

        entry = {
            "id": len(history) + 1,
            "session_id": session_id,
            "timestamp": now_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp_epoch": now_dt.timestamp(),
            "question": question_text,
            "category": category,
            "detected_machine": detected_machine,
            "country_code": geo_info["code"],
            "country_name": geo_info["name"],
            "flag": geo_info["flag"],
            "city": geo_info["city"],
            "lat": geo_info["lat"],
            "lon": geo_info["lon"],
            "client_ip": client_ip,
            "has_contact_info": has_contact_info,
            "is_success": is_success,
            "answer_snippet": bot_answer[:300] + ("..." if len(bot_answer) > 300 else ""),
            "full_answer": bot_answer
        }

        history.append(entry)

        with open(LOG_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    except Exception as e:
        print(f"⚠️ Błąd logowania pytania klienta: {e}")

@app.post("/chat")
def handle_chat(request: ChatRequest, req: Request):
    client_ip = req.headers.get("x-forwarded-for", req.client.host if req.client else "127.0.0.1").split(",")[0]
    session_id = request.session_id or "sess_default"
    try:
        response = str(chat_engine.chat(request.question))
        log_customer_question(request.question, response, client_ip, session_id)
        return {"answer": response}
    except Exception as e:
        print(f"⚠️ Błąd podczas generowania odpowiedzi chat: {e}")
        try:
            memory.reset()
            response = str(chat_engine.chat(request.question))
            log_customer_question(request.question, response, client_ip, session_id)
            return {"answer": response}
        except Exception as ex:
            err_resp = "Przepraszam, wystąpił problem z przetworzeniem pytania. Wyczyść czat i spróbuj ponownie."
            log_customer_question(request.question, err_resp, client_ip, session_id)
            return {"answer": err_resp}

@app.post("/reset")
def reset_chat():
    try:
        memory.reset()
        chat_engine.reset()
        return {"status": "reset_success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/analytics")
def get_analytics():
    if not LOG_FILE_PATH.exists():
        return {"total_questions": 0, "categories": {}, "machines": {}, "countries": {}, "recent_questions": []}
    
    try:
        with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
            history = json.load(f)
        
        categories = {}
        machines = {}
        countries = {}
        for item in history:
            cat = item.get("category", "OGÓLNE")
            mac = item.get("detected_machine", "BRAK")
            c_name = f"{item.get('flag', '🌐')} {item.get('country_name', 'Nieznany')}"
            categories[cat] = categories.get(cat, 0) + 1
            machines[mac] = machines.get(mac, 0) + 1
            countries[c_name] = countries.get(c_name, 0) + 1
            
        return {
            "total_questions": len(history),
            "categories": categories,
            "machines": machines,
            "countries": countries,
            "recent_questions": history[-20:]
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/admin/login", response_class=HTMLResponse)
def login_page(error: str = ""):
    error_msg = f"<div style='color: #ef4444; margin-bottom: 16px; font-weight: 600; text-align: center;'>{error}</div>" if error else ""
    html = f"""<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <title>Logowanie | BDJ Analityka</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }}
        body {{ 
            background: #0b1120; color: #f8fafc; min-height: 100vh; display: flex; align-items: center; justify-content: center;
            background-image: radial-gradient(circle at 15% 50%, rgba(14, 165, 233, 0.05), transparent 25%),
                              radial-gradient(circle at 85% 30%, rgba(99, 102, 241, 0.05), transparent 25%);
        }}
        .login-box {{
            background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(148, 163, 184, 0.1); border-radius: 24px; padding: 40px; width: 100%; max-width: 420px;
            box-shadow: 0 8px 32px -8px rgba(0,0,0,0.5); text-align: center;
            animation: popIn 0.5s cubic-bezier(0.16, 1, 0.3, 1);
        }}
        @keyframes popIn {{ from {{ opacity: 0; transform: translateY(20px) scale(0.95); }} to {{ opacity: 1; transform: translateY(0) scale(1); }} }}
        h1 {{ font-size: 1.7rem; font-weight: 800; margin-bottom: 8px; background: linear-gradient(135deg, #e0f2fe, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        p.subtitle {{ color: #94a3b8; font-size: 0.9rem; margin-bottom: 32px; }}
        .input-group {{ text-align: left; margin-bottom: 20px; }}
        label {{ display: block; color: #cbd5e1; font-weight: 600; font-size: 0.85rem; margin-bottom: 8px; }}
        input {{ 
            width: 100%; padding: 14px 16px; background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255,255,255,0.1); 
            border-radius: 12px; color: #f8fafc; font-size: 0.95rem; outline: none; transition: all 0.2s;
        }}
        input:focus {{ border-color: #38bdf8; background: rgba(15, 23, 42, 0.8); box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.1); }}
        .btn-submit {{
            width: 100%; padding: 14px; border: none; border-radius: 12px; background: #38bdf8; color: #0b1120;
            font-weight: 800; font-size: 1rem; cursor: pointer; transition: all 0.2s; margin-top: 10px;
        }}
        .btn-submit:hover {{ background: #7dd3fc; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(56, 189, 248, 0.3); }}
    </style>
</head>
<body>
    <div class="login-box">
        <div style="display: flex; justify-content: center; margin-bottom: 16px; color: #38bdf8;"><i data-lucide="lock" style="width: 48px; height: 48px;"></i></div>
        <h1>Panel Administracyjny</h1>
        <p class="subtitle">Zaloguj się, aby uzyskać dostęp do analityki</p>
        {error_msg}
        <form method="POST" action="/admin/login">
            <div class="input-group">
                <label>Login (Użytkownik)</label>
                <input type="text" name="username" required autocomplete="username">
            </div>
            <div class="input-group">
                <label>Hasło</label>
                <input type="password" name="password" required autocomplete="current-password">
            </div>
            <button type="submit" class="btn-submit">Zaloguj się</button>
        </form>
    </div>
    <script>lucide.createIcons();</script>
</body>
</html>"""
    return HTMLResponse(content=html)

@app.post("/admin/login")
def login_post(username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USER and password == ADMIN_PASSWORD:
        session_token = str(uuid.uuid4())
        ACTIVE_SESSIONS.add(session_token)
        response = RedirectResponse(url="/admin/pytania", status_code=303)
        response.set_cookie(
            key="admin_session", 
            value=session_token, 
            httponly=True, 
            max_age=86400, # 24h
            samesite="lax"
        )
        return response
    return RedirectResponse(url="/admin/login?error=Nieprawidłowy+login+lub+hasło", status_code=303)

@app.get("/admin/logout")
def logout():
    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie(key="admin_session")
    return response

@app.get("/admin/pytania", response_class=HTMLResponse)
def get_admin_dashboard(admin_session: str = Cookie(None)):
    if not require_auth(admin_session):
        return RedirectResponse(url="/admin/login", status_code=303)

    history = []
    if LOG_FILE_PATH.exists():
        try:
            with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []

    # Agregacja Sesji Klientów
    sessions = {}
    total_contact_count = 0
    total_success_count = 0

    for item in history:
        sid = item.get("session_id", "sess_default")
        if item.get("has_contact_info"): total_contact_count += 1
        if item.get("is_success", True): total_success_count += 1

        if sid not in sessions:
            sessions[sid] = {
                "session_id": sid,
                "country_code": item.get("country_code", "PL"),
                "country_name": item.get("country_name", "Polska"),
                "flag": item.get("flag", "🇵🇱"),
                "city": item.get("city", "Polska"),
                "lat": item.get("lat", 52.2297),
                "lon": item.get("lon", 21.0122),
                "start_time": item.get("timestamp"),
                "start_epoch": item.get("timestamp_epoch", 0),
                "end_epoch": item.get("timestamp_epoch", 0),
                "questions_count": 0,
                "answers_count": 0,
                "contact_count": 0,
                "items": []
            }
        
        s = sessions[sid]
        s["questions_count"] += 1
        s["answers_count"] += 1
        if item.get("has_contact_info"): s["contact_count"] += 1
        t_epoch = item.get("timestamp_epoch", 0)
        if t_epoch > s["end_epoch"]: s["end_epoch"] = t_epoch
        s["items"].append(item)

    # Budowanie HTML tabeli sesji
    session_rows_html = ""
    total_duration_sec = 0

    for sid, s in reversed(list(sessions.items())):
        dur_sec = max(0, int(s["end_epoch"] - s["start_epoch"]))
        total_duration_sec += dur_sec
        if dur_sec < 60:
            dur_str = f"{dur_sec} sek"
        else:
            dur_str = f"{dur_sec // 60} min {dur_sec % 60}s"

        has_contact_badge = '<span class="badge badge-contact-yes">📞 TAK (Podano Kontakt)</span>' if s["contact_count"] > 0 else '<span class="badge badge-contact-no">❌ NIE</span>'
        
        q_list_html = "".join([f"<li><strong>P:</strong> {it.get('question')} <br><span style='color:#64748b;'><strong>O:</strong> {it.get('answer_snippet')}</span></li>" for it in s["items"]])

        session_rows_html += f"""
        <tr>
            <td><strong>{s['session_id']}</strong></td>
            <td style="white-space:nowrap;">{s['start_time']}</td>
            <td><span class="badge badge-country">{s['flag']} {s['country_name']}</span></td>
            <td><strong>{dur_str}</strong></td>
            <td><span class="badge badge-cat">{s['questions_count']} pytań / {s['answers_count']} odp.</span></td>
            <td>{has_contact_badge}</td>
            <td>
                <details>
                    <summary style="cursor:pointer; font-weight:700; color:#2563eb;">Rozwiń przebieg rozmowy ({len(s['items'])})</summary>
                    <ul style="margin-top:8px; padding-left:18px; font-size:0.85rem; line-height:1.5;">
                        {q_list_html}
                    </ul>
                </details>
            </td>
        </tr>
        """

    # Budowanie HTML tabeli pojedynczych zapytań
    query_rows_html = ""
    countries_count = {}
    for item in reversed(history):
        c_flag = item.get('flag', '🇵🇱')
        c_name = item.get('country_name', 'Polska')
        c_str = f"{c_flag} {c_name}"
        countries_count[c_str] = countries_count.get(c_str, 0) + 1
        
        contact_badge = '<span class="badge badge-contact-yes">📞 Dane Kontaktowe</span>' if item.get('has_contact_info') else '<span class="badge badge-contact-no">Brak</span>'

        query_rows_html += f"""
        <tr>
            <td><strong>#{item.get('id', '')}</strong></td>
            <td style="white-space:nowrap;">{item.get('timestamp', '')}</td>
            <td><span class="badge badge-country">{c_flag} {c_name}</span></td>
            <td><span class="badge badge-cat">{item.get('category', 'OGÓLNE')}</span></td>
            <td><span class="badge badge-mac">{item.get('detected_machine', 'BRAK')}</span></td>
            <td>{contact_badge}</td>
            <td><strong>{item.get('question', '')}</strong></td>
            <td style="font-size: 0.85rem; color: #475569;">{item.get('answer_snippet', '')}</td>
        </tr>
        """

    avg_dur_sec = (total_duration_sec // len(sessions)) if len(sessions) > 0 else 0
    avg_dur_str = f"{avg_dur_sec} sek" if avg_dur_sec < 60 else f"{avg_dur_sec // 60}m {avg_dur_sec % 60}s"
    
    conversion_rate = 0
    if len(sessions) > 0:
        sess_with_contact = sum(1 for s in sessions.values() if s["contact_count"] > 0)
        conversion_rate = round((sess_with_contact / len(sessions)) * 100, 1)

    json_history = json.dumps(history, ensure_ascii=False)


    html_content = f"""<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <title>Analityka BDJ AI | Premium Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        :root {{
            --bg-base: #0b1120;
            --bg-card: rgba(30, 41, 59, 0.7);
            --bg-card-hover: rgba(30, 41, 59, 0.9);
            --border-color: rgba(148, 163, 184, 0.1);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent-glow: rgba(56, 189, 248, 0.5);
            --accent-color: #38bdf8;
            --font-family: 'Plus Jakarta Sans', sans-serif;
        }}
        
        * {{ box-sizing: border-box; }}
        body {{ 
            font-family: var(--font-family); background: var(--bg-base); color: var(--text-main); 
            margin: 0; padding: 32px 48px; min-height: 100vh;
            background-image: radial-gradient(circle at 15% 50%, rgba(14, 165, 233, 0.05), transparent 25%),
                              radial-gradient(circle at 85% 30%, rgba(99, 102, 241, 0.05), transparent 25%);
        }}

        @keyframes fadeUp {{
            from {{ opacity: 0; transform: translateY(16px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .header {{ 
            display: flex; justify-content: space-between; align-items: center; 
            margin-bottom: 32px; animation: fadeUp 0.5s ease-out forwards;
        }}
        .header h1 {{ margin: 0; font-size: 1.8rem; font-weight: 800; background: linear-gradient(135deg, #e0f2fe, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: -0.5px; display: flex; align-items: center; gap: 12px; }}
        .header p {{ margin: 6px 0 0 0; color: var(--text-muted); font-size: 0.95rem; }}
        
        .header-actions {{ display: flex; gap: 12px; }}
        .btn-action {{ 
            background: rgba(255,255,255,0.05); color: #e2e8f0; padding: 10px 20px; 
            border-radius: 12px; text-decoration: none; font-weight: 600; font-size: 0.9rem;
            border: 1px solid var(--border-color); transition: all 0.2s ease;
            display: inline-flex; align-items: center; gap: 8px; cursor: pointer;
        }}
        .btn-action:hover {{ background: rgba(255,255,255,0.1); border-color: rgba(255,255,255,0.2); transform: translateY(-1px); }}
        .btn-primary {{ background: rgba(56, 189, 248, 0.1); color: #38bdf8; border-color: rgba(56, 189, 248, 0.3); }}
        .btn-primary:hover {{ background: rgba(56, 189, 248, 0.2); border-color: rgba(56, 189, 248, 0.5); }}

        .stats-grid {{ 
            display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 20px; margin-bottom: 32px; 
        }}
        .stat-card {{ 
            background: var(--bg-card); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--border-color); border-radius: 20px; padding: 24px; 
            text-align: left; box-shadow: 0 4px 24px -8px rgba(0,0,0,0.5);
            animation: fadeUp 0.6s ease-out forwards; opacity: 0;
            display: flex; flex-direction: column;
        }}
        .stat-card-header {{ display: flex; align-items: center; gap: 10px; margin-bottom: 12px; color: var(--text-muted); }}
        
        .stat-card .num {{ font-size: 2.2rem; font-weight: 800; color: var(--text-main); line-height: 1; }}
        .stat-card .label {{ font-size: 0.85rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }}

        .charts-grid {{
            display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 32px;
        }}

        .glass-panel {{ 
            background: var(--bg-card); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--border-color); border-radius: 24px; padding: 28px; 
            box-shadow: 0 8px 32px -8px rgba(0,0,0,0.5); margin-bottom: 32px;
            animation: fadeUp 0.7s ease-out forwards; opacity: 0; 
        }}
        .glass-panel h2 {{ margin-top: 0; margin-bottom: 20px; font-size: 1.25rem; font-weight: 700; color: #e2e8f0; display: flex; align-items: center; gap: 10px; }}
        
        #map {{ height: 420px; width: 100%; border-radius: 16px; z-index: 1; border: 1px solid rgba(255,255,255,0.05); }}
        
        .leaflet-container {{ background: #0f172a; font-family: var(--font-family); }}
        .leaflet-popup-content-wrapper {{ background: #1e293b; color: #f8fafc; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 10px 25px -5px rgba(0,0,0,0.5); }}
        .leaflet-popup-tip {{ background: #1e293b; }}
        .leaflet-popup-content {{ margin: 16px; }}

        table {{ width: 100%; border-collapse: separate; border-spacing: 0; font-size: 0.9rem; }}
        th, td {{ padding: 16px 20px; text-align: left; border-bottom: 1px solid var(--border-color); }}
        th {{ color: var(--text-muted); font-weight: 600; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.8px; padding-top: 8px; }}
        tbody tr {{ transition: background 0.2s; }}
        tbody tr:hover {{ background: rgba(255,255,255,0.03); }}
        tbody tr:last-child td {{ border-bottom: none; }}
        
        .badge {{ padding: 6px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; display: inline-flex; align-items: center; gap: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border: 1px solid rgba(255,255,255,0.05); }}
        .badge-cat {{ background: rgba(59, 130, 246, 0.15); color: #93c5fd; }}
        .badge-mac {{ background: rgba(245, 158, 11, 0.15); color: #fcd34d; }}
        .badge-country {{ background: rgba(139, 92, 246, 0.15); color: #c4b5fd; }}
        .badge-contact-yes {{ background: rgba(16, 185, 129, 0.15); color: #6ee7b7; border-color: rgba(16, 185, 129, 0.3); }}
        .badge-contact-no {{ background: rgba(100, 116, 139, 0.15); color: #94a3b8; }}

        details summary {{ cursor: pointer; color: var(--accent-color); font-weight: 600; transition: color 0.2s; outline: none; }}
        details summary:hover {{ color: #7dd3fc; }}
        details ul {{ margin-top: 12px; padding-left: 20px; color: #cbd5e1; font-size: 0.85rem; line-height: 1.6; background: rgba(0,0,0,0.2); padding: 16px 16px 16px 32px; border-radius: 12px; border-left: 2px solid var(--accent-color); list-style: none; }}
        details li {{ margin-bottom: 12px; }}
        details li:last-child {{ margin-bottom: 0; }}
        .ans-snippet {{ color: #94a3b8; font-style: normal; margin-top: 4px; display: block; }}
        
        @media (max-width: 1024px) {{
            .charts-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1><i data-lucide="bar-chart-2"></i> Analityka Sesji i Rozmów AI</h1>
            <p>Zaawansowany panel monitorowania zapytań i geolokalizacji klientów BDJ</p>
        </div>
        <div class="header-actions">
            <a href="/admin/export_csv" class="btn-action btn-primary" download>
                <i data-lucide="download" style="width:18px;height:18px;"></i> Pobierz CSV
            </a>
            <a href="/admin/logout" class="btn-action" style="color: #ef4444; border-color: rgba(239, 68, 68, 0.3);"><i data-lucide="log-out" style="width:18px;height:18px;"></i> Wyloguj</a>
            <a href="/" class="btn-action">
                <i data-lucide="arrow-left" style="width:18px;height:18px;"></i> Konfigurator
            </a>
        </div>
    </div>

    <div class="stats-grid">
        <div class="stat-card" style="animation-delay: 0.05s;">
            <div class="stat-card-header"><i data-lucide="users"></i> <span class="label">Liczba Sesji</span></div>
            <div class="num">{len(sessions)}</div>
        </div>
        <div class="stat-card" style="animation-delay: 0.1s;">
            <div class="stat-card-header"><i data-lucide="message-square-text"></i> <span class="label">Zadanych Pytań</span></div>
            <div class="num">{len(history)}</div>
        </div>
        <div class="stat-card" style="animation-delay: 0.15s;">
            <div class="stat-card-header"><i data-lucide="bot"></i> <span class="label">Udzielonych Odp.</span></div>
            <div class="num">{len(history)}</div>
        </div>
        <div class="stat-card" style="animation-delay: 0.2s;">
            <div class="stat-card-header"><i data-lucide="clock"></i> <span class="label">Średni Czas Sesji</span></div>
            <div class="num">{avg_dur_str}</div>
        </div>
        <div class="stat-card" style="animation-delay: 0.25s;">
            <div class="stat-card-header"><i data-lucide="globe"></i> <span class="label">Krajów na Świecie</span></div>
            <div class="num">{len(countries_count)}</div>
        </div>
        <div class="stat-card" style="animation-delay: 0.3s; border-color: rgba(16, 185, 129, 0.3);">
            <div class="stat-card-header" style="color: #6ee7b7;"><i data-lucide="phone-call"></i> <span class="label">Współczynnik Konwersji (Leady)</span></div>
            <div class="num" style="color: #6ee7b7;">{conversion_rate}%</div>
        </div>
    </div>

    <div class="charts-grid">
        <div class="glass-panel" style="animation-delay: 0.35s; margin-bottom: 0;">
            <h2><i data-lucide="pie-chart"></i> Popularność Maszyn BDJ</h2>
            <div style="position: relative; height: 260px; width: 100%;">
                <canvas id="machinesChart"></canvas>
            </div>
        </div>
        <div class="glass-panel" style="animation-delay: 0.4s; margin-bottom: 0;">
            <h2><i data-lucide="bar-chart-horizontal"></i> Tematyka Zapytań</h2>
            <div style="position: relative; height: 260px; width: 100%;">
                <canvas id="categoriesChart"></canvas>
            </div>
        </div>
    </div>

    <div class="glass-panel" style="animation-delay: 0.45s;">
        <h2><i data-lucide="map"></i> Interaktywna Mapa Geograficzna</h2>
        <div id="map"></div>
    </div>

    <div class="glass-panel" style="animation-delay: 0.5s;">
        <h2><i data-lucide="folder-open"></i> Rejestr Sesji Klientów</h2>
        <div style="overflow-x: auto;">
            <table>
                <thead>
                    <tr>
                        <th>ID Sesji</th>
                        <th>Początek</th>
                        <th>Kraj</th>
                        <th>Czas trwania</th>
                        <th>Pytania / Odp.</th>
                        <th>Zostawiono Kontakt?</th>
                        <th>Szczegóły rozmowy</th>
                    </tr>
                </thead>
                <tbody>
                    {session_rows_html if session_rows_html else '<tr><td colspan="7" style="text-align:center; padding:40px; color:#64748b;">Brak zalogowanych sesji.</td></tr>'}
                </tbody>
            </table>
        </div>
    </div>

    <div class="glass-panel" style="animation-delay: 0.55s;">
        <h2><i data-lucide="list"></i> Rejestr Pojedynczych Zapytań</h2>
        <div style="overflow-x: auto;">
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Data i czas</th>
                        <th>Kraj</th>
                        <th>Kategoria</th>
                        <th>Model BDJ</th>
                        <th>Kontakt</th>
                        <th>Pytanie Klienta</th>
                        <th>Odpowiedź Bota AI</th>
                    </tr>
                </thead>
                <tbody>
                    {query_rows_html if query_rows_html else '<tr><td colspan="8" style="text-align:center; padding:40px; color:#64748b;">Brak zapisanych pytań.</td></tr>'}
                </tbody>
            </table>
        </div>
    </div>

    <script>
        lucide.createIcons();
        
        const historyData = {json_history};
        
        // --- INICJALIZACJA MAPY LEAFLET ---
        const map = L.map('map').setView([50.0, 15.0], 4);
        L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
            maxZoom: 18,
            attribution: '&copy; <a href="https://carto.com/">CARTO</a>'
        }}).addTo(map);

        historyData.forEach(item => {{
            const lat = item.lat || 52.2297;
            const lon = item.lon || 21.0122;
            const flag = item.flag || '🌐';
            const country = item.country_name || 'Nieznany';
            const city = item.city || '';
            const hasContact = item.has_contact_info ? '📞 Podano kontakt BDJ' : 'Brak danych kontaktowych';
            const contactColor = item.has_contact_info ? '#6ee7b7' : '#94a3b8';
            
            const customIcon = L.divIcon({{
                className: 'custom-marker',
                html: `<div style="background:#38bdf8; width:12px; height:12px; border-radius:50%; border:2px solid #0f172a; box-shadow:0 0 10px rgba(56,189,248,0.8);"></div>`,
                iconSize: [12, 12],
                iconAnchor: [6, 6]
            }});

            const marker = L.marker([lat, lon], {{icon: customIcon}}).addTo(map);
            marker.bindPopup(`
                <div style="font-family:'Plus Jakarta Sans',sans-serif; min-width:220px;">
                    <div style="font-weight:700; font-size:1rem; color:#f8fafc; margin-bottom:4px; display:flex; align-items:center; gap:6px;">
                        <span>${{flag}}</span> ${{country}} <span style="color:#94a3b8;font-size:0.8rem;font-weight:500;">(${{city}})</span>
                    </div>
                    <div style="font-size:0.75rem; color:#64748b; margin-bottom:10px;">🕒 ${{item.timestamp || ''}}</div>
                    <div style="font-weight:500; font-size:0.85rem; color:#e2e8f0; margin-bottom:12px; line-height:1.4;">"${{item.question || ''}}"</div>
                    <div style="font-size:0.75rem; font-weight:700; color:${{contactColor}}; background:rgba(255,255,255,0.05); padding:6px 10px; border-radius:8px; display:inline-block;">${{hasContact}}</div>
                </div>
            `);
        }});

        // --- INICJALIZACJA WYKRESÓW CHART.JS ---
        Chart.defaults.color = '#94a3b8';
        Chart.defaults.font.family = "'Plus Jakarta Sans', sans-serif";

        const catCounts = {{}};
        const macCounts = {{}};
        
        historyData.forEach(i => {{
            const c = i.category || 'OGÓLNE';
            const m = i.detected_machine || 'BRAK';
            catCounts[c] = (catCounts[c] || 0) + 1;
            if(m !== 'BRAK') macCounts[m] = (macCounts[m] || 0) + 1;
        }});

        new Chart(document.getElementById('categoriesChart'), {{
            type: 'bar',
            data: {{
                labels: Object.keys(catCounts),
                datasets: [{{
                    label: 'Ilość Zapytań',
                    data: Object.values(catCounts),
                    backgroundColor: 'rgba(56, 189, 248, 0.7)',
                    borderColor: '#38bdf8',
                    borderWidth: 1,
                    borderRadius: 6
                }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }} }}
        }});

        new Chart(document.getElementById('machinesChart'), {{
            type: 'doughnut',
            data: {{
                labels: Object.keys(macCounts),
                datasets: [{{
                    data: Object.values(macCounts),
                    backgroundColor: ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ec4899', '#06b6d4'],
                    borderWidth: 0,
                    hoverOffset: 4
                }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'right', labels: {{ color: '#e2e8f0' }} }} }}, cutout: '65%' }}
        }});
    </script>
</body>
</html>"""
    return HTMLResponse(content=html_content)

@app.get("/")
def read_index():
    return FileResponse("index.html")

@app.get("/avatar.png")
def get_avatar():
    return FileResponse("avatar.png")

@app.post("/offer")
def handle_offer(request: OfferRequest):
    print("\n" + "="*50)
    print("📩 NOWE ZAPYTANIE OFERTOWE Z CZATBOTA")
    print("="*50)
    print(f"🏢 Firma:   {request.company}")
    print(f"📧 Email:   {request.email}")
    print(f"📞 Telefon: {request.phone}")
    
    if request.machine:
        print(f"🎯 Dotyczy maszyny: {request.machine}")
        
    if request.items and len(request.items) > 0:
        print("🔧 Wybrane pozycje z tabeli:")
        for item in request.items:
            zaznaczony_element = " | ".join(item) if isinstance(item, list) else item
            print(f"   -> {zaznaczony_element}")
    print("="*50 + "\n")
    
    # --- WYSYŁKA GMAIL SMTP ---
    msg = MIMEMultipart()
    msg['Subject'] = f"Nowe zapytanie z Bota AI - {request.company}"
    msg['From'] = SMTP_LOGIN 
    msg['To'] = "info@gamm-bud.pl"   # <--- Zmieniono na docelowy adres firmy

    body = f"Nowy lead z Chatbota!\n\nFirma: {request.company}\nEmail: {request.email}\nTelefon: {request.phone}\n\n"
    
    if request.machine:
        body += f"🎯 Klient prosi o wycenę maszyny: {request.machine}\n\n"
        
    if request.items and len(request.items) > 0:
        body += "🔧 Wybrane części zamienne/akcesoria:\n"
        for item in request.items:
            zaznaczony_element = " | ".join(item) if isinstance(item, list) else item
            body += f"- {zaznaczony_element}\n"

    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        print("Wysyłanie e-maila przez Gmail...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_LOGIN, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("✅ E-mail został pomyślnie wysłany na info@gamm-bud.pl!")
    except Exception as e:
        print(f"⚠️ Błąd wysyłki e-mail: {e}")
        
    return {"status": "success"}


@app.get("/admin/export_csv")
def export_csv(admin_session: str = Cookie(None)):
    if not require_auth(admin_session):
        return RedirectResponse(url="/admin/login", status_code=303)

    history = []
    if LOG_FILE_PATH.exists():
        try:
            with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            pass
            
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(['ID', 'Data', 'Kraj', 'Kategoria', 'Model BDJ', 'Podano Kontakt', 'Pytanie Klienta', 'Odpowiedz (Skrot)'])
    
    for item in history:
        writer.writerow([
            item.get('id', ''),
            item.get('timestamp', ''),
            item.get('country_name', ''),
            item.get('category', ''),
            item.get('detected_machine', ''),
            'TAK' if item.get('has_contact_info') else 'NIE',
            item.get('question', '').replace(';', ','),
            item.get('answer_snippet', '').replace(';', ',').replace('\n', ' ')
        ])
        
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=bdj_lead_report.csv"}
    )

if __name__ == "__main__":

    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)