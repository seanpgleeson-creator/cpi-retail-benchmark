"""
Tests for BLS data processing functionality
"""

import pytest

from app.data_processing.calculations import BLSCalculator
from app.data_processing.validators import BLSDataValidator
from app.models.bls_models import BLSObservation


class TestBLSCalculator:
    """Test BLS calculation functions"""

    def test_calculate_mom_change(self):
        """Test month-over-month change calculation"""
        calculator = BLSCalculator()

        # Test normal case
        net, pct = calculator.calculate_mom_change(105.0, 100.0)
        assert net == 5.0
        assert pct == 5.0

        # Test negative change
        net, pct = calculator.calculate_mom_change(95.0, 100.0)
        assert net == -5.0
        assert pct == -5.0

        # Test zero previous value (should raise error)
        with pytest.raises(ValueError):
            calculator.calculate_mom_change(105.0, 0.0)

    def test_calculate_yoy_change(self):
        """Test year-over-year change calculation"""
        calculator = BLSCalculator()

        # Test normal case
        net, pct = calculator.calculate_yoy_change(110.0, 100.0)
        assert net == 10.0
        assert pct == 10.0

        # Test negative change
        net, pct = calculator.calculate_yoy_change(90.0, 100.0)
        assert net == -10.0
        assert pct == -10.0

    def test_rebase_index(self):
        """Test index rebasing"""
        calculator = BLSCalculator()

        values = [100.0, 105.0, 110.0, 115.0]

        # Rebase to first period = 100
        rebased = calculator.rebase_index(values, 0, 100.0)
        assert rebased == [100.0, 105.0, 110.0, 115.0]

        # Rebase to second period = 100
        rebased = calculator.rebase_index(values, 1, 100.0)
        expected = [
            100.0 * (100.0 / 105.0),
            100.0,
            100.0 * (110.0 / 105.0),
            100.0 * (115.0 / 105.0),
        ]
        assert abs(rebased[0] - expected[0]) < 0.01
        assert rebased[1] == 100.0

    def test_calculate_moving_average(self):
        """Test moving average calculation"""
        calculator = BLSCalculator()

        values = [100.0, 102.0, 104.0, 106.0, 108.0]

        # 3-period moving average
        ma = calculator.calculate_moving_average(values, 3)
        expected = [(100 + 102 + 104) / 3, (102 + 104 + 106) / 3, (104 + 106 + 108) / 3]

        assert len(ma) == 3
        assert abs(ma[0] - expected[0]) < 0.01
        assert abs(ma[1] - expected[1]) < 0.01
        assert abs(ma[2] - expected[2]) < 0.01

    def test_calculate_volatility(self):
        """Test volatility calculation"""
        calculator = BLSCalculator()

        # Test with known values
        values = [100.0, 100.0, 100.0, 100.0]  # No volatility
        volatility = calculator.calculate_volatility(values)
        assert volatility == 0.0

        # Test with some variation
        values = [98.0, 100.0, 102.0, 100.0]
        volatility = calculator.calculate_volatility(values)
        assert volatility > 0

    def test_calculate_cagr(self):
        """Test CAGR calculation"""
        calculator = BLSCalculator()

        # Test 10% annual growth over 2 years
        cagr = calculator.calculate_compound_annual_growth_rate(100.0, 121.0, 2.0)
        assert abs(cagr - 10.0) < 0.01  # Should be approximately 10%

        # Test with invalid inputs
        with pytest.raises(ValueError):
            calculator.calculate_compound_annual_growth_rate(-100.0, 121.0, 2.0)


class TestBLSDataValidator:
    """Test BLS data validation functions"""

    def test_validate_bls_response(self):
        """Test BLS API response validation"""
        validator = BLSDataValidator()

        # Valid response
        valid_response = {
            "status": "REQUEST_SUCCEEDED",
            "Results": {
                "series": [
                    {
                        "seriesID": "CUUR0000SA0",
                        "data": [{"year": "2023", "period": "M01", "value": "100.0"}],
                    }
                ]
            },
        }

        assert validator.validate_bls_response(valid_response) is True

        # Invalid response - missing Results
        invalid_response = {"status": "REQUEST_SUCCEEDED"}
        assert validator.validate_bls_response(invalid_response) is False

        # Invalid response - failed status
        failed_response = {
            "status": "REQUEST_NOT_PROCESSED",
            "message": "Invalid series ID",
        }
        assert validator.validate_bls_response(failed_response) is False

    def test_validate_observation(self):
        """Test individual observation validation"""
        validator = BLSDataValidator()

        # Valid observation
        valid_obs = BLSObservation(
            series_id="CUUR0000SA0", year=2023, period="M01", value=100.0
        )

        errors = validator.validate_observation(valid_obs)
        assert len(errors) == 0

        # Invalid observation - empty series ID
        invalid_obs = BLSObservation(series_id="", year=2023, period="M01", value=100.0)

        errors = validator.validate_observation(invalid_obs)
        assert len(errors) > 0
        assert any("Series ID is empty" in error for error in errors)

        # Invalid observation - future year
        future_obs = BLSObservation(
            series_id="CUUR0000SA0", year=2030, period="M01", value=100.0
        )

        errors = validator.validate_observation(future_obs)
        assert len(errors) > 0
        assert any("future" in error for error in errors)

    def test_assess_data_quality(self):
        """Test data quality assessment"""
        validator = BLSDataValidator()

        # Good quality data
        good_observations = [
            BLSObservation(
                series_id="CUUR0000SA0", year=2023, period="M01", value=100.0
            ),
            BLSObservation(
                series_id="CUUR0000SA0", year=2023, period="M02", value=101.0
            ),
            BLSObservation(
                series_id="CUUR0000SA0", year=2023, period="M03", value=102.0
            ),
        ]

        quality = validator.assess_data_quality(good_observations)
        assert quality["overall_quality"] in ["GOOD", "EXCELLENT"]
        assert quality["total_observations"] == 3

        # Empty data
        empty_quality = validator.assess_data_quality([])
        assert empty_quality["overall_quality"] == "POOR"
        assert "No observations provided" in empty_quality["issues"]


class TestProcessingIntegration:
    """Integration tests for data processing"""

    def test_process_observation_series(self):
        """Test processing a series of observations"""
        calculator = BLSCalculator()

        # Create test observations
        observations = [
            BLSObservation(series_id="TEST", year=2023, period="M01", value=100.0),
            BLSObservation(series_id="TEST", year=2023, period="M02", value=102.0),
            BLSObservation(series_id="TEST", year=2023, period="M03", value=101.0),
        ]

        processed = calculator.process_observation_series(observations)

        assert len(processed) == 3

        # Check that calculations were added
        # Second observation should have MoM change
        assert processed[1].net_change_1_month == 2.0
        assert processed[1].pct_change_1_month == 2.0

        # Third observation should have MoM change
        assert processed[2].net_change_1_month == -1.0
        assert abs(processed[2].pct_change_1_month - (-1.0 / 102.0 * 100)) < 0.01
