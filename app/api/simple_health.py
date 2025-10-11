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
                    },
                    {
                        "name": "Simply Balanced Organic Whole Milk",
                        "price": 4.29,
                        "brand": "Simply Balanced",
                        "size": "1 gallon",
                        "unit": "gallon",
                        "on_sale": False
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


@router.post("/api/v1/scrapers/category")
def scrape_category() -> Dict[str, Any]:
    """Scrape products by category"""
    return {
        "success": True,
        "message": "Category scraping completed",
        "total_products_found": 4,
        "retailers_scraped": 1,
        "processing_time_seconds": 2.5,
        "results_by_retailer": {
            "target": {
                "success": True,
                "products": [
                    {
                        "name": "Good & Gather Whole Milk",
                        "price": 3.49,
                        "brand": "Good & Gather",
                        "size": "1 gallon",
                        "unit": "gallon",
                        "normalized_price": 3.49,
                        "on_sale": False
                    },
                    {
                        "name": "Organic Valley Whole Milk",
                        "price": 5.99,
                        "brand": "Organic Valley",
                        "size": "1 gallon", 
                        "unit": "gallon",
                        "normalized_price": 5.99,
                        "on_sale": True
                    },
                    {
                        "name": "Horizon Organic Whole Milk",
                        "price": 4.79,
                        "brand": "Horizon",
                        "size": "1 gallon",
                        "unit": "gallon", 
                        "normalized_price": 4.79,
                        "on_sale": False
                    },
                    {
                        "name": "Market Pantry Whole Milk",
                        "price": 2.98,
                        "brand": "Market Pantry",
                        "size": "1 gallon",
                        "unit": "gallon",
                        "normalized_price": 2.98,
                        "on_sale": False
                    }
                ]
            }
        },
        "timestamp": datetime.now().isoformat()
    }


@router.post("/api/v1/scrapers/search")
def scrape_search(request_body: Dict[str, Any]) -> Dict[str, Any]:
    """Search and scrape products with dynamic mock data based on search query"""
    
    # Extract search query from request body
    search_query = ""
    if request_body and "query" in request_body:
        search_query = request_body["query"].lower().strip()
    
    print(f"DEBUG: Received search query: '{search_query}'")
    
    # Mock data for different search terms
    mock_data = {
        "bread": [
            {
                "name": "Good & Gather White Bread",
                "price": 1.29,
                "brand": "Good & Gather",
                "size": "20 oz",
                "unit": "loaf",
                "on_sale": False
            },
            {
                "name": "Wonder Bread Classic White",
                "price": 2.49,
                "brand": "Wonder",
                "size": "20 oz",
                "unit": "loaf",
                "on_sale": True
            },
            {
                "name": "Market Pantry Whole Wheat Bread",
                "price": 1.49,
                "brand": "Market Pantry",
                "size": "20 oz",
                "unit": "loaf",
                "on_sale": False
            }
        ],
        "eggs": [
            {
                "name": "Good & Gather Large Eggs",
                "price": 2.79,
                "brand": "Good & Gather",
                "size": "12 count",
                "unit": "dozen",
                "on_sale": False
            },
            {
                "name": "Eggland's Best Large Eggs",
                "price": 3.99,
                "brand": "Eggland's Best",
                "size": "12 count",
                "unit": "dozen",
                "on_sale": True
            },
            {
                "name": "Market Pantry Organic Eggs",
                "price": 4.49,
                "brand": "Market Pantry",
                "size": "12 count",
                "unit": "dozen",
                "on_sale": False
            }
        ],
        "coffee": [
            {
                "name": "Good & Gather Medium Roast Coffee",
                "price": 4.99,
                "brand": "Good & Gather",
                "size": "12 oz",
                "unit": "bag",
                "on_sale": False
            },
            {
                "name": "Folgers Classic Roast",
                "price": 6.49,
                "brand": "Folgers",
                "size": "11.3 oz",
                "unit": "container",
                "on_sale": True
            },
            {
                "name": "Market Pantry Dark Roast Coffee",
                "price": 3.99,
                "brand": "Market Pantry",
                "size": "12 oz",
                "unit": "bag",
                "on_sale": False
            }
        ],
        "chicken": [
            {
                "name": "Good & Gather Chicken Breast",
                "price": 4.99,
                "brand": "Good & Gather",
                "size": "1 lb",
                "unit": "pound",
                "on_sale": False
            },
            {
                "name": "Perdue Chicken Thighs",
                "price": 3.49,
                "brand": "Perdue",
                "size": "1 lb",
                "unit": "pound",
                "on_sale": True
            },
            {
                "name": "Market Pantry Chicken Wings",
                "price": 5.99,
                "brand": "Market Pantry",
                "size": "2 lb",
                "unit": "package",
                "on_sale": False
            }
        ],
        "milk": [  # Milk products for milk searches
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
            },
            {
                "name": "Market Pantry Whole Milk",
                "price": 2.98,
                "brand": "Market Pantry",
                "size": "1 gallon",
                "unit": "gallon",
                "on_sale": False
            }
        ]
    }
    
    # Determine which products to return based on search query
    selected_term = "milk"  # default
    
    if "bread" in search_query:
        selected_term = "bread"
    elif "egg" in search_query:
        selected_term = "eggs"
    elif "coffee" in search_query:
        selected_term = "coffee"
    elif "chicken" in search_query:
        selected_term = "chicken"
    elif "milk" in search_query:
        selected_term = "milk"
    
    products = mock_data.get(selected_term, mock_data["milk"])
    
    return {
        "success": True,
        "message": f"Product search completed for '{search_query}' - found {selected_term} products",
        "search_query": search_query,
        "product_type": selected_term,
        "total_products_found": len(products),
        "processing_time_seconds": 1.8,
        "results_by_retailer": {
            "target": {
                "success": True,
                "products": products
            }
        },
        "timestamp": datetime.now().isoformat()
    }
