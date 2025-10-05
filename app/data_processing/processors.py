"""
BLS Data Processors

This module provides high-level processors for BLS data that orchestrate
calculations, transformations, and analysis workflows.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.bls_client import BLSAPIClient
from app.models.bls_models import BLSObservation, BLSSeries

from .calculations import BLSCalculator
from .validators import BLSDataValidator

logger = logging.getLogger(__name__)


class BLSDataProcessor:
    """
    High-level processor for BLS data analysis and transformation
    """

    def __init__(self, bls_client: Optional[BLSAPIClient] = None):
        """
        Initialize the BLS data processor

        Args:
            bls_client: Optional BLS API client instance
        """
        self.bls_client = bls_client or BLSAPIClient()
        self.calculator = BLSCalculator()
        self.validator = BLSDataValidator()

    def fetch_and_process_series(
        self,
        series_id: str,
        start_year: int,
        end_year: int,
        include_calculations: bool = True,
    ) -> Dict[str, Any]:
        """
        Fetch BLS series data and process it with calculations

        Args:
            series_id: BLS series identifier
            start_year: Starting year for data
            end_year: Ending year for data
            include_calculations: Whether to include MoM/YoY calculations

        Returns:
            Dictionary with processed series data and metadata
        """
        msg = f"Fetching and processing series {series_id} ({start_year}-{end_year})"
        logger.info(msg)

        try:
            # Fetch raw data from BLS API
            with self.bls_client as client:
                raw_data = client.fetch_series_data(
                    series_ids=[series_id],
                    start_year=start_year,
                    end_year=end_year,
                    calculations=include_calculations,
                )

            # Validate the response
            if not self.validator.validate_bls_response(raw_data):
                raise ValueError("Invalid BLS API response")

            # Extract series information
            series_info = raw_data["Results"]["series"][0]

            # Convert to BLS observation objects
            observations = []
            for data_point in series_info.get("data", []):
                obs = BLSObservation(
                    series_id=series_id,
                    year=int(data_point["year"]),
                    period=data_point["period"],
                    value=float(data_point["value"]),
                    footnotes=data_point.get("footnotes", ""),
                )

                # Add BLS-calculated fields if available
                if "calculations" in data_point:
                    calc = data_point["calculations"]
                    obs.net_change_1_month = calc.get("net_changes", {}).get("1")
                    obs.net_change_12_months = calc.get("net_changes", {}).get("12")
                    obs.pct_change_1_month = calc.get("pct_changes", {}).get("1")
                    obs.pct_change_12_months = calc.get("pct_changes", {}).get("12")

                observations.append(obs)

            # Process observations with our calculations if BLS didn't provide them
            if include_calculations:
                observations = self.calculator.process_observation_series(observations)

            # Create series metadata
            series_metadata = BLSSeries(
                series_id=series_id,
                title=series_info.get("title", "Unknown"),
                units=series_info.get("units", "Unknown"),
                seasonal_adjustment=series_info.get("seasonalAdjustment", "Unknown"),
                area=series_info.get("area", {}).get("areaName"),
                item=series_info.get("item", {}).get("itemName"),
            )

            # Calculate additional analytics
            analytics = self._calculate_series_analytics(observations)

            return {
                "series_metadata": series_metadata,
                "observations": observations,
                "analytics": analytics,
                "data_quality": self.validator.assess_data_quality(observations),
                "processing_timestamp": datetime.now().isoformat(),
                "total_observations": len(observations),
            }

        except Exception as e:
            logger.error(f"Error processing series {series_id}: {e}")
            raise

    def _calculate_series_analytics(
        self, observations: List[BLSObservation]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive analytics for a series

        Args:
            observations: List of BLS observations

        Returns:
            Dictionary with analytics results
        """
        if not observations:
            return {}

        values = [obs.value for obs in observations]

        analytics = {
            "summary_statistics": {
                "count": len(values),
                "mean": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "range": max(values) - min(values),
                "latest_value": observations[-1].value if observations else None,
                "latest_period": f"{observations[-1].year}-{observations[-1].period}"
                if observations
                else None,
            }
        }

        # Calculate volatility if we have enough data
        if len(values) >= 2:
            analytics["volatility"] = self.calculator.calculate_volatility(values)

        # Calculate CAGR if we have data spanning multiple years
        if len(observations) >= 2:
            first_obs = observations[0]
            last_obs = observations[-1]
            years_span = last_obs.year - first_obs.year

            if years_span > 0:
                try:
                    cagr = self.calculator.calculate_compound_annual_growth_rate(
                        first_obs.value, last_obs.value, years_span
                    )
                    analytics["cagr_percent"] = cagr
                except ValueError:
                    pass

        # Calculate moving averages if we have enough data
        if len(values) >= 12:  # At least 12 months for annual moving average
            try:
                ma_12 = self.calculator.calculate_moving_average(values, 12)
                analytics["moving_average_12_months"] = ma_12[-1] if ma_12 else None
            except ValueError:
                pass

        # Detect seasonal patterns
        seasonal_patterns = self.calculator.detect_seasonal_patterns(observations)
        if seasonal_patterns:
            analytics["seasonal_patterns"] = seasonal_patterns

        # Calculate recent trends (last 12 months if available)
        recent_obs = [
            obs for obs in observations if obs.year >= datetime.now().year - 1
        ]
        if len(recent_obs) >= 2:
            recent_values = [obs.value for obs in recent_obs]
            analytics["recent_trend"] = {
                "observations": len(recent_obs),
                "change_from_start": recent_obs[-1].value - recent_obs[0].value,
                "percent_change": (
                    (recent_obs[-1].value - recent_obs[0].value) / recent_obs[0].value
                )
                * 100,
                "volatility": self.calculator.calculate_volatility(recent_values),
            }

        return analytics

    def compare_series(
        self,
        series_ids: List[str],
        start_year: int,
        end_year: int,
        rebase_to_common_period: bool = True,
    ) -> Dict[str, Any]:
        """
        Compare multiple BLS series

        Args:
            series_ids: List of BLS series identifiers
            start_year: Starting year for comparison
            end_year: Ending year for comparison
            rebase_to_common_period: Whether to rebase all series to a common base period

        Returns:
            Dictionary with comparison results
        """
        msg = f"Comparing {len(series_ids)} series: {series_ids}"
        logger.info(msg)

        series_data = {}

        # Fetch and process each series
        for series_id in series_ids:
            try:
                processed_data = self.fetch_and_process_series(
                    series_id, start_year, end_year
                )
                series_data[series_id] = processed_data
            except Exception as e:
                logger.error(f"Failed to process series {series_id}: {e}")
                continue

        if not series_data:
            raise ValueError("No series data could be processed")

        # Perform comparison analysis
        comparison_results = {
            "series_count": len(series_data),
            "comparison_period": f"{start_year}-{end_year}",
            "series_data": series_data,
            "cross_series_analysis": self._perform_cross_series_analysis(series_data),
        }

        # Rebase series if requested
        if rebase_to_common_period and len(series_data) > 1:
            rebased_data = self._rebase_series_to_common_period(series_data)
            comparison_results["rebased_data"] = rebased_data

        return comparison_results

    def _perform_cross_series_analysis(
        self, series_data: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Perform cross-series analysis and correlation

        Args:
            series_data: Dictionary of series data

        Returns:
            Cross-series analysis results
        """
        analysis = {
            "correlation_matrix": {},
            "relative_performance": {},
            "summary_comparison": {},
        }

        series_ids = list(series_data.keys())

        # Calculate summary statistics for comparison
        for series_id, data in series_data.items():
            if data["observations"]:
                latest_obs = data["observations"][-1]
                analysis["summary_comparison"][series_id] = {
                    "latest_value": latest_obs.value,
                    "latest_period": f"{latest_obs.year}-{latest_obs.period}",
                    "total_observations": len(data["observations"]),
                    "mean_value": data["analytics"]["summary_statistics"]["mean"],
                    "volatility": data["analytics"].get("volatility"),
                    "cagr": data["analytics"].get("cagr_percent"),
                }

        # Calculate simple correlation between series (if we have multiple)
        if len(series_ids) >= 2:
            for i, series_a in enumerate(series_ids):
                for series_b in series_ids[i + 1 :]:
                    correlation = self._calculate_simple_correlation(
                        series_data[series_a]["observations"],
                        series_data[series_b]["observations"],
                    )
                    analysis["correlation_matrix"][
                        f"{series_a}_vs_{series_b}"
                    ] = correlation

        return analysis

    def _calculate_simple_correlation(
        self, obs_a: List[BLSObservation], obs_b: List[BLSObservation]
    ) -> Optional[float]:
        """
        Calculate simple correlation between two observation series

        Args:
            obs_a: First series observations
            obs_b: Second series observations

        Returns:
            Correlation coefficient or None if calculation fails
        """
        try:
            # Find matching periods
            values_a = []
            values_b = []

            for obs_a_item in obs_a:
                for obs_b_item in obs_b:
                    if (
                        obs_a_item.year == obs_b_item.year
                        and obs_a_item.period == obs_b_item.period
                    ):
                        values_a.append(obs_a_item.value)
                        values_b.append(obs_b_item.value)
                        break

            if len(values_a) < 2:
                return None

            # Calculate Pearson correlation coefficient
            n = len(values_a)
            sum_a = sum(values_a)
            sum_b = sum(values_b)
            sum_a_sq = sum(x * x for x in values_a)
            sum_b_sq = sum(x * x for x in values_b)
            sum_ab = sum(a * b for a, b in zip(values_a, values_b))

            numerator = n * sum_ab - sum_a * sum_b
            denominator = (
                (n * sum_a_sq - sum_a * sum_a) * (n * sum_b_sq - sum_b * sum_b)
            ) ** 0.5

            if denominator == 0:
                return None

            correlation = numerator / denominator
            return correlation

        except Exception as e:
            logger.warning(f"Could not calculate correlation: {e}")
            return None

    def _rebase_series_to_common_period(
        self, series_data: Dict[str, Dict[str, Any]]
    ) -> Dict[str, List[float]]:
        """
        Rebase all series to a common base period for comparison

        Args:
            series_data: Dictionary of series data

        Returns:
            Dictionary of rebased series values
        """
        rebased_data = {}

        for series_id, data in series_data.items():
            observations = data["observations"]
            if observations:
                values = [obs.value for obs in observations]
                try:
                    # Rebase to first period = 100
                    rebased_values = self.calculator.rebase_index(values, 0, 100.0)
                    rebased_data[series_id] = rebased_values
                except ValueError as e:
                    logger.warning(f"Could not rebase series {series_id}: {e}")

        return rebased_data
