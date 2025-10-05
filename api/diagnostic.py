"""
Step-by-step diagnostic to identify the main app issue
"""

from datetime import datetime
from fastapi import FastAPI

app = FastAPI(title="Diagnostic App")


@app.get("/")
async def root():
    return {"status": "diagnostic", "timestamp": datetime.now().isoformat()}


@app.get("/test-step-1")
async def test_basic_imports():
    """Test basic Python imports"""
    results = {}
    
    try:
        from typing import Any, Dict
        results["typing"] = "✅ OK"
    except Exception as e:
        results["typing"] = f"❌ {e}"
    
    try:
        from datetime import datetime
        results["datetime"] = "✅ OK"
    except Exception as e:
        results["datetime"] = f"❌ {e}"
    
    return {"step": 1, "basic_imports": results}


@app.get("/test-step-2")
async def test_fastapi_imports():
    """Test FastAPI related imports"""
    results = {}
    
    try:
        from fastapi import FastAPI, Request
        results["fastapi_core"] = "✅ OK"
    except Exception as e:
        results["fastapi_core"] = f"❌ {e}"
    
    try:
        from fastapi.middleware.cors import CORSMiddleware
        results["cors_middleware"] = "✅ OK"
    except Exception as e:
        results["cors_middleware"] = f"❌ {e}"
    
    try:
        from fastapi.responses import JSONResponse
        results["json_response"] = "✅ OK"
    except Exception as e:
        results["json_response"] = f"❌ {e}"
    
    return {"step": 2, "fastapi_imports": results}


@app.get("/test-step-3")
async def test_app_imports():
    """Test our app module imports"""
    results = {}
    
    try:
        from app import __version__
        results["app_version"] = f"✅ OK - {__version__}"
    except Exception as e:
        results["app_version"] = f"❌ {e}"
    
    try:
        from app.config import settings
        results["app_config"] = "✅ OK"
        results["bls_api_key"] = settings.bls_api_key is not None
    except Exception as e:
        results["app_config"] = f"❌ {e}"
    
    return {"step": 3, "app_imports": results}


@app.get("/test-step-4")
async def test_bls_imports():
    """Test BLS client imports"""
    results = {}
    
    try:
        from app.api.bls_routes import router as bls_router
        results["bls_routes"] = "✅ OK"
    except Exception as e:
        results["bls_routes"] = f"❌ {e}"
    
    try:
        from app.bls_client import BLSAPIClient
        results["bls_client"] = "✅ OK"
    except Exception as e:
        results["bls_client"] = f"❌ {e}"
    
    return {"step": 4, "bls_imports": results}


@app.get("/test-step-5")
async def test_dependencies():
    """Test external dependencies"""
    results = {}
    
    try:
        import httpx
        results["httpx"] = "✅ OK"
    except Exception as e:
        results["httpx"] = f"❌ {e}"
    
    try:
        import tenacity
        results["tenacity"] = "✅ OK"
    except Exception as e:
        results["tenacity"] = f"❌ {e}"
    
    try:
        import pydantic
        results["pydantic"] = "✅ OK"
    except Exception as e:
        results["pydantic"] = f"❌ {e}"
    
    return {"step": 5, "dependencies": results}
