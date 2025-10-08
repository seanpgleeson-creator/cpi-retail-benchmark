"""
Tests for database functionality
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.db.models import BLSSeriesDB, BLSObservationDB, BLSReleaseDB
from app.db.crud import BLSSeriesCRUD, BLSObservationCRUD, BLSDataManager
from app.models.bls_models import BLSSeries, BLSObservation


@pytest.fixture
def test_db():
    """Create a test database"""
    # Use in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    
    yield session
    
    session.close()


class TestBLSSeriesCRUD:
    """Test BLS series CRUD operations"""

    def test_create_series(self, test_db):
        """Test creating a BLS series"""
        series = BLSSeries(
            series_id="TEST001",
            title="Test Series",
            units="Index",
            seasonal_adjustment="Not Seasonally Adjusted",
            area="U.S. City Average",
            item="Test Item"
        )
        
        db_series = BLSSeriesCRUD.create_series(test_db, series)
        
        assert db_series.series_id == "TEST001"
        assert db_series.title == "Test Series"
        assert db_series.is_active is True

    def test_get_series(self, test_db):
        """Test retrieving a BLS series"""
        # Create a series first
        series = BLSSeries(
            series_id="TEST002",
            title="Test Series 2",
            units="Index"
        )
        BLSSeriesCRUD.create_series(test_db, series)
        
        # Retrieve it
        retrieved = BLSSeriesCRUD.get_series(test_db, "TEST002")
        
        assert retrieved is not None
        assert retrieved.series_id == "TEST002"
        assert retrieved.title == "Test Series 2"

    def test_get_nonexistent_series(self, test_db):
        """Test retrieving a non-existent series"""
        retrieved = BLSSeriesCRUD.get_series(test_db, "NONEXISTENT")
        assert retrieved is None

    def test_update_series(self, test_db):
        """Test updating a BLS series"""
        # Create a series first
        series = BLSSeries(
            series_id="TEST003",
            title="Original Title",
            units="Index"
        )
        BLSSeriesCRUD.create_series(test_db, series)
        
        # Update it
        updated = BLSSeriesCRUD.update_series(
            test_db, "TEST003", title="Updated Title", units="Percent"
        )
        
        assert updated is not None
        assert updated.title == "Updated Title"
        assert updated.units == "Percent"

    def test_delete_series(self, test_db):
        """Test soft deleting a BLS series"""
        # Create a series first
        series = BLSSeries(
            series_id="TEST004",
            title="To Be Deleted",
            units="Index"
        )
        BLSSeriesCRUD.create_series(test_db, series)
        
        # Delete it (soft delete)
        success = BLSSeriesCRUD.delete_series(test_db, "TEST004")
        
        assert success is True
        
        # Verify it's marked as inactive
        retrieved = BLSSeriesCRUD.get_series(test_db, "TEST004")
        assert retrieved is not None
        assert retrieved.is_active is False


class TestBLSObservationCRUD:
    """Test BLS observation CRUD operations"""

    def test_create_observation(self, test_db):
        """Test creating a BLS observation"""
        # Create a series first
        series = BLSSeries(series_id="OBS001", title="Observation Test Series")
        BLSSeriesCRUD.create_series(test_db, series)
        
        # Create an observation
        observation = BLSObservation(
            series_id="OBS001",
            year=2023,
            period="M01",
            value=100.5,
            footnotes=""
        )
        
        db_obs = BLSObservationCRUD.create_observation(test_db, observation)
        
        assert db_obs.series_id == "OBS001"
        assert db_obs.year == 2023
        assert db_obs.period == "M01"
        assert db_obs.value == 100.5

    def test_get_observation(self, test_db):
        """Test retrieving a specific observation"""
        # Create series and observation
        series = BLSSeries(series_id="OBS002", title="Test Series")
        BLSSeriesCRUD.create_series(test_db, series)
        
        observation = BLSObservation(
            series_id="OBS002",
            year=2023,
            period="M02",
            value=101.0
        )
        BLSObservationCRUD.create_observation(test_db, observation)
        
        # Retrieve it
        retrieved = BLSObservationCRUD.get_observation(test_db, "OBS002", 2023, "M02")
        
        assert retrieved is not None
        assert retrieved.value == 101.0

    def test_bulk_create_observations(self, test_db):
        """Test creating multiple observations at once"""
        # Create a series first
        series = BLSSeries(series_id="BULK001", title="Bulk Test Series")
        BLSSeriesCRUD.create_series(test_db, series)
        
        # Create multiple observations
        observations = [
            BLSObservation(series_id="BULK001", year=2023, period="M01", value=100.0),
            BLSObservation(series_id="BULK001", year=2023, period="M02", value=101.0),
            BLSObservation(series_id="BULK001", year=2023, period="M03", value=102.0),
        ]
        
        db_observations = BLSObservationCRUD.bulk_create_observations(test_db, observations)
        
        assert len(db_observations) == 3
        assert all(obs.series_id == "BULK001" for obs in db_observations)

    def test_get_series_observations(self, test_db):
        """Test retrieving observations for a series"""
        # Create series and observations
        series = BLSSeries(series_id="SERIES001", title="Series Test")
        BLSSeriesCRUD.create_series(test_db, series)
        
        observations = [
            BLSObservation(series_id="SERIES001", year=2022, period="M12", value=99.0),
            BLSObservation(series_id="SERIES001", year=2023, period="M01", value=100.0),
            BLSObservation(series_id="SERIES001", year=2023, period="M02", value=101.0),
        ]
        BLSObservationCRUD.bulk_create_observations(test_db, observations)
        
        # Get all observations
        all_obs = BLSObservationCRUD.get_series_observations(test_db, "SERIES001")
        assert len(all_obs) == 3
        
        # Get observations for specific year
        year_2023_obs = BLSObservationCRUD.get_series_observations(
            test_db, "SERIES001", start_year=2023, end_year=2023
        )
        assert len(year_2023_obs) == 2

    def test_get_latest_observation(self, test_db):
        """Test getting the most recent observation"""
        # Create series and observations
        series = BLSSeries(series_id="LATEST001", title="Latest Test")
        BLSSeriesCRUD.create_series(test_db, series)
        
        observations = [
            BLSObservation(series_id="LATEST001", year=2023, period="M01", value=100.0),
            BLSObservation(series_id="LATEST001", year=2023, period="M03", value=102.0),
            BLSObservation(series_id="LATEST001", year=2023, period="M02", value=101.0),
        ]
        BLSObservationCRUD.bulk_create_observations(test_db, observations)
        
        # Get latest observation
        latest = BLSObservationCRUD.get_latest_observation(test_db, "LATEST001")
        
        assert latest is not None
        assert latest.year == 2023
        assert latest.period == "M03"  # Should be the latest chronologically
        assert latest.value == 102.0

    def test_upsert_observation(self, test_db):
        """Test upserting (insert or update) observations"""
        # Create series
        series = BLSSeries(series_id="UPSERT001", title="Upsert Test")
        BLSSeriesCRUD.create_series(test_db, series)
        
        # First upsert (should insert)
        observation = BLSObservation(
            series_id="UPSERT001",
            year=2023,
            period="M01",
            value=100.0
        )
        
        db_obs1 = BLSObservationCRUD.upsert_observation(test_db, observation)
        assert db_obs1.value == 100.0
        assert db_obs1.revision_count == 0
        
        # Second upsert (should update)
        observation.value = 100.5
        db_obs2 = BLSObservationCRUD.upsert_observation(test_db, observation)
        
        assert db_obs2.id == db_obs1.id  # Same record
        assert db_obs2.value == 100.5
        assert db_obs2.revision_count == 1
        assert db_obs2.is_revised is True


class TestBLSDataManager:
    """Test the high-level data manager"""

    def test_store_series_data(self, test_db):
        """Test storing complete series data"""
        manager = BLSDataManager(test_db)
        
        # Create test data
        series = BLSSeries(
            series_id="MANAGER001",
            title="Manager Test Series",
            units="Index"
        )
        
        observations = [
            BLSObservation(series_id="MANAGER001", year=2023, period="M01", value=100.0),
            BLSObservation(series_id="MANAGER001", year=2023, period="M02", value=101.0),
        ]
        
        # Store the data
        stored_series, stored_observations = manager.store_series_data(series, observations)
        
        assert stored_series.series_id == "MANAGER001"
        assert len(stored_observations) == 2

    def test_get_series_summary(self, test_db):
        """Test getting series summary"""
        manager = BLSDataManager(test_db)
        
        # Create and store test data
        series = BLSSeries(
            series_id="SUMMARY001",
            title="Summary Test Series",
            units="Index"
        )
        
        observations = [
            BLSObservation(series_id="SUMMARY001", year=2023, period="M01", value=100.0),
            BLSObservation(series_id="SUMMARY001", year=2023, period="M02", value=101.0),
        ]
        
        manager.store_series_data(series, observations)
        
        # Get summary
        summary = manager.get_series_summary("SUMMARY001")
        
        assert summary is not None
        assert summary["series_id"] == "SUMMARY001"
        assert summary["title"] == "Summary Test Series"
        assert summary["observation_count"] == 2
        assert summary["latest_observation"] is not None

    def test_get_database_stats(self, test_db):
        """Test getting database statistics"""
        manager = BLSDataManager(test_db)
        
        # Create some test data
        series1 = BLSSeries(series_id="STATS001", title="Stats Test 1")
        series2 = BLSSeries(series_id="STATS002", title="Stats Test 2")
        
        observations1 = [
            BLSObservation(series_id="STATS001", year=2023, period="M01", value=100.0),
            BLSObservation(series_id="STATS001", year=2023, period="M02", value=101.0),
        ]
        
        observations2 = [
            BLSObservation(series_id="STATS002", year=2023, period="M01", value=200.0),
        ]
        
        manager.store_series_data(series1, observations1)
        manager.store_series_data(series2, observations2)
        
        # Get stats
        stats = manager.get_database_stats()
        
        assert stats["total_series"] >= 2
        assert stats["active_series"] >= 2
        assert stats["total_observations"] >= 3
        assert stats["avg_observations_per_series"] > 0
