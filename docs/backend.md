# Backend Architecture Analysis

## Overview

This system requires a robust backend architecture that handles daily retailer price scraping, BLS API integration, and time-period aggregation for comparison analysis. The key architectural principle is to scrape retailer data daily and aggregate it into periods defined by BLS release cycles, then compare the delta between consecutive periods when new BLS data becomes available.

## Core Backend Components

### 1. **Data Storage Layer (SQLite + SQLAlchemy)**

#### Database Schema Design

**BLS Data Tables:**
```sql
-- BLS series metadata
CREATE TABLE bls_series (
    id VARCHAR(20) PRIMARY KEY,  -- e.g., 'CUUR0000SEFJ01'
    title TEXT NOT NULL,
    units VARCHAR(50),
    frequency CHAR(1),  -- 'M' for monthly
    seasonal_adjustment VARCHAR(10),  -- 'NSA', 'SA'
    series_type VARCHAR(20),  -- 'CPI-U', 'APU'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- BLS time series observations
CREATE TABLE bls_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    series_id VARCHAR(20) REFERENCES bls_series(id),
    period VARCHAR(7),  -- 'YYYY-MM' format
    value DECIMAL(10,4),
    footnotes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(series_id, period)
);
```

**Retailer and Product Tables:**
```sql
-- Retailer configuration
CREATE TABLE retailers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) UNIQUE NOT NULL,  -- 'Target', 'Walmart', 'Kroger'
    base_url TEXT,
    scraping_enabled BOOLEAN DEFAULT TRUE,
    last_scrape_at TIMESTAMP,
    scrape_frequency_hours INTEGER DEFAULT 24,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Product catalog across all retailers
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    retailer_id INTEGER REFERENCES retailers(id),
    external_id VARCHAR(50),  -- retailer's product ID (TCIN, UPC, etc.)
    title TEXT NOT NULL,
    brand TEXT,
    category TEXT,  -- matches BLS category structure
    bls_series_id VARCHAR(20),  -- links to BLS product category
    size_qty DECIMAL(8,2),
    size_unit VARCHAR(10),
    normalized_unit_qty DECIMAL(8,4),  -- normalized to BLS unit (gallon, pound, etc.)
    url TEXT,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(retailer_id, external_id),
    INDEX(retailer_id, category),
    INDEX(bls_series_id)
);

-- Daily price observations
CREATE TABLE daily_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER REFERENCES products(id),
    retailer_id INTEGER REFERENCES retailers(id),
    zip_code VARCHAR(5),
    price DECIMAL(8,2),
    unit_price_normalized DECIMAL(8,4),  -- price per normalized unit
    availability BOOLEAN DEFAULT TRUE,
    scrape_date DATE,  -- date of scraping (not timestamp)
    observed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, zip_code, scrape_date),
    INDEX(retailer_id, scrape_date),
    INDEX(product_id, scrape_date),
    INDEX(zip_code, scrape_date)
);
```

**BLS Release Tracking and Aggregation Tables:**
```sql
-- Track BLS data release cycles
CREATE TABLE bls_releases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    release_date DATE NOT NULL,
    data_period VARCHAR(7),  -- 'YYYY-MM' - the month the data represents
    series_ids TEXT,  -- JSON array of series IDs updated
    is_processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(release_date, data_period)
);

-- Aggregated retailer data for BLS comparison periods
CREATE TABLE retailer_period_aggregates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    retailer_id INTEGER REFERENCES retailers(id),
    bls_series_id VARCHAR(20),
    zip_code VARCHAR(5),
    period_start DATE,
    period_end DATE,
    bls_release_id INTEGER REFERENCES bls_releases(id),
    
    -- Aggregated metrics
    avg_price_normalized DECIMAL(8,4),
    median_price_normalized DECIMAL(8,4),
    price_std_dev DECIMAL(8,4),
    sample_size INTEGER,
    days_with_data INTEGER,
    
    -- Comparison metrics (calculated when BLS data available)
    bls_avg_price DECIMAL(8,4),
    price_gap_amount DECIMAL(8,4),
    price_gap_percent DECIMAL(6,3),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(retailer_id, bls_series_id, zip_code, bls_release_id),
    INDEX(retailer_id, period_start),
    INDEX(bls_series_id, period_start)
);

-- Period-over-period comparison results
CREATE TABLE period_comparisons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    current_period_id INTEGER REFERENCES retailer_period_aggregates(id),
    previous_period_id INTEGER REFERENCES retailer_period_aggregates(id),
    
    -- Retailer delta metrics
    retailer_price_change_amount DECIMAL(8,4),
    retailer_price_change_percent DECIMAL(6,3),
    
    -- BLS delta metrics  
    bls_price_change_amount DECIMAL(8,4),
    bls_price_change_percent DECIMAL(6,3),
    
    -- Comparison verdict
    delta_difference_pp DECIMAL(6,3),  -- percentage points difference
    verdict VARCHAR(20),  -- 'ABOVE', 'INLINE', 'BELOW'
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(current_period_id, previous_period_id)
);
```

#### SQLAlchemy Models Structure

