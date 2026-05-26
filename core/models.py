from datetime import date, datetime
from sqlalchemy import (
    Column, String, Float, Integer, Date, DateTime, BigInteger, Text, Index, UniqueConstraint
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)
    market = Column(String(10), nullable=False)  # cn, us, hk
    sector = Column(String(50), default="")
    industry = Column(String(50), default="")
    list_date = Column(Date, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Stock(code={self.code}, name={self.name}, market={self.market})>"


class KLine(Base):
    __tablename__ = "klines"
    __table_args__ = (
        UniqueConstraint("stock_id", "date", name="uq_kline_stock_date"),
        Index("idx_kline_stock_date", "stock_id", "date"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, nullable=False, index=True)
    date = Column(Date, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False)
    amount = Column(Float, default=0.0)
    turnover_rate = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<KLine(stock_id={self.stock_id}, date={self.date}, close={self.close})>"


class RealtimeQuote(Base):
    __tablename__ = "realtime_quotes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, nullable=False, unique=True, index=True)
    price = Column(Float, nullable=False)
    change_pct = Column(Float, default=0.0)
    change_amount = Column(Float, default=0.0)
    volume = Column(BigInteger, default=0)
    high = Column(Float, default=0.0)
    low = Column(Float, default=0.0)
    open = Column(Float, default=0.0)
    pre_close = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FinancialReport(Base):
    __tablename__ = "financial_reports"
    __table_args__ = (
        UniqueConstraint("stock_id", "period", "report_type", name="uq_financial_stock_period_type"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, nullable=False, index=True)
    period = Column(String(20), nullable=False)  # e.g. "2025Q4", "2025FY"
    report_type = Column(String(20), default="annual")  # annual, quarterly
    revenue = Column(Float, default=0.0)
    net_profit = Column(Float, default=0.0)
    eps = Column(Float, default=0.0)
    bvps = Column(Float, default=0.0)
    roe = Column(Float, default=0.0)
    total_assets = Column(Float, default=0.0)
    total_liabilities = Column(Float, default=0.0)
    operating_cash_flow = Column(Float, default=0.0)
    gross_margin = Column(Float, default=0.0)
    net_margin = Column(Float, default=0.0)
    debt_ratio = Column(Float, default=0.0)
    current_ratio = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)


class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, nullable=True, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, default="")
    source = Column(String(100), default="")
    url = Column(String(500), default="")
    published_at = Column(DateTime, nullable=True)
    sentiment_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)


class Watchlist(Base):
    __tablename__ = "watchlist"
    __table_args__ = (
        UniqueConstraint("stock_id", name="uq_watchlist_stock"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, nullable=False, index=True)
    added_at = Column(DateTime, default=datetime.utcnow)
    note = Column(String(200), default="")
