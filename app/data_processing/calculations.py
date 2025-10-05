"""
BLS Data Calculations

This module provides functions for calculating various metrics from BLS CPI data,
including month-over-month changes, year-over-year changes, and rebased indices.
"""

import logging
from typing import Dict, List, Tuple

from app.models.bls_models import BLSObservation

logger = logging.getLogger(__name__)


class BLSCalculator:
    """
    Calculator for BLS CPI data metrics and transformations
    """

    @staticmethod
    def calculate_mom_change(
        current_value: float, previous_value: float
    ) -> Tuple[float, float]:
        """
        Calculate month-over-month change (both net and percentage)

        Args:
            current_value: Current period value
            previous_value: Previous period value

        Returns:
            Tuple of (net_change, percent_change)
        """
        if previous_value == 0:
            raise ValueError("Previous value cannot be zero for percentage calculation")

        net_change = current_value - previous_value
        percent_change = (net_change / previous_value) * 100

        return net_change, percent_change

    @staticmethod
    def calculate_yoy_change(
        current_value: float, year_ago_value: float
    ) -> Tuple[float, float]:
        """
        Calculate year-over-year change (both net and percentage)

        Args:
            current_value: Current period value
            year_ago_value: Same period one year ago value

        Returns:
            Tuple of (net_change, percent_change)
        """
        if year_ago_value == 0:
            raise ValueError("Year ago value cannot be zero for percentage calculation")

        net_change = current_value - year_ago_value
        percent_change = (net_change / year_ago_value) * 100

        return net_change, percent_change

    @staticmethod
    def rebase_index(
        values: List[float], base_period_index: int = 0, new_base_value: float = 100.0
    ) -> List[float]:
        """
        Rebase a series of index values to a new base period

        Args:
            values: List of index values
            base_period_index: Index of the period to use as new base (default: 0)
            new_base_value: New base value (default: 100.0)

        Returns:
            List of rebased index values
        """
        if not values or base_period_index >= len(values):
            raise ValueError("Invalid base period index or empty values list")

        base_value = values[base_period_index]
        if base_value == 0:
            raise ValueError("Base period value cannot be zero")

        rebased_values = []
        for value in values:
            rebased_value = (value / base_value) * new_base_value
            rebased_values.append(rebased_value)

        return rebased_values

    @staticmethod
    def calculate_compound_annual_growth_rate(
        start_value: float, end_value: float, years: float
    ) -> float:
        """
        Calculate Compound Annual Growth Rate (CAGR)

        Args:
            start_value: Starting value
            end_value: Ending value
            years: Number of years between start and end

        Returns:
            CAGR as a percentage
        """
        if start_value <= 0 or end_value <= 0:
            raise ValueError("Values must be positive for CAGR calculation")
        if years <= 0:
            raise ValueError("Years must be positive")

        cagr = ((end_value / start_value) ** (1 / years) - 1) * 100
        return cagr

    @staticmethod
    def calculate_moving_average(values: List[float], window_size: int) -> List[float]:
        """
        Calculate moving average for a series of values

        Args:
            values: List of values
            window_size: Size of the moving window

        Returns:
            List of moving averages (shorter than input by window_size - 1)
        """
        if window_size <= 0:
            raise ValueError("Window size must be positive")
        if len(values) < window_size:
            raise ValueError("Not enough values for the specified window size")

        moving_averages = []
        for i in range(len(values) - window_size + 1):
            window_values = values[i : i + window_size]
            avg = sum(window_values) / window_size
            moving_averages.append(avg)

        return moving_averages

    @staticmethod
    def calculate_volatility(values: List[float]) -> float:
        """
        Calculate volatility (standard deviation) of a series

        Args:
            values: List of values

        Returns:
            Standard deviation of the values
        """
        if len(values) < 2:
            raise ValueError("Need at least 2 values to calculate volatility")

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        volatility = variance**0.5

        return volatility

    @classmethod
    def process_observation_series(
        cls, observations: List[BLSObservation]
    ) -> List[BLSObservation]:
        """
        Process a series of BLS observations to add calculated fields

        Args:
            observations: List of BLS observations (should be sorted by date)

        Returns:
            List of observations with calculated fields populated
        """
        if not observations:
            return observations

        # Sort observations by year and period to ensure correct order
        sorted_obs = sorted(observations, key=lambda x: (x.year, x.period))
        processed_obs = []

        for i, obs in enumerate(sorted_obs):
            # Create a copy to avoid modifying the original
            processed_obs.append(
                BLSObservation(
                    series_id=obs.series_id,
                    year=obs.year,
                    period=obs.period,
                    value=obs.value,
                    footnotes=obs.footnotes,
                    created_at=obs.created_at,
                    updated_at=obs.updated_at,
                )
            )

            current_obs = processed_obs[i]

            # Calculate month-over-month changes
            if i > 0:
                prev_obs = sorted_obs[i - 1]
                try:
                    net_change, pct_change = cls.calculate_mom_change(
                        obs.value, prev_obs.value
                    )
                    current_obs.net_change_1_month = net_change
                    current_obs.pct_change_1_month = pct_change
                except ValueError as e:
                    logger.warning(f"Could not calculate MoM change: {e}")

            # Calculate year-over-year changes
            # Look for observation from same period one year ago
            year_ago_obs = None
            for j in range(i):
                if (
                    sorted_obs[j].year == obs.year - 1
                    and sorted_obs[j].period == obs.period
                ):
                    year_ago_obs = sorted_obs[j]
                    break

            if year_ago_obs:
                try:
                    net_change, pct_change = cls.calculate_yoy_change(
                        obs.value, year_ago_obs.value
                    )
                    current_obs.net_change_12_months = net_change
                    current_obs.pct_change_12_months = pct_change
                except ValueError as e:
                    logger.warning(f"Could not calculate YoY change: {e}")

        return processed_obs

    @staticmethod
    def detect_seasonal_patterns(
        observations: List[BLSObservation],
    ) -> Dict[str, float]:
        """
        Detect seasonal patterns in BLS data

        Args:
            observations: List of BLS observations

        Returns:
            Dictionary with seasonal statistics by month/period
        """
        if not observations:
            return {}

        # Group observations by period (month)
        period_groups: Dict[str, List[float]] = {}

        for obs in observations:
            if obs.is_monthly:
                period = obs.period
                if period not in period_groups:
                    period_groups[period] = []
                period_groups[period].append(obs.value)

        # Calculate statistics for each period
        seasonal_stats = {}
        for period, values in period_groups.items():
            if len(values) > 1:
                mean_value = sum(values) / len(values)
                seasonal_stats[period] = {
                    "mean": mean_value,
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "volatility": BLSCalculator.calculate_volatility(values),
                }

        return seasonal_stats
