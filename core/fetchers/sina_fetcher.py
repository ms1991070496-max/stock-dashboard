"""Sina Finance fetcher — works from Chinese cloud servers. Supports A-shares, HK, US."""

import logging
import re
import time
import urllib.request
from datetime import date, datetime

import pandas as pd

from core.fetchers.base import BaseFetcher, TemporaryError

logger = logging.getLogger(__name__)

# ── Rate-limit + cache ────────────────────────────────
_cache: dict[str, tuple[float, str]] = {}
_CACHE_TTL = 30  # seconds
_LAST_CALL = 0.0
_MIN_INTERVAL = 0.3  # seconds between Sina calls

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
    """Fetch raw Sina quote line with rate limiting and cache."""
    global _LAST_CALL
    now = time.time()

    # Check cache
    if symbol in _cache:
        ts, val = _cache[symbol]
        if now - ts < _CACHE_TTL:
            return val

    # Rate limit
    elapsed = now - _LAST_CALL
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)
    _LAST_CALL = time.time()

    for attempt in range(3):
        try:
            req = urllib.request.Request(
                f'https://hq.sinajs.cn/list={symbol}',
                headers={'Referer': 'https://finance.sina.com.cn'}
            )
            resp = urllib.request.urlopen(req, timeout=8)
            raw = resp.read().decode('gbk')
            # Check if data is valid (not empty "")
            if raw and '"");' not in raw:
                _cache[symbol] = (time.time(), raw)
                return raw
            time.sleep(0.5 * (attempt + 1))
        except Exception as e:
            if attempt == 2:
                logger.warning(f"Sina fetch failed for {symbol}: {e}")
            time.sleep(0.5)
    # Return cached stale data if available
    if symbol in _cache:
        return _cache[symbol][1]
    return None
    except Exception as e:
        logger.warning(f"Sina fetch failed for {symbol}: {e}")
        # Return cached stale data if available
        if symbol in _cache:
            return _cache[symbol][1]
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
