"""Saved trips: store, list, view, delete — plus public share links.

Sharing gives out an unguessable token; anyone with the link can view
(read-only, no owner identity exposed). The owner can revoke it anytime.
"""

import json
import secrets
import sqlite3

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth import current_user
from db import get_db

router = APIRouter(prefix="/api/trips", tags=["trips"])
public = APIRouter(prefix="/api", tags=["trips"])


class SaveTripRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    params: dict
    plan: dict


def _summary(plan: dict) -> dict:
    return {
        "total_cost": plan.get("total_cost"),
        "total_places": plan.get("total_places"),
        "days": len(plan.get("days", [])),
    }


@router.post("", status_code=201)
def save_trip(req: SaveTripRequest, user: dict = Depends(current_user),
              db: sqlite3.Connection = Depends(get_db)):
    cur = db.execute(
        "INSERT INTO trips (user_id, name, params_json, plan_json) VALUES (?, ?, ?, ?)",
        (user["id"], req.name.strip(), json.dumps(req.params), json.dumps(req.plan)))
    return {"id": cur.lastrowid}


@router.get("")
def list_trips(user: dict = Depends(current_user),
               db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute(
        "SELECT id, name, plan_json, share_token, created_at FROM trips "
        "WHERE user_id = ? ORDER BY created_at DESC", (user["id"],)).fetchall()
    return [{"id": r["id"], "name": r["name"], "created_at": r["created_at"],
             "share_token": r["share_token"],
             **_summary(json.loads(r["plan_json"]))} for r in rows]


@router.get("/{trip_id}")
def get_trip(trip_id: int, user: dict = Depends(current_user),
             db: sqlite3.Connection = Depends(get_db)):
    row = db.execute("SELECT * FROM trips WHERE id = ? AND user_id = ?",
                     (trip_id, user["id"])).fetchone()
    if row is None:
        raise HTTPException(404, "Trip not found")
    return {"id": row["id"], "name": row["name"], "created_at": row["created_at"],
            "params": json.loads(row["params_json"]),
            "plan": json.loads(row["plan_json"])}


@router.delete("/{trip_id}")
def delete_trip(trip_id: int, user: dict = Depends(current_user),
                db: sqlite3.Connection = Depends(get_db)):
    cur = db.execute("DELETE FROM trips WHERE id = ? AND user_id = ?",
                     (trip_id, user["id"]))
    if cur.rowcount == 0:
        raise HTTPException(404, "Trip not found")
    return {"ok": True}


# --- sharing --------------------------------------------------------------

@router.post("/{trip_id}/share")
def share_trip(trip_id: int, user: dict = Depends(current_user),
               db: sqlite3.Connection = Depends(get_db)):
    row = db.execute("SELECT share_token FROM trips WHERE id = ? AND user_id = ?",
                     (trip_id, user["id"])).fetchone()
    if row is None:
        raise HTTPException(404, "Trip not found")
    token = row["share_token"]
    if not token:
        token = secrets.token_urlsafe(16)
        db.execute("UPDATE trips SET share_token = ? WHERE id = ?", (token, trip_id))
    return {"token": token, "url": f"/share.html?t={token}"}


@router.delete("/{trip_id}/share")
def revoke_share(trip_id: int, user: dict = Depends(current_user),
                 db: sqlite3.Connection = Depends(get_db)):
    cur = db.execute("UPDATE trips SET share_token = NULL "
                     "WHERE id = ? AND user_id = ?", (trip_id, user["id"]))
    if cur.rowcount == 0:
        raise HTTPException(404, "Trip not found")
    return {"ok": True}


@public.get("/shared/{token}")
def get_shared(token: str, db: sqlite3.Connection = Depends(get_db)):
    row = db.execute("SELECT name, plan_json, created_at FROM trips "
                     "WHERE share_token = ?", (token,)).fetchone()
    if row is None:
        raise HTTPException(404, "This share link is invalid or was revoked")
    return {"name": row["name"], "created_at": row["created_at"],
            "plan": json.loads(row["plan_json"])}
