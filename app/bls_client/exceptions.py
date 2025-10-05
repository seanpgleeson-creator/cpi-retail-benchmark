"""
Custom exceptions for BLS API client
"""

from typing import Optional


class BLSAPIError(Exception):
    """Base exception for BLS API related errors"""

    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class BLSRateLimitError(BLSAPIError):
    """Raised when BLS API rate limit is exceeded"""

    def __init__(self, message: str = "BLS API rate limit exceeded") -> None:
        super().__init__(message, status_code=429)


class BLSDataError(BLSAPIError):
    """Raised when BLS API returns invalid or unexpected data"""

    def __init__(self, message: str = "Invalid data received from BLS API") -> None:
        super().__init__(message, status_code=422)


class BLSConnectionError(BLSAPIError):
    """Raised when unable to connect to BLS API"""

    def __init__(self, message: str = "Unable to connect to BLS API") -> None:
        super().__init__(message, status_code=503)
