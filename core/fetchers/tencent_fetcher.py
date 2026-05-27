"""Tencent Finance fetcher — accurate, fast, accessible from China."""

import logging
import re
import time
import urllib.request
from datetime import date

import pandas as pd

from core.fetchers.base import BaseFetcher, TemporaryError

logger = logging.getLogger(__name__)

_cache: dict[str, tuple[float, str]] = {}
_CACHE_TTL = 30
_LAST_CALL = 0.0
_MIN_INTERVAL = 0.25


def _to_tx(code: str) -> str:
    code = code.strip().upper()
    if re.match(r'^[A-Z]{1,5}$', code) and not code.startswith(('SH', 'SZ', 'HK')):
        return f'us{code}'
    if code.endswith('.HK'):
        return f'hk{code[:-3]}'
    if re.match(r'^\d{4,5}$', code):
        return f'hk{int(code):05d}'
    if code.startswith('SH'): return f'sh{code[2:]}'
    if code.startswith('SZ'): return f'sz{code[2:]}'
    if code.isdigit() and len(code) == 6:
        return ('sh' if code.startswith(('6','9')) else 'sz') + code
    return code


def _detect_mkt(sym: str) -> str:
    if sym.startswith('us'): return 'us'
    if sym.startswith('hk'): return 'hk'
    return 'cn'


def _fetch_tx(symbol: str) -> str | None:
    """Simple fetch — no cache complexity."""
    try:
        req = urllib.request.Request(
            f'https://qt.gtimg.cn/q={symbol}',
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        resp = urllib.request.urlopen(req, timeout=8)
        raw = resp.read().decode('gbk', errors='replace')
        if raw and len(raw) > 50:
            return raw
    except Exception as e:
        logger.warning(f"Tencent fetch failed for {symbol}: {e}")
    return None


def _tx_fetch(code: str) -> dict:
    """Synchronous fetch — called from async wrapper."""
    import subprocess
    sym = _to_tx(code)
    r = subprocess.run(['curl', '-s', '-H', 'User-Agent: Mozilla/5.0',
        f'https://qt.gtimg.cn/q={sym}'], capture_output=True, timeout=8)
    raw = r.stdout.decode('gbk', errors='replace')
    if not raw or len(raw) < 50:
        raise TemporaryError(f'Tencent no data for {code}')
    body = raw.split('"')[1] if '"' in raw else raw
    parts = body.split('~')
    mkt = _detect_mkt(sym)
    if mkt == 'cn':
        return {'code': code, 'name': parts[1], 'price': float(parts[3]), 'pre_close': float(parts[4]),
                'open': float(parts[5]), 'high': float(parts[33]), 'low': float(parts[34]),
                'change_pct': round((float(parts[3])-float(parts[4]))/float(parts[4])*100,2), 'volume': int(float(parts[6]))}
    elif mkt == 'hk':
        return {'code': code, 'name': parts[1], 'price': float(parts[3]), 'pre_close': float(parts[4]),
                'open': float(parts[5]), 'high': float(parts[33]), 'low': float(parts[34]),
                'change_pct': float(parts[32]), 'volume': int(float(parts[6]))}
    else:
        return {'code': code, 'name': parts[1] if parts[1] else code, 'price': float(parts[3]), 'pre_close': float(parts[4]),
                'open': float(parts[5]), 'high': float(parts[33]), 'low': float(parts[34]),
                'change_pct': round((float(parts[3])-float(parts[4]))/float(parts[4])*100,2), 'volume': int(float(parts[6]))}


class TencentFetcher(BaseFetcher):
    market = "all"
    name = "tencent"

    async def fetch_realtime(self, code: str) -> dict:
        return _tx_fetch(code)

    async def fetch_stock_info(self, code: str) -> dict:
        q = await self.fetch_realtime(code)
        return {'code': code, 'name': q['name'], 'market': _detect_mkt(_to_tx(code)), 'sector': '', 'industry': ''}

    async def fetch_kline(self, code: str, start_date=None, end_date=None) -> pd.DataFrame:
        import subprocess, json
        sym = _to_tx(code)
        days = 365
        if start_date:
            from datetime import date
            days = (date.today() - start_date).days + 1
        url = f'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={sym},day,,,{min(days,400)},qfq'
        try:
            r = subprocess.run(['curl', '-s', '-H', 'User-Agent: Mozilla/5.0', url],
                             capture_output=True, timeout=15)
            raw = r.stdout.decode('gbk', errors='replace')
            data = json.loads(raw)
            rows = data.get('data', {}).get(sym, {}).get('qfqday') or data.get('data', {}).get(sym, {}).get('day', [])
            if not rows:
                raise TemporaryError(f'No kline for {code}')
            df = pd.DataFrame(rows, columns=['date','open','close','high','low','volume','_','__','___','____','_____','______','_______','________'][:len(rows[0])])
            for col in ['open','high','low','close','volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df['date'] = pd.to_datetime(df['date']).dt.date
            df['amount'] = 0.0
            df['turnover_rate'] = 0.0
            return df[['date','open','high','low','close','volume','amount','turnover_rate']]
        except Exception as e:
            raise TemporaryError(f'Tencent kline failed: {e}')

    async def fetch_financials(self, code: str) -> pd.DataFrame:
        return pd.DataFrame()

    async def search_stocks(self, keyword: str) -> list[dict]:
        return []

    async def fetch_news(self, code=None, limit=20) -> list[dict]:
        return []
