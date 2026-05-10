from typing import Annotated
from fastapi import APIRouter, Depends
from app.dependencies import get_status_cache, get_roll_tracker
from app.services.status_cache import StatusCache
from app.services.roll_tracker import RollTracker

router = APIRouter()
CacheDep = Annotated[StatusCache, Depends(get_status_cache)]
TrackerDep = Annotated[RollTracker, Depends(get_roll_tracker)]


@router.get("/api/v1/status")
def get_status(cache: CacheDep, tracker: TrackerDep):
    status = cache.get_cached()
    status["estimated_remaining_pct"] = tracker.estimate_remaining()
    return status