```python
# /db/models.py
from sqlalchemy import Column, Integer, String, Decimal, Boolean, DateTime, Date, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, date

Base = declarative_base()

class Retailer(Base):
    __tablename__ = 'retailers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    base_url = Column(Text)
    scraping_enabled = Column(Boolean, default=True)
    last_scrape_at = Column(DateTime)
    scrape_frequency_hours = Column(Integer, default=24)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    products = relationship("Product", back_populates="retailer")
    daily_prices = relationship("DailyPrice", back_populates="retailer")

class BLSSeries(Base):
    __tablename__ = 'bls_series'
    
    id = Column(String(20), primary_key=True)
    title = Column(Text, nullable=False)
    units = Column(String(50))
    frequency = Column(String(1))
    seasonal_adjustment = Column(String(10))
    series_type = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    observations = relationship("BLSObservation", back_populates="series")
    products = relationship("Product", back_populates="bls_series")

class BLSObservation(Base):
    __tablename__ = 'bls_observations'
    
    id = Column(Integer, primary_key=True)
    series_id = Column(String(20), ForeignKey('bls_series.id'))
    period = Column(String(7))  # YYYY-MM
    value = Column(Decimal(10, 4))
    footnotes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    series = relationship("BLSSeries", back_populates="observations")

class BLSRelease(Base):
    __tablename__ = 'bls_releases'
    
    id = Column(Integer, primary_key=True)
    release_date = Column(Date, nullable=False)
    data_period = Column(String(7))  # YYYY-MM
    series_ids = Column(Text)  # JSON array
    is_processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    period_aggregates = relationship("RetailerPeriodAggregate", back_populates="bls_release")

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    retailer_id = Column(Integer, ForeignKey('retailers.id'))
    external_id = Column(String(50))  # retailer's product ID
    title = Column(Text, nullable=False)
    brand = Column(Text)
    category = Column(Text)
    bls_series_id = Column(String(20), ForeignKey('bls_series.id'))
    size_qty = Column(Decimal(8, 2))
    size_unit = Column(String(10))
    normalized_unit_qty = Column(Decimal(8, 4))
    url = Column(Text)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    retailer = relationship("Retailer", back_populates="products")
    bls_series = relationship("BLSSeries", back_populates="products")
    daily_prices = relationship("DailyPrice", back_populates="product")

class DailyPrice(Base):
    __tablename__ = 'daily_prices'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    retailer_id = Column(Integer, ForeignKey('retailers.id'))
    zip_code = Column(String(5))
    price = Column(Decimal(8, 2))
    unit_price_normalized = Column(Decimal(8, 4))
    availability = Column(Boolean, default=True)
    scrape_date = Column(Date)
    observed_at = Column(DateTime, default=datetime.utcnow)
    
    product = relationship("Product", back_populates="daily_prices")
    retailer = relationship("Retailer", back_populates="daily_prices")

class RetailerPeriodAggregate(Base):
    __tablename__ = 'retailer_period_aggregates'
    
    id = Column(Integer, primary_key=True)
    retailer_id = Column(Integer, ForeignKey('retailers.id'))
    bls_series_id = Column(String(20))
    zip_code = Column(String(5))
    period_start = Column(Date)
    period_end = Column(Date)
    bls_release_id = Column(Integer, ForeignKey('bls_releases.id'))
    
    # Aggregated metrics
    avg_price_normalized = Column(Decimal(8, 4))
    median_price_normalized = Column(Decimal(8, 4))
    price_std_dev = Column(Decimal(8, 4))
    sample_size = Column(Integer)
    days_with_data = Column(Integer)
    
    # Comparison metrics
    bls_avg_price = Column(Decimal(8, 4))
    price_gap_amount = Column(Decimal(8, 4))
    price_gap_percent = Column(Decimal(6, 3))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    bls_release = relationship("BLSRelease", back_populates="period_aggregates")

class PeriodComparison(Base):
    __tablename__ = 'period_comparisons'
    
    id = Column(Integer, primary_key=True)
    current_period_id = Column(Integer, ForeignKey('retailer_period_aggregates.id'))
    previous_period_id = Column(Integer, ForeignKey('retailer_period_aggregates.id'))
    
    # Delta metrics
    retailer_price_change_amount = Column(Decimal(8, 4))
    retailer_price_change_percent = Column(Decimal(6, 3))
    bls_price_change_amount = Column(Decimal(8, 4))
    bls_price_change_percent = Column(Decimal(6, 3))
    
    # Verdict
    delta_difference_pp = Column(Decimal(6, 3))
    verdict = Column(String(20))
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 2. **BLS API Integration Layer**

#### API Client Architecture (`/bls_client/api.py`)

```python
# Core BLS API client with retry logic
class BLSAPIClient:
    def __init__(self, api_key: Optional[str] = None):
        self.base_url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
        self.api_key = api_key
        self.session = requests.Session()
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((requests.RequestException, requests.Timeout))
    )
    def get_series_data(self, series_ids: List[str], start_year: int, end_year: int) -> Dict:
        """Fetch time series data with automatic retry and rate limiting"""
        
    def validate_series_response(self, response_data: Dict) -> bool:
        """Validate BLS API response structure and data quality"""
        
    def parse_observations(self, series_data: Dict) -> List[BLSObservation]:
        """Parse BLS response into structured observation objects"""
