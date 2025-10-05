"""
Ultra-simple debug endpoint for Vercel
"""

from datetime import datetime


def handler(request):
    """Ultra-simple handler for debugging"""
    timestamp = datetime.now().isoformat()
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": f'{{"status": "working", "timestamp": "{timestamp}", '
        f'"message": "Ultra-simple debug endpoint"}}',
    }


# Also try FastAPI version
try:
    from fastapi import FastAPI

    app = FastAPI(title="Debug App")

    @app.get("/")
    async def root():
        return {
            "status": "working",
            "timestamp": datetime.now().isoformat(),
            "message": "Simple FastAPI debug endpoint",
        }

except Exception as import_error:
    # If FastAPI fails, create a simple function
    def app(request):
        timestamp = datetime.now().isoformat()
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": f'{{"error": "FastAPI failed", '
            f'"message": "{str(import_error)}", '
            f'"timestamp": "{timestamp}"}}',
        }
