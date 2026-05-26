"""Sina Finance fetcher — works from Chinese cloud servers. Supports A-shares, HK, US."""

import logging
import re
import urllib.request
from datetime import date, datetime

import pandas as pd

from core.fetchers.base import BaseFetcher, TemporaryError

logger = logging.getLogger(__name__)

# ── Sina symbol mapping ──────────────────────────────
def _to_sina(code: str) -> str:
    """Convert unified code to Sina Finance symbol."""
    code = code.strip().upper()
    # US stock
    if re.match(r'^[A-Z]{1,5}$', code) and not code.startswith(('SH', 'SZ', 'HK')):
        return f'gb_{code.lower()}'
    # HK stock
    if code.endswith('.HK'):
        return f'hk{code[:-3]}'
    if re.match(r'^\d{4,5}$', code):
        return f'hk{code}'
    # A-share
    if code.startswith('SH'):
        return f'sh{code[2:]}'
    if code.startswith('SZ'):
        return f'sz{code[2:]}'
    if code.isdigit() and len(code) == 6:
        prefix = 'sh' if code.startswith(('6', '9')) else 'sz'
        return f'{prefix}{code}'
    return code


def _fetch_sina(symbol: str) -> str | None:
    """Fetch raw Sina quote line."""
    try:
        req = urllib.request.Request(
            f'https://hq.sinajs.cn/list={symbol}',
            headers={'Referer': 'https://finance.sina.com.cn'}
        )
        resp = urllib.request.urlopen(req, timeout=8)
        return resp.read().decode('gbk')
    except Exception as e:
        logger.warning(f"Sina fetch failed for {symbol}: {e}")
        return None


def _detect_mkt(symbol: str) -> str:
    if symbol.startswith('gb_'): return 'us'
    if symbol.startswith('hk'): return 'hk'
    return 'cn'


# ── Fetcher class ─────────────────────────────────────
class SinaFetcher(BaseFetcher):
    market = "all"
    name = "sina"

    async def fetch_realtime(self, code: str) -> dict:
        symbol = _to_sina(code)
        raw = _fetch_sina(symbol)
        if not raw:
            raise TemporaryError(f"Sina no data for {code}")

        mkt = _detect_mkt(symbol)
        try:
            body = raw.split('"')[1] if '"' in raw else raw
            parts = body.split(',')
            if len(parts) < 9:
                raise TemporaryError(f"Sina short response for {code}: {len(parts)} fields")

            if mkt == 'cn':
                return {
                    'code': code, 'name': parts[0],
                    'open': float(parts[1]), 'pre_close': float(parts[2]),
                    'price': float(parts[3]), 'high': float(parts[4]), 'low': float(parts[5]),
                    'volume': int(float(parts[8])), 'change_pct': round((float(parts[3]) - float(parts[2])) / float(parts[2]) * 100, 2),
                }
            elif mkt == 'hk':
                return {
                    'code': code, 'name': parts[1],
                    'open': float(parts[2]), 'pre_close': float(parts[3]),
                    'high': float(parts[4]), 'low': float(parts[5]),
                    'price': float(parts[6]),
                    'change_pct': float(parts[8]),  # Sina already gives pct
                    'volume': 0,
                }
            else:  # US
                return {
                    'code': code, 'name': parts[0],
                    'price': float(parts[1]),
                    'change_pct': float(parts[2]),
                    'open': float(parts[5]), 'high': float(parts[6]), 'low': float(parts[7]),
                    'pre_close': float(parts[8]), 'volume': 0,
                }
        except (IndexError, ValueError) as e:
            raise TemporaryError(f"Sina parse error for {code}: {e}")

    async def fetch_stock_info(self, code: str) -> dict:
        q = await self.fetch_realtime(code)
        mkt = _detect_mkt(_to_sina(code))
        return {'code': code, 'name': q['name'], 'market': mkt, 'sector': '', 'industry': ''}

    async def fetch_kline(self, code: str, start_date: date | None = None, end_date: date | None = None) -> pd.DataFrame:
        """K-line via Baostock for A-shares; demo fallback for HK/US."""
        code_u = code.strip().upper()
        if code_u.isdigit() and len(code_u) == 6:
            prefix = 'sh' if code_u.startswith(('6', '9')) else 'sz'
            return self._baostock_kline(f'{prefix}.{code_u}', start_date, end_date)
        raise TemporaryError(f"K-line not supported for {code} via Sina")

    def _baostock_kline(self, bs_code: str, start: date | None, end: date | None) -> pd.DataFrame:
        try:
            import baostock as bs
            bs.login()
            s = start.strftime('%Y-%m-%d') if start else '2015-01-01'
            e = end.strftime('%Y-%m-%d') if end else date.today().strftime('%Y-%m-%d')
            rs = bs.query_history_k_data_plus(bs_code, 'date,open,high,low,close,volume,amount,turn', start_date=s, end_date=e, frequency='d', adjustflag='2')
            rows = []
            while rs.next(): rows.append(rs.get_row_data())
            bs.logout()
            df = pd.DataFrame(rows, columns=['date','open','high','low','close','volume','amount','turnover_rate'])
            for col in ['open','high','low','close','volume','amount','turnover_rate']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df['date'] = pd.to_datetime(df['date']).dt.date
            return df
        except Exception as e:
            logger.warning(f"Baostock kline failed: {e}")
            raise TemporaryError(f"Baostock error: {e}")

    async def fetch_financials(self, code: str) -> pd.DataFrame:
        return pd.DataFrame()

    async def search_stocks(self, keyword: str) -> list[dict]:
        return []

    async def fetch_news(self, code: str | None = None, limit: int = 20) -> list[dict]:
        return []