```

#### Data Synchronization Logic (`/bls_client/compute.py`)

```python
class BLSDataProcessor:
    def __init__(self, db_session: Session):
        self.db = db_session
        
    def sync_series_data(self, series_ids: List[str]) -> SyncResult:
        """Synchronize BLS data with local database"""
        
    def compute_mom_change(self, series_id: str, target_period: str) -> Optional[Decimal]:
        """Calculate month-over-month percentage change"""
        # Formula: (current_month / previous_month - 1) * 100
        
    def compute_yoy_change(self, series_id: str, target_period: str) -> Optional[Decimal]:
        """Calculate year-over-year percentage change"""
        # Formula: (current_month / same_month_previous_year - 1) * 100
        
    def compute_rebased_index(self, series_id: str, base_period: str = None) -> List[Tuple]:
        """Generate rebased index with base=100 at specified period"""
        # Default base: first observation in database
```

#### Error Handling & Resilience

```python
# BLS API error handling patterns
class BLSAPIError(Exception):
    """Base exception for BLS API issues"""
    
class BLSRateLimitError(BLSAPIError):
    """Rate limit exceeded"""
    
class BLSDataValidationError(BLSAPIError):
    """Data validation failed"""

# Fallback strategies
def get_latest_bls_data_with_fallback(series_id: str) -> BLSObservation:
    """
    Try fresh API call, fall back to cached data if API unavailable
    Log warnings about data staleness
    """
```

### 3. **Daily Scraping Layer (Multi-Retailer)**

#### Daily Scraping Orchestrator (`/scrapers/daily_scraper.py`)

```python
class DailyScrapeOrchestrator:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.scrapers = {
            'Target': TargetScraper(),
            'Walmart': WalmartScraper(),
            'Kroger': KrogerScraper(),
            # Additional retailers...
        }
        
    async def run_daily_scrapes(self) -> DailyScrapeResult:
        """Execute daily scraping for all enabled retailers"""
        scrape_date = date.today()
        results = []
        
        # Get all enabled retailers
        retailers = self.db.query(Retailer).filter(
            Retailer.scraping_enabled == True
        ).all()
        
        # Run scrapers in parallel (with rate limiting)
        scrape_tasks = []
        for retailer in retailers:
            if self.should_scrape_retailer(retailer):
                task = self.scrape_retailer_products(retailer, scrape_date)
                scrape_tasks.append(task)
                
        # Execute with concurrency limit
        semaphore = asyncio.Semaphore(3)  # Max 3 concurrent scrapers
        results = await asyncio.gather(*[
            self.scrape_with_semaphore(semaphore, task) 
            for task in scrape_tasks
        ])
        
        return DailyScrapeResult(
            scrape_date=scrape_date,
            retailer_results=results,
            total_products_updated=sum(r.products_updated for r in results)
        )
        
    def should_scrape_retailer(self, retailer: Retailer) -> bool:
        """Check if retailer should be scraped today based on frequency"""
        if not retailer.last_scrape_at:
            return True
            
        hours_since_last = (datetime.utcnow() - retailer.last_scrape_at).total_seconds() / 3600
        return hours_since_last >= retailer.scrape_frequency_hours
        
    async def scrape_retailer_products(self, retailer: Retailer, scrape_date: date) -> RetailerScrapeResult:
        """Scrape all products for a specific retailer"""
        scraper = self.scrapers.get(retailer.name)
        if not scraper:
            raise ValueError(f"No scraper configured for {retailer.name}")
            
        # Get configured ZIP codes for this retailer
        zip_codes = self.get_retailer_zip_codes(retailer)
        
        all_price_data = []
        for zip_code in zip_codes:
            try:
                # Scrape products for this ZIP code
                price_data = await scraper.scrape_products(zip_code, scrape_date)
                all_price_data.extend(price_data)
                
                # Rate limiting between ZIP codes
                await asyncio.sleep(random.uniform(2, 5))
                
            except Exception as e:
                logger.error(f"Failed to scrape {retailer.name} for ZIP {zip_code}: {e}")
                continue
                
        # Store the scraped data
        products_updated = self.store_daily_prices(retailer, all_price_data, scrape_date)
        
        # Update retailer's last scrape timestamp
        retailer.last_scrape_at = datetime.utcnow()
        self.db.commit()
        
        return RetailerScrapeResult(
            retailer_name=retailer.name,
            products_updated=products_updated,
            zip_codes_scraped=len(zip_codes),
            scrape_duration=time.time() - start_time
        )
            
    async def set_store_location(self, page: Page, zip_code: str):
        """Set Target store location via UI interaction"""
        # Navigate to store locator
        # Input ZIP code
        # Select store for fulfillment
        # Verify location is set
        
    async def search_milk_category(self, page: Page) -> List[ProductData]:
        """Search dairy category, filter for milk"""
        await page.goto(f"https://www.target.com/c/dairy-refrigerated-grocery/-/N-5xt2r")
        return await self.extract_products_from_listing(page)
        
    async def search_milk_keyword(self, page: Page) -> List[ProductData]:
        """Search 'milk' keyword"""
        await page.goto(f"https://www.target.com/s?searchTerm=milk")
        return await self.extract_products_from_listing(page)
        
    async def extract_products_from_listing(self, page: Page) -> List[ProductData]:
        """Extract product data from listing pages with pagination"""
        products = []
        page_count = 0
        max_pages = int(os.getenv('SCRAPE_MAX_PAGES', 5))
        
        while page_count < max_pages:
            # Extract product cards
            product_cards = await page.query_selector_all('[data-test="product-card"]')
            
            for card in product_cards:
                try:
                    product = await self.extract_product_data(card)
                    if self.is_gallon_milk_product(product):
                        products.append(product)
                except Exception as e:
                    logger.warning(f"Failed to extract product: {e}")
                    
            # Handle pagination
            next_button = await page.query_selector('[data-test="next"]')
            if not next_button or not await next_button.is_enabled():
                break
                
            await self.rate_limiter.wait()
            await next_button.click()
            await page.wait_for_load_state('networkidle')
            page_count += 1
            
        return products
        
    def is_gallon_milk_product(self, product: ProductData) -> bool:
        """Filter logic for gallon-equivalent milk products"""
        # Check title contains "milk"
        # Check size is gallon or half-gallon equivalent
        # Exclude non-dairy alternatives (configurable)
        # Check for whole/2%/skim varieties
