"""
FastAPI routes for retail scraping operations
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.scrapers import ScraperManager, ProductCategory

router = APIRouter(prefix="/api/v1/scrapers", tags=["Retail Scrapers"])


class ScrapeRequest(BaseModel):
    """Request model for scraping operations"""
    
    query: str = Field(..., description="Search query for products")
    retailers: Optional[List[str]] = Field(None, description="List of retailers to scrape (None for all)")
    category: Optional[str] = Field(None, description="Product category filter")
    max_results_per_retailer: int = Field(10, ge=1, le=50, description="Max results per retailer")
    zip_code: Optional[str] = Field(None, description="ZIP code for location-based pricing")
    store_results: bool = Field(True, description="Whether to store results in database")


class CategoryScrapeRequest(BaseModel):
    """Request model for category-based scraping"""
    
    category: str = Field(..., description="Product category to scrape")
    retailers: Optional[List[str]] = Field(None, description="List of retailers to scrape")
    max_results_per_retailer: int = Field(20, ge=1, le=100, description="Max results per retailer")
    zip_code: Optional[str] = Field(None, description="ZIP code for location-based pricing")
    store_results: bool = Field(True, description="Whether to store results in database")


class ScrapingResultResponse(BaseModel):
    """Response model for scraping results"""
    
    success: bool
    session_id: str
    retailers_scraped: int
    total_products_found: int
    results_by_retailer: Dict[str, Any]
    storage_stats: Optional[Dict[str, int]] = None
    processing_time_seconds: float
    timestamp: str


@router.get("/health")
async def scrapers_health_check() -> Dict[str, Any]:
    """
    Check the health of all scraper services
    """
    try:
        manager = ScraperManager()
        health_results = await manager.health_check_all_scrapers()
        await manager.cleanup_all_scrapers()
        
        # Calculate overall health
        total_scrapers = len(health_results)
        healthy_scrapers = sum(
            1 for result in health_results.values() 
            if result.get("status") == "healthy"
        )
        
        overall_status = "healthy" if healthy_scrapers == total_scrapers else "degraded"
        if healthy_scrapers == 0:
            overall_status = "unhealthy"
        
        return {
            "status": overall_status,
            "service": "Retail Scrapers",
            "total_scrapers": total_scrapers,
            "healthy_scrapers": healthy_scrapers,
            "scraper_details": health_results,
            "timestamp": datetime.now().isoformat(),
            "capabilities": [
                "Multi-retailer scraping",
                "Product search and categorization",
                "Price extraction and normalization",
                "Rate limiting and anti-detection",
                "Database storage integration"
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check scraper health: {str(e)}"
        )


@router.get("/retailers")
async def get_available_retailers() -> Dict[str, Any]:
    """
    Get list of available retailer scrapers
    """
    try:
        manager = ScraperManager()
        retailers = manager.get_available_retailers()
        
        # Get configuration for each retailer
        retailer_configs = {}
        for retailer in retailers:
            config = manager.get_scraper_config(retailer)
            if config:
                retailer_configs[retailer] = config
        
        return {
            "success": True,
            "available_retailers": retailers,
            "retailer_configs": retailer_configs,
            "total_retailers": len(retailers),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get available retailers: {str(e)}"
        )


@router.get("/categories")
async def get_product_categories() -> Dict[str, Any]:
    """
    Get list of supported product categories
    """
    try:
        categories = [category.value for category in ProductCategory]
        
        # Get category descriptions
        category_info = {
            "milk": "Dairy milk products (whole, 2%, skim, etc.)",
            "gasoline": "Gasoline and fuel products",
            "bread": "Bread and bakery products",
            "eggs": "Chicken eggs (dozen, etc.)",
            "chicken": "Chicken and poultry products",
            "ground_beef": "Ground beef and meat products",
            "bananas": "Bananas and tropical fruits",
            "apples": "Apples and tree fruits",
            "coffee": "Coffee products and beverages",
            "sugar": "Sugar and sweeteners"
        }
        
        return {
            "success": True,
            "categories": categories,
            "category_descriptions": category_info,
            "total_categories": len(categories),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get product categories: {str(e)}"
        )


@router.post("/search", response_model=ScrapingResultResponse)
async def search_products(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> ScrapingResultResponse:
    """
    Search for products across retailers
    
    This endpoint searches for products matching the query across
    specified retailers and optionally stores the results in the database.
    """
    start_time = datetime.now()
    session_id = f"search_{start_time.strftime('%Y%m%d_%H%M%S')}"
    
    try:
        manager = ScraperManager(db)
        
        # Parse category if provided
        category = None
        if request.category:
            try:
                category = ProductCategory(request.category.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid category: {request.category}"
                )
        
        # Perform search across retailers
        results = await manager.search_all_retailers(
            query=request.query,
            category=category,
            max_results_per_retailer=request.max_results_per_retailer
        )
        
        # Calculate summary statistics
        total_products = sum(len(result.products) for result in results.values())
        successful_retailers = sum(1 for result in results.values() if result.success)
        
        # Store results in database if requested
        storage_stats = None
        if request.store_results:
            storage_stats = await manager.store_scraping_results(results, session_id)
        
        # Clean up scrapers
        await manager.cleanup_all_scrapers()
        
        # Serialize results for response
        serialized_results = {}
        for retailer, result in results.items():
            serialized_results[retailer] = {
                "success": result.success,
                "products_found": len(result.products),
                "pages_scraped": result.pages_scraped,
                "duration_seconds": result.duration_seconds,
                "error_message": result.error_message,
                "products": [
                    {
                        "name": p.name,
                        "brand": p.brand,
                        "price": p.price,
                        "original_price": p.original_price,
                        "size": p.size,
                        "unit": p.unit,
                        "on_sale": p.on_sale,
                        "discount_percent": p.discount_percent,
                        "category": p.category.value if p.category else None,
                        "url": p.url
                    } for p in result.products
                ]
            }
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return ScrapingResultResponse(
            success=True,
            session_id=session_id,
            retailers_scraped=successful_retailers,
            total_products_found=total_products,
            results_by_retailer=serialized_results,
            storage_stats=storage_stats,
            processing_time_seconds=processing_time,
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search products: {str(e)}"
        )


@router.post("/category", response_model=ScrapingResultResponse)
async def scrape_by_category(
    request: CategoryScrapeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> ScrapingResultResponse:
    """
    Scrape products by category across retailers
    
    This endpoint scrapes products in a specific category from
    specified retailers, optimized for category-specific searches.
    """
    start_time = datetime.now()
    session_id = f"category_{request.category}_{start_time.strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # Parse and validate category
        try:
            category = ProductCategory(request.category.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category: {request.category}. Available: {[c.value for c in ProductCategory]}"
            )
        
        manager = ScraperManager(db)
        
        # Perform category-based scraping
        results = await manager.scrape_by_category(
            category=category,
            retailers=request.retailers,
            max_results_per_retailer=request.max_results_per_retailer
        )
        
        # Calculate summary statistics
        total_products = sum(len(result.products) for result in results.values())
        successful_retailers = sum(1 for result in results.values() if result.success)
        
        # Store results in database if requested
        storage_stats = None
        if request.store_results:
            storage_stats = await manager.store_scraping_results(results, session_id)
        
        # Clean up scrapers
        await manager.cleanup_all_scrapers()
        
        # Serialize results for response
        serialized_results = {}
        for retailer, result in results.items():
            serialized_results[retailer] = {
                "success": result.success,
                "products_found": len(result.products),
                "pages_scraped": result.pages_scraped,
                "duration_seconds": result.duration_seconds,
                "error_message": result.error_message,
                "products": [
                    {
                        "name": p.name,
                        "brand": p.brand,
                        "price": p.price,
                        "original_price": p.original_price,
                        "size": p.size,
                        "unit": p.unit,
                        "on_sale": p.on_sale,
                        "discount_percent": p.discount_percent,
                        "normalized_price": p.normalized_price_per_unit,
                        "url": p.url
                    } for p in result.products
                ]
            }
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return ScrapingResultResponse(
            success=True,
            session_id=session_id,
            retailers_scraped=successful_retailers,
            total_products_found=total_products,
            results_by_retailer=serialized_results,
            storage_stats=storage_stats,
            processing_time_seconds=processing_time,
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to scrape by category: {str(e)}"
        )


@router.get("/results/{session_id}")
async def get_scraping_results(
    session_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get stored scraping results by session ID
    
    Args:
        session_id: Scraping session identifier
    
    Returns:
        Stored scraping results and statistics
    """
    try:
        from app.db.models import RetailerPriceDB, RetailerProductDB, RetailerDB
        
        # Query prices from the scraping session
        prices = (
            db.query(RetailerPriceDB)
            .join(RetailerProductDB)
            .join(RetailerDB)
            .filter(RetailerPriceDB.scrape_session_id == session_id)
            .all()
        )
        
        if not prices:
            raise HTTPException(
                status_code=404,
                detail=f"No results found for session: {session_id}"
            )
        
        # Group results by retailer
        results_by_retailer = {}
        for price in prices:
            retailer_name = price.product.retailer.retailer_name
            
            if retailer_name not in results_by_retailer:
                results_by_retailer[retailer_name] = []
            
            results_by_retailer[retailer_name].append({
                "product_name": price.product.product_name,
                "brand": price.product.brand,
                "category": price.product.category,
                "price": float(price.price),
                "original_price": float(price.original_price) if price.original_price else None,
                "size": price.product.size,
                "unit": price.product.unit,
                "on_sale": price.is_on_sale,
                "discount_percent": float(price.discount_percent) if price.discount_percent else None,
                "observed_at": price.observed_at.isoformat(),
                "zip_code": price.zip_code
            })
        
        # Calculate summary statistics
        total_products = len(prices)
        retailers_count = len(results_by_retailer)
        avg_price = sum(float(p.price) for p in prices) / total_products if total_products > 0 else 0
        
        return {
            "success": True,
            "session_id": session_id,
            "total_products": total_products,
            "retailers_count": retailers_count,
            "average_price": avg_price,
            "results_by_retailer": results_by_retailer,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get scraping results: {str(e)}"
        )


