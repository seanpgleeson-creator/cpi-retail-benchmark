"""
Main FastAPI application for CPI Retail Benchmark Platform
"""

from datetime import datetime
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api.bls_routes import router as bls_router
from app.api.simple_bls import router as simple_bls_router
from app.config import settings

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

# Include API routers
app.include_router(simple_bls_router)  # Simple version for debugging
try:
    app.include_router(bls_router)  # Full version with error handling
except Exception as e:
    print(f"Warning: Could not load full BLS router: {e}")


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
