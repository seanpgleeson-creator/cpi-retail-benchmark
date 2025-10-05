"""
FastAPI routes for BLS data processing and analysis
"""

from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.data_processing import BLSDataProcessor

router = APIRouter(prefix="/api/v1/processing", tags=["BLS Data Processing"])


class ProcessSeriesRequest(BaseModel):
    """Request model for processing BLS series data"""

    series_id: str = Field(..., description="BLS series ID to process")
    start_year: int = Field(..., ge=1913, le=datetime.now().year + 1)
    end_year: int = Field(..., ge=1913, le=datetime.now().year + 1)
    include_calculations: bool = Field(True, description="Include MoM/YoY calculations")


class CompareSeriesRequest(BaseModel):
    """Request model for comparing multiple BLS series"""

    series_ids: List[str] = Field(..., min_items=2, max_items=10)
    start_year: int = Field(..., ge=1913, le=datetime.now().year + 1)
    end_year: int = Field(..., ge=1913, le=datetime.now().year + 1)
    rebase_to_common_period: bool = Field(
        True, description="Rebase all series to common base period"
    )


@router.get("/health")
def processing_health_check() -> Dict[str, Any]:
    """
    Check the health of the data processing service
    """
    return {
        "status": "healthy",
        "service": "BLS Data Processing",
        "timestamp": datetime.now().isoformat(),
        "capabilities": [
            "Series data processing",
            "MoM/YoY calculations",
            "Multi-series comparison",
            "Data quality validation",
            "Statistical analysis",
        ],
    }


