from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Paths
    data_dir: Path = Path("data")

    # Database
    database_url: str = "sqlite:///data/stock.db"

    # Cache TTL in seconds
    cache_ttl_quote: int = 900
    cache_ttl_kline: int = 86400
    cache_ttl_financial: int = 604800
    cache_ttl_news: int = 1800

    # API keys (optional for Phase 1)
    alpha_vantage_key: str = ""
    polygon_api_key: str = ""
    newsapi_key: str = ""

    # Scheduler
    scheduler_enabled: bool = True

    @property
    def db_path(self) -> Path:
        return self.data_dir / "stock.db"

    @property
    def cache_dir(self) -> Path:
        return self.data_dir / "cache"


settings = Settings()
