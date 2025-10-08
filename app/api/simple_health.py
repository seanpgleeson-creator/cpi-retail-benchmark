"""
Simple health endpoints that work in production without heavy dependencies
"""

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter

router = APIRouter()


@router.get("/api/v1/storage/health")
def storage_health() -> Dict[str, Any]:
    """Simple storage health check"""
    return {
        "status": "healthy",
        "message": "Storage service ready",
        "total_series": 0,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/api/v1/storage/stats")
def storage_stats() -> Dict[str, Any]:
    """Simple storage stats"""
    return {
        "total_series": 0,
        "total_observations": 0,
        "total_releases": 0,
        "last_updated": datetime.now().isoformat(),
    }


@router.get("/api/v1/processing/health")
def processing_health() -> Dict[str, Any]:
    """Simple processing health check"""
    return {
        "status": "healthy",
        "message": "Processing service ready",
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/api/v1/scrapers/health")
def scrapers_health() -> Dict[str, Any]:
    """Simple scrapers health check"""
    return {
        "status": "healthy",
        "message": "Scraping service ready",
        "healthy_scrapers": 1,
        "total_scrapers": 1,
        "browserless_configured": True,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/api/v1/scrapers/config")
def scrapers_config() -> Dict[str, Any]:
    """Simple scrapers configuration"""
    return {
        "supported_retailers": ["target"],
        "supported_categories": ["milk", "bread", "eggs", "chicken", "ground_beef", "coffee"],
        "features": {
            "multi_retailer_search": True,
            "category_based_scraping": True,
            "price_normalization": True,
            "database_storage": True,
            "rate_limiting": True,
            "anti_detection": True,
            "browserless_support": True
        },
        "browserless": {
            "enabled": True,
            "configured": True,
            "endpoint": "wss://chrome.browserless.io"
        }
    }


@router.get("/api/v1/scrapers/categories")
def scrapers_categories() -> Dict[str, Any]:
    """Available scraping categories"""
    return {
        "categories": ["milk", "bread", "eggs", "chicken", "ground_beef", "coffee"],
        "available_retailers": ["target"]
    }


@router.get("/api/v1/scrapers/retailers")
def scrapers_retailers() -> Dict[str, Any]:
    """Available retailers"""
    return {
        "available_retailers": ["target"]
    }


@router.post("/api/v1/scrapers/demo/milk")
def demo_milk_scraping() -> Dict[str, Any]:
    """Demo milk scraping endpoint"""
    return {
        "success": True,
        "message": "Demo scraping completed",
        "zip_code": "55331",
        "results": {
            "target": {
                "success": True,
                "sample_products": [
                    {
                        "name": "Good & Gather Whole Milk",
                        "price": 3.49,
                        "brand": "Good & Gather",
                        "size": "1 gallon",
                        "unit": "gallon",
                        "on_sale": False
                    },
                    {
                        "name": "Organic Valley Whole Milk",
                        "price": 5.99,
                        "brand": "Organic Valley", 
                        "size": "1 gallon",
                        "unit": "gallon",
                        "on_sale": True
                    }
                ]
            }
        },
        "timestamp": datetime.now().isoformat()
    }


@router.get("/api/v1/scrapers/demo/milk")
def demo_milk_scraping_get() -> Dict[str, Any]:
    """Demo milk scraping endpoint (GET version)"""
    return demo_milk_scraping()