```

#### Rate Limiting & Anti-Detection (`/scrapers/target/rate_limiter.py`)

```python
class RateLimiter:
    def __init__(self, requests_per_second: float = 0.5):
        self.min_delay = 1.0 / requests_per_second
        self.last_request = 0
        self.delay_range = self.parse_delay_range()
        
    def parse_delay_range(self) -> Tuple[float, float]:
        """Parse SCRAPE_DELAY_RANGE_MS env var (e.g., '500-1500')"""
        range_str = os.getenv('SCRAPE_DELAY_RANGE_MS', '500-1500')
        min_ms, max_ms = map(int, range_str.split('-'))
        return min_ms / 1000.0, max_ms / 1000.0
        
    async def wait(self):
        """Apply rate limiting with jitter"""
        elapsed = time.time() - self.last_request
        base_delay = max(0, self.min_delay - elapsed)
        jitter = random.uniform(*self.delay_range)
        total_delay = base_delay + jitter
        
        if total_delay > 0:
            await asyncio.sleep(total_delay)
            
        self.last_request = time.time()

class UserAgentRotator:
    def __init__(self):
        self.agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ...",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...",
            # Rotate through realistic user agents
        ]
        
    def get_random_agent(self) -> str:
        return random.choice(self.agents)
```

#### Product Normalization (`/scrapers/target/normalize.py`)

```python
class SizeNormalizer:
    """Convert various size formats to standardized gallon measurements"""
    
    CONVERSION_FACTORS = {
        'fl oz': 1/128,      # 1 gallon = 128 fl oz
        'oz': 1/128,         # assume fl oz for liquids
        'qt': 1/4,           # 1 gallon = 4 quarts
        'pt': 1/8,           # 1 gallon = 8 pints
        'gal': 1,            # base unit
        'gallon': 1,
        'l': 33.814/128,     # 1 liter ≈ 33.814 fl oz
        'ml': 33.814/128000, # 1000 ml = 1 liter
    }
    
    def __init__(self):
        # Regex for size parsing: (number)(optional decimal)(unit)
        self.size_pattern = re.compile(
            r'(\d+(?:\.\d+)?)\s*(fl\s*oz|oz|qt|pt|gal|gallon|ml|l)\b',
            re.IGNORECASE
        )
        
    def parse_size(self, size_text: str) -> Tuple[float, str]:
        """Extract quantity and unit from size text"""
        match = self.size_pattern.search(size_text)
        if match:
            qty = float(match.group(1))
            unit = match.group(2).lower().replace(' ', '')
            return qty, unit
        raise ValueError(f"Could not parse size: {size_text}")
        
    def normalize_to_gallons(self, qty: float, unit: str) -> float:
        """Convert quantity and unit to gallon equivalent"""
        unit_clean = unit.lower().replace(' ', '')
        if unit_clean not in self.CONVERSION_FACTORS:
            raise ValueError(f"Unknown unit: {unit}")
        return qty * self.CONVERSION_FACTORS[unit_clean]
        
    def calculate_price_per_gallon(self, price: float, qty: float, unit: str) -> float:
        """Calculate normalized price per gallon"""
        gallons = self.normalize_to_gallons(qty, unit)
        return price / gallons if gallons > 0 else 0
