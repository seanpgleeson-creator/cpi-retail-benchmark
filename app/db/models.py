"""
SQLAlchemy database models for BLS data storage
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship, Mapped

from .database import Base


class BLSSeriesDB(Base):
    """
    Database model for BLS series metadata
    """
    
    __tablename__ = "bls_series"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Series identification
    series_id = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(500), nullable=True)
    units = Column(String(100), nullable=True)
    seasonal_adjustment = Column(String(50), nullable=True)
    
    # Geographic and item information
    area_code = Column(String(20), nullable=True)
    area_name = Column(String(200), nullable=True)
    item_code = Column(String(20), nullable=True)
    item_name = Column(String(200), nullable=True)
    
    # Survey information
    survey_name = Column(String(100), nullable=True)
    survey_abbreviation = Column(String(20), nullable=True)
    
    # Data availability
    begin_year = Column(Integer, nullable=True)
    begin_period = Column(String(10), nullable=True)
    end_year = Column(Integer, nullable=True)
    end_period = Column(String(10), nullable=True)
    
    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Additional metadata as JSON-like text
    metadata_json = Column(Text, nullable=True)
    
    # Relationships
    observations: Mapped[List["BLSObservationDB"]] = relationship(
        "BLSObservationDB", 
        back_populates="series",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<BLSSeriesDB(series_id='{self.series_id}', title='{self.title}')>"


class BLSObservationDB(Base):
    """
    Database model for individual BLS observations
    """
    
    __tablename__ = "bls_observations"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to series
    series_id = Column(String(50), ForeignKey("bls_series.series_id"), nullable=False)
    
    # Time period
    year = Column(Integer, nullable=False)
    period = Column(String(10), nullable=False)  # M01, M02, etc.
    period_name = Column(String(20), nullable=True)  # January, February, etc.
    
    # Data values
    value = Column(Float, nullable=False)
    footnotes = Column(Text, nullable=True)
    
    # Calculated fields (from BLS or our calculations)
    net_change_1_month = Column(Float, nullable=True)
    net_change_3_months = Column(Float, nullable=True)
    net_change_6_months = Column(Float, nullable=True)
    net_change_12_months = Column(Float, nullable=True)
    
    pct_change_1_month = Column(Float, nullable=True)
    pct_change_3_months = Column(Float, nullable=True)
    pct_change_6_months = Column(Float, nullable=True)
    pct_change_12_months = Column(Float, nullable=True)
    
    # Data quality indicators
    is_preliminary = Column(Boolean, default=False, nullable=False)
    is_revised = Column(Boolean, default=False, nullable=False)
    revision_count = Column(Integer, default=0, nullable=False)
    
    # Metadata
    data_source = Column(String(50), default="BLS_API", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    series: Mapped["BLSSeriesDB"] = relationship("BLSSeriesDB", back_populates="observations")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('series_id', 'year', 'period', name='uq_series_year_period'),
        Index('ix_obs_series_year_period', 'series_id', 'year', 'period'),
        Index('ix_obs_year_period', 'year', 'period'),
    )
    
    def __repr__(self) -> str:
        return f"<BLSObservationDB(series_id='{self.series_id}', year={self.year}, period='{self.period}', value={self.value})>"


class BLSReleaseDB(Base):
    """
    Database model for tracking BLS data releases
    """
    
    __tablename__ = "bls_releases"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Release identification
    release_id = Column(String(50), unique=True, index=True, nullable=False)
    release_name = Column(String(200), nullable=False)
    
    # Release timing
    reference_year = Column(Integer, nullable=False)
    reference_period = Column(String(10), nullable=False)  # M01, M02, etc.
    reference_period_name = Column(String(20), nullable=True)
    
    # Release dates
    scheduled_release_date = Column(DateTime, nullable=True)
    actual_release_date = Column(DateTime, nullable=True)
    
    # Release status
    is_preliminary = Column(Boolean, default=True, nullable=False)
    is_final = Column(Boolean, default=False, nullable=False)
    is_revised = Column(Boolean, default=False, nullable=False)
    
    # Data coverage
    series_count = Column(Integer, default=0, nullable=False)
    observations_count = Column(Integer, default=0, nullable=False)
    
    # Processing status
    is_processed = Column(Boolean, default=False, nullable=False)
    processing_started_at = Column(DateTime, nullable=True)
    processing_completed_at = Column(DateTime, nullable=True)
    processing_error = Column(Text, nullable=True)
    
    # Metadata
    release_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('ix_release_ref_year_period', 'reference_year', 'reference_period'),
        Index('ix_release_dates', 'scheduled_release_date', 'actual_release_date'),
        Index('ix_release_status', 'is_processed', 'is_final'),
    )
    
    def __repr__(self) -> str:
        return f"<BLSReleaseDB(release_id='{self.release_id}', ref_period={self.reference_year}-{self.reference_period})>"


class RetailerDB(Base):
    """
    Database model for retailer information (for future use)
    """
    
    __tablename__ = "retailers"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Retailer identification
    retailer_code = Column(String(20), unique=True, index=True, nullable=False)
    retailer_name = Column(String(200), nullable=False)
    
    # Configuration
    base_url = Column(String(500), nullable=True)
    scraper_config = Column(Text, nullable=True)  # JSON configuration
    
    # Geographic coverage
    zip_codes = Column(Text, nullable=True)  # JSON list of zip codes
    states = Column(Text, nullable=True)  # JSON list of states
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    last_scraped_at = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<RetailerDB(code='{self.retailer_code}', name='{self.retailer_name}')>"


class RetailerProductDB(Base):
    """
    Database model for retailer product data (for future use)
    """
    
    __tablename__ = "retailer_products"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Product identification
    retailer_code = Column(String(20), ForeignKey("retailers.retailer_code"), nullable=False)
    product_id = Column(String(100), nullable=False)  # Retailer's internal ID
    
    # Product information
    product_name = Column(String(500), nullable=False)
    brand = Column(String(200), nullable=True)
    category = Column(String(100), nullable=True)
    subcategory = Column(String(100), nullable=True)
    
    # BLS mapping
    bls_series_id = Column(String(50), ForeignKey("bls_series.series_id"), nullable=True)
    
    # Product specifications
    size = Column(String(50), nullable=True)
    unit = Column(String(20), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('retailer_code', 'product_id', name='uq_retailer_product'),
        Index('ix_product_retailer_category', 'retailer_code', 'category'),
        Index('ix_product_bls_mapping', 'bls_series_id'),
    )
    
    def __repr__(self) -> str:
        return f"<RetailerProductDB(retailer='{self.retailer_code}', product='{self.product_name}')>"


class RetailerPriceDB(Base):
    """
    Database model for retailer price observations (for future use)
    """
    
    __tablename__ = "retailer_prices"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Product reference
    product_id = Column(Integer, ForeignKey("retailer_products.id"), nullable=False)
    
    # Price data
    price = Column(Float, nullable=False)
    original_price = Column(Float, nullable=True)  # Before discounts
    currency = Column(String(3), default="USD", nullable=False)
    
    # Geographic data
    zip_code = Column(String(10), nullable=True)
    store_id = Column(String(50), nullable=True)
    
    # Temporal data
    observed_at = Column(DateTime, nullable=False)
    
    # Price metadata
    is_on_sale = Column(Boolean, default=False, nullable=False)
    discount_percent = Column(Float, nullable=True)
    availability_status = Column(String(20), default="in_stock", nullable=False)
    
    # Data source
    scrape_session_id = Column(String(100), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Constraints and indexes
    __table_args__ = (
        Index('ix_price_product_date', 'product_id', 'observed_at'),
        Index('ix_price_zip_date', 'zip_code', 'observed_at'),
        Index('ix_price_date', 'observed_at'),
    )
    
    def __repr__(self) -> str:
        return f"<RetailerPriceDB(product_id={self.product_id}, price=${self.price}, date={self.observed_at})>"
