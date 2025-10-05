"""
Vercel serverless function entry point for the CPI Retail Benchmark Platform
"""

from app.main import app

# Export app for Vercel
__all__ = ["app"]
