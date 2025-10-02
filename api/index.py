"""
Vercel serverless function entry point for the CPI Retail Benchmark Platform
"""

from app.main import app

# Export the FastAPI app for Vercel
handler = app