@router.get("/demo/milk")
async def demo_milk_scraping(
    zip_code: str = Query("55331", description="ZIP code for pricing"),
    max_results: int = Query(5, ge=1, le=20, description="Max results per retailer")
) -> Dict[str, Any]:
    """
    Demo endpoint for scraping milk prices
    
    This is a demonstration endpoint that shows how to scrape
    milk prices from Target for a specific ZIP code.
    """
    try:
        manager = ScraperManager()
        
        # Search for milk products
        results = await manager.scrape_by_category(
            category=ProductCategory.MILK,
            retailers=["target"],
            max_results_per_retailer=max_results
        )
        
        await manager.cleanup_all_scrapers()
        
        # Format results for demo
        demo_results = {}
        for retailer, result in results.items():
            if result.success and result.products:
                demo_results[retailer] = {
                    "products_found": len(result.products),
                    "sample_products": [
                        {
                            "name": p.name,
                            "price": f"${p.price:.2f}",
                            "size": p.size,
                            "unit": p.unit,
                            "brand": p.brand,
                            "on_sale": p.on_sale
                        } for p in result.products[:3]  # Show first 3 products
                    ],
                    "price_range": {
                        "min": f"${min(p.price for p in result.products):.2f}",
                        "max": f"${max(p.price for p in result.products):.2f}",
                        "avg": f"${sum(p.price for p in result.products) / len(result.products):.2f}"
                    }
                }
            else:
                demo_results[retailer] = {
                    "error": result.error_message or "No products found"
                }
        
        return {
            "success": True,
            "demo": "Milk Price Scraping",
            "zip_code": zip_code,
            "results": demo_results,
            "note": "This is a demonstration of the scraping capabilities",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Demo scraping failed: {str(e)}"
        )


@router.get("/config")
def get_scraper_config() -> Dict[str, Any]:
    """
    Get scraper configuration and capabilities
    """
    return {
        "supported_retailers": ["target"],
        "supported_categories": [category.value for category in ProductCategory],
        "features": {
            "multi_retailer_search": True,
            "category_based_scraping": True,
            "price_normalization": True,
            "database_storage": True,
            "rate_limiting": True,
            "anti_detection": True
        },
        "rate_limits": {
            "requests_per_second": 0.5,
            "max_concurrent_scrapers": 3,
            "delay_range_ms": [500, 1500]
        },
        "configuration": {
            "default_zip_code": "55331",
            "headless_browser": True,
            "max_pages_per_search": 3,
            "max_results_per_retailer": 50
        }
    }
