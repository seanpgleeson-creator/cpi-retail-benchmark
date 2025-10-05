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

        app = FastAPI()

        @app.get("/")
        async def fallback_root():
            return {
                "error": "App failed to initialize",
                "main_error": main_error,
                "minimal_error": minimal_error,
                "status": "fallback_mode",
            }


# Export app for Vercel
__all__ = ["app"]
