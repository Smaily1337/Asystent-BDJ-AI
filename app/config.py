"""Konfiguracja aplikacji — wyłącznie ze zmiennych środowiskowych."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent

_env_candidates = [ROOT_DIR / "api.env", ROOT_DIR / ".env"]
for _env_path in _env_candidates:
    if _env_path.exists():
        load_dotenv(_env_path)
        break
else:
    load_dotenv()


@dataclass(frozen=True)
class Settings:
    root_dir: Path = ROOT_DIR
    deepseek_api_key: str = field(default_factory=lambda: os.getenv("DEEPSEEK_API_KEY", ""))
    deepseek_model: str = field(default_factory=lambda: os.getenv("DEEPSEEK_MODEL", "deepseek-chat"))
    deepseek_api_base: str = field(
        default_factory=lambda: os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
    )

    admin_user: str = field(default_factory=lambda: os.getenv("ADMIN_USER", "admin"))
    admin_password: str = field(default_factory=lambda: os.getenv("ADMIN_PASSWORD", "admin123"))

    smtp_server: str = field(default_factory=lambda: os.getenv("SMTP_SERVER", "smtp.gmail.com"))
    smtp_port_ssl: int = field(default_factory=lambda: int(os.getenv("SMTP_PORT_SSL", "465")))
    smtp_port_tls: int = field(default_factory=lambda: int(os.getenv("SMTP_PORT_TLS", "587")))
    smtp_login: str = field(default_factory=lambda: os.getenv("SMTP_LOGIN", ""))
    smtp_password: str = field(default_factory=lambda: os.getenv("SMTP_PASSWORD", ""))
    resend_api_key: str = field(default_factory=lambda: os.getenv("RESEND_API_KEY", ""))
    resend_from: str = field(
        default_factory=lambda: os.getenv("RESEND_FROM", "Dragon AI <onboarding@resend.dev>")
    )
    offer_recipients: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            r.strip()
            for r in os.getenv(
                "OFFER_RECIPIENTS",
                "info@gamm-bud.pl,info@bluedragonjet.com",
            ).split(",")
            if r.strip()
        )
    )

    # Backup: przekaż lead do Contact Form 7 na WordPress (formularz ofertowy na stronie głównej)
    wp_site_url: str = field(
        default_factory=lambda: os.getenv("WP_SITE_URL", "https://bluedragonjet.com")
    )
    wp_cf7_enabled: bool = field(
        default_factory=lambda: os.getenv("WP_CF7_ENABLED", "true").lower() in ("1", "true", "yes")
    )
    wp_cf7_form_id: int = field(default_factory=lambda: int(os.getenv("WP_CF7_FORM_ID", "358")))
    wp_cf7_unit_tag: str = field(
        default_factory=lambda: os.getenv("WP_CF7_UNIT_TAG", "wpcf7-f358-o1")
    )
    wp_cf7_version: str = field(default_factory=lambda: os.getenv("WP_CF7_VERSION", "5.6.4"))
    wp_cf7_locale: str = field(default_factory=lambda: os.getenv("WP_CF7_LOCALE", "pl_PL"))

    # Jedna baza wiedzy
    knowledge_dirs: tuple[str, ...] = ("knowledge",)
    karty_subdir: str = "knowledge/karty_produktow/PL"
    questions_log: str = "knowledge/data/historia_pytan_klientow.json"
    offers_log: str = "knowledge/data/historia_ofert.json"

    host: str = field(default_factory=lambda: os.getenv("HOST", "127.0.0.1"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8000")))

    chunk_size: int = 1000
    chunk_overlap: int = 150
    bm25_top_k: int = 12
    memory_token_limit: int = 3000
    llm_temperature: float = 0.0
    context_window: int = 32768
    max_tokens: int = 2048

    @property
    def static_dir(self) -> Path:
        return self.root_dir / "static"

    @property
    def karty_dir(self) -> Path:
        return self.root_dir / self.karty_subdir

    @property
    def questions_log_path(self) -> Path:
        return self.root_dir / self.questions_log

    @property
    def offers_log_path(self) -> Path:
        return self.root_dir / self.offers_log

    def knowledge_paths(self) -> list[Path]:
        paths = [self.root_dir / d for d in self.knowledge_dirs if (self.root_dir / d).exists()]
        # Fallback na stare lokalizacje (gdyby knowledge/ jeszcze nie było)
        if not paths:
            for legacy in ("baza_wiedzy", "czesci_nowe"):
                p = self.root_dir / legacy
                if p.exists():
                    paths.append(p)
        return paths


settings = Settings()
