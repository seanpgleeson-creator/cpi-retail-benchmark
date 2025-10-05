"""
Configuration settings for the CPI Retail Benchmark Platform
"""

from typing import List, Optional

# Removed pydantic imports to avoid pydantic-settings dependency issues


class Settings:
    """Simple application settings without pydantic-settings dependency"""

    def __init__(self) -> None:
        # BLS API Configuration
        self.bls_api_key: Optional[str] = None
        self.bls_base_url: str = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
        self.default_bls_series: List[str] = ["CUUR0000SEFJ01", "APU0000709112"]

        # Database Configuration
        self.database_url: str = "sqlite:///data/cpi_benchmark.db"

        # Scraping Configuration
        self.zip_code: str = "55331"
        self.headless: bool = True
        self.scrape_max_pages: int = 5
        self.scrape_delay_range_ms: str = "500-1500"
        self.user_agent_rotation: bool = True
        self.requests_per_second: float = 0.5
        self.max_retries: int = 3

        # Logging Configuration
        self.log_level: str = "INFO"
        self.log_file: Optional[str] = "logs/app.log"

        # Development Configuration
        self.debug: bool = False
        self.environment: str = "development"

        # Security
        self.secret_key: str = "dev-secret-key"
        self.cors_origins: List[str] = [
            "http://localhost:3000",
            "https://localhost:3000",
        ]

        # Rate Limiting
        self.api_rate_limit: int = 100
        self.api_rate_limit_window: int = 3600

        # Cache Configuration
        self.redis_url: Optional[str] = None
        self.cache_ttl: int = 3600


# Global settings instance
settings = Settings()
