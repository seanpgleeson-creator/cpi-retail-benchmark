"""
Configuration settings for the CPI Retail Benchmark Platform
"""

from typing import List, Optional

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # BLS API Configuration
    bls_api_key: Optional[str] = Field(default=None)
    bls_base_url: str = Field(
        default="https://api.bls.gov/publicAPI/v2/timeseries/data/"
    )
    default_bls_series: List[str] = Field(default=["CUUR0000SEFJ01", "APU0000709112"])

    # Database Configuration
    database_url: str = Field(default="sqlite:///data/cpi_benchmark.db")

    # Scraping Configuration
    zip_code: str = Field(default="55331")
    headless: bool = Field(default=True)
    scrape_max_pages: int = Field(default=5)
    scrape_delay_range_ms: str = Field(default="500-1500")
    user_agent_rotation: bool = Field(default=True)
    requests_per_second: float = Field(default=0.5)
    max_retries: int = Field(default=3)

    # Logging Configuration
    log_level: str = Field(default="INFO")
    log_file: Optional[str] = Field(default="logs/app.log")

    # Development Configuration
    debug: bool = Field(default=False)
    environment: str = Field(default="development")

    # Security
    secret_key: str = Field(default="dev-secret-key")
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "https://localhost:3000"]
    )

    # Rate Limiting
    api_rate_limit: int = Field(default=100)
    api_rate_limit_window: int = Field(default=3600)

    # Cache Configuration
    redis_url: Optional[str] = Field(default=None)
    cache_ttl: int = Field(default=3600)

    model_config = ConfigDict(env_file=".env", case_sensitive=False, extra="ignore")


# Global settings instance
settings = Settings()
