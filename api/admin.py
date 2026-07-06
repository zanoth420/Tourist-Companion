"""Admin dashboard API: platform stats and user management.

Every endpoint requires an admin session (see auth.require_admin). Admins
are granted via TC_ADMIN_EMAILS — matching accounts are promoted on their
next login or at registration.
"""

from fastapi import APIRouter, Depends, HTTPException

from auth import require_admin
from db import Db, get_db

router = APIRouter(prefix="/api/admin", tags=["admin"],
                   dependencies=[Depends(require_admin)])


def _count(db: Db, sql: str) -> int:
    return db.execute(sql).fetchone()["n"]


@router.get("/stats")
def stats(db: Db = Depends(get_db)):
    recent_users = db.execute(
        "SELECT u.id, u.name, u.email, u.created_at, u.is_admin, "
        "       (SELECT COUNT(*) FROM trips t WHERE t.user_id = u.id) AS trips "
        "FROM users u ORDER BY u.id DESC LIMIT 10").fetchall()
    recent_trips = db.execute(
        "SELECT t.id, t.name, t.created_at, u.email AS user_email, "
        "       (t.share_token IS NOT NULL) AS shared "
        "FROM trips t JOIN users u ON u.id = t.user_id "
        "ORDER BY t.id DESC LIMIT 10").fetchall()
    return {
        "users": _count(db, "SELECT COUNT(*) AS n FROM users"),
        "trips": _count(db, "SELECT COUNT(*) AS n FROM trips"),
        "shared_trips": _count(
            db, "SELECT COUNT(*) AS n FROM trips WHERE share_token IS NOT NULL"),
        "active_sessions": _count(db, "SELECT COUNT(*) AS n FROM sessions"),
        "recent_users": [dict(r) for r in recent_users],
        "recent_trips": [dict(r) for r in recent_trips],
    }


@router.get("/users")
def list_users(db: Db = Depends(get_db)):
    rows = db.execute(
        "SELECT u.id, u.name, u.email, u.created_at, u.is_admin, "
        "       (SELECT COUNT(*) FROM trips t WHERE t.user_id = u.id) AS trips "
        "FROM users u ORDER BY u.id").fetchall()
    return [dict(r) for r in rows]


@router.delete("/users/{user_id}")
def delete_user(user_id: int, admin: dict = Depends(require_admin),
                db: Db = Depends(get_db)):
    if user_id == admin["id"]:
        raise HTTPException(400, "You cannot delete your own account")
    cur = db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    if cur.rowcount == 0:
        raise HTTPException(404, "User not found")
    return {"ok": True}  # sessions and trips cascade via foreign keys
