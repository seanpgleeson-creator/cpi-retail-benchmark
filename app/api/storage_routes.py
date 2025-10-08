"""
FastAPI routes for BLS data storage and database operations
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db, init_db, BLSDataManager
from app.data_processing.storage import BLSStorageProcessor

router = APIRouter(prefix="/api/v1/storage", tags=["BLS Data Storage"])


class StorageStatsResponse(BaseModel):
    """Response model for storage statistics"""
    
    total_series: int
    active_series: int
    total_observations: int
    total_releases: int
    avg_observations_per_series: float


class SeriesSummaryResponse(BaseModel):
    """Response model for series summary"""
    
    series_id: str
    title: Optional[str]
    units: Optional[str]
    observation_count: int
    latest_observation: Optional[Dict[str, Any]]
    last_updated: Optional[datetime]


class StoreSeriesRequest(BaseModel):
    """Request model for storing series data"""
    
    series_id: str = Field(..., description="BLS series ID to store")
    start_year: int = Field(..., ge=1913, le=datetime.now().year + 1)
    end_year: int = Field(..., ge=1913, le=datetime.now().year + 1)
    force_refresh: bool = Field(False, description="Force refresh from BLS API")
    include_calculations: bool = Field(True, description="Include MoM/YoY calculations")


@router.get("/health")
def storage_health_check() -> Dict[str, Any]:
    """
    Check the health of the storage service
    """
    return {
        "status": "healthy",
        "service": "BLS Data Storage",
        "timestamp": datetime.now().isoformat(),
        "capabilities": [
            "Data persistence",
            "Series caching",
            "Database operations",
            "Historical data storage",
            "Release tracking"
        ]
    }


@router.post("/init")
def initialize_database() -> Dict[str, Any]:
    """
    Initialize the database (create tables)
    
    This endpoint creates all necessary database tables.
    Safe to call multiple times.
    """
    try:
        init_db()
        return {
            "success": True,
            "message": "Database initialized successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize database: {str(e)}"
        )


@router.get("/stats", response_model=StorageStatsResponse)
def get_storage_statistics(db: Session = Depends(get_db)) -> StorageStatsResponse:
    """
    Get database storage statistics
    
    Returns comprehensive statistics about stored BLS data including
    series counts, observation counts, and storage efficiency metrics.
    """
    try:
        data_manager = BLSDataManager(db)
        stats = data_manager.get_database_stats()
        
        return StorageStatsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get storage statistics: {str(e)}"
        )


@router.get("/series/{series_id}/summary", response_model=SeriesSummaryResponse)
def get_series_summary(
    series_id: str,
    db: Session = Depends(get_db)
) -> SeriesSummaryResponse:
    """
    Get summary information for a stored series
    
    Args:
        series_id: BLS series identifier
    
    Returns:
        Series summary with metadata and latest observation info
    """
    try:
        data_manager = BLSDataManager(db)
        summary = data_manager.get_series_summary(series_id)
        
        if not summary:
            raise HTTPException(
                status_code=404,
                detail=f"Series {series_id} not found in storage"
            )
        
        return SeriesSummaryResponse(**summary)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get series summary: {str(e)}"
        )


@router.post("/series/store")
def store_series_data(
    request: StoreSeriesRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Fetch and store BLS series data
    
    This endpoint fetches data from the BLS API and stores it in the database.
    It supports caching and will use cached data unless force_refresh is True.
    """
    try:
        processor = BLSStorageProcessor(db=db)
        
        result = processor.fetch_and_store_series(
            series_id=request.series_id,
            start_year=request.start_year,
            end_year=request.end_year,
            force_refresh=request.force_refresh,
            include_calculations=request.include_calculations
        )
        
        # Serialize the result for JSON response
        serialized_result = {
            "success": True,
            "series_id": request.series_id,
            "period": f"{request.start_year}-{request.end_year}",
            "observations_count": result["total_observations"],
            "storage_info": result.get("storage_info", {}),
            "data_quality": result["data_quality"]["overall_quality"],
            "processing_timestamp": result["processing_timestamp"]
        }
        
        processor.close()
        return serialized_result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to store series data: {str(e)}"
        )


