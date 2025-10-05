"""
BLS Data Validators

This module provides validation functions for BLS data quality,
completeness, and consistency checks.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from app.models.bls_models import BLSObservation

logger = logging.getLogger(__name__)


class BLSDataValidator:
    """
    Validator for BLS data quality and consistency
    """

    @staticmethod
    def validate_bls_response(response: Dict[str, Any]) -> bool:
        """
        Validate the structure of a BLS API response

        Args:
            response: Raw BLS API response

        Returns:
            True if response is valid, False otherwise
        """
        try:
            # Check basic response structure
            if not isinstance(response, dict):
                logger.error("Response is not a dictionary")
                return False

            if response.get("status") != "REQUEST_SUCCEEDED":
                msg = response.get("message", "Unknown error")
                logger.error(f"BLS API request failed: {msg}")
                return False

            # Check for Results section
            if "Results" not in response:
                logger.error("No Results section in response")
                return False

            results = response["Results"]
            if "series" not in results:
                logger.error("No series data in Results")
                return False

            # Validate series structure
            series_list = results["series"]
            if not isinstance(series_list, list) or len(series_list) == 0:
                logger.error("Series data is empty or not a list")
                return False

            # Check first series has required fields
            first_series = series_list[0]
            required_fields = ["seriesID", "data"]
            for field in required_fields:
                if field not in first_series:
                    logger.error(f"Missing required field: {field}")
                    return False

            # Validate data points structure
            data_points = first_series["data"]
            if not isinstance(data_points, list):
                logger.error("Data points is not a list")
                return False

            # Check at least one data point has required fields
            if data_points:
                first_point = data_points[0]
                required_data_fields = ["year", "period", "value"]
                for field in required_data_fields:
                    if field not in first_point:
                        logger.error(f"Missing required data field: {field}")
                        return False

            return True

        except Exception as e:
            logger.error(f"Error validating BLS response: {e}")
            return False

    @staticmethod
    def validate_observation(observation: BLSObservation) -> List[str]:
        """
        Validate a single BLS observation

        Args:
            observation: BLS observation to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Validate series ID
        if not observation.series_id or not observation.series_id.strip():
            errors.append("Series ID is empty")

        # Validate year
        current_year = datetime.now().year
        if observation.year < 1913:  # BLS data starts from 1913
            errors.append(f"Year {observation.year} is before BLS data availability (1913)")
        elif observation.year > current_year + 1:
            errors.append(f"Year {observation.year} is in the future")

        # Validate period
        if not observation.period:
            errors.append("Period is empty")
        elif observation.is_monthly:
            try:
                month_num = observation.month_number
                if month_num is None or month_num < 1 or month_num > 12:
                    errors.append(f"Invalid month number: {month_num}")
            except Exception:
                errors.append(f"Invalid monthly period format: {observation.period}")

        # Validate value
        if observation.value is None:
            errors.append("Value is None")
        elif observation.value < 0:
            errors.append(f"Negative value: {observation.value}")
        elif observation.value == 0:
            errors.append("Value is zero (unusual for CPI data)")

        # Validate calculated fields if present
        if observation.pct_change_1_month is not None:
            if abs(observation.pct_change_1_month) > 50:  # Sanity check
                errors.append(f"Extreme 1-month change: {observation.pct_change_1_month}%")

        if observation.pct_change_12_months is not None:
            if abs(observation.pct_change_12_months) > 100:  # Sanity check
                errors.append(f"Extreme 12-month change: {observation.pct_change_12_months}%")

        return errors

    @classmethod
    def assess_data_quality(
        cls, observations: List[BLSObservation]
    ) -> Dict[str, Any]:
        """
        Assess the overall quality of a series of observations

        Args:
            observations: List of BLS observations

        Returns:
            Dictionary with data quality assessment
        """
        if not observations:
            return {
                "overall_quality": "POOR",
                "issues": ["No observations provided"],
                "statistics": {},
            }

        quality_report = {
            "total_observations": len(observations),
            "validation_errors": [],
            "warnings": [],
            "statistics": {},
            "completeness": {},
            "consistency": {},
        }

        # Validate each observation
        total_errors = 0
        for i, obs in enumerate(observations):
            errors = cls.validate_observation(obs)
            if errors:
                total_errors += len(errors)
                quality_report["validation_errors"].extend(
                    [f"Observation {i}: {error}" for error in errors]
                )

        # Check data completeness
        quality_report["completeness"] = cls._assess_completeness(observations)

        # Check data consistency
        quality_report["consistency"] = cls._assess_consistency(observations)

        # Calculate quality statistics
        quality_report["statistics"] = {
            "error_rate": total_errors / len(observations) if observations else 0,
            "observations_with_errors": sum(
                1 for obs in observations if cls.validate_observation(obs)
            ),
            "date_range": cls._get_date_range(observations) if observations else None,
        }

        # Determine overall quality score
        error_rate = quality_report["statistics"]["error_rate"]
        completeness_score = quality_report["completeness"].get("score", 0)
        consistency_score = quality_report["consistency"].get("score", 0)

        overall_score = (completeness_score + consistency_score) / 2 * (1 - error_rate)

        if overall_score >= 0.9:
            quality_report["overall_quality"] = "EXCELLENT"
        elif overall_score >= 0.7:
            quality_report["overall_quality"] = "GOOD"
        elif overall_score >= 0.5:
            quality_report["overall_quality"] = "FAIR"
        else:
            quality_report["overall_quality"] = "POOR"

        quality_report["overall_score"] = overall_score

        return quality_report

    @staticmethod
    def _assess_completeness(observations: List[BLSObservation]) -> Dict[str, Any]:
        """
        Assess data completeness

        Args:
            observations: List of BLS observations

        Returns:
            Completeness assessment
        """
        if not observations:
            return {"score": 0, "issues": ["No data"]}

        completeness = {
            "total_observations": len(observations),
            "missing_values": 0,
            "missing_periods": [],
            "issues": [],
        }

        # Check for missing values
        for obs in observations:
            if obs.value is None:
                completeness["missing_values"] += 1

        # Check for gaps in time series (for monthly data)
        monthly_obs = [obs for obs in observations if obs.is_monthly]
        if len(monthly_obs) > 1:
            # Sort by year and month
            sorted_obs = sorted(
                monthly_obs, key=lambda x: (x.year, x.month_number or 0)
            )

            # Check for gaps
            for i in range(1, len(sorted_obs)):
                prev_obs = sorted_obs[i - 1]
                curr_obs = sorted_obs[i]

                # Calculate expected next period
                expected_year = prev_obs.year
                expected_month = (prev_obs.month_number or 0) + 1

                if expected_month > 12:
                    expected_month = 1
                    expected_year += 1

                # Check if current observation matches expected
                if (
                    curr_obs.year != expected_year
                    or curr_obs.month_number != expected_month
                ):
                    completeness["missing_periods"].append(
                        f"{expected_year}-{expected_month:02d}"
                    )

        # Calculate completeness score
        missing_rate = completeness["missing_values"] / len(observations)
        gap_penalty = min(len(completeness["missing_periods"]) * 0.1, 0.5)
        completeness["score"] = max(0, 1 - missing_rate - gap_penalty)

        # Add issues
        if completeness["missing_values"] > 0:
            completeness["issues"].append(
                f"{completeness['missing_values']} missing values"
            )

        if completeness["missing_periods"]:
            completeness["issues"].append(
                f"{len(completeness['missing_periods'])} missing periods"
            )

        return completeness

    @staticmethod
    def _assess_consistency(observations: List[BLSObservation]) -> Dict[str, Any]:
        """
        Assess data consistency

        Args:
            observations: List of BLS observations

        Returns:
            Consistency assessment
        """
        if len(observations) < 2:
            return {"score": 1.0, "issues": []}

        consistency = {"outliers": [], "extreme_changes": [], "issues": []}

        values = [obs.value for obs in observations if obs.value is not None]

        if len(values) < 2:
            return {"score": 0, "issues": ["Insufficient valid values"]}

        # Calculate basic statistics
        mean_value = sum(values) / len(values)

        # Simple outlier detection (values more than 3 standard deviations from mean)
        if len(values) >= 3:
            variance = sum((x - mean_value) ** 2 for x in values) / (len(values) - 1)
            std_dev = variance**0.5

            for i, obs in enumerate(observations):
                if obs.value is not None:
                    z_score = (
                        abs(obs.value - mean_value) / std_dev if std_dev > 0 else 0
                    )
                    if z_score > 3:
                        consistency["outliers"].append(
                            {
                                "index": i,
                                "period": f"{obs.year}-{obs.period}",
                                "value": obs.value,
                                "z_score": z_score,
                            }
                        )

        # Check for extreme period-to-period changes
        for i in range(1, len(observations)):
            prev_obs = observations[i - 1]
            curr_obs = observations[i]

            if prev_obs.value is not None and curr_obs.value is not None:
                if prev_obs.value > 0:  # Avoid division by zero
                    pct_change = (
                        abs((curr_obs.value - prev_obs.value) / prev_obs.value) * 100
                    )
                    if pct_change > 20:  # More than 20% change
                        consistency["extreme_changes"].append(
                            {
                                "from_period": f"{prev_obs.year}-{prev_obs.period}",
                                "to_period": f"{curr_obs.year}-{curr_obs.period}",
                                "change_percent": pct_change,
                            }
                        )

        # Calculate consistency score
        outlier_penalty = min(len(consistency["outliers"]) * 0.1, 0.4)
        extreme_change_penalty = min(len(consistency["extreme_changes"]) * 0.05, 0.3)
        consistency["score"] = max(0, 1 - outlier_penalty - extreme_change_penalty)

        # Add issues
        if consistency["outliers"]:
            consistency["issues"].append(
                f"{len(consistency['outliers'])} statistical outliers detected"
            )

        if consistency["extreme_changes"]:
            consistency["issues"].append(
                f"{len(consistency['extreme_changes'])} extreme period changes detected"
            )

        return consistency

    @staticmethod
    def _get_date_range(observations: List[BLSObservation]) -> Dict[str, str]:
        """Helper method to get date range from observations"""
        if not observations:
            return {}

        min_year = min(obs.year for obs in observations)
        max_year = max(obs.year for obs in observations)

        start_period = min(obs.period for obs in observations if obs.year == min_year)
        end_period = max(obs.period for obs in observations if obs.year == max_year)

        return {
            "start": f"{min_year}-{start_period}",
            "end": f"{max_year}-{end_period}",
        }