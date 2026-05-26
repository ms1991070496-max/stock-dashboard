import logging
from datetime import date
from typing import Optional

import pandas as pd

from core.fetchers.base import BaseFetcher, TemporaryError, retry

logger = logging.getLogger(__name__)


class AkShareFetcher(BaseFetcher):
    market = "cn"
    name = "akshare"

    @retry(max_attempts=3, base_delay=2.0)
    async def fetch_kline(self, code: str, start_date: date | None = None, end_date: date | None = None) -> pd.DataFrame:
        try:
            import akshare as ak
        except ImportError:
            raise TemporaryError("akshare not installed")

        try:
            symbol = self._normalize_code(code)
            start = start_date.strftime("%Y%m%d") if start_date else "20000101"
            end = end_date.strftime("%Y%m%d") if end_date else date.today().strftime("%Y%m%d")

            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start, end_date=end, adjust="qfq")
            if df.empty:
                raise TemporaryError(f"No K-line data for {code}")

            df = df.rename(columns={
                "日期": "date", "开盘": "open", "收盘": "close",
                "最高": "high", "最低": "low", "成交量": "volume",
                "成交额": "amount", "换手率": "turnover_rate",
            })
            df["date"] = pd.to_datetime(df["date"]).dt.date
            numeric_cols = ["open", "close", "high", "low", "volume", "amount"]
            df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
            return df
        except TemporaryError:
            raise
        except Exception as e:
            raise TemporaryError(f"AkShare K-line failed for {code}: {e}")

    @retry(max_attempts=2, base_delay=1.0)
    async def fetch_realtime(self, code: str) -> dict:
        try:
            import akshare as ak
        except ImportError:
            raise TemporaryError("akshare not installed")

        try:
            df = ak.stock_zh_a_spot_em()
            row = df[df["代码"] == code]
            if row.empty:
                raise TemporaryError(f"Stock {code} not found in spot data")
            r = row.iloc[0]
            return {
                "code": code,
                "name": r["名称"],
                "price": float(r["最新价"]),
                "change_pct": float(r["涨跌幅"]),
                "change_amount": float(r["涨跌额"]),
                "volume": int(r["成交量"]),
                "high": float(r["最高"]),
                "low": float(r["最低"]),
                "open": float(r["今开"]),
                "pre_close": float(r["昨收"]),
            }
        except TemporaryError:
            raise
        except Exception as e:
            raise TemporaryError(f"AkShare realtime failed for {code}: {e}")

    @retry(max_attempts=2, base_delay=1.0)
    async def fetch_stock_info(self, code: str) -> dict:
        try:
            import akshare as ak
        except ImportError:
            raise TemporaryError("akshare not installed")

        try:
            df = ak.stock_individual_info_em(symbol=code)
            info = {}
            for _, row in df.iterrows():
                info[row["item"]] = row["value"]
            return {
                "code": code,
                "name": info.get("股票简称", code),
                "market": "cn",
                "sector": info.get("板块", ""),
                "industry": info.get("行业", ""),
            }
        except Exception as e:
            logger.warning(f"stock_info failed for {code}: {e}, returning basic info")
            return {"code": code, "name": code, "market": "cn", "sector": "", "industry": ""}

    async def fetch_financials(self, code: str) -> pd.DataFrame:
        try:
            import akshare as ak
        except ImportError:
            raise TemporaryError("akshare not installed")

        try:
            df = ak.stock_financial_abstract_ths(symbol=code, indicator="按报告期")
            return df
        except Exception as e:
            logger.warning(f"financials failed for {code}: {e}")
            return pd.DataFrame()

    async def search_stocks(self, keyword: str) -> list[dict]:
        results = []
        try:
            import akshare as ak
            df = ak.stock_zh_a_spot_em()
            matched = df[df["名称"].str.contains(keyword, na=False) | df["代码"].str.contains(keyword, na=False)]
            for _, row in matched.head(20).iterrows():
                results.append({
                    "code": row["代码"], "name": row["名称"], "market": "cn",
                    "price": float(row["最新价"]), "change_pct": float(row["涨跌幅"]),
                })
        except Exception as e:
            logger.warning(f"search_stocks failed: {e}")
        return results

    async def fetch_news(self, code: str | None = None, limit: int = 20) -> list[dict]:
        try:
            import akshare as ak
            df = ak.stock_news_em()
            if df.empty:
                return []
            news_list = []
            for _, row in df.head(limit).iterrows():
                news_list.append({
                    "title": str(row.get("标题", "")),
                    "source": "EastMoney",
                    "url": str(row.get("链接", "")),
                    "published_at": None,
                    "sentiment_score": 0.0,
                })
            return news_list
        except Exception as e:
            logger.warning(f"news fetch failed: {e}")
            return []

    @staticmethod
    def _normalize_code(code: str) -> str:
        code = code.strip().upper()
        if code.startswith("SH") or code.startswith("SZ"):
            return code
        if len(code) == 6 and code.isdigit():
            if code.startswith(("6", "9")):
                return f"SH{code}"
            else:
                return f"SZ{code}"
        return code
