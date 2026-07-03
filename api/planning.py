"""Trip planning endpoints: the dataset, curated presets, and the planner."""

import csv
import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import config  # noqa: F401  (adds algorithm/ to sys.path — must precede planner import)
from planner import plan_as_json
from solver import DATA_FILE

router = APIRouter(prefix="/api", tags=["planning"])


class PlanRequest(BaseModel):
    budget: int = Field(gt=0, description="ticket budget in EGP")
    tier: str = Field("foreign", pattern="^(foreign|egyptian)$")
    student: bool = False
    days: int = Field(3, ge=1, le=14)
    hours_per_day: float = Field(9.0, ge=2, le=16)
    cities: list[str] | None = None
    preferences: dict[str, float] | None = None  # e.g. {"ancient": 2}


@router.get("/places")
def get_places():
    with open(DATA_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


@router.get("/presets")
def get_presets():
    with open(config.PRESETS_FILE, encoding="utf-8") as f:
        return json.load(f)


@router.post("/plan")
def post_plan(req: PlanRequest):
    try:
        return plan_as_json(budget=req.budget, tier=req.tier, student=req.student,
                            days=req.days, hours_per_day=req.hours_per_day,
                            weights=req.preferences, cities=req.cities)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
