import logging
from datetime import date, datetime

import pandas as pd

from core.fetchers.base import BaseFetcher, TemporaryError, retry

logger = logging.getLogger(__name__)


class YFinanceFetcher(BaseFetcher):
    market = "us"
    name = "yfinance"

    def _to_ticker(self, code: str) -> str:
        code = code.strip().upper()
        if code.endswith(".HK"):
            self.market = "hk"
            return code
        if code.endswith((".SS", ".SZ")):
            self.market = "cn"
            return code
        if len(code) == 5 and code.isdigit():
            self.market = "hk"
            return f"{code}.HK"
        if len(code) == 4 and code.isdigit():
            self.market = "hk"
            return f"{code}.HK"
        self.market = "us"
        return code

    @retry(max_attempts=3, base_delay=2.0)
    async def fetch_kline(self, code: str, start_date: date | None = None, end_date: date | None = None) -> pd.DataFrame:
        try:
            import yfinance as yf
        except ImportError:
            raise TemporaryError("yfinance not installed")

        try:
            ticker_str = self._to_ticker(code)
            ticker = yf.Ticker(ticker_str)
            start = start_date or date(2015, 1, 1)
            end = end_date or date.today()

            df = ticker.history(start=start, end=end, auto_adjust=True)
            if df.empty:
                raise TemporaryError(f"No K-line data for {ticker_str}")

            df = df.reset_index()
            df = df.rename(columns={
                "Date": "date", "Open": "open", "High": "high",
                "Low": "low", "Close": "close", "Volume": "volume",
            })
            df["date"] = pd.to_datetime(df["date"]).dt.date
            df["amount"] = 0.0
            df["turnover_rate"] = 0.0
            return df[["date", "open", "high", "low", "close", "volume", "amount", "turnover_rate"]]
        except TemporaryError:
            raise
        except Exception as e:
            raise TemporaryError(f"YFinance K-line failed for {code}: {e}")

    @retry(max_attempts=2, base_delay=1.0)
    async def fetch_realtime(self, code: str) -> dict:
        try:
            import yfinance as yf
        except ImportError:
            raise TemporaryError("yfinance not installed")

        try:
            ticker_str = self._to_ticker(code)
            ticker = yf.Ticker(ticker_str)
            info = ticker.info or {}
            fast_info = ticker.fast_info
            return {
                "code": code,
                "name": info.get("shortName", info.get("longName", code)),
                "price": float(fast_info.get("lastPrice", info.get("currentPrice", 0))),
                "change_pct": float(info.get("regularMarketChangePercent", 0)),
                "change_amount": float(info.get("regularMarketChange", 0)),
                "volume": int(info.get("volume", 0)),
                "high": float(fast_info.get("dayHigh", info.get("dayHigh", 0))),
                "low": float(fast_info.get("dayLow", info.get("dayLow", 0))),
                "open": float(fast_info.get("open", info.get("open", 0))),
                "pre_close": float(info.get("previousClose", 0)),
            }
        except Exception as e:
            raise TemporaryError(f"YFinance realtime failed for {code}: {e}")

    async def fetch_stock_info(self, code: str) -> dict:
        try:
            import yfinance as yf
        except ImportError:
            raise TemporaryError("yfinance not installed")

        try:
            ticker_str = self._to_ticker(code)
            ticker = yf.Ticker(ticker_str)
            info = ticker.info or {}
            return {
                "code": code,
                "name": info.get("shortName", info.get("longName", code)),
                "market": self.market,
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
            }
        except Exception as e:
            logger.warning(f"stock_info failed for {code}: {e}")
            return {"code": code, "name": code, "market": self.market, "sector": "", "industry": ""}

    async def fetch_financials(self, code: str) -> pd.DataFrame:
        try:
            import yfinance as yf
        except ImportError:
            raise TemporaryError("yfinance not installed")

        try:
            ticker_str = self._to_ticker(code)
            ticker = yf.Ticker(ticker_str)
            info = ticker.info or {}

            data = [{
                "period": "latest",
                "revenue": float(info.get("totalRevenue", 0) or 0),
                "net_profit": float(info.get("netIncomeToCommon", 0) or 0),
                "eps": float(info.get("trailingEps", 0) or 0),
                "bvps": float(info.get("bookValue", 0) or 0),
                "roe": float(info.get("returnOnEquity", 0) or 0) * 100,
                "gross_margin": float(info.get("grossMargins", 0) or 0) * 100,
                "net_margin": float(info.get("profitMargins", 0) or 0) * 100,
                "debt_ratio": float(info.get("debtToEquity", 0) or 0),
                "current_ratio": float(info.get("currentRatio", 0) or 0),
                "pe": float(info.get("trailingPE", 0) or 0),
                "pb": float(info.get("priceToBook", 0) or 0),
                "market_cap": float(info.get("marketCap", 0) or 0),
            }]
            return pd.DataFrame(data)
        except Exception as e:
            logger.warning(f"financials failed for {code}: {e}")
            return pd.DataFrame()

    async def search_stocks(self, keyword: str) -> list[dict]:
        try:
            import yfinance as yf
            ticker = yf.Ticker(keyword.strip().upper())
            info = ticker.info or {}
            if info.get("symbol"):
                return [{
                    "code": keyword,
                    "name": info.get("shortName", info.get("longName", keyword)),
                    "market": self.market,
                    "price": float(info.get("currentPrice", 0) or 0),
                    "change_pct": float(info.get("regularMarketChangePercent", 0) or 0),
                }]
        except Exception:
            pass
        return []
