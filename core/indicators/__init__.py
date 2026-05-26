import numpy as np
import pandas as pd


def compute_all(klines: list[dict]) -> dict:
    """Compute all indicators from a list of kline dicts. Returns dict of list[float|None]."""
    if not klines:
        return {}

    close = np.array([k["close"] for k in klines], dtype=float)
    high = np.array([k["high"] for k in klines], dtype=float)
    low = np.array([k["low"] for k in klines], dtype=float)
    volume = np.array([k["volume"] for k in klines], dtype=float)

    return {
        "ma5": _to_list(sma(close, 5)),
        "ma10": _to_list(sma(close, 10)),
        "ma20": _to_list(sma(close, 20)),
        "ma60": _to_list(sma(close, 60)),
        "macd_dif": _to_list(macd_dif(close)),
        "macd_dea": _to_list(macd_dea(close)),
        "macd_hist": _to_list(macd_hist(close)),
        "rsi6": _to_list(rsi(close, 6)),
        "rsi14": _to_list(rsi(close, 14)),
        "rsi24": _to_list(rsi(close, 24)),
        "boll_upper": _to_list(boll_upper(close, 20, 2)),
        "boll_mid": _to_list(sma(close, 20)),
        "boll_lower": _to_list(boll_lower(close, 20, 2)),
        "kdj_k": _to_list(kdj_k(high, low, close)),
        "kdj_d": _to_list(kdj_d(high, low, close)),
        "kdj_j": _to_list(kdj_j(high, low, close)),
        "obv": _to_list(obv(close, volume)),
    }


def _to_list(arr: np.ndarray) -> list[float | None]:
    return [None if np.isnan(x) else float(x) for x in arr]


# --- Moving Averages ---

def sma(data: np.ndarray, period: int) -> np.ndarray:
    if len(data) < period:
        return np.full(len(data), np.nan)
    result = np.full(len(data), np.nan)
    result[period - 1:] = np.convolve(data, np.ones(period) / period, mode="valid")
    return result


def ema(data: np.ndarray, period: int) -> np.ndarray:
    result = np.full(len(data), np.nan)
    if len(data) < period:
        return result
    multiplier = 2 / (period + 1)
    result[period - 1] = np.mean(data[:period])
    for i in range(period, len(data)):
        result[i] = (data[i] - result[i - 1]) * multiplier + result[i - 1]
    return result


# --- MACD (12, 26, 9) ---

def macd_dif(close: np.ndarray, fast: int = 12, slow: int = 26) -> np.ndarray:
    return ema(close, fast) - ema(close, slow)


def macd_dea(close: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> np.ndarray:
    return ema(macd_dif(close, fast, slow), signal)


def macd_hist(close: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> np.ndarray:
    dif = macd_dif(close, fast, slow)
    dea = ema(dif, signal)
    return dif - dea


# --- RSI ---

def rsi(close: np.ndarray, period: int = 14) -> np.ndarray:
    delta = np.diff(close, prepend=close[0])
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = np.full(len(close), np.nan)
    avg_loss = np.full(len(close), np.nan)
    if len(close) <= period:
        return np.full(len(close), np.nan)

    avg_gain[period] = np.mean(gain[1:period + 1])
    avg_loss[period] = np.mean(loss[1:period + 1])
    for i in range(period + 1, len(close)):
        avg_gain[i] = (avg_gain[i - 1] * (period - 1) + gain[i]) / period
        avg_loss[i] = (avg_loss[i - 1] * (period - 1) + loss[i]) / period

    rs = avg_gain / np.where(avg_loss == 0, 1e-10, avg_loss)
    return 100 - (100 / (1 + rs))


# --- Bollinger Bands ---

def boll_upper(close: np.ndarray, period: int = 20, k: float = 2) -> np.ndarray:
    mid = sma(close, period)
    std = np.full(len(close), np.nan)
    for i in range(period - 1, len(close)):
        std[i] = np.std(close[i - period + 1:i + 1], ddof=0)
    return mid + k * std


def boll_lower(close: np.ndarray, period: int = 20, k: float = 2) -> np.ndarray:
    mid = sma(close, period)
    std = np.full(len(close), np.nan)
    for i in range(period - 1, len(close)):
        std[i] = np.std(close[i - period + 1:i + 1], ddof=0)
    return mid - k * std


# --- KDJ (9, 3, 3) ---

def _kdj_rsv(high: np.ndarray, low: np.ndarray, close: np.ndarray, n: int = 9) -> np.ndarray:
    rsv = np.full(len(close), np.nan)
    for i in range(n - 1, len(close)):
        h = np.max(high[i - n + 1:i + 1])
        l = np.min(low[i - n + 1:i + 1])
        rsv[i] = (close[i] - l) / (h - l) * 100 if h != l else 50
    return rsv


def kdj_k(high: np.ndarray, low: np.ndarray, close: np.ndarray, n: int = 9) -> np.ndarray:
    return sma(_kdj_rsv(high, low, close, n), 3)


def kdj_d(high: np.ndarray, low: np.ndarray, close: np.ndarray, n: int = 9) -> np.ndarray:
    return sma(kdj_k(high, low, close, n), 3)


def kdj_j(high: np.ndarray, low: np.ndarray, close: np.ndarray, n: int = 9) -> np.ndarray:
    k = kdj_k(high, low, close, n)
    d = kdj_d(high, low, close, n)
    return 3 * k - 2 * d


# --- OBV ---

def obv(close: np.ndarray, volume: np.ndarray) -> np.ndarray:
    result = np.zeros(len(close))
    result[0] = volume[0]
    for i in range(1, len(close)):
        if close[i] > close[i - 1]:
            result[i] = result[i - 1] + volume[i]
        elif close[i] < close[i - 1]:
            result[i] = result[i - 1] - volume[i]
        else:
            result[i] = result[i - 1]
    return result
