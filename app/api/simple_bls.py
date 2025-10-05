"""
Simple BLS routes for debugging Vercel deployment issues
"""

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter

# Create a simple router without complex imports
router = APIRouter(prefix="/api/v1/bls-simple", tags=["BLS Simple"])


@router.get("/test")
async def simple_test() -> Dict[str, Any]:
    """Simple test endpoint that should always work"""
    return {
        "status": "working",
        "message": "Simple BLS endpoint is functional",
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/popular")
async def simple_popular_series() -> Dict[str, Any]:
    """Simple popular series without any complex imports"""
    return {
        "categories": {
            "food_and_beverages": {
                "CUUR0000SAF": "Food and beverages",
                "CUUR0000SEFJ": "Dairy and related products",
                "CUUR0000SEFJ01": "Milk",
            },
            "overall_inflation": {
                "CUUR0000SA0": "All items (CPI-U)",
            },
        },
        "description": "Popular BLS CPI series for retail price comparison",
        "timestamp": datetime.now().isoformat(),
    }
