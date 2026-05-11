from typing import Annotated
from fastapi import APIRouter, Depends
from app.auth import require_api_key
from app.dependencies import get_roll_tracker
from app.services.roll_tracker import RollTracker
from app.models.admin_models import NewRollRequest

router = APIRouter(prefix="/api/v1/admin", tags=["admin"], dependencies=[Depends(require_api_key)])
TrackerDep = Annotated[RollTracker, Depends(get_roll_tracker)]


@router.post("/roll")
def reset_roll(req: NewRollRequest, tracker: TrackerDep):
    tracker.reset(req.width_mm, req.diameter_mm)
    return {"success": True}


@router.get("/roll")
def get_roll_state(tracker: TrackerDep):
    state = tracker.state
    return {
        "bytes_printed": state["bytes_printed"],
        "roll_width_mm": state["roll_width_mm"],
        "roll_diameter_mm": state["roll_diameter_mm"],
        "last_reset": state["last_reset"],
        "estimated_remaining_pct": tracker.estimate_remaining(),
    }