```

### 4. **BLS Release Tracking and Period Aggregation**

#### BLS Release Monitor (`/bls_client/release_monitor.py`)

```python
class BLSReleaseMonitor:
    """Monitor BLS data releases and trigger aggregation"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.bls_client = BLSAPIClient()
        
    async def check_for_new_releases(self) -> List[BLSRelease]:
        """Check for new BLS data releases"""
        # BLS typically releases data on 2nd Tuesday of month at 8:30 AM ET
        # Check if today is a likely release date
        today = date.today()
        
        # Get latest release we've processed
        latest_processed = self.db.query(BLSRelease).order_by(
            BLSRelease.release_date.desc()
        ).first()
        
        # Check BLS API for new data since last processed release
        new_releases = []
        if self.is_likely_release_date(today):
            series_with_updates = await self.check_bls_series_for_updates()
            
            if series_with_updates:
                release = self.create_bls_release_record(today, series_with_updates)
                new_releases.append(release)
                
        return new_releases
        
    def create_bls_release_record(self, release_date: date, series_data: Dict) -> BLSRelease:
        """Create BLS release record and trigger aggregation"""
        # Determine data period from the series data
        data_period = self.extract_data_period(series_data)
        
        release = BLSRelease(
            release_date=release_date,
            data_period=data_period,
            series_ids=json.dumps(list(series_data.keys())),
            is_processed=False
        )
        
        self.db.add(release)
        self.db.commit()
        
        # Trigger period aggregation
        self.trigger_period_aggregation(release)
        
        return release
        
    def trigger_period_aggregation(self, bls_release: BLSRelease):
        """Trigger aggregation of retailer data for the new BLS release period"""
        # Calculate the period boundaries
        period_end = datetime.strptime(bls_release.data_period, '%Y-%m').date()
        
        # Find previous BLS release to determine period start
        previous_release = self.db.query(BLSRelease).filter(
            BLSRelease.release_date < bls_release.release_date
        ).order_by(BLSRelease.release_date.desc()).first()
        
        if previous_release:
            period_start = datetime.strptime(previous_release.data_period, '%Y-%m').date()
        else:
            # First release - use 1 month back
            period_start = period_end.replace(day=1) - timedelta(days=1)
            period_start = period_start.replace(day=1)
            
        # Aggregate retailer data for this period
        aggregation_engine = RetailerAggregationEngine(self.db)
        aggregation_engine.aggregate_period(
            period_start=period_start,
            period_end=period_end,
            bls_release=bls_release
        )

#### Retailer Data Aggregation Engine (`/aggregation/period_aggregator.py`)

```python
class RetailerAggregationEngine:
    """Aggregate daily retailer data into BLS comparison periods"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        
    def aggregate_period(self, period_start: date, period_end: date, bls_release: BLSRelease):
        """Aggregate retailer data for the specified period"""
        
        # Get all active retailers and their BLS series mappings
        retailer_series_combinations = self.get_retailer_series_combinations()
        
        for retailer_id, bls_series_id in retailer_series_combinations:
            # Get all ZIP codes with data for this retailer/series
            zip_codes = self.get_zip_codes_with_data(retailer_id, bls_series_id, period_start, period_end)
            
            for zip_code in zip_codes:
                aggregate = self.create_period_aggregate(
                    retailer_id=retailer_id,
                    bls_series_id=bls_series_id,
                    zip_code=zip_code,
                    period_start=period_start,
                    period_end=period_end,
                    bls_release=bls_release
                )
                
                if aggregate:
                    self.db.add(aggregate)
                    
        self.db.commit()
        
        # Mark BLS release as processed
        bls_release.is_processed = True
        self.db.commit()
        
        # Trigger comparison with previous period
        self.trigger_period_comparisons(bls_release)
        
    def create_period_aggregate(self, retailer_id: int, bls_series_id: str, 
                              zip_code: str, period_start: date, period_end: date,
                              bls_release: BLSRelease) -> RetailerPeriodAggregate:
        """Create aggregated metrics for a retailer/series/location/period"""
        
        # Get daily prices for this period
        daily_prices = self.db.query(DailyPrice).join(Product).filter(
            DailyPrice.retailer_id == retailer_id,
            Product.bls_series_id == bls_series_id,
            DailyPrice.zip_code == zip_code,
            DailyPrice.scrape_date >= period_start,
            DailyPrice.scrape_date <= period_end,
            DailyPrice.availability == True
        ).all()
        
        if not daily_prices:
            return None
            
        # Calculate aggregated metrics
        prices = [p.unit_price_normalized for p in daily_prices]
        
        avg_price = statistics.mean(prices)
        median_price = statistics.median(prices)
        price_std_dev = statistics.stdev(prices) if len(prices) > 1 else 0
        sample_size = len(prices)
        
        # Count unique days with data
        unique_dates = set(p.scrape_date for p in daily_prices)
        days_with_data = len(unique_dates)
        
        # Get corresponding BLS data
        bls_observation = self.get_bls_observation(bls_series_id, bls_release.data_period)
        bls_avg_price = bls_observation.value if bls_observation else None
        
        # Calculate comparison metrics
        price_gap_amount = avg_price - bls_avg_price if bls_avg_price else None
        price_gap_percent = (price_gap_amount / bls_avg_price * 100) if bls_avg_price else None
        
        return RetailerPeriodAggregate(
            retailer_id=retailer_id,
            bls_series_id=bls_series_id,
            zip_code=zip_code,
            period_start=period_start,
            period_end=period_end,
            bls_release_id=bls_release.id,
            avg_price_normalized=avg_price,
            median_price_normalized=median_price,
            price_std_dev=price_std_dev,
            sample_size=sample_size,
            days_with_data=days_with_data,
            bls_avg_price=bls_avg_price,
            price_gap_amount=price_gap_amount,
            price_gap_percent=price_gap_percent
        )
        
    def apply_selection_policy(self, products: List[Product]) -> List[Product]:
        """
        MVP Policy:
        1. Prefer 1-gallon sizes over normalized half-gallons
        2. Must include Good & Gather (store brand)
        3. Must include at least one national brand (Kemps, Land O'Lakes, etc.)
        4. Maximum 4 SKUs total
        5. All must be in stock and have recent price data
        """
        
        # Filter for in-stock gallon products
        gallon_products = [p for p in products if p.normalized_gallons >= 0.95]  # ~1 gallon
        in_stock = [p for p in gallon_products if self.is_in_stock(p)]
        
        # Categorize by brand type
        store_brand = [p for p in in_stock if 'good & gather' in p.brand.lower()]
        national_brands = [p for p in in_stock if p not in store_brand]
        
        selected = []
        
        # Select store brand (required)
        if store_brand:
            selected.append(store_brand[0])  # Pick first available
            
        # Select national brand(s)
        for brand_product in national_brands[:2]:  # Max 2 national brands
            selected.append(brand_product)
            
        if len(selected) < 2:
            logger.warning("Could not find minimum 2 SKUs meeting criteria")
            
        return selected[:4]  # Cap at 4 SKUs
        
    def freeze_basket_prices(self, basket: Basket) -> None:
        """Snapshot current prices for basket items"""
        for item in basket.items:
            latest_price = self.get_latest_price(item.product_id, basket.zip_code)
            item.selected_price_id = latest_price.id
            self.db.commit()
