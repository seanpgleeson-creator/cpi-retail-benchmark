"""
Target.com scraper implementation
"""

import asyncio
import logging
import random
from typing import List, Optional
from urllib.parse import urljoin, quote

from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError

from .base import BaseScraper, ScrapingResult, ProductInfo, ProductCategory

logger = logging.getLogger(__name__)


class TargetScraper(BaseScraper):
    """
    Scraper for Target.com product prices
    """
    
    def __init__(self, zip_code: str = "55331", **kwargs):
        super().__init__(
            retailer_name="Target",
            base_url="https://www.target.com",
            zip_code=zip_code,
            **kwargs
        )
        
        # Target-specific configuration
        self.search_url = "https://www.target.com/s"
        
        # Browser and page instances
        self._playwright = None
        self._browser = None
        self._page = None
        
        # User agents for rotation
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        ]
    
    async def setup_session(self) -> bool:
        """
        Setup Playwright browser session
        
        Returns:
            True if setup successful, False otherwise
        """
        try:
            logger.info("Setting up Target scraper session")
            
            # Launch Playwright
            self._playwright = await async_playwright().start()
            
            # Launch browser
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            # Create page with random user agent
            user_agent = random.choice(self.user_agents) if self.user_agent_rotation else self.user_agents[0]
            
            self._page = await self._browser.new_page(
                user_agent=user_agent,
                viewport={'width': 1920, 'height': 1080}
            )
            
            # Set additional headers to appear more human-like
            await self._page.set_extra_http_headers({
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            })
            
            # Navigate to Target homepage to establish session
            await self._page.goto(self.base_url, wait_until='networkidle')
            
            # Set location if zip code is provided
            if self.zip_code:
                await self._set_location(self.zip_code)
            
            logger.info("Target scraper session setup complete")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Target scraper session: {e}")
            await self.cleanup_session()
            return False
    
    async def cleanup_session(self) -> None:
        """
        Clean up browser session resources
        """
        try:
            if self._page:
                await self._page.close()
                self._page = None
            
            if self._browser:
                await self._browser.close()
                self._browser = None
            
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
            
            logger.info("Target scraper session cleaned up")
            
        except Exception as e:
            logger.error(f"Error during Target scraper cleanup: {e}")
    
    async def _set_location(self, zip_code: str) -> bool:
        """
        Set the store location for Target
        
        Args:
            zip_code: ZIP code for store location
            
        Returns:
            True if location set successfully
        """
        try:
            # Look for location/store selector
            # This is a simplified implementation - Target's actual location setting
            # might require more complex interaction
            
            # Try to find and click store locator
            store_locator = await self._page.query_selector('[data-test="store-locator-button"]')
            if store_locator:
                await store_locator.click()
                await self._page.wait_for_timeout(1000)
                
                # Enter zip code
                zip_input = await self._page.query_selector('input[placeholder*="ZIP"]')
                if zip_input:
                    await zip_input.fill(zip_code)
                    await self._page.keyboard.press('Enter')
                    await self._page.wait_for_timeout(2000)
                    
                    logger.info(f"Set Target location to ZIP: {zip_code}")
                    return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Could not set Target location: {e}")
            return False
    
    async def search_products(
        self, 
        query: str, 
        category: Optional[ProductCategory] = None,
        max_results: int = 20
    ) -> ScrapingResult:
        """
        Search for products on Target.com
        
        Args:
            query: Search query string
            category: Optional product category filter
            max_results: Maximum number of results to return
            
        Returns:
            ScrapingResult with found products
        """
        result = ScrapingResult(
            retailer=self.retailer_name,
            search_query=query,
            zip_code=self.zip_code
        )
        
        try:
            if not self._page:
                raise Exception("Scraper session not initialized")
            
            logger.info(f"Searching Target for: {query}")
            
            # Navigate to search page
            search_url = f"{self.search_url}?searchTerm={quote(query)}"
            await self._page.goto(search_url, wait_until='networkidle')
            
            # Wait for search results to load
            await self._page.wait_for_selector('[data-test="product-card"]', timeout=10000)
            
            # Extract products from search results
            products = await self._extract_products_from_page(max_results)
            
            for product in products:
                if category:
                    product.category = category
                else:
                    product.category = self._categorize_product(product.name)
                
                result.add_product(product)
            
            result.pages_scraped = 1
            result.success = True
            
            logger.info(f"Found {len(products)} products for query: {query}")
            
        except PlaywrightTimeoutError:
            result.success = False
            result.error_message = "Timeout waiting for search results"
            logger.error(f"Timeout searching Target for: {query}")
            
        except Exception as e:
            result.success = False
            result.error_message = str(e)
            logger.error(f"Error searching Target for {query}: {e}")
        
        finally:
            result.completed_at = result.completed_at or result.started_at
        
        return result
    
    async def _extract_products_from_page(self, max_results: int) -> List[ProductInfo]:
        """
        Extract product information from current search results page
        
        Args:
            max_results: Maximum number of products to extract
            
        Returns:
            List of ProductInfo objects
        """
        products = []
        
        try:
            # Get all product cards
            product_cards = await self._page.query_selector_all('[data-test="product-card"]')
            
            for i, card in enumerate(product_cards[:max_results]):
                if i >= max_results:
                    break
                
                try:
                    product = await self._extract_product_from_card(card)
                    if product:
                        products.append(product)
                        
                        # Add delay between extractions
                        await self._random_delay()
                        
                except Exception as e:
                    logger.warning(f"Failed to extract product {i}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error extracting products from page: {e}")
        
        return products
    
    async def _extract_product_from_card(self, card_element) -> Optional[ProductInfo]:
        """
        Extract product information from a single product card
        
        Args:
            card_element: Playwright element for product card
            
        Returns:
            ProductInfo object or None if extraction failed
        """
        try:
            # Extract product name
            name_element = await card_element.query_selector('[data-test="product-title"]')
            name = await name_element.inner_text() if name_element else "Unknown Product"
            
            # Extract price
            price_element = await card_element.query_selector('[data-test="product-price"]')
            price_text = await price_element.inner_text() if price_element else None
            price = self._normalize_price(price_text) if price_text else None
            
            if not price:
                return None
            
            # Extract original price (if on sale)
            original_price_element = await card_element.query_selector('[data-test="product-price-original"]')
            original_price_text = await original_price_element.inner_text() if original_price_element else None
            original_price = self._normalize_price(original_price_text) if original_price_text else None
            
            # Extract product URL
            link_element = await card_element.query_selector('a')
            relative_url = await link_element.get_attribute('href') if link_element else None
            product_url = urljoin(self.base_url, relative_url) if relative_url else None
            
            # Extract image URL
            img_element = await card_element.query_selector('img')
            image_url = await img_element.get_attribute('src') if img_element else None
            
            # Extract brand (if available)
            brand_element = await card_element.query_selector('[data-test="product-brand"]')
            brand = await brand_element.inner_text() if brand_element else None
            
            # Extract size and unit from product name
            size, unit = self._extract_size_and_unit(name)
            
            # Check if product is on sale
            on_sale = original_price is not None and original_price > price
            discount_percent = None
            if on_sale and original_price:
                discount_percent = ((original_price - price) / original_price) * 100
            
            # Generate product ID (simplified)
            product_id = f"target_{hash(name + str(price))}"
            
            return ProductInfo(
                product_id=product_id,
                name=name.strip(),
                brand=brand.strip() if brand else None,
                price=price,
                original_price=original_price,
                size=size,
                unit=unit,
                on_sale=on_sale,
                discount_percent=discount_percent,
                url=product_url,
                image_url=image_url,
                zip_code=self.zip_code,
            )
            
        except Exception as e:
            logger.warning(f"Failed to extract product from card: {e}")
            return None
    
    async def get_product_details(self, product_url: str) -> Optional[ProductInfo]:
        """
        Get detailed information about a specific product
        
        Args:
            product_url: URL of the product page
            
        Returns:
            ProductInfo with detailed product data or None if failed
        """
        try:
            if not self._page:
                raise Exception("Scraper session not initialized")
            
            logger.info(f"Getting Target product details: {product_url}")
            
            # Navigate to product page
            await self._page.goto(product_url, wait_until='networkidle')
            
            # Wait for product details to load
            await self._page.wait_for_selector('[data-test="product-title"]', timeout=10000)
            
            # Extract detailed product information
            # This would include more comprehensive extraction logic
            # For now, return basic info similar to card extraction
            
            name_element = await self._page.query_selector('[data-test="product-title"]')
            name = await name_element.inner_text() if name_element else "Unknown Product"
            
            price_element = await self._page.query_selector('[data-test="product-price"]')
            price_text = await price_element.inner_text() if price_element else None
            price = self._normalize_price(price_text) if price_text else None
            
            if not price:
                return None
            
            # Extract more detailed information available on product page
            description_element = await self._page.query_selector('[data-test="item-details-description"]')
            description = await description_element.inner_text() if description_element else None
            
            size, unit = self._extract_size_and_unit(name + (description or ""))
            
            product_id = f"target_{hash(product_url)}"
            
            return ProductInfo(
                product_id=product_id,
                name=name.strip(),
                price=price,
                size=size,
                unit=unit,
                description=description.strip() if description else None,
                url=product_url,
                zip_code=self.zip_code,
            )
            
        except Exception as e:
            logger.error(f"Failed to get Target product details: {e}")
            return None
    
    async def _random_delay(self) -> None:
        """
        Add random delay between requests to appear more human-like
        """
        min_delay, max_delay = self.delay_range_ms
        delay_ms = random.randint(min_delay, max_delay)
        await asyncio.sleep(delay_ms / 1000.0)
    
    async def search_by_category(self, category: ProductCategory, max_results: int = 20) -> ScrapingResult:
        """
        Search for products by category
        
        Args:
            category: Product category to search for
            max_results: Maximum number of results
            
        Returns:
            ScrapingResult with category products
        """
        # Map categories to Target search terms
        category_queries = {
            ProductCategory.MILK: "milk dairy",
            ProductCategory.GASOLINE: "gas fuel",  # Note: Target doesn't sell gasoline
            ProductCategory.BREAD: "bread loaf",
            ProductCategory.EGGS: "eggs dozen",
            ProductCategory.CHICKEN: "chicken breast",
            ProductCategory.GROUND_BEEF: "ground beef",
            ProductCategory.BANANAS: "bananas",
            ProductCategory.APPLES: "apples",
            ProductCategory.COFFEE: "coffee",
            ProductCategory.SUGAR: "sugar",
        }
        
        query = category_queries.get(category, category.value)
        return await self.search_products(query, category, max_results)
    
    def get_supported_categories(self) -> List[ProductCategory]:
        """
        Get list of product categories supported by Target
        
        Returns:
            List of supported ProductCategory values
        """
        # Target doesn't sell gasoline, so exclude it
        return [
            ProductCategory.MILK,
            ProductCategory.BREAD,
            ProductCategory.EGGS,
            ProductCategory.CHICKEN,
            ProductCategory.GROUND_BEEF,
            ProductCategory.BANANAS,
            ProductCategory.APPLES,
            ProductCategory.COFFEE,
            ProductCategory.SUGAR,
        ]
