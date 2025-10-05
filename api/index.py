"""
Vercel serverless function entry point for the CPI Retail Benchmark Platform
"""

main_error = None
minimal_error = None

try:
    from app.main import app
except Exception as e:
    # Fallback to minimal app if main app fails
    main_error = str(e)
    print(f"Failed to import main app: {e}")
    try:
        from api.minimal import app
    except Exception as e2:
        minimal_error = str(e2)
        print(f"Failed to import minimal app: {e2}")
        # Ultra-simple fallback
        from fastapi import FastAPI
        from datetime import datetime

        app = FastAPI(title="Fallback App")

        @app.get("/")
        async def fallback_root():
            return {
                "error": "App failed to initialize",
                "main_error": main_error,
                "minimal_error": minimal_error,
                "status": "fallback_mode",
                "timestamp": datetime.now().isoformat(),
            }

        @app.get("/debug/app-status")
        async def fallback_app_status():
            return {
                "app_type": "ultra_simple_fallback",
                "main_error": main_error,
                "minimal_error": minimal_error,
                "timestamp": datetime.now().isoformat(),
            }

        @app.get("/test-packages")
        async def fallback_test_packages():
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
                results["python_version"] = sys.version
                results["python_path"] = sys.path[:3]
            except Exception as e:
                results["python_info"] = f"❌ {e}"
            
            return {
                "package_test": results,
                "app_type": "ultra_simple_fallback",
                "timestamp": datetime.now().isoformat(),
            }


# Export app for Vercel
__all__ = ["app"]