```

#### Basket Computation (`/basket/compute.py`)

```python
class BasketCalculator:
    """Calculate basket metrics and changes over time"""
    
    def compute_basket_average(self, basket: Basket) -> Decimal:
        """Calculate weighted average price per gallon for basket"""
        total_weighted_price = Decimal(0)
        total_weight = Decimal(0)
        
        for item in basket.items:
            weight = item.weight or Decimal(1.0)  # Equal weights by default
            price_per_gal = item.selected_price.unit_price_per_gal
            
            total_weighted_price += price_per_gal * weight
            total_weight += weight
            
        return total_weighted_price / total_weight if total_weight > 0 else Decimal(0)
        
    def compute_basket_mom_change(self, current_month: str, zip_code: str) -> Optional[Decimal]:
        """Calculate month-over-month change in basket average"""
        current_basket = self.get_basket(current_month, zip_code)
        previous_month = self.get_previous_month(current_month)
        previous_basket = self.get_basket(previous_month, zip_code)
        
        if not (current_basket and previous_basket):
            return None
            
        current_avg = self.compute_basket_average(current_basket)
        previous_avg = self.compute_basket_average(previous_basket)
        
        if previous_avg == 0:
            return None
            
        return ((current_avg / previous_avg) - 1) * 100
```

### 5. **Period Comparison Engine**

#### Period-over-Period Comparison Logic (`/comparison/period_comparisons.py`)

```python
class PeriodComparisonEngine:
    """Compare retailer price changes vs BLS changes between periods"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        
    def trigger_period_comparisons(self, current_bls_release: BLSRelease):
        """Generate comparisons between current and previous periods"""
        
        # Get previous BLS release
        previous_release = self.db.query(BLSRelease).filter(
            BLSRelease.release_date < current_bls_release.release_date
        ).order_by(BLSRelease.release_date.desc()).first()
        
        if not previous_release:
            logger.info("No previous release found - skipping period comparison")
            return
            
        # Get all current period aggregates
        current_aggregates = self.db.query(RetailerPeriodAggregate).filter(
            RetailerPeriodAggregate.bls_release_id == current_bls_release.id
        ).all()
        
        for current_aggregate in current_aggregates:
            # Find corresponding previous period aggregate
            previous_aggregate = self.find_matching_previous_aggregate(
                current_aggregate, previous_release
            )
            
            if previous_aggregate:
                comparison = self.create_period_comparison(
                    current_aggregate, previous_aggregate
                )
                self.db.add(comparison)
                
        self.db.commit()
        
    def find_matching_previous_aggregate(self, current_aggregate: RetailerPeriodAggregate, 
                                       previous_release: BLSRelease) -> RetailerPeriodAggregate:
        """Find the matching aggregate from the previous period"""
        return self.db.query(RetailerPeriodAggregate).filter(
            RetailerPeriodAggregate.bls_release_id == previous_release.id,
            RetailerPeriodAggregate.retailer_id == current_aggregate.retailer_id,
            RetailerPeriodAggregate.bls_series_id == current_aggregate.bls_series_id,
            RetailerPeriodAggregate.zip_code == current_aggregate.zip_code
        ).first()
        
    def create_period_comparison(self, current: RetailerPeriodAggregate, 
                               previous: RetailerPeriodAggregate) -> PeriodComparison:
        """Create comparison between two periods"""
        
        # Calculate retailer price changes
        retailer_price_change_amount = current.avg_price_normalized - previous.avg_price_normalized
        retailer_price_change_percent = (
            (current.avg_price_normalized / previous.avg_price_normalized - 1) * 100
            if previous.avg_price_normalized > 0 else 0
        )
        
        # Calculate BLS price changes
        bls_price_change_amount = current.bls_avg_price - previous.bls_avg_price
        bls_price_change_percent = (
            (current.bls_avg_price / previous.bls_avg_price - 1) * 100
            if previous.bls_avg_price > 0 else 0
        )
        
        # Calculate delta difference in percentage points
        delta_difference_pp = retailer_price_change_percent - bls_price_change_percent
        
        # Generate verdict based on ±0.2pp threshold
        verdict = self.generate_verdict(delta_difference_pp)
        
        return PeriodComparison(
            current_period_id=current.id,
            previous_period_id=previous.id,
            retailer_price_change_amount=retailer_price_change_amount,
            retailer_price_change_percent=retailer_price_change_percent,
            bls_price_change_amount=bls_price_change_amount,
            bls_price_change_percent=bls_price_change_percent,
            delta_difference_pp=delta_difference_pp,
            verdict=verdict
        )
        
    def generate_verdict(self, delta_difference_pp: float) -> str:
        """
        Generate verdict based on delta difference threshold
        ±0.2pp = INLINE, else ABOVE/BELOW
        """
        if abs(delta_difference_pp) <= 0.2:
            return "INLINE"
        elif delta_difference_pp > 0.2:
            return "ABOVE"
        else:
            return "BELOW"

#### Multi-Retailer Comparison Report Generator (`/reports/multi_retailer_report.py`)

```python
class MultiRetailerReportGenerator:
    """Generate comprehensive reports across multiple retailers"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        
    def generate_latest_comparison_report(self, 
                                        retailer_ids: List[int] = None,
                                        bls_series_ids: List[str] = None,
                                        zip_codes: List[str] = None) -> MultiRetailerReport:
        """Generate report for the latest BLS release across selected criteria"""
        
        # Get latest BLS release
        latest_release = self.db.query(BLSRelease).filter(
            BLSRelease.is_processed == True
        ).order_by(BLSRelease.release_date.desc()).first()
        
        if not latest_release:
            raise ValueError("No processed BLS releases found")
            
        # Build filters
        filters = [RetailerPeriodAggregate.bls_release_id == latest_release.id]
        
        if retailer_ids:
            filters.append(RetailerPeriodAggregate.retailer_id.in_(retailer_ids))
        if bls_series_ids:
            filters.append(RetailerPeriodAggregate.bls_series_id.in_(bls_series_ids))
        if zip_codes:
            filters.append(RetailerPeriodAggregate.zip_code.in_(zip_codes))
            
        # Get period aggregates
        current_aggregates = self.db.query(RetailerPeriodAggregate).filter(*filters).all()
        
        # Get corresponding period comparisons
        comparison_data = []
        for aggregate in current_aggregates:
            comparison = self.db.query(PeriodComparison).filter(
                PeriodComparison.current_period_id == aggregate.id
            ).first()
            
            if comparison:
                comparison_data.append({
                    'aggregate': aggregate,
                    'comparison': comparison,
                    'retailer': self.get_retailer(aggregate.retailer_id),
                    'bls_series': self.get_bls_series(aggregate.bls_series_id)
                })
                
        return MultiRetailerReport(
            release_date=latest_release.release_date,
            data_period=latest_release.data_period,
            comparisons=comparison_data,
            summary_stats=self.calculate_summary_statistics(comparison_data)
        )
        
    def calculate_summary_statistics(self, comparison_data: List[Dict]) -> Dict:
        """Calculate cross-retailer summary statistics"""
        if not comparison_data:
            return {}
            
        verdicts = [c['comparison'].verdict for c in comparison_data]
        retailer_changes = [c['comparison'].retailer_price_change_percent for c in comparison_data]
        bls_changes = [c['comparison'].bls_price_change_percent for c in comparison_data]
        
        return {
            'total_comparisons': len(comparison_data),
            'verdict_distribution': {
                'ABOVE': verdicts.count('ABOVE'),
                'INLINE': verdicts.count('INLINE'),  
                'BELOW': verdicts.count('BELOW')
            },
            'avg_retailer_change': statistics.mean(retailer_changes),
            'avg_bls_change': statistics.mean(bls_changes),
            'avg_delta_difference': statistics.mean([
                c['comparison'].delta_difference_pp for c in comparison_data
            ])
        }
        
    def compute_comparison_metrics(self, target: TargetMetrics, bls: BLSMetrics) -> ComparisonMetrics:
        """Calculate comparison metrics between Target and BLS"""
        
        price_gap = target.avg_price_per_gal - bls.avg_price_per_gal
        price_gap_pct = (price_gap / bls.avg_price_per_gal) * 100 if bls.avg_price_per_gal > 0 else 0
        
        mom_difference_pp = target.mom_change_pct - bls.mom_change_pct  # percentage points
        yoy_difference_pp = target.yoy_change_pct - bls.yoy_change_pct
        
        return ComparisonMetrics(
            price_gap=price_gap,
            price_gap_pct=price_gap_pct,
            mom_difference_pp=mom_difference_pp,
            yoy_difference_pp=yoy_difference_pp
        )
        
    def generate_verdict(self, comparison: ComparisonMetrics) -> str:
        """
        Generate verdict based on comparison thresholds
        Threshold: ±0.2pp for 'Inline', else 'Above'/'Below'
        """
        mom_diff = comparison.mom_difference_pp
        
        if abs(mom_diff) <= 0.2:
            return "Target INLINE with BLS (MoM)"
        elif mom_diff > 0.2:
            return "Target ABOVE BLS (MoM)"
        else:
            return "Target BELOW BLS (MoM)"
