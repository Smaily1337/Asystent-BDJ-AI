"""Punkt wejścia — kompatybilność wsteczna z `python server.py`."""

from app.config import settings
from app.main import app

__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )
