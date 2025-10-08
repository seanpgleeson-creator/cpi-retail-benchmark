"""
Base scraper classes and data models
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Union
from enum import Enum

logger = logging.getLogger(__name__)


class ProductCategory(Enum):
    """Product categories mapped to BLS series"""
    MILK = "milk"
    GASOLINE = "gasoline"
    BREAD = "bread"
    EGGS = "eggs"
    CHICKEN = "chicken"
    GROUND_BEEF = "ground_beef"
    BANANAS = "bananas"
    APPLES = "apples"
    COFFEE = "coffee"
    SUGAR = "sugar"


class PriceUnit(Enum):
    """Standard price units for normalization"""
    PER_GALLON = "per_gallon"
    PER_POUND = "per_pound"
    PER_DOZEN = "per_dozen"
    PER_LOAF = "per_loaf"
    PER_OUNCE = "per_ounce"
    EACH = "each"


@dataclass
class ProductInfo:
    """Information about a scraped product"""
    
    # Product identification
    product_id: str
    name: str
    brand: Optional[str] = None
    
    # Price information
    price: float
    original_price: Optional[float] = None  # Before discounts
    currency: str = "USD"
    
    # Product details
    size: Optional[str] = None
    unit: Optional[str] = None
    category: Optional[ProductCategory] = None
    
    # Availability
    in_stock: bool = True
    availability_status: str = "available"
    
    # Discount information
    on_sale: bool = False
    discount_percent: Optional[float] = None
    
    # Metadata
    url: Optional[str] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    
    # Scraping metadata
    scraped_at: datetime = None
    zip_code: Optional[str] = None
    store_id: Optional[str] = None
    
    def __post_init__(self):
        if self.scraped_at is None:
            self.scraped_at = datetime.now()
    
    @property
    def normalized_price_per_unit(self) -> Optional[float]:
        """Calculate normalized price per standard unit"""
        if not self.size or not self.unit:
            return None
        
        # This is a simplified version - real implementation would need
        # comprehensive unit conversion logic
        try:
            if "gallon" in self.unit.lower():
                return self.price  # Already per gallon
            elif "quart" in self.unit.lower():
                return self.price * 4  # Convert to per gallon
            elif "lb" in self.unit.lower() or "pound" in self.unit.lower():
                return self.price  # Already per pound
            elif "oz" in self.unit.lower():
                # Convert ounces to pounds (16 oz = 1 lb)
                return self.price * 16
        except (ValueError, AttributeError):
            pass
        
        return None
    
    @property
    def effective_price(self) -> float:
        """Get the effective price (after discounts)"""
        return self.price


@dataclass
class ScrapingResult:
    """Result of a scraping operation"""
    
    # Operation metadata
    retailer: str
    search_query: str
    zip_code: Optional[str] = None
    
    # Results
    products: List[ProductInfo] = None
    total_found: int = 0
    pages_scraped: int = 0
    
    # Timing and status
    started_at: datetime = None
    completed_at: datetime = None
    success: bool = True
    error_message: Optional[str] = None
    
    # Performance metrics
    products_per_second: Optional[float] = None
    
    def __post_init__(self):
        if self.products is None:
            self.products = []
        if self.started_at is None:
            self.started_at = datetime.now()
        if self.completed_at is None:
            self.completed_at = datetime.now()
        
        self.total_found = len(self.products)
        
        # Calculate performance metrics
        if self.completed_at and self.started_at:
            duration = (self.completed_at - self.started_at).total_seconds()
            if duration > 0:
                self.products_per_second = len(self.products) / duration
    
    @property
    def duration_seconds(self) -> float:
        """Get scraping duration in seconds"""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0
    
    def add_product(self, product: ProductInfo) -> None:
        """Add a product to the results"""
        self.products.append(product)
        self.total_found = len(self.products)


class BaseScraper(ABC):
    """
    Abstract base class for all retail scrapers
    """
    
    def __init__(
        self,
        retailer_name: str,
        base_url: str,
        zip_code: str = "55331",
        headless: bool = True,
        max_pages: int = 5,
        delay_range_ms: tuple = (500, 1500),
        user_agent_rotation: bool = True,
    ):
        self.retailer_name = retailer_name
        self.base_url = base_url
        self.zip_code = zip_code
        self.headless = headless
        self.max_pages = max_pages
        self.delay_range_ms = delay_range_ms
        self.user_agent_rotation = user_agent_rotation
        
        # Rate limiting
        self.requests_per_second = 0.5
        self.max_retries = 3
        
        # Session state
        self._session_id = None
        self._last_request_time = None
        
        logger.info(f"Initialized {retailer_name} scraper")
    
    @abstractmethod
    async def search_products(
        self, 
        query: str, 
        category: Optional[ProductCategory] = None,
        max_results: int = 20
    ) -> ScrapingResult:
        """
        Search for products on the retailer's website
        
        Args:
            query: Search query string
            category: Optional product category filter
            max_results: Maximum number of results to return
            
        Returns:
            ScrapingResult with found products
        """
        pass
    
    @abstractmethod
    async def get_product_details(self, product_url: str) -> Optional[ProductInfo]:
        """
        Get detailed information about a specific product
        
        Args:
            product_url: URL of the product page
            
        Returns:
            ProductInfo with detailed product data or None if failed
        """
        pass
    
    @abstractmethod
    async def setup_session(self) -> bool:
        """
        Setup scraping session (browser, authentication, etc.)
        
        Returns:
            True if setup successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def cleanup_session(self) -> None:
        """
        Clean up scraping session resources
        """
        pass
    
    def _normalize_price(self, price_text: str) -> Optional[float]:
        """
        Extract and normalize price from text
        
        Args:
            price_text: Raw price text from website
            
        Returns:
            Normalized price as float or None if parsing failed
        """
        if not price_text:
            return None
        
        try:
            # Remove currency symbols and whitespace
            cleaned = price_text.replace('$', '').replace(',', '').strip()
            
            # Handle price ranges (take the first price)
            if '-' in cleaned:
                cleaned = cleaned.split('-')[0].strip()
            
            # Convert to float
            return float(cleaned)
        except (ValueError, AttributeError):
            logger.warning(f"Failed to parse price: {price_text}")
            return None
    
    def _extract_size_and_unit(self, product_text: str) -> tuple[Optional[str], Optional[str]]:
        """
        Extract size and unit information from product text
        
        Args:
            product_text: Product name or description
            
        Returns:
            Tuple of (size, unit) or (None, None) if not found
        """
        import re
        
        # Common patterns for size and unit
        patterns = [
            r'(\d+(?:\.\d+)?)\s*(fl\s*oz|oz|lb|lbs|gallon|gal|quart|qt|pint|pt)',
            r'(\d+(?:\.\d+)?)\s*(ounce|pound|pounds)',
            r'(\d+)\s*(count|ct|pack)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, product_text, re.IGNORECASE)
            if match:
                size = match.group(1)
                unit = match.group(2)
                return size, unit
        
        return None, None
    
    def _categorize_product(self, product_name: str) -> Optional[ProductCategory]:
        """
        Categorize a product based on its name
        
        Args:
            product_name: Product name or title
            
        Returns:
            ProductCategory or None if no match
        """
        name_lower = product_name.lower()
        
        # Simple keyword-based categorization
        if any(word in name_lower for word in ['milk', 'dairy']):
            return ProductCategory.MILK
        elif any(word in name_lower for word in ['gas', 'gasoline', 'fuel']):
            return ProductCategory.GASOLINE
        elif any(word in name_lower for word in ['bread', 'loaf']):
            return ProductCategory.BREAD
        elif any(word in name_lower for word in ['egg', 'eggs']):
            return ProductCategory.EGGS
        elif any(word in name_lower for word in ['chicken', 'poultry']):
            return ProductCategory.CHICKEN
        elif any(word in name_lower for word in ['beef', 'ground beef']):
            return ProductCategory.GROUND_BEEF
        elif any(word in name_lower for word in ['banana', 'bananas']):
            return ProductCategory.BANANAS
        elif any(word in name_lower for word in ['apple', 'apples']):
            return ProductCategory.APPLES
        elif any(word in name_lower for word in ['coffee']):
            return ProductCategory.COFFEE
        elif any(word in name_lower for word in ['sugar']):
            return ProductCategory.SUGAR
        
        return None
    
    async def health_check(self) -> Dict[str, Union[str, bool]]:
        """
        Perform a health check on the scraper
        
        Returns:
            Health status information
        """
        try:
            # Try to setup and cleanup session
            setup_success = await self.setup_session()
            if setup_success:
                await self.cleanup_session()
            
            return {
                "retailer": self.retailer_name,
                "status": "healthy" if setup_success else "unhealthy",
                "base_url": self.base_url,
                "zip_code": self.zip_code,
                "headless": self.headless,
                "session_setup": setup_success,
            }
        except Exception as e:
            logger.error(f"Health check failed for {self.retailer_name}: {e}")
            return {
                "retailer": self.retailer_name,
                "status": "unhealthy",
                "error": str(e),
            }
    
    def get_config(self) -> Dict[str, Union[str, int, bool]]:
        """
        Get scraper configuration
        
        Returns:
            Configuration dictionary
        """
        return {
            "retailer_name": self.retailer_name,
            "base_url": self.base_url,
            "zip_code": self.zip_code,
            "headless": self.headless,
            "max_pages": self.max_pages,
            "delay_range_ms": self.delay_range_ms,
            "user_agent_rotation": self.user_agent_rotation,
            "requests_per_second": self.requests_per_second,
            "max_retries": self.max_retries,
        }
