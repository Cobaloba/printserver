import os
import signal
import threading
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


@router.post("/restart")
def restart_service():
    def _delayed_shutdown():
        import time
        time.sleep(1)
        os.kill(os.getpid(), signal.SIGTERM)
    threading.Thread(target=_delayed_shutdown, daemon=False).start()
    return {"success": True}


@router.get("/bot-log")
def get_bot_log():
    from app.dependencies import get_telegram_bot
    bot = get_telegram_bot()
    return bot.get_log() if bot is not None else []