```

### 6. **Configuration & Environment Management**

#### Environment Configuration
```python
# /config/settings.py
from pydantic import BaseSettings, Field
from typing import Optional, List

class Settings(BaseSettings):
    # Database
    database_url: str = Field(default="sqlite:///data/cpi_benchmark.db")
    
    # BLS API
    bls_api_key: Optional[str] = Field(default=None)
    bls_base_url: str = Field(default="https://api.bls.gov/publicAPI/v2/timeseries/data/")
    default_bls_series: List[str] = Field(default=["CUUR0000SEFJ01", "APU0000709112"])
    
    # Scraping
    default_zip_code: str = Field(default="55331")
    headless: bool = Field(default=True)
    scrape_max_pages: int = Field(default=5)
    scrape_delay_range_ms: str = Field(default="500-1500")
    user_agent_rotation: bool = Field(default=True)
    
    # Rate Limiting
    requests_per_second: float = Field(default=0.5)
    max_retries: int = Field(default=3)
    
    # Logging
    log_level: str = Field(default="INFO")
    log_file: Optional[str] = Field(default="logs/app.log")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
```

### 7. **Error Handling & Monitoring**

#### Comprehensive Error Handling
```python
# /utils/exceptions.py
class CPIBenchmarkError(Exception):
    """Base exception for CPI benchmark application"""

