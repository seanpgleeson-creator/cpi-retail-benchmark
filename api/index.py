"""
Vercel serverless function entry point for the CPI Retail Benchmark Platform
"""

from typing import Any, Dict

# Global variable to store import error
import_error_msg = None

try:
    from app.main import app
except ImportError as e:
    # Fallback simple app for debugging
    import_error_msg = str(e)
    from fastapi import FastAPI

    app = FastAPI(title="CPI Benchmark - Debug Mode")

    @app.get("/")
    async def root() -> Dict[str, Any]:
        return {
            "error": "Import failed",
            "message": import_error_msg,
            "status": "debug_mode",
        }

    @app.get("/health")
    async def health() -> Dict[str, Any]:
        return {"status": "debug_mode", "error": import_error_msg}
