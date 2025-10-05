"""
Minimal FastAPI app for debugging Vercel issues
"""

from datetime import datetime
from typing import Any, Dict

from fastapi import FastAPI

# Create minimal FastAPI app
app = FastAPI(title="Minimal CPI Benchmark")


@app.get("/")
async def root() -> Dict[str, Any]:
    """Minimal root endpoint"""
    return {
        "name": "CPI Retail Benchmark Platform - Minimal",
        "status": "working",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/health")
async def health() -> Dict[str, Any]:
    """Minimal health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/test-imports")
async def test_imports() -> Dict[str, Any]:
    """Test basic imports"""
    results = {}

    try:
        import json

        results["json"] = "✅ OK"
    except Exception as e:
        results["json"] = f"❌ {e}"

    try:
        import sys

        results["sys"] = "✅ OK"
        results["python_version"] = sys.version
    except Exception as e:
        results["sys"] = f"❌ {e}"

    try:
        from typing import List

        results["typing"] = "✅ OK"
    except Exception as e:
        results["typing"] = f"❌ {e}"

    return {
        "imports": results,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/diagnostic/step-1")
async def diagnostic_step_1() -> Dict[str, Any]:
    """Test basic Python imports"""
    results = {}
    
    try:
        from typing import Any, Dict  # noqa: F401
        results["typing"] = "✅ OK"
    except Exception as e:
        results["typing"] = f"❌ {e}"
    
    try:
        from datetime import datetime  # noqa: F401
        results["datetime"] = "✅ OK"
    except Exception as e:
        results["datetime"] = f"❌ {e}"
    
    return {"step": 1, "basic_imports": results}


@app.get("/diagnostic/step-3")
async def diagnostic_step_3() -> Dict[str, Any]:
    """Test our app module imports"""
    results = {}
    
    try:
        from app import __version__  # noqa: F401
        results["app_version"] = f"✅ OK - {__version__}"
    except Exception as e:
        results["app_version"] = f"❌ {e}"
    
    try:
        from app.config import settings  # noqa: F401
        results["app_config"] = "✅ OK"
        results["bls_api_key"] = settings.bls_api_key is not None
    except Exception as e:
        results["app_config"] = f"❌ {e}"
    
    return {"step": 3, "app_imports": results}


@app.get("/diagnostic/step-4")
async def diagnostic_step_4() -> Dict[str, Any]:
    """Test BLS client imports"""
    results = {}
    
    try:
        from app.bls_client import BLSAPIClient  # noqa: F401
        results["bls_client"] = "✅ OK"
    except Exception as e:
        results["bls_client"] = f"❌ {e}"
    
    return {"step": 4, "bls_imports": results}


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
        results["python_path"] = sys.path
        results["python_version"] = sys.version
    except Exception as e:
        results["python_info"] = f"❌ {e}"
    
    return {"package_test": results}
