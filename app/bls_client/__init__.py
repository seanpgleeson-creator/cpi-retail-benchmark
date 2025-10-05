"""
BLS (Bureau of Labor Statistics) API client module

This module provides functionality to interact with the BLS Public Data API
to fetch Consumer Price Index (CPI) and other economic data.
"""

from .client import BLSAPIClient
from .exceptions import BLSAPIError, BLSDataError, BLSRateLimitError

__all__ = ["BLSAPIClient", "BLSAPIError", "BLSRateLimitError", "BLSDataError"]
