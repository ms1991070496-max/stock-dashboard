"""FastAPI application — REST API + static frontend."""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from api.middleware.cors import setup_cors
from api.routers import stocks, indicators, screener, news

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Stock Analysis Dashboard",
    version="0.4.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

setup_cors(app)

app.include_router(stocks.router_api)
app.include_router(indicators.router_api)
app.include_router(screener.router_api)
app.include_router(news.router_api)

static_dir = Path(__file__).resolve().parent.parent / "static"
static_dir.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.on_event("startup")
async def startup():
    try:
        from core.database import init_db
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning(f"DB init skipped (non-fatal): {e}")


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.4.0"}


@app.get("/{path:path}")
async def serve_frontend(path: str):
    """Serve static frontend — all non-API paths get index.html."""
    file_path = static_dir / path
    if file_path.is_file():
        return FileResponse(file_path)
    return FileResponse(static_dir / "index.html")
