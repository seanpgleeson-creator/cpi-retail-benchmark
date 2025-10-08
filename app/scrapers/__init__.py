"""
Web scraping module for retail price collection

This module provides scrapers for various retailers to collect
product prices for comparison with BLS CPI data.
"""

from .base import BaseScraper, ScrapingResult, ProductInfo
from .target import TargetScraper
from .manager import ScraperManager

__all__ = [
    "BaseScraper",
    "ScrapingResult", 
    "ProductInfo",
    "TargetScraper",
    "ScraperManager",
]
