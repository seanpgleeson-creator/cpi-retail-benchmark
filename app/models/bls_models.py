"""
Data models for BLS (Bureau of Labor Statistics) data
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class BLSSeries:
    """Represents a BLS time series"""

    series_id: str
    title: str
    units: str
    seasonal_adjustment: str
    area: Optional[str] = None
    item: Optional[str] = None
    base_period: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


@dataclass
class BLSObservation:
    """Represents a single BLS data observation"""

    series_id: str
    year: int
    period: str  # M01-M12 for months, A01 for annual
    value: float
    footnotes: Optional[str] = None

    # Calculated fields (if available)
    net_change_1_month: Optional[float] = None
    net_change_12_months: Optional[float] = None
    pct_change_1_month: Optional[float] = None
    pct_change_12_months: Optional[float] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    @property
    def date_string(self) -> str:
        """Get a human-readable date string"""
        if self.period == "A01":
            return str(self.year)
        elif self.period.startswith("M"):
            month = int(self.period[1:])
            return f"{self.year}-{month:02d}"
        else:
            return f"{self.year}-{self.period}"

    @property
    def is_monthly(self) -> bool:
        """Check if this is monthly data"""
        return self.period.startswith("M")

    @property
    def is_annual(self) -> bool:
        """Check if this is annual data"""
        return self.period == "A01"

    @property
    def month_number(self) -> Optional[int]:
        """Get the month number (1-12) if this is monthly data"""
        if self.is_monthly:
            return int(self.period[1:])
        return None
