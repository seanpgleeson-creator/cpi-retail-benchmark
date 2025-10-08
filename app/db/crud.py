"""
CRUD operations for BLS data
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from app.models.bls_models import BLSObservation, BLSSeries
from .models import BLSSeriesDB, BLSObservationDB, BLSReleaseDB

logger = logging.getLogger(__name__)


class BLSSeriesCRUD:
    """CRUD operations for BLS series"""

    @staticmethod
    def create_series(db: Session, series: BLSSeries) -> BLSSeriesDB:
        """
        Create a new BLS series in the database
        
        Args:
            db: Database session
            series: BLS series model
            
        Returns:
            Created database series
        """
        db_series = BLSSeriesDB(
            series_id=series.series_id,
            title=series.title,
            units=series.units,
            seasonal_adjustment=series.seasonal_adjustment,
            area_name=series.area,
            item_name=series.item,
        )
        
        db.add(db_series)
        db.commit()
        db.refresh(db_series)
        
        logger.info(f"Created BLS series: {series.series_id}")
        return db_series

    @staticmethod
    def get_series(db: Session, series_id: str) -> Optional[BLSSeriesDB]:
        """
        Get a BLS series by ID
        
        Args:
            db: Database session
            series_id: BLS series identifier
            
        Returns:
            BLS series or None if not found
        """
        return db.query(BLSSeriesDB).filter(BLSSeriesDB.series_id == series_id).first()

    @staticmethod
    def get_all_series(db: Session, active_only: bool = True) -> List[BLSSeriesDB]:
        """
        Get all BLS series
        
        Args:
            db: Database session
            active_only: Whether to return only active series
            
        Returns:
            List of BLS series
        """
        query = db.query(BLSSeriesDB)
        if active_only:
            query = query.filter(BLSSeriesDB.is_active == True)
        
        return query.all()

    @staticmethod
    def update_series(db: Session, series_id: str, **kwargs) -> Optional[BLSSeriesDB]:
        """
        Update a BLS series
        
        Args:
            db: Database session
            series_id: BLS series identifier
            **kwargs: Fields to update
            
        Returns:
            Updated series or None if not found
        """
        db_series = BLSSeriesCRUD.get_series(db, series_id)
        if not db_series:
            return None
        
        for key, value in kwargs.items():
            if hasattr(db_series, key):
                setattr(db_series, key, value)
        
        db.commit()
        db.refresh(db_series)
        
        logger.info(f"Updated BLS series: {series_id}")
        return db_series

    @staticmethod
    def delete_series(db: Session, series_id: str) -> bool:
        """
        Delete a BLS series (soft delete by setting inactive)
        
        Args:
            db: Database session
            series_id: BLS series identifier
            
        Returns:
            True if deleted, False if not found
        """
        db_series = BLSSeriesCRUD.get_series(db, series_id)
        if not db_series:
            return False
        
        db_series.is_active = False
        db.commit()
        
        logger.info(f"Deactivated BLS series: {series_id}")
        return True


class BLSObservationCRUD:
    """CRUD operations for BLS observations"""

    @staticmethod
    def create_observation(db: Session, observation: BLSObservation) -> BLSObservationDB:
        """
        Create a new BLS observation
        
        Args:
            db: Database session
            observation: BLS observation model
            
        Returns:
            Created database observation
        """
        db_obs = BLSObservationDB(
            series_id=observation.series_id,
            year=observation.year,
            period=observation.period,
            value=observation.value,
            footnotes=observation.footnotes,
            net_change_1_month=observation.net_change_1_month,
            net_change_12_months=observation.net_change_12_months,
            pct_change_1_month=observation.pct_change_1_month,
            pct_change_12_months=observation.pct_change_12_months,
        )
        
        db.add(db_obs)
        db.commit()
        db.refresh(db_obs)
        
        return db_obs

    @staticmethod
    def bulk_create_observations(
        db: Session, observations: List[BLSObservation]
    ) -> List[BLSObservationDB]:
        """
        Create multiple BLS observations efficiently
        
        Args:
            db: Database session
            observations: List of BLS observation models
            
        Returns:
            List of created database observations
        """
        db_observations = []
        
        for obs in observations:
            db_obs = BLSObservationDB(
                series_id=obs.series_id,
                year=obs.year,
                period=obs.period,
                value=obs.value,
                footnotes=obs.footnotes,
                net_change_1_month=obs.net_change_1_month,
                net_change_12_months=obs.net_change_12_months,
                pct_change_1_month=obs.pct_change_1_month,
                pct_change_12_months=obs.pct_change_12_months,
            )
            db_observations.append(db_obs)
        
        db.add_all(db_observations)
        db.commit()
        
        logger.info(f"Created {len(db_observations)} BLS observations")
        return db_observations

    @staticmethod
    def get_observation(
        db: Session, series_id: str, year: int, period: str
    ) -> Optional[BLSObservationDB]:
        """
        Get a specific BLS observation
        
        Args:
            db: Database session
            series_id: BLS series identifier
            year: Year
            period: Period (e.g., 'M01')
            
        Returns:
            BLS observation or None if not found
        """
        return (
            db.query(BLSObservationDB)
            .filter(
                and_(
                    BLSObservationDB.series_id == series_id,
                    BLSObservationDB.year == year,
                    BLSObservationDB.period == period,
                )
            )
            .first()
        )

    @staticmethod
    def get_series_observations(
        db: Session,
        series_id: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[BLSObservationDB]:
        """
        Get observations for a series
        
        Args:
            db: Database session
            series_id: BLS series identifier
            start_year: Optional start year filter
            end_year: Optional end year filter
            limit: Optional limit on number of results
            
        Returns:
            List of BLS observations
        """
        query = db.query(BLSObservationDB).filter(
            BLSObservationDB.series_id == series_id
        )
        
        if start_year:
            query = query.filter(BLSObservationDB.year >= start_year)
        
        if end_year:
            query = query.filter(BLSObservationDB.year <= end_year)
        
        # Order by year and period (most recent first)
        query = query.order_by(desc(BLSObservationDB.year), desc(BLSObservationDB.period))
        
        if limit:
            query = query.limit(limit)
        
        return query.all()

    @staticmethod
    def get_latest_observation(db: Session, series_id: str) -> Optional[BLSObservationDB]:
        """
        Get the most recent observation for a series
        
        Args:
            db: Database session
            series_id: BLS series identifier
            
        Returns:
            Latest BLS observation or None if not found
        """
        return (
            db.query(BLSObservationDB)
            .filter(BLSObservationDB.series_id == series_id)
            .order_by(desc(BLSObservationDB.year), desc(BLSObservationDB.period))
            .first()
        )

    @staticmethod
    def upsert_observation(db: Session, observation: BLSObservation) -> BLSObservationDB:
        """
        Insert or update a BLS observation
        
        Args:
            db: Database session
            observation: BLS observation model
            
        Returns:
            Created or updated database observation
        """
        # Check if observation already exists
        existing = BLSObservationCRUD.get_observation(
            db, observation.series_id, observation.year, observation.period
        )
        
        if existing:
            # Update existing observation
            existing.value = observation.value
            existing.footnotes = observation.footnotes
            existing.net_change_1_month = observation.net_change_1_month
            existing.net_change_12_months = observation.net_change_12_months
            existing.pct_change_1_month = observation.pct_change_1_month
            existing.pct_change_12_months = observation.pct_change_12_months
            existing.is_revised = True
            existing.revision_count += 1
            
            db.commit()
            db.refresh(existing)
            return existing
        else:
            # Create new observation
            return BLSObservationCRUD.create_observation(db, observation)

    @staticmethod
    def get_observation_count(db: Session, series_id: Optional[str] = None) -> int:
        """
        Get count of observations
        
        Args:
            db: Database session
            series_id: Optional series filter
            
        Returns:
            Count of observations
        """
        query = db.query(func.count(BLSObservationDB.id))
        
        if series_id:
            query = query.filter(BLSObservationDB.series_id == series_id)
        
        return query.scalar()


class BLSReleaseCRUD:
    """CRUD operations for BLS releases"""

    @staticmethod
    def create_release(
        db: Session,
        release_id: str,
        release_name: str,
        reference_year: int,
        reference_period: str,
        **kwargs
    ) -> BLSReleaseDB:
        """
        Create a new BLS release record
        
        Args:
            db: Database session
            release_id: Unique release identifier
            release_name: Human-readable release name
            reference_year: Year the data refers to
            reference_period: Period the data refers to
            **kwargs: Additional fields
            
        Returns:
            Created database release
        """
        db_release = BLSReleaseDB(
            release_id=release_id,
            release_name=release_name,
            reference_year=reference_year,
            reference_period=reference_period,
            **kwargs
        )
        
        db.add(db_release)
        db.commit()
        db.refresh(db_release)
        
        logger.info(f"Created BLS release: {release_id}")
        return db_release

    @staticmethod
    def get_release(db: Session, release_id: str) -> Optional[BLSReleaseDB]:
        """
        Get a BLS release by ID
        
        Args:
            db: Database session
            release_id: Release identifier
            
        Returns:
            BLS release or None if not found
        """
        return db.query(BLSReleaseDB).filter(BLSReleaseDB.release_id == release_id).first()

    @staticmethod
    def get_latest_releases(db: Session, limit: int = 10) -> List[BLSReleaseDB]:
        """
        Get the most recent BLS releases
        
        Args:
            db: Database session
            limit: Maximum number of releases to return
            
        Returns:
            List of recent BLS releases
        """
        return (
            db.query(BLSReleaseDB)
            .order_by(desc(BLSReleaseDB.actual_release_date))
            .limit(limit)
            .all()
        )

    @staticmethod
    def mark_release_processed(
        db: Session, release_id: str, success: bool = True, error: Optional[str] = None
    ) -> Optional[BLSReleaseDB]:
        """
        Mark a release as processed
        
        Args:
            db: Database session
            release_id: Release identifier
            success: Whether processing was successful
            error: Error message if processing failed
            
        Returns:
            Updated release or None if not found
        """
        db_release = BLSReleaseCRUD.get_release(db, release_id)
        if not db_release:
            return None
        
        db_release.is_processed = success
        db_release.processing_completed_at = datetime.utcnow()
        if error:
            db_release.processing_error = error
        
        db.commit()
        db.refresh(db_release)
        
        logger.info(f"Marked release {release_id} as processed (success={success})")
        return db_release


class BLSDataManager:
    """High-level manager for BLS data operations"""

    def __init__(self, db: Session):
        self.db = db
        self.series_crud = BLSSeriesCRUD()
        self.obs_crud = BLSObservationCRUD()
        self.release_crud = BLSReleaseCRUD()

    def store_series_data(
        self, series: BLSSeries, observations: List[BLSObservation]
    ) -> Tuple[BLSSeriesDB, List[BLSObservationDB]]:
        """
        Store a complete series with its observations
        
        Args:
            series: BLS series metadata
            observations: List of observations for the series
            
        Returns:
            Tuple of (stored series, stored observations)
        """
        # Ensure series exists
        db_series = self.series_crud.get_series(self.db, series.series_id)
        if not db_series:
            db_series = self.series_crud.create_series(self.db, series)
        else:
            # Update series metadata
            self.series_crud.update_series(
                self.db,
                series.series_id,
                title=series.title,
                units=series.units,
                seasonal_adjustment=series.seasonal_adjustment,
                area_name=series.area,
                item_name=series.item,
                last_updated=datetime.utcnow(),
            )

        # Store observations (upsert to handle updates)
        stored_observations = []
        for obs in observations:
            stored_obs = self.obs_crud.upsert_observation(self.db, obs)
            stored_observations.append(stored_obs)

        logger.info(
            f"Stored series {series.series_id} with {len(stored_observations)} observations"
        )
        return db_series, stored_observations

    def get_series_summary(self, series_id: str) -> Optional[Dict]:
        """
        Get a summary of a series including latest data
        
        Args:
            series_id: BLS series identifier
            
        Returns:
            Series summary dictionary or None if not found
        """
        db_series = self.series_crud.get_series(self.db, series_id)
        if not db_series:
            return None

        latest_obs = self.obs_crud.get_latest_observation(self.db, series_id)
        obs_count = self.obs_crud.get_observation_count(self.db, series_id)

        return {
            "series_id": db_series.series_id,
            "title": db_series.title,
            "units": db_series.units,
            "observation_count": obs_count,
            "latest_observation": {
                "year": latest_obs.year,
                "period": latest_obs.period,
                "value": latest_obs.value,
                "date": latest_obs.updated_at,
            } if latest_obs else None,
            "last_updated": db_series.last_updated,
        }

    def get_database_stats(self) -> Dict:
        """
        Get overall database statistics
        
        Returns:
            Database statistics dictionary
        """
        series_count = self.db.query(func.count(BLSSeriesDB.id)).scalar()
        active_series_count = (
            self.db.query(func.count(BLSSeriesDB.id))
            .filter(BLSSeriesDB.is_active == True)
            .scalar()
        )
        obs_count = self.db.query(func.count(BLSObservationDB.id)).scalar()
        release_count = self.db.query(func.count(BLSReleaseDB.id)).scalar()

        return {
            "total_series": series_count,
            "active_series": active_series_count,
            "total_observations": obs_count,
            "total_releases": release_count,
            "avg_observations_per_series": obs_count / max(series_count, 1),
        }
