"""
BLS API Client for fetching Consumer Price Index and economic data
"""

# Remove unused import
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings

from .exceptions import BLSAPIError, BLSConnectionError, BLSDataError, BLSRateLimitError

logger = logging.getLogger(__name__)


class BLSAPIClient:
    """
    Robust client for the Bureau of Labor Statistics Public Data API

    Features:
    - Automatic retry logic with exponential backoff
    - Rate limiting to respect BLS API limits
    - Response validation and error handling
    - Support for both registered and unregistered API access
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.bls.gov/publicAPI/v2/timeseries/data/",
        timeout: int = 30,
        max_retries: int = 3,
    ) -> None:
        """
        Initialize BLS API client

        Args:
            api_key: BLS API key (optional, increases rate limits)
            base_url: BLS API base URL
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.api_key = api_key or settings.bls_api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        # Rate limiting configuration
        if self.api_key:
            # Registered users: 500 queries per day, 25 per 10 seconds
            self.daily_limit = 500
            self.burst_limit = 25
            self.burst_window = 10
        else:
            # Unregistered users: 25 queries per day, 10 per 5 minutes
            self.daily_limit = 25
            self.burst_limit = 10
            self.burst_window = 300

        # Request tracking for rate limiting
        self._request_times: List[datetime] = []
        self._daily_requests = 0
        self._last_reset = datetime.now().date()

        # HTTP client configuration  
        self._session = requests.Session()
        self._session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "CPI-Retail-Benchmark/1.0",
        })
        self._session.timeout = timeout

    async def __aenter__(self) -> "BLSAPIClient":
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit"""
        self._session.close()

    def _check_rate_limits(self) -> None:
        """Check if we're within rate limits"""
        now = datetime.now()

        # Reset daily counter if it's a new day
        if now.date() > self._last_reset:
            self._daily_requests = 0
            self._last_reset = now.date()

        # Check daily limit
        if self._daily_requests >= self.daily_limit:
            raise BLSRateLimitError(
                f"Daily limit of {self.daily_limit} requests exceeded"
            )

        # Check burst limit
        cutoff_time = now - timedelta(seconds=self.burst_window)
        self._request_times = [
            req_time for req_time in self._request_times if req_time > cutoff_time
        ]

        if len(self._request_times) >= self.burst_limit:
            raise BLSRateLimitError(
                f"Burst limit of {self.burst_limit} requests per "
                f"{self.burst_window} seconds exceeded"
            )

    def _record_request(self) -> None:
        """Record a request for rate limiting purposes"""
        now = datetime.now()
        self._request_times.append(now)
        self._daily_requests += 1

    def _validate_series_ids(self, series_ids: List[str]) -> None:
        """Validate BLS series IDs format"""
        if not series_ids:
            raise BLSDataError("At least one series ID must be provided")

        if len(series_ids) > 50:
            raise BLSDataError("Maximum 50 series IDs allowed per request")

        for series_id in series_ids:
            if not isinstance(series_id, str) or len(series_id.strip()) == 0:
                raise BLSDataError(f"Invalid series ID: {series_id}")

    def _validate_years(self, start_year: int, end_year: int) -> None:
        """Validate year range"""
        current_year = datetime.now().year

        if start_year < 1913:  # BLS data starts from 1913
            raise BLSDataError("Start year cannot be before 1913")

        if end_year > current_year + 1:
            raise BLSDataError(f"End year cannot be after {current_year + 1}")

        if start_year > end_year:
            raise BLSDataError("Start year cannot be after end year")

        # API limits: 20 years for registered users, 10 for unregistered
        max_years = 20 if self.api_key else 10
        if (end_year - start_year + 1) > max_years:
            raise BLSDataError(
                f"Year range cannot exceed {max_years} years "
                f"({'registered' if self.api_key else 'unregistered'} user)"
            )

    @retry(
        retry=retry_if_exception_type((requests.RequestException, BLSConnectionError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    def _make_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make HTTP request to BLS API with retry logic

        Args:
            payload: Request payload

        Returns:
            API response data

        Raises:
            BLSAPIError: For API-related errors
            BLSConnectionError: For connection issues
            BLSRateLimitError: For rate limit violations
        """
        self._check_rate_limits()

        try:
            logger.info(
                f"Making BLS API request for {len(payload.get('seriesid', []))} series"
            )

            response = self._session.post(
                self.base_url,
                json=payload,
            )

            self._record_request()

            # Handle HTTP errors
            if response.status_code == 429:
                raise BLSRateLimitError("BLS API rate limit exceeded")
            elif response.status_code >= 400:
                raise BLSConnectionError(
                    f"HTTP {response.status_code}: {response.text}"
                )

            # Parse JSON response
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                raise BLSDataError(f"Invalid JSON response: {e}")

            # Validate BLS API response structure
            if not isinstance(data, dict):
                raise BLSDataError("Response is not a JSON object")

            if data.get("status") != "REQUEST_SUCCEEDED":
                error_msg = data.get("message", ["Unknown error"])
                if isinstance(error_msg, list):
                    error_msg = "; ".join(error_msg)
                raise BLSAPIError(f"BLS API error: {error_msg}")

            logger.info("BLS API request completed successfully")
            return data

        except requests.RequestException as e:
            logger.error(f"Connection error to BLS API: {e}")
            raise BLSConnectionError(f"Failed to connect to BLS API: {e}")
        except Exception as e:
            if isinstance(e, (BLSAPIError, BLSConnectionError, BLSRateLimitError)):
                raise
            logger.error(f"Unexpected error in BLS API request: {e}")
            raise BLSAPIError(f"Unexpected error: {e}")

    def fetch_series_data(
        self,
        series_ids: Union[str, List[str]],
        start_year: int,
        end_year: int,
        calculations: bool = True,
        annual_averages: bool = False,
    ) -> Dict[str, Any]:
        """
        Fetch time series data from BLS API

        Args:
            series_ids: BLS series ID(s) to fetch
            start_year: Starting year for data
            end_year: Ending year for data
            calculations: Include percent changes and net changes
            annual_averages: Include annual averages

        Returns:
            BLS API response with series data

        Example:
            >>> client = BLSAPIClient()
            >>> data = client.fetch_series_data(
            ...     ["CUUR0000SEFJ01"],  # CPI for milk
            ...     2020, 2023
            ... )
        """
        # Normalize series_ids to list
        if isinstance(series_ids, str):
            series_ids = [series_ids]

        # Validate inputs
        self._validate_series_ids(series_ids)
        self._validate_years(start_year, end_year)

        # Build request payload
        payload = {
            "seriesid": series_ids,
            "startyear": str(start_year),
            "endyear": str(end_year),
            "calculations": calculations,
            "annualaverage": annual_averages,
        }

        # Add API key if available
        if self.api_key:
            payload["registrationkey"] = self.api_key

        result = self._make_request(payload)
        return result  # type: ignore[no-any-return]

    def fetch_latest_data(
        self, series_ids: Union[str, List[str]], months: int = 12
    ) -> Dict[str, Any]:
        """
        Fetch the most recent data for given series

        Args:
            series_ids: BLS series ID(s) to fetch
            months: Number of recent months to fetch (default: 12)

        Returns:
            BLS API response with recent data
        """
        current_year = datetime.now().year
        start_year = current_year - 1 if months > 12 else current_year

        return self.fetch_series_data(
            series_ids=series_ids,
            start_year=start_year,
            end_year=current_year,
            calculations=True,
        )

    def get_series_info(self, series_id: str) -> Dict[str, Any]:
        """
        Get information about a specific BLS series

        Args:
            series_id: BLS series ID

        Returns:
            Series metadata and recent data
        """
        data = self.fetch_latest_data([series_id], months=6)

        if not data.get("Results", {}).get("series"):
            raise BLSDataError(f"No data found for series {series_id}")

        series_data = data["Results"]["series"][0]

        return {
            "series_id": series_data.get("seriesID"),
            "title": series_data.get("title", "Unknown"),
            "units": series_data.get("units", "Unknown"),
            "seasonal_adjustment": series_data.get("seasonalAdjustment", "Unknown"),
            "last_updated": datetime.now().isoformat(),
            "data_points": len(series_data.get("data", [])),
            "latest_value": (
                series_data["data"][0]["value"] if series_data.get("data") else None
            ),
            "latest_period": (
                f"{series_data['data'][0]['year']}-{series_data['data'][0]['period']}"
                if series_data.get("data")
                else None
            ),
        }

    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the BLS API

        Returns:
            Health status information
        """
        try:
            # Use a well-known series for health check
            test_series = "CUUR0000SA0"  # CPI-U All Items
            current_year = datetime.now().year

            start_time = datetime.now()
            self.fetch_series_data([test_series], current_year, current_year)
            response_time = (datetime.now() - start_time).total_seconds()

            return {
                "status": "healthy",
                "response_time_seconds": response_time,
                "api_key_configured": self.api_key is not None,
                "daily_requests_used": self._daily_requests,
                "daily_limit": self.daily_limit,
                "last_check": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "api_key_configured": self.api_key is not None,
                "last_check": datetime.now().isoformat(),
            }
