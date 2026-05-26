"""FastAPI application — REST API for stock analysis dashboard."""

import logging

from fastapi import FastAPI

from api.middleware.cors import setup_cors
from api.routers import stocks, indicators, screener, news
from core.database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

init_db()

app = FastAPI(
    title="Stock Analysis Dashboard API",
    description="Multi-market stock analysis (A-shares / US / HK) — K-line, technical indicators, screener, sentiment",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

setup_cors(app)

app.include_router(stocks.router_api)
app.include_router(indicators.router_api)
app.include_router(screener.router_api)
app.include_router(news.router_api)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.2.0"}
