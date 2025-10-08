"""
Tests for scraper functionality
"""

import pytest
from unittest.mock import Mock, AsyncMock

from app.scrapers.base import BaseScraper, ScrapingResult, ProductInfo, ProductCategory
from app.scrapers.manager import ScraperManager


class MockScraper(BaseScraper):
    """Mock scraper for testing"""
    
    def __init__(self, **kwargs):
        super().__init__(
            retailer_name="MockRetailer",
            base_url="https://mock-retailer.com",
            **kwargs
        )
        self.setup_called = False
        self.cleanup_called = False
    
    async def setup_session(self) -> bool:
        self.setup_called = True
        return True
    
    async def cleanup_session(self) -> None:
        self.cleanup_called = True
    
    async def search_products(
        self, 
        query: str, 
        category=None,
        max_results: int = 20
    ) -> ScrapingResult:
        # Return mock results
        result = ScrapingResult(
            retailer=self.retailer_name,
            search_query=query
        )
        
        # Add some mock products
        for i in range(min(3, max_results)):
            product = ProductInfo(
                product_id=f"mock_{i}",
                name=f"Mock Product {i} - {query}",
                brand="MockBrand",
                price=10.99 + i,
                size="1",
                unit="lb",
                category=category
            )
            result.add_product(product)
        
        result.success = True
        return result
    
    async def get_product_details(self, product_url: str) -> ProductInfo:
        return ProductInfo(
            product_id="mock_detail",
            name="Mock Product Detail",
            price=15.99,
            url=product_url
        )