@router.post("/series/process")
def process_series(request: ProcessSeriesRequest) -> Dict[str, Any]:
    """
    Process a single BLS series with calculations and analysis

    This endpoint fetches BLS data and performs comprehensive processing including:
    - Month-over-month and year-over-year calculations
    - Statistical analysis and trend detection
    - Data quality assessment
    - Seasonal pattern analysis
    """
    try:
        processor = BLSDataProcessor()

        result = processor.fetch_and_process_series(
            series_id=request.series_id,
            start_year=request.start_year,
            end_year=request.end_year,
            include_calculations=request.include_calculations,
        )

        # Convert BLS objects to dictionaries for JSON serialization
        serialized_result = _serialize_processing_result(result)

        return {
            "success": True,
            "data": serialized_result,
            "processing_info": {
                "series_id": request.series_id,
                "period": f"{request.start_year}-{request.end_year}",
                "calculations_included": request.include_calculations,
                "processed_at": datetime.now().isoformat(),
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process series {request.series_id}: {str(e)}",
        )


@router.post("/series/compare")
def compare_series(request: CompareSeriesRequest) -> Dict[str, Any]:
    """
    Compare multiple BLS series with cross-series analysis

    This endpoint performs comprehensive comparison of multiple BLS series including:
    - Individual series processing and analysis
    - Cross-series correlation analysis
    - Rebased comparison (optional)
    - Relative performance metrics
    """
    try:
        processor = BLSDataProcessor()

        result = processor.compare_series(
            series_ids=request.series_ids,
            start_year=request.start_year,
            end_year=request.end_year,
            rebase_to_common_period=request.rebase_to_common_period,
        )

        # Serialize the complex result
        serialized_result = _serialize_comparison_result(result)

        return {
            "success": True,
            "data": serialized_result,
            "comparison_info": {
                "series_count": len(request.series_ids),
                "series_ids": request.series_ids,
                "period": f"{request.start_year}-{request.end_year}",
                "rebased": request.rebase_to_common_period,
                "processed_at": datetime.now().isoformat(),
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to compare series: {str(e)}"
        )


@router.get("/series/{series_id}/quick-stats")
def get_quick_stats(
    series_id: str,
    months: int = Query(12, ge=1, le=60, description="Number of recent months"),
) -> Dict[str, Any]:
    """
    Get quick statistics for a BLS series (recent data only)

    Args:
        series_id: BLS series identifier
        months: Number of recent months to analyze
    """
    try:
        processor = BLSDataProcessor()

        # Fetch recent data
        current_year = datetime.now().year
        start_year = current_year - 2 if months > 24 else current_year - 1

        result = processor.fetch_and_process_series(
            series_id=series_id,
            start_year=start_year,
            end_year=current_year,
            include_calculations=True,
        )

        # Extract quick stats
        observations = result["observations"]
        recent_obs = (
            observations[-months:] if len(observations) >= months else observations
        )

        if not recent_obs:
            raise HTTPException(status_code=404, detail="No recent data available")

        latest_obs = recent_obs[-1]

        quick_stats = {
            "series_info": {
                "series_id": series_id,
                "title": result["series_metadata"].title,
                "units": result["series_metadata"].units,
            },
            "latest_data": {
                "value": latest_obs.value,
                "period": f"{latest_obs.year}-{latest_obs.period}",
                "mom_change": latest_obs.pct_change_1_month,
                "yoy_change": latest_obs.pct_change_12_months,
            },
            "recent_trend": {
                "observations_count": len(recent_obs),
                "period_start": f"{recent_obs[0].year}-{recent_obs[0].period}",
                "period_end": f"{recent_obs[-1].year}-{recent_obs[-1].period}",
                "total_change": recent_obs[-1].value - recent_obs[0].value,
                "percent_change": (
                    (recent_obs[-1].value - recent_obs[0].value) / recent_obs[0].value
                )
                * 100,
            },
            "data_quality": result["data_quality"]["overall_quality"],
            "generated_at": datetime.now().isoformat(),
        }

        return quick_stats

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get quick stats for {series_id}: {str(e)}",
        )


@router.get("/calculations/demo")
def calculation_demo() -> Dict[str, Any]:
    """
    Demonstrate the calculation capabilities with sample data
    """
    from app.data_processing.calculations import BLSCalculator

    # Sample data for demonstration
    sample_values = [100.0, 102.1, 103.5, 101.8, 104.2, 105.1, 106.3, 107.0]

    calculator = BLSCalculator()

    demo_results = {
        "sample_data": sample_values,
        "calculations": {
            "mom_change": {
                "description": "Month-over-month change (last two values)",
                "net_change": None,
                "percent_change": None,
            },
            "yoy_change": {
                "description": "Year-over-year change (first vs last)",
                "net_change": None,
                "percent_change": None,
            },
            "rebased_index": {
                "description": "Rebased to first period = 100",
                "values": None,
            },
            "moving_average": {
                "description": "3-period moving average",
                "values": None,
            },
            "volatility": {
                "description": "Standard deviation of sample",
                "value": None,
            },
            "cagr": {
                "description": "Compound Annual Growth Rate (assuming 7 years)",
                "value": None,
            },
        },
    }

    try:
        # Calculate MoM change
        if len(sample_values) >= 2:
            net, pct = calculator.calculate_mom_change(
                sample_values[-1], sample_values[-2]
            )
            demo_results["calculations"]["mom_change"]["net_change"] = net
            demo_results["calculations"]["mom_change"]["percent_change"] = pct

        # Calculate YoY change
        if len(sample_values) >= 2:
            net, pct = calculator.calculate_yoy_change(
                sample_values[-1], sample_values[0]
            )
            demo_results["calculations"]["yoy_change"]["net_change"] = net
            demo_results["calculations"]["yoy_change"]["percent_change"] = pct

        # Rebase index
        rebased = calculator.rebase_index(sample_values, 0, 100.0)
        demo_results["calculations"]["rebased_index"]["values"] = rebased

        # Moving average
        if len(sample_values) >= 3:
            ma = calculator.calculate_moving_average(sample_values, 3)
            demo_results["calculations"]["moving_average"]["values"] = ma

        # Volatility
        volatility = calculator.calculate_volatility(sample_values)
        demo_results["calculations"]["volatility"]["value"] = volatility

        # CAGR
        cagr = calculator.calculate_compound_annual_growth_rate(
            sample_values[0], sample_values[-1], 7
        )
        demo_results["calculations"]["cagr"]["value"] = cagr

    except Exception as e:
        demo_results["error"] = f"Calculation error: {str(e)}"

    return demo_results


def _serialize_processing_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serialize processing result for JSON response

    Args:
        result: Processing result with BLS objects

    Returns:
        Serialized result dictionary
    """
    serialized = {
        "series_metadata": {
            "series_id": result["series_metadata"].series_id,
            "title": result["series_metadata"].title,
            "units": result["series_metadata"].units,
            "seasonal_adjustment": result["series_metadata"].seasonal_adjustment,
            "area": result["series_metadata"].area,
            "item": result["series_metadata"].item,
        },
        "observations": [],
        "analytics": result["analytics"],
        "data_quality": result["data_quality"],
        "processing_timestamp": result["processing_timestamp"],
        "total_observations": result["total_observations"],
    }

    # Serialize observations
    for obs in result["observations"]:
        obs_dict = {
            "series_id": obs.series_id,
            "year": obs.year,
            "period": obs.period,
            "value": obs.value,
            "date_string": obs.date_string,
            "is_monthly": obs.is_monthly,
            "footnotes": obs.footnotes,
        }

        # Add calculated fields if present
        if obs.net_change_1_month is not None:
            obs_dict["net_change_1_month"] = obs.net_change_1_month
        if obs.pct_change_1_month is not None:
            obs_dict["pct_change_1_month"] = obs.pct_change_1_month
        if obs.net_change_12_months is not None:
            obs_dict["net_change_12_months"] = obs.net_change_12_months
        if obs.pct_change_12_months is not None:
            obs_dict["pct_change_12_months"] = obs.pct_change_12_months

        serialized["observations"].append(obs_dict)

    return serialized


def _serialize_comparison_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serialize comparison result for JSON response

    Args:
        result: Comparison result with BLS objects

    Returns:
        Serialized result dictionary
    """
    serialized = {
        "series_count": result["series_count"],
        "comparison_period": result["comparison_period"],
        "cross_series_analysis": result["cross_series_analysis"],
        "series_data": {},
    }

    # Serialize each series data
    for series_id, series_data in result["series_data"].items():
        serialized["series_data"][series_id] = _serialize_processing_result(series_data)

    # Add rebased data if present
    if "rebased_data" in result:
        serialized["rebased_data"] = result["rebased_data"]

    return serialized