@router.get("/series/search")
def search_series(
    keywords: str = Query(..., description="Keywords to search for in series titles"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results to return"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Search for stored series by keywords
    
    Args:
        keywords: Space-separated keywords to search for
        limit: Maximum number of results to return
    
    Returns:
        List of matching series summaries
    """
    try:
        processor = BLSStorageProcessor(db=db)
        
        # Split keywords and search
        keyword_list = keywords.strip().split()
        matching_series = processor.get_series_by_category(keyword_list)
        
        # Limit results
        limited_results = matching_series[:limit]
        
        processor.close()
        
        return {
            "success": True,
            "query": keywords,
            "results_count": len(limited_results),
            "total_matches": len(matching_series),
            "series": limited_results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search series: {str(e)}"
        )


@router.get("/series/list")
def list_stored_series(
    active_only: bool = Query(True, description="Return only active series"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results to return"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    List all stored series
    
    Args:
        active_only: Whether to return only active series
        limit: Maximum number of series to return
    
    Returns:
        List of stored series with basic information
    """
    try:
        data_manager = BLSDataManager(db)
        
        # Get all series from database
        all_series = data_manager.series_crud.get_all_series(db, active_only=active_only)
        
        # Limit results and create summaries
        limited_series = all_series[:limit]
        series_list = []
        
        for series in limited_series:
            series_list.append({
                "series_id": series.series_id,
                "title": series.title,
                "units": series.units,
                "area_name": series.area_name,
                "item_name": series.item_name,
                "is_active": series.is_active,
                "last_updated": series.last_updated.isoformat() if series.last_updated else None
            })
        
        return {
            "success": True,
            "total_series": len(all_series),
            "returned_count": len(series_list),
            "active_only": active_only,
            "series": series_list,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list series: {str(e)}"
        )


@router.delete("/series/{series_id}")
def deactivate_series(
    series_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Deactivate a stored series (soft delete)
    
    Args:
        series_id: BLS series identifier to deactivate
    
    Returns:
        Confirmation of deactivation
    """
    try:
        data_manager = BLSDataManager(db)
        
        success = data_manager.series_crud.delete_series(db, series_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Series {series_id} not found"
            )
        
        return {
            "success": True,
            "message": f"Series {series_id} deactivated successfully",
            "series_id": series_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to deactivate series: {str(e)}"
        )


@router.post("/maintenance/cleanup")
def cleanup_old_data(
    days_to_keep: int = Query(90, ge=1, le=365, description="Days of data to keep"),
    dry_run: bool = Query(True, description="Perform dry run without actual deletion"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Clean up old data from the database
    
    Args:
        days_to_keep: Number of days of data to keep
        dry_run: If True, only report what would be deleted
    
    Returns:
        Cleanup statistics
    """
    try:
        processor = BLSStorageProcessor(db=db)
        
        if dry_run:
            # For now, just return placeholder statistics
            cleanup_stats = {
                "observations_to_remove": 0,
                "series_to_deactivate": 0,
                "releases_to_archive": 0
            }
        else:
            cleanup_stats = processor.cleanup_old_data(days_to_keep)
        
        processor.close()
        
        return {
            "success": True,
            "dry_run": dry_run,
            "days_to_keep": days_to_keep,
            "cleanup_stats": cleanup_stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cleanup data: {str(e)}"
        )


@router.get("/config")
def get_storage_config() -> Dict[str, Any]:
    """
    Get storage configuration information
    """
    from app.config import settings
    
    return {
        "database_url": settings.database_url.split("://")[0] + "://***",  # Hide credentials
        "storage_features": {
            "caching": True,
            "historical_data": True,
            "release_tracking": True,
            "bulk_operations": True
        },
        "cache_settings": {
            "default_cache_hours": 24,
            "force_refresh_available": True
        },
        "maintenance": {
            "cleanup_available": True,
            "bulk_updates_available": True
        }
    }
