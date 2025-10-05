"""
FastAPI routes for BLS data integration
"""

from datetime import datetime
from typing import Any, Dict, List, Union

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.bls_client import BLSAPIClient, BLSAPIError
from app.config import settings

router = APIRouter(prefix="/api/v1/bls", tags=["BLS Data"])


class SeriesRequest(BaseModel):
    """Request model for fetching BLS series data"""

    series_ids: Union[str, List[str]] = Field(
        ..., description="BLS series ID(s) to fetch"
    )
    start_year: int = Field(
        ..., ge=1913, le=datetime.now().year + 1, description="Starting year for data"
    )
    end_year: int = Field(
        ..., ge=1913, le=datetime.now().year + 1, description="Ending year for data"
    )
    calculations: bool = Field(
        True, description="Include percent changes and net changes"
    )
    annual_averages: bool = Field(False, description="Include annual averages")


class SeriesInfoResponse(BaseModel):
    """Response model for series information"""

    series_id: str
    title: str
    units: str
    seasonal_adjustment: str
    last_updated: str
    data_points: int
    latest_value: Union[str, None]
    latest_period: Union[str, None]


@router.get("/health")
async def bls_health_check() -> Dict[str, Any]:
    """
    Check the health of the BLS API connection
    """
    try:
        async with BLSAPIClient() as client:
            health_status = await client.health_check()
        return health_status
    except Exception as e:
        raise HTTPException(
            status_code=503, detail=f"BLS API health check failed: {str(e)}"
        )


@router.get("/series/{series_id}/info")
async def get_series_info(series_id: str) -> SeriesInfoResponse:
    """
    Get information about a specific BLS series

    Args:
        series_id: BLS series identifier (e.g., CUUR0000SEFJ01 for milk CPI)
    """
    try:
        async with BLSAPIClient() as client:
            info = await client.get_series_info(series_id)
        return SeriesInfoResponse(**info)
    except BLSAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch series info: {str(e)}"
        )


@router.get("/series/{series_id}/latest")
async def get_latest_data(
    series_id: str,
    months: int = Query(12, ge=1, le=60, description="Number of recent months"),
) -> Dict[str, Any]:
    """
    Get the most recent data for a BLS series

    Args:
        series_id: BLS series identifier
        months: Number of recent months to fetch (1-60)
    """
    try:
        async with BLSAPIClient() as client:
            data = await client.fetch_latest_data([series_id], months=months)
        return data
    except BLSAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch latest data: {str(e)}"
        )


@router.post("/series/data")
async def fetch_series_data(request: SeriesRequest) -> Dict[str, Any]:
    """
    Fetch time series data from BLS API

    This endpoint allows you to fetch historical data for one or more BLS series.
    """
    try:
        async with BLSAPIClient() as client:
            data = await client.fetch_series_data(
                series_ids=request.series_ids,
                start_year=request.start_year,
                end_year=request.end_year,
                calculations=request.calculations,
                annual_averages=request.annual_averages,
            )
        return data
    except BLSAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch series data: {str(e)}"
        )


@router.get("/series/popular")
async def get_popular_series() -> Dict[str, Any]:
    """
    Get information about popular CPI series relevant to retail price tracking
    """
    popular_series = {
        "food_and_beverages": {
            "CUUR0000SAF": "Food and beverages",
            "CUUR0000SEFJ": "Dairy and related products",
            "CUUR0000SEFJ01": "Milk",
            "CUUR0000SEFD": "Cereals and bakery products",
            "CUUR0000SEFF": "Meats, poultry, fish, and eggs",
        },
        "gasoline": {
            "CUUR0000SETB01": "Gasoline (all types)",
            "CUUR0000SETB0101": "Gasoline, unleaded regular",
            "CUUR0000SETB0102": "Gasoline, unleaded midgrade",
            "CUUR0000SETB0103": "Gasoline, unleaded premium",
        },
        "household_items": {
            "CUUR0000SEHF": "Household furnishings and operations",
            "CUUR0000SEHE": "Household energy",
            "CUUR0000SEHF01": "Furniture and bedding",
        },
        "overall_inflation": {
            "CUUR0000SA0": "All items (CPI-U)",
            "CUUR0000SA0L1E": "All items less food and energy",
            "CUUR0000SA0E": "Energy",
        },
    }

    return {
        "categories": popular_series,
        "description": "Popular BLS CPI series for retail price comparison",
        "usage": "Use these series IDs with other endpoints to fetch data",
        "api_key_info": {
            "configured": settings.bls_api_key is not None,
            "benefits": [
                "500 requests per day (vs 25 without key)",
                "25 requests per 10 seconds (vs 10 per 5 minutes)",
                "20-year data range (vs 10 years)",
            ],
        },
    }


@router.get("/config")
async def get_bls_config() -> Dict[str, Any]:
    """
    Get BLS API configuration information
    """
    return {
        "api_key_configured": settings.bls_api_key is not None,
        "base_url": settings.bls_base_url,
        "default_series": settings.default_bls_series,
        "rate_limits": {
            "with_key": {"daily": 500, "burst": "25 per 10 seconds"},
            "without_key": {"daily": 25, "burst": "10 per 5 minutes"},
        },
        "data_range_limits": {"with_key": "20 years", "without_key": "10 years"},
    }
