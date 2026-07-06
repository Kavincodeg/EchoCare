from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from database import get_db
from routers.auth import get_current_user

router = APIRouter(prefix="/api/tracker", tags=["tracker"])


# ── Schema ────────────────────────────────────────────────────────────────────

class TrackerLog(BaseModel):
    date: Optional[str] = None
    fatigue: Optional[float] = 5
    joint_pain: Optional[float] = 3
    brain_fog: Optional[float] = 3
    dizziness: Optional[float] = 2
    mood: Optional[str] = "good"
    sleep_hours: Optional[float] = 7.0
    water_intake: Optional[float] = 2.0
    notes: Optional[str] = ""


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("")
async def save_tracker(log: TrackerLog, current_user: dict = Depends(get_current_user)):
    db = get_db()
    today = log.date or date.today().isoformat()

    doc = {
        "user_email": current_user["email"],
        "date": today,
        "fatigue": log.fatigue,
        "joint_pain": log.joint_pain,
        "brain_fog": log.brain_fog,
        "dizziness": log.dizziness,
        "mood": log.mood,
        "sleep_hours": log.sleep_hours,
        "water_intake": log.water_intake,
        "notes": log.notes,
        "updated_at": datetime.utcnow().isoformat(),
    }

    # Upsert — one log per user per day
    await db.tracker_logs.update_one(
        {"user_email": current_user["email"], "date": today},
        {"$set": doc},
        upsert=True,
    )

    saved = await db.tracker_logs.find_one(
        {"user_email": current_user["email"], "date": today}
    )
    saved["_id"] = str(saved["_id"])
    return saved


@router.get("/history")
async def get_history(current_user: dict = Depends(get_current_user)):
    db = get_db()
    cursor = db.tracker_logs.find(
        {"user_email": current_user["email"]},
        sort=[("date", -1)],
    ).limit(30)

    logs = []
    async for log in cursor:
        log["_id"] = str(log["_id"])
        logs.append(log)

    return logs
