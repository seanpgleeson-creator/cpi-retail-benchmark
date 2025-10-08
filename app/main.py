"""
Main FastAPI application for CPI Retail Benchmark Platform
"""

from datetime import datetime
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.config import settings

# Import routers conditionally to avoid crashes
bls_router = None
simple_bls_router = None
processing_router = None
storage_router = None
scraper_router = None

try:
    from app.api.simple_bls import router as simple_bls_router

    print("✅ Simple BLS router loaded")
except Exception as e:
    print(f"⚠️ Simple BLS router failed: {e}")

try:
    from app.api.bls_routes import router as bls_router

    print("✅ Full BLS router loaded")
except Exception as e:
    print(f"⚠️ Full BLS router failed: {e}")

try:
    from app.api.processing_routes import router as processing_router

    print("✅ Processing router loaded")
except Exception as e:
    print(f"⚠️ Processing router failed: {e}")

try:
    from app.api.storage_routes import router as storage_router

    print("✅ Storage router loaded")
except Exception as e:
    print(f"⚠️ Storage router failed: {e}")

try:
    from app.api.scraper_routes import router as scraper_router

    print("✅ Scraper router loaded")
except Exception as e:
    print(f"⚠️ Scraper router failed: {e}")

# Create FastAPI application
app = FastAPI(
    title="CPI Retail Benchmark Platform",
    description=(
        "Multi-Retailer CPI Price Benchmark Platform - "
        "Real-time retail price tracking vs government inflation data"
    ),
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers conditionally
if simple_bls_router:
    app.include_router(simple_bls_router)
    print("✅ Simple BLS router included")

if bls_router:
    app.include_router(bls_router)
    print("✅ Full BLS router included")

if processing_router:
    app.include_router(processing_router)
    print("✅ Processing router included")

if storage_router:
    app.include_router(storage_router)
    print("✅ Storage router included")

if scraper_router:
    app.include_router(scraper_router)
    print("✅ Scraper router included")

# Initialize database on startup
try:
    from app.db import init_db
    init_db()
    print("✅ Database initialized")
except Exception as e:
    print(f"⚠️ Database initialization failed: {e}")


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint with basic application information"""
    return {
        "name": "CPI Retail Benchmark Platform",
        "version": __version__,
        "description": "Multi-Retailer CPI Price Benchmark Platform",
        "status": "healthy",
        "environment": settings.environment,
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "version": __version__,
        "environment": settings.environment,
        "timestamp": "2025-01-01T00:00:00Z",  # Will be dynamic later
    }


@app.get("/api/v1/status")
async def api_status() -> Dict[str, Any]:
    """API status endpoint"""
    return {
        "api_version": "v1",
        "status": "operational",
        "features": {
            "bls_integration": "planned",
            "multi_retailer_scraping": "planned",
            "price_comparison": "planned",
            "alerts": "planned",
        },
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "status": "/api/v1/status",
        },
    }


@app.get("/api/v1/config")
async def get_config() -> Dict[str, Any]:
    """Get public configuration information"""
    return {
        "environment": settings.environment,
        "debug": settings.debug,
        "default_zip_code": settings.zip_code,
        "bls_api_configured": settings.bls_api_key is not None,
        "default_bls_series": settings.default_bls_series,
    }


@app.get("/debug/imports")
async def debug_imports() -> Dict[str, Any]:
    """Debug endpoint to check what imports are working"""
    import_status = {}

    try:
        from app.config import settings  # noqa: F401

        import_status["config"] = "✅ OK"
    except Exception as e:
        import_status["config"] = f"❌ Error: {e}"

    try:
        from app.bls_client import BLSAPIClient  # noqa: F401

        import_status["bls_client"] = "✅ OK"
    except Exception as e:
        import_status["bls_client"] = f"❌ Error: {e}"

    try:
        import httpx  # noqa: F401

        import_status["httpx"] = "✅ OK"
    except Exception as e:
        import_status["httpx"] = f"❌ Error: {e}"

    try:
        import tenacity  # noqa: F401

        import_status["tenacity"] = "✅ OK"
    except Exception as e:
        import_status["tenacity"] = f"❌ Error: {e}"

        return {
            "imports": import_status,
            "routers_loaded": {
                "simple_bls_router": simple_bls_router is not None,
                "bls_router": bls_router is not None,
                "processing_router": processing_router is not None,
                "storage_router": storage_router is not None,
                "scraper_router": scraper_router is not None,
            },
            "timestamp": datetime.now().isoformat(),
        }


@app.get("/test-packages")
async def test_packages() -> Dict[str, Any]:
    """Test if ANY external packages work in Vercel"""
    results = {}

    try:
        import requests  # noqa: F401

        results["requests"] = "✅ OK"
    except Exception as e:
        results["requests"] = f"❌ {e}"

    try:
        import httpx  # noqa: F401

        results["httpx"] = "✅ OK"
    except Exception as e:
        results["httpx"] = f"❌ {e}"

    try:
        import sys

        results["python_path"] = sys.path[:3]  # First 3 paths only
        results["python_version"] = sys.version
    except Exception as e:
        results["python_info"] = f"❌ {e}"

    return {"package_test": results, "timestamp": datetime.now().isoformat()}


@app.get("/debug/app-status")
async def app_status() -> Dict[str, Any]:
    """Show which app is actually running"""
    return {
        "app_type": "main_app",
        "title": app.title,
        "routers_loaded": {
            "simple_bls_router": simple_bls_router is not None,
            "bls_router": bls_router is not None,
            "processing_router": processing_router is not None,
            "storage_router": storage_router is not None,
            "scraper_router": scraper_router is not None,
        },
        "available_endpoints": [
            "/",
            "/health",
            "/test-packages",
            "/debug/imports",
            "/debug/app-status",
            "/api/v1/status",
            "/api/v1/config",
            "/api/v1/processing/health",
            "/api/v1/storage/health",
            "/api/v1/scrapers/health",
            "/docs",
        ],
        "timestamp": datetime.now().isoformat(),
    }


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested resource was not found",
            "path": str(request.url.path),
            "available_endpoints": [
                "/",
                "/health",
                "/docs",
                "/api/v1/status",
                "/api/v1/config",
            ],
        },
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Custom 500 handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An internal server error occurred",
            "environment": settings.environment,
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
