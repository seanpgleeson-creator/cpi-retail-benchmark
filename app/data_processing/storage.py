"""
Storage integration for BLS data processing

This module integrates the data processing workflows with persistent storage,
enabling caching, historical analysis, and data persistence.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.bls_client import BLSAPIClient
from app.db import get_db_session, BLSDataManager
from app.models.bls_models import BLSObservation, BLSSeries
from .processors import BLSDataProcessor

logger = logging.getLogger(__name__)


class BLSStorageProcessor(BLSDataProcessor):
    """
    Enhanced BLS data processor with database storage capabilities
    """

    def __init__(self, bls_client: Optional[BLSAPIClient] = None, db: Optional[Session] = None):
        """
        Initialize the storage-enabled processor
        
        Args:
            bls_client: Optional BLS API client instance
            db: Optional database session
        """
        super().__init__(bls_client)
        self.db = db or get_db_session()
        self.data_manager = BLSDataManager(self.db)

    def fetch_and_store_series(
        self,
        series_id: str,
        start_year: int,
        end_year: int,
        force_refresh: bool = False,
        include_calculations: bool = True
    ) -> Dict[str, Any]:
        """
        Fetch BLS series data and store it in the database
        
        Args:
            series_id: BLS series identifier
            start_year: Starting year for data
            end_year: Ending year for data
            force_refresh: Whether to force refresh from BLS API
            include_calculations: Whether to include MoM/YoY calculations
            
        Returns:
            Dictionary with processed and stored series data
        """
        logger.info(f"Fetching and storing series {series_id} ({start_year}-{end_year})")
        
        # Check if we have recent data in the database
        if not force_refresh:
            cached_data = self._get_cached_series_data(series_id, start_year, end_year)
            if cached_data:
                logger.info(f"Using cached data for series {series_id}")
                return cached_data
        
        # Fetch fresh data from BLS API
        processed_data = self.fetch_and_process_series(
            series_id, start_year, end_year, include_calculations
        )
        
        # Store the data in the database
        stored_series, stored_observations = self.data_manager.store_series_data(
            processed_data["series_metadata"],
            processed_data["observations"]
        )
        
        # Update the processed data with storage information
        processed_data["storage_info"] = {
            "stored_at": datetime.now().isoformat(),
            "series_db_id": stored_series.id,
            "observations_stored": len(stored_observations),
            "storage_method": "fresh_fetch"
        }
        
        logger.info(f"Successfully stored series {series_id} with {len(stored_observations)} observations")
        return processed_data

    def _get_cached_series_data(
        self, 
        series_id: str, 
        start_year: int, 
        end_year: int,
        max_age_hours: int = 24
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached series data from the database if available and recent
        
        Args:
            series_id: BLS series identifier
            start_year: Starting year for data
            end_year: Ending year for data
            max_age_hours: Maximum age of cached data in hours
            
        Returns:
            Cached processed data or None if not available/too old
        """
        try:
            # Get series metadata
            db_series = self.data_manager.series_crud.get_series(self.db, series_id)
            if not db_series:
                return None
            
            # Check if data is recent enough
            if db_series.last_updated:
                age_hours = (datetime.utcnow() - db_series.last_updated).total_seconds() / 3600
                if age_hours > max_age_hours:
                    logger.info(f"Cached data for {series_id} is {age_hours:.1f} hours old, refreshing")
                    return None
            
            # Get observations from database
            db_observations = self.data_manager.obs_crud.get_series_observations(
                self.db, series_id, start_year, end_year
            )
            
            if not db_observations:
                return None
            
            # Convert database models back to our models
            series_metadata = BLSSeries(
                series_id=db_series.series_id,
                title=db_series.title or "Unknown",
                units=db_series.units or "Unknown",
                seasonal_adjustment=db_series.seasonal_adjustment or "Unknown",
                area=db_series.area_name,
                item=db_series.item_name
            )
            
            observations = []
            for db_obs in reversed(db_observations):  # Reverse to get chronological order
                obs = BLSObservation(
                    series_id=db_obs.series_id,
                    year=db_obs.year,
                    period=db_obs.period,
                    value=db_obs.value,
                    footnotes=db_obs.footnotes or "",
                    created_at=db_obs.created_at,
                    updated_at=db_obs.updated_at
                )
                
                # Add calculated fields if available
                obs.net_change_1_month = db_obs.net_change_1_month
                obs.net_change_12_months = db_obs.net_change_12_months
                obs.pct_change_1_month = db_obs.pct_change_1_month
                obs.pct_change_12_months = db_obs.pct_change_12_months
                
                observations.append(obs)
            
            # Calculate analytics for cached data
            analytics = self._calculate_series_analytics(observations)
            
            # Assess data quality
            data_quality = self.validator.assess_data_quality(observations)
            
            return {
                "series_metadata": series_metadata,
                "observations": observations,
                "analytics": analytics,
                "data_quality": data_quality,
                "processing_timestamp": datetime.now().isoformat(),
                "total_observations": len(observations),
                "storage_info": {
                    "retrieved_from": "database_cache",
                    "last_updated": db_series.last_updated.isoformat() if db_series.last_updated else None,
                    "cache_age_hours": age_hours if db_series.last_updated else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error retrieving cached data for {series_id}: {e}")
            return None

    def get_stored_series_summary(self, series_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a summary of stored series data
        
        Args:
            series_id: BLS series identifier
            
        Returns:
            Series summary or None if not found
        """
        return self.data_manager.get_series_summary(series_id)

    def get_database_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics
        
        Returns:
            Database statistics dictionary
        """
        return self.data_manager.get_database_stats()

    def cleanup_old_data(self, days_to_keep: int = 90) -> Dict[str, int]:
        """
        Clean up old data from the database
        
        Args:
            days_to_keep: Number of days of data to keep
            
        Returns:
            Dictionary with cleanup statistics
        """
        # This is a placeholder for future implementation
        # In a real system, you'd implement logic to remove old observations
        # while keeping important historical data
        
        logger.info(f"Cleanup requested for data older than {days_to_keep} days")
        
        return {
            "observations_removed": 0,
            "series_deactivated": 0,
            "releases_archived": 0
        }

    def bulk_update_series(self, series_ids: List[str], **kwargs) -> Dict[str, Any]:
        """
        Bulk update multiple series
        
        Args:
            series_ids: List of series identifiers to update
            **kwargs: Fields to update
            
        Returns:
            Update statistics
        """
        updated_count = 0
        failed_count = 0
        
        for series_id in series_ids:
            try:
                result = self.data_manager.series_crud.update_series(
                    self.db, series_id, **kwargs
                )
                if result:
                    updated_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                logger.error(f"Failed to update series {series_id}: {e}")
                failed_count += 1
        
        return {
            "total_requested": len(series_ids),
            "updated": updated_count,
            "failed": failed_count
        }

    def get_series_by_category(self, category_keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Get series that match category keywords
        
        Args:
            category_keywords: Keywords to search for in series titles/items
            
        Returns:
            List of matching series summaries
        """
        # This would implement search functionality across stored series
        # For now, return empty list as placeholder
        
        logger.info(f"Searching for series with keywords: {category_keywords}")
        
        all_series = self.data_manager.series_crud.get_all_series(self.db)
        matching_series = []
        
        for series in all_series:
            # Simple keyword matching in title and item name
            search_text = f"{series.title or ''} {series.item_name or ''}".lower()
            
            if any(keyword.lower() in search_text for keyword in category_keywords):
                summary = self.data_manager.get_series_summary(series.series_id)
                if summary:
                    matching_series.append(summary)
        
        return matching_series

    def close(self):
        """Close database connection"""
        if self.db:
            self.db.close()