class ScrapingError(CPIBenchmarkError):
    """Scraping-related errors"""
    
class BLSAPIError(CPIBenchmarkError):
    """BLS API-related errors"""
    
class DataValidationError(CPIBenchmarkError):
    """Data validation errors"""
    
class BasketError(CPIBenchmarkError):
    """Basket management errors"""

# /utils/monitoring.py
class PerformanceMonitor:
    """Monitor system performance and health"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        
    def record_scraping_stats(self, pages_scraped: int, products_found: int, duration: float):
        """Record scraping performance metrics"""
        
    def record_bls_api_stats(self, series_count: int, observations_count: int, duration: float):
        """Record BLS API performance metrics"""
        
    def check_data_freshness(self) -> Dict[str, timedelta]:
        """Check age of latest data in each table"""
        
    def generate_health_report(self) -> HealthReport:
        """Generate system health summary"""
```

### 8. **Data Flow Architecture**

#### Main Data Processing Pipeline

```
1. Daily Scraping (Continuous):
   Multi-retailer scrapers → extract/normalize → store to daily_prices
   
2. BLS Release Monitoring (Event-driven):
   BLS API → detect new releases → create bls_releases record
   
3. Period Aggregation (Triggered by BLS releases):
   Daily prices → aggregate by period → retailer_period_aggregates
   
4. Period Comparison (Triggered after aggregation):
   Current period vs previous period → period_comparisons
   
5. Report Generation (On-demand):
   Aggregated data → multi-retailer reports → UI/export formats
```

#### Daily Processing Workflow

```python
# Daily scraping orchestration
async def daily_processing_workflow():
    """Main daily processing pipeline"""
    
    # 1. Run daily scrapers for all enabled retailers
    scrape_orchestrator = DailyScrapeOrchestrator(db_session)
    scrape_results = await scrape_orchestrator.run_daily_scrapes()
    
    # 2. Check for new BLS releases (typically on release days)
    release_monitor = BLSReleaseMonitor(db_session)
    new_releases = await release_monitor.check_for_new_releases()
    
    # 3. If new BLS data, trigger aggregation and comparison
    if new_releases:
        for release in new_releases:
            # Aggregation happens automatically in trigger_period_aggregation
            logger.info(f"Processing BLS release {release.data_period}")
            
    return DailyProcessingResult(
        scrape_results=scrape_results,
        new_bls_releases=new_releases
    )
```

#### Event-Driven BLS Processing

```python
# BLS release processing workflow  
async def bls_release_workflow(bls_release: BLSRelease):
    """Process new BLS release through aggregation and comparison"""
    
    # 1. Aggregate retailer data for the new period
    aggregation_engine = RetailerAggregationEngine(db_session)
    aggregation_engine.aggregate_period(
        period_start=calculate_period_start(bls_release),
        period_end=calculate_period_end(bls_release),
        bls_release=bls_release
    )
    
    # 2. Generate period comparisons
    comparison_engine = PeriodComparisonEngine(db_session)
    comparison_engine.trigger_period_comparisons(bls_release)
    
    # 3. Trigger notification/alert system
    alert_system = PriceAlertSystem(db_session)
    alert_system.check_and_send_alerts(bls_release)
    
    # 4. Update UI data caches
    ui_cache = UIDataCache(db_session)
    ui_cache.refresh_latest_comparison_data()
```

## Production Considerations

### 1. **Scalability**
- Connection pooling for database
- Async processing for I/O-bound operations
- Configurable concurrency limits
- Efficient SQL queries with proper indexing

### 2. **Reliability**
- Comprehensive retry logic with exponential backoff
- Graceful degradation when APIs are unavailable
- Data validation at ingestion points
- Atomic transactions for data consistency

### 3. **Security**
- Environment variable management for sensitive data
- Input validation and sanitization
- Respect for robots.txt and rate limiting
- API key rotation support

### 4. **Monitoring**
- Structured logging with correlation IDs
- Performance metrics collection
- Data quality monitoring
- Health check endpoints for automation

This backend architecture provides a robust, scalable foundation for the CPI benchmark system while maintaining clear separation of concerns and production-quality error handling.