class TestBaseScraper:
    """Test base scraper functionality"""

    def test_scraper_initialization(self):
        """Test scraper initialization"""
        scraper = MockScraper(
            zip_code="12345",
            headless=False,
            max_pages=10
        )
        
        assert scraper.retailer_name == "MockRetailer"
        assert scraper.base_url == "https://mock-retailer.com"
        assert scraper.zip_code == "12345"
        assert scraper.headless is False
        assert scraper.max_pages == 10

    def test_normalize_price(self):
        """Test price normalization"""
        scraper = MockScraper()
        
        # Test various price formats
        assert scraper._normalize_price("$10.99") == 10.99
        assert scraper._normalize_price("$1,234.56") == 1234.56
        assert scraper._normalize_price("15.00") == 15.00
        assert scraper._normalize_price("$5.99 - $7.99") == 5.99  # Range
        assert scraper._normalize_price("invalid") is None
        assert scraper._normalize_price("") is None

    def test_extract_size_and_unit(self):
        """Test size and unit extraction"""
        scraper = MockScraper()
        
        # Test various product text formats
        size, unit = scraper._extract_size_and_unit("Milk 1 gallon")
        assert size == "1"
        assert unit == "gallon"
        
        size, unit = scraper._extract_size_and_unit("Bread 24 oz loaf")
        assert size == "24"
        assert unit == "oz"
        
        size, unit = scraper._extract_size_and_unit("Eggs 12 count")
        assert size == "12"
        assert unit == "count"
        
        size, unit = scraper._extract_size_and_unit("Regular product")
        assert size is None
        assert unit is None

    def test_categorize_product(self):
        """Test product categorization"""
        scraper = MockScraper()
        
        # Test category detection
        assert scraper._categorize_product("Whole Milk 1 Gallon") == ProductCategory.MILK
        assert scraper._categorize_product("White Bread Loaf") == ProductCategory.BREAD
        assert scraper._categorize_product("Large Eggs Dozen") == ProductCategory.EGGS
        assert scraper._categorize_product("Ground Coffee") == ProductCategory.COFFEE
        assert scraper._categorize_product("Random Product") is None

    @pytest.mark.asyncio
    async def test_scraper_session_lifecycle(self):
        """Test scraper session setup and cleanup"""
        scraper = MockScraper()
        
        # Test setup
        setup_result = await scraper.setup_session()
        assert setup_result is True
        assert scraper.setup_called is True
        
        # Test cleanup
        await scraper.cleanup_session()
        assert scraper.cleanup_called is True

    @pytest.mark.asyncio
    async def test_search_products(self):
        """Test product search functionality"""
        scraper = MockScraper()
        await scraper.setup_session()
        
        # Test search
        result = await scraper.search_products("milk", ProductCategory.MILK, max_results=2)
        
        assert result.success is True
        assert result.retailer == "MockRetailer"
        assert result.search_query == "milk"
        assert len(result.products) == 2
        
        # Check product details
        product = result.products[0]
        assert product.name == "Mock Product 0 - milk"
        assert product.brand == "MockBrand"
        assert product.price == 10.99
        assert product.category == ProductCategory.MILK
        
        await scraper.cleanup_session()

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test scraper health check"""
        scraper = MockScraper()
        
        health_result = await scraper.health_check()
        
        assert health_result["retailer"] == "MockRetailer"
        assert health_result["status"] == "healthy"
        assert health_result["session_setup"] is True

    def test_get_config(self):
        """Test scraper configuration retrieval"""
        scraper = MockScraper(
            zip_code="54321",
            headless=True,
            max_pages=5
        )
        
        config = scraper.get_config()
        
        assert config["retailer_name"] == "MockRetailer"
        assert config["zip_code"] == "54321"
        assert config["headless"] is True
        assert config["max_pages"] == 5


class TestProductInfo:
    """Test ProductInfo data model"""

    def test_product_info_creation(self):
        """Test ProductInfo creation and properties"""
        product = ProductInfo(
            product_id="test_123",
            name="Test Product",
            brand="TestBrand",
            price=19.99,
            original_price=24.99,
            size="2",
            unit="lb",
            category=ProductCategory.MILK,
            on_sale=True
        )
        
        assert product.product_id == "test_123"
        assert product.name == "Test Product"
        assert product.brand == "TestBrand"
        assert product.price == 19.99
        assert product.original_price == 24.99
        assert product.effective_price == 19.99
        assert product.on_sale is True
        assert product.category == ProductCategory.MILK

    def test_normalized_price_calculation(self):
        """Test normalized price calculation"""
        # Test gallon product
        product_gallon = ProductInfo(
            product_id="milk_gal",
            name="Milk",
            price=4.99,
            size="1",
            unit="gallon"
        )
        assert product_gallon.normalized_price_per_unit == 4.99
        
        # Test quart product (should convert to gallon)
        product_quart = ProductInfo(
            product_id="milk_qt",
            name="Milk",
            price=1.49,
            size="1",
            unit="quart"
        )
        assert product_quart.normalized_price_per_unit == 5.96  # 1.49 * 4
        
        # Test pound product
        product_lb = ProductInfo(
            product_id="meat_lb",
            name="Ground Beef",
            price=6.99,
            size="1",
            unit="lb"
        )
        assert product_lb.normalized_price_per_unit == 6.99


class TestScrapingResult:
    """Test ScrapingResult data model"""

    def test_scraping_result_creation(self):
        """Test ScrapingResult creation and properties"""
        result = ScrapingResult(
            retailer="TestRetailer",
            search_query="test query"
        )
        
        assert result.retailer == "TestRetailer"
        assert result.search_query == "test query"
        assert result.products == []
        assert result.total_found == 0
        assert result.success is True

    def test_add_product(self):
        """Test adding products to result"""
        result = ScrapingResult(
            retailer="TestRetailer",
            search_query="test"
        )
        
        product = ProductInfo(
            product_id="test_1",
            name="Test Product",
            price=10.99
        )
        
        result.add_product(product)
        
        assert len(result.products) == 1
        assert result.total_found == 1
        assert result.products[0] == product

    def test_duration_calculation(self):
        """Test duration calculation"""
        result = ScrapingResult(
            retailer="TestRetailer",
            search_query="test"
        )
        
        # Duration should be calculated automatically
        assert result.duration_seconds >= 0


class TestScraperManager:
    """Test ScraperManager functionality"""

    def test_manager_initialization(self):
        """Test manager initialization"""
        # Mock the database session
        mock_db = Mock()
        manager = ScraperManager(db=mock_db)
        
        assert manager.db == mock_db
        assert "target" in manager._scraper_classes
        assert manager.default_zip_code == "55331"

    def test_register_scraper(self):
        """Test scraper registration"""
        mock_db = Mock()
        manager = ScraperManager(db=mock_db)
        
        # Register mock scraper
        manager.register_scraper("mock", MockScraper)
        
        assert "mock" in manager._scraper_classes
        assert manager._scraper_classes["mock"] == MockScraper

    def test_get_available_retailers(self):
        """Test getting available retailers"""
        mock_db = Mock()
        manager = ScraperManager(db=mock_db)
        
        retailers = manager.get_available_retailers()
        
        assert isinstance(retailers, list)
        assert "target" in retailers

    @pytest.mark.asyncio
    async def test_get_scraper(self):
        """Test getting scraper instance"""
        mock_db = Mock()
        manager = ScraperManager(db=mock_db)
        
        # Register mock scraper
        manager.register_scraper("mock", MockScraper)
        
        # Get scraper instance
        scraper = await manager.get_scraper("mock", zip_code="12345")
        
        assert scraper is not None
        assert isinstance(scraper, MockScraper)
        assert scraper.zip_code == "12345"
        assert scraper.setup_called is True
        
        # Clean up
        await manager.cleanup_all_scrapers()

    @pytest.mark.asyncio
    async def test_get_nonexistent_scraper(self):
        """Test getting non-existent scraper"""
        mock_db = Mock()
        manager = ScraperManager(db=mock_db)
        
        scraper = await manager.get_scraper("nonexistent")
        
        assert scraper is None
