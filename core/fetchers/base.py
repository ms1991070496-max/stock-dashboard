"""Abstract base class and retry/fallback infrastructure for data fetchers."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import date
from functools import wraps
from typing import Callable

import pandas as pd

logger = logging.getLogger(__name__)


class FetchError(Exception):
    pass


class TemporaryError(FetchError):
    """Transient error — retry may succeed."""
    pass


class PermanentError(FetchError):
    """Non-retryable error — do not retry."""
    pass


def retry(max_attempts: int = 3, base_delay: float = 2.0):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_err = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except TemporaryError as e:
                    last_err = e
                    delay = base_delay * (2 ** attempt)
                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1}/{max_attempts} failed: {e}, retrying in {delay}s"
                    )
                    await asyncio.sleep(delay)
                except PermanentError:
                    raise
            raise TemporaryError(f"All {max_attempts} attempts exhausted: {last_err}")
        return wrapper
    return decorator


class BaseFetcher(ABC):
    """Abstract base for all stock data fetchers."""

    market: str = ""
    name: str = "base"

    @abstractmethod
    async def fetch_kline(self, code: str, start_date: date | None = None, end_date: date | None = None) -> pd.DataFrame:
        ...

    @abstractmethod
    async def fetch_realtime(self, code: str) -> dict:
        ...

    @abstractmethod
    async def fetch_stock_info(self, code: str) -> dict:
        ...

    @abstractmethod
    async def fetch_financials(self, code: str) -> pd.DataFrame:
        ...

    @abstractmethod
    async def search_stocks(self, keyword: str) -> list[dict]:
        ...

    async def fetch_news(self, code: str | None = None, limit: int = 20) -> list[dict]:
        return []
