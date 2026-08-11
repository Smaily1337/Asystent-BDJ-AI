"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from app.api import admin, chat, offer
from app.config import settings
from app.rag.engine import SessionChatManager
from app.rag.knowledge import build_retriever, create_llm


def create_app() -> FastAPI:
    application = FastAPI(
        title="Asystent BDJ AI",
        description="Chatbot doboru części zamiennych Blue Dragon Jet",
        version="0.0.7",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if settings.karty_dir.exists():
        application.mount("/karty", StaticFiles(directory=str(settings.karty_dir)), name="karty")

    llm = create_llm(settings)
    retriever = build_retriever(settings)
    manager = SessionChatManager(retriever=retriever, llm=llm)
    chat.bind_chat_manager(manager)

    application.include_router(chat.router)
    application.include_router(offer.router)
    application.include_router(admin.router)

    static_dir = settings.static_dir
    index_path = static_dir / "index.html"
    avatar_path = static_dir / "avatar.png"
    # Fallback na stare lokalizacje w root (kompatybilność wsteczna)
    if not index_path.exists():
        index_path = settings.root_dir / "index.html"
    if not avatar_path.exists():
        avatar_path = settings.root_dir / "avatar.png"

    @application.get("/")
    def read_index():
        return FileResponse(str(index_path))

    @application.head("/")
    def read_index_head():
        # Render robi HEAD / przy deployu — bez tego 405 i deploy może timeoutować
        return Response(status_code=200)

    @application.head("/health")
    def health_head():
        return Response(status_code=200)

    @application.get("/avatar.png")
    def get_avatar():
        return FileResponse(str(avatar_path))

    @application.get("/embed.js")
    def get_embed_js():
        embed_path = static_dir / "embed.js"
        if not embed_path.exists():
            embed_path = settings.root_dir / "static" / "embed.js"
        return FileResponse(
            str(embed_path),
            media_type="application/javascript; charset=utf-8",
            headers={"Cache-Control": "public, max-age=60"},
        )

    @application.get("/api/machines")
    def list_machines():
        from app.rag.machine_web import machines_for_api

        return machines_for_api()

    @application.get("/health")
    def health():
        return {
            "status": "ok",
            "version": "0.0.7",
            "email_configured": bool(
                settings.resend_api_key
                or (settings.smtp_login and settings.smtp_password)
            ),
            "email_provider": "resend" if settings.resend_api_key else (
                "smtp" if settings.smtp_login and settings.smtp_password else "none"
            ),
        }

    return application


app = create_app()
