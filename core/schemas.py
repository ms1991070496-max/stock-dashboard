from datetime import date, datetime
from pydantic import BaseModel, Field


class StockInfo(BaseModel):
    code: str
    name: str
    market: str
    sector: str = ""
    industry: str = ""


class KLineItem(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    amount: float = 0.0
    turnover_rate: float = 0.0


class QuoteItem(BaseModel):
    code: str
    name: str
    price: float
    change_pct: float
    change_amount: float = 0.0
    volume: int = 0
    high: float = 0.0
    low: float = 0.0
    open: float = 0.0
    pre_close: float = 0.0
    updated_at: datetime | None = None


class IndicatorResult(BaseModel):
    code: str
    name: str
    klines: list[KLineItem]
    ma5: list[float | None] = []
    ma10: list[float | None] = []
    ma20: list[float | None] = []
    ma60: list[float | None] = []
    macd_dif: list[float | None] = []
    macd_dea: list[float | None] = []
    macd_hist: list[float | None] = []
    rsi6: list[float | None] = []
    rsi14: list[float | None] = []
    rsi24: list[float | None] = []
    boll_upper: list[float | None] = []
    boll_mid: list[float | None] = []
    boll_lower: list[float | None] = []
    kdj_k: list[float | None] = []
    kdj_d: list[float | None] = []
    kdj_j: list[float | None] = []
    obv: list[float | None] = []


class FinancialItem(BaseModel):
    period: str
    revenue: float
    net_profit: float
    eps: float
    bvps: float
    roe: float
    gross_margin: float
    net_margin: float
    debt_ratio: float


class NewsItem(BaseModel):
    title: str
    source: str = ""
    url: str = ""
    published_at: datetime | None = None
    sentiment_score: float = 0.0


class ScreenerCondition(BaseModel):
    field: str
    operator: str  # gt, lt, gte, lte, eq, between
    value: float | str


class ScreenerResult(BaseModel):
    code: str
    name: str
    market: str
    price: float
    change_pct: float
    pe: float | None = None
    pb: float | None = None
    market_cap: float | None = None
    roe: float | None = None
    rsi14: float | None = None
    match_score: int = 0
