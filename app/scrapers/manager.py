"""
Scraper manager for coordinating multiple retail scrapers
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Type, Union

from sqlalchemy.orm import Session

from app.db import get_db_session, BLSDataManager
from app.db.models import RetailerDB, RetailerProductDB, RetailerPriceDB
from .base import BaseScraper, ScrapingResult, ProductInfo, ProductCategory
from .target import TargetScraper

logger = logging.getLogger(__name__)


class ScraperManager:
    """
    Manager for coordinating multiple retail scrapers
    """
    
    def __init__(self, db: Optional[Session] = None):
        """
        Initialize scraper manager
        
        Args:
            db: Optional database session
        """
        self.db = db or get_db_session()
        self.data_manager = BLSDataManager(self.db)
        
        # Registry of available scrapers
        self._scraper_classes: Dict[str, Type[BaseScraper]] = {
            "target": TargetScraper,
        }
        
        # Active scraper instances
        self._active_scrapers: Dict[str, BaseScraper] = {}
        
        # Configuration
        self.default_zip_code = "55331"
        self.max_concurrent_scrapers = 3
        
        logger.info("Scraper manager initialized")
    
    def register_scraper(self, name: str, scraper_class: Type[BaseScraper]) -> None:
        """
        Register a new scraper class
        
        Args:
            name: Unique name for the scraper
            scraper_class: Scraper class to register
        """
        self._scraper_classes[name] = scraper_class
        logger.info(f"Registered scraper: {name}")
    
    async def get_scraper(self, retailer: str, **kwargs) -> Optional[BaseScraper]:
        """
        Get or create a scraper instance
        
        Args:
            retailer: Retailer name (e.g., 'target')
            **kwargs: Additional configuration for scraper
            
        Returns:
            Scraper instance or None if not available
        """
        if retailer not in self._scraper_classes:
            logger.error(f"Unknown retailer: {retailer}")
            return None
        
        # Check if we already have an active instance
        if retailer in self._active_scrapers:
            return self._active_scrapers[retailer]
        
        # Create new scraper instance
        try:
            scraper_class = self._scraper_classes[retailer]
            
            # Set default configuration
            config = {
                "zip_code": self.default_zip_code,
                "headless": True,
                "max_pages": 3,
            }
            config.update(kwargs)
            
            scraper = scraper_class(**config)
            
            # Setup session
            setup_success = await scraper.setup_session()
            if not setup_success:
                logger.error(f"Failed to setup {retailer} scraper")
                return None
            
            self._active_scrapers[retailer] = scraper
            logger.info(f"Created and activated {retailer} scraper")
            
            return scraper
            
        except Exception as e:
            logger.error(f"Failed to create {retailer} scraper: {e}")
            return None
    
    async def search_all_retailers(
        self, 
        query: str, 
        category: Optional[ProductCategory] = None,
        max_results_per_retailer: int = 10
    ) -> Dict[str, ScrapingResult]:
        """
        Search for products across all available retailers
        
        Args:
            query: Search query string
            category: Optional product category filter
            max_results_per_retailer: Max results per retailer
            
        Returns:
            Dictionary mapping retailer names to ScrapingResult
        """
        results = {}
        
        # Create tasks for concurrent scraping
        tasks = []
        for retailer_name in self._scraper_classes.keys():
            task = self._search_retailer_task(
                retailer_name, query, category, max_results_per_retailer
            )
            tasks.append((retailer_name, task))
        
        # Execute searches concurrently
        for retailer_name, task in tasks:
            try:
                result = await task
                results[retailer_name] = result
            except Exception as e:
                logger.error(f"Failed to search {retailer_name}: {e}")
                results[retailer_name] = ScrapingResult(
                    retailer=retailer_name,
                    search_query=query,
                    success=False,
                    error_message=str(e)
                )
        
        return results
    
    async def _search_retailer_task(
        self, 
        retailer: str, 
        query: str, 
        category: Optional[ProductCategory],
        max_results: int
    ) -> ScrapingResult:
        """
        Task for searching a single retailer
        
        Args:
            retailer: Retailer name
            query: Search query
            category: Product category
            max_results: Maximum results
            
        Returns:
            ScrapingResult for the retailer
        """
        scraper = await self.get_scraper(retailer)
        if not scraper:
            return ScrapingResult(
                retailer=retailer,
                search_query=query,
                success=False,
                error_message="Scraper not available"
            )
        
        return await scraper.search_products(query, category, max_results)
    
    async def scrape_by_category(
        self, 
        category: ProductCategory,
        retailers: Optional[List[str]] = None,
        max_results_per_retailer: int = 20
    ) -> Dict[str, ScrapingResult]:
        """
        Scrape products by category from specified retailers
        
        Args:
            category: Product category to scrape
            retailers: List of retailer names (None for all)
            max_results_per_retailer: Max results per retailer
            
        Returns:
            Dictionary mapping retailer names to ScrapingResult
        """
        if retailers is None:
            retailers = list(self._scraper_classes.keys())
        
        results = {}
        
        for retailer in retailers:
            try:
                scraper = await self.get_scraper(retailer)
                if not scraper:
                    continue
                
                # Check if retailer supports this category
                if hasattr(scraper, 'get_supported_categories'):
                    supported = scraper.get_supported_categories()
                    if category not in supported:
                        logger.info(f"{retailer} doesn't support category {category.value}")
                        continue
                
                # Perform category search
                if hasattr(scraper, 'search_by_category'):
                    result = await scraper.search_by_category(category, max_results_per_retailer)
                else:
                    # Fallback to regular search with category name
                    result = await scraper.search_products(
                        category.value, category, max_results_per_retailer
                    )
                
                results[retailer] = result
                
            except Exception as e:
                logger.error(f"Failed to scrape {retailer} for category {category.value}: {e}")
                results[retailer] = ScrapingResult(
                    retailer=retailer,
                    search_query=category.value,
                    success=False,
                    error_message=str(e)
                )
        
        return results
    
    async def store_scraping_results(
        self, 
        results: Dict[str, ScrapingResult],
        session_id: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Store scraping results in the database
        
        Args:
            results: Dictionary of scraping results by retailer
            session_id: Optional session identifier
            
        Returns:
            Dictionary with storage statistics
        """
        storage_stats = {
            "products_stored": 0,
            "retailers_processed": 0,
            "errors": 0
        }
        
        session_id = session_id or f"scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        for retailer_name, result in results.items():
            try:
                if not result.success or not result.products:
                    continue
                
                # Ensure retailer exists in database
                retailer_db = self._ensure_retailer_exists(retailer_name)
                
                # Store products and prices
                for product in result.products:
                    try:
                        # Store or update product
                        product_db = self._store_product(retailer_db, product)
                        
                        # Store price observation
                        self._store_price(product_db, product, session_id)
                        
                        storage_stats["products_stored"] += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to store product {product.name}: {e}")
                        storage_stats["errors"] += 1
                
                storage_stats["retailers_processed"] += 1
                
            except Exception as e:
                logger.error(f"Failed to process results for {retailer_name}: {e}")
                storage_stats["errors"] += 1
        
        # Commit all changes
        self.db.commit()
        
        logger.info(f"Stored scraping results: {storage_stats}")
        return storage_stats
    
    def _ensure_retailer_exists(self, retailer_name: str) -> RetailerDB:
        """
        Ensure retailer exists in database
        
        Args:
            retailer_name: Name of the retailer
            
        Returns:
            RetailerDB instance
        """
        retailer = self.db.query(RetailerDB).filter(
            RetailerDB.retailer_code == retailer_name.lower()
        ).first()
        
        if not retailer:
            retailer = RetailerDB(
                retailer_code=retailer_name.lower(),
                retailer_name=retailer_name.title(),
                is_active=True
            )
            self.db.add(retailer)
            self.db.flush()  # Get the ID without committing
        
        return retailer
    
    def _store_product(self, retailer: RetailerDB, product: ProductInfo) -> RetailerProductDB:
        """
        Store or update product in database
        
        Args:
            retailer: RetailerDB instance
            product: ProductInfo to store
            
        Returns:
            RetailerProductDB instance
        """
        # Check if product already exists
        existing_product = self.db.query(RetailerProductDB).filter(
            RetailerProductDB.retailer_code == retailer.retailer_code,
            RetailerProductDB.product_id == product.product_id
        ).first()
        
        if existing_product:
            # Update existing product
            existing_product.product_name = product.name
            existing_product.brand = product.brand
            existing_product.size = product.size
            existing_product.unit = product.unit
            if product.category:
                existing_product.category = product.category.value
            return existing_product
        else:
            # Create new product
            new_product = RetailerProductDB(
                retailer_code=retailer.retailer_code,
                product_id=product.product_id,
                product_name=product.name,
                brand=product.brand,
                category=product.category.value if product.category else None,
                size=product.size,
                unit=product.unit,
                is_active=True
            )
            self.db.add(new_product)
            self.db.flush()  # Get the ID without committing
            return new_product
    
    def _store_price(
        self, 
        product: RetailerProductDB, 
        product_info: ProductInfo,
        session_id: str
    ) -> RetailerPriceDB:
        """
        Store price observation in database
        
        Args:
            product: RetailerProductDB instance
            product_info: ProductInfo with price data
            session_id: Scraping session identifier
            
        Returns:
            RetailerPriceDB instance
        """
        price_record = RetailerPriceDB(
            product_id=product.id,
            price=product_info.price,
            original_price=product_info.original_price,
            observed_at=product_info.scraped_at,
            zip_code=product_info.zip_code,
            is_on_sale=product_info.on_sale,
            discount_percent=product_info.discount_percent,
            availability_status="in_stock" if product_info.in_stock else "out_of_stock",
            scrape_session_id=session_id
        )
        
        self.db.add(price_record)
        return price_record
    
    async def health_check_all_scrapers(self) -> Dict[str, Dict[str, Union[str, bool]]]:
        """
        Perform health check on all available scrapers
        
        Returns:
            Dictionary mapping retailer names to health status
        """
        health_results = {}
        
        for retailer_name in self._scraper_classes.keys():
            try:
                scraper = await self.get_scraper(retailer_name)
                if scraper:
                    health_results[retailer_name] = await scraper.health_check()
                else:
                    health_results[retailer_name] = {
                        "retailer": retailer_name,
                        "status": "unavailable",
                        "error": "Could not initialize scraper"
                    }
            except Exception as e:
                health_results[retailer_name] = {
                    "retailer": retailer_name,
                    "status": "error",
                    "error": str(e)
                }
        
        return health_results
    
    async def cleanup_all_scrapers(self) -> None:
        """
        Clean up all active scraper sessions
        """
        for retailer, scraper in self._active_scrapers.items():
            try:
                await scraper.cleanup_session()
                logger.info(f"Cleaned up {retailer} scraper")
            except Exception as e:
                logger.error(f"Error cleaning up {retailer} scraper: {e}")
        
        self._active_scrapers.clear()
        
        if self.db:
            self.db.close()
    
    def get_available_retailers(self) -> List[str]:
        """
        Get list of available retailer scrapers
        
        Returns:
            List of retailer names
        """
        return list(self._scraper_classes.keys())
    
    def get_scraper_config(self, retailer: str) -> Optional[Dict]:
        """
        Get configuration for a specific scraper
        
        Args:
            retailer: Retailer name
            
        Returns:
            Configuration dictionary or None if not found
        """
        if retailer in self._active_scrapers:
            return self._active_scrapers[retailer].get_config()
        elif retailer in self._scraper_classes:
            # Return default config for inactive scraper
            return {
                "retailer_name": retailer,
                "status": "inactive",
                "available": True
            }
        else:
            return None
