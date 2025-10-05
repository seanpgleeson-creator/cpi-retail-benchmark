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
