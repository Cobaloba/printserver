from typing import Annotated
from fastapi import APIRouter, Depends
from app.dependencies import get_status_cache
from app.services.status_cache import StatusCache

router = APIRouter()
CacheDep = Annotated[StatusCache, Depends(get_status_cache)]


@router.get("/api/v1/status")
def get_status(cache: CacheDep):
    return cache.get_cached()
