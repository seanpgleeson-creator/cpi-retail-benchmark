"""
API routes for the CPI Retail Benchmark Platform
"""

from .bls_routes import router as bls_router

__all__ = ["bls_router"]
