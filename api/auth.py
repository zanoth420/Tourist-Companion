"""Authentication: register / login / logout / me.

Passwords are hashed with PBKDF2-SHA256 (stdlib, OWASP-recommended
iteration count). Sessions are opaque random tokens in an HttpOnly
SameSite=Lax cookie; only the token's SHA-256 is stored server-side.
"""

import hashlib
import hmac
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

from config import COOKIE_SECURE, SESSION_COOKIE, SESSION_DAYS
from db import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])

PBKDF2_ITERATIONS = 600_000
EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


# --- password hashing ---------------------------------------------------

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt),
                                 PBKDF2_ITERATIONS).hex()
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iterations, salt, digest = stored.split("$")
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode(),
                                        bytes.fromhex(salt), int(iterations)).hex()
        return hmac.compare_digest(candidate, digest)
    except (ValueError, TypeError):
        return False


# --- sessions -----------------------------------------------------------

def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _create_session(db: sqlite3.Connection, user_id: int, response: Response):
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)
    db.execute("INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
               (_token_hash(token), user_id, expires.isoformat()))
    response.set_cookie(SESSION_COOKIE, token, max_age=SESSION_DAYS * 86400,
                        httponly=True, samesite="lax", secure=COOKIE_SECURE)


def current_user(request: Request, db: sqlite3.Connection = Depends(get_db)):
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(401, "Not logged in")
    db.execute("DELETE FROM sessions WHERE expires_at < ?",
               (datetime.now(timezone.utc).isoformat(),))
    row = db.execute(
        "SELECT u.id, u.email, u.name FROM sessions s JOIN users u ON u.id = s.user_id "
        "WHERE s.token_hash = ? AND s.expires_at >= ?",
        (_token_hash(token), datetime.now(timezone.utc).isoformat())).fetchone()
    if row is None:
        raise HTTPException(401, "Session expired — please log in again")
    return dict(row)


# --- endpoints ----------------------------------------------------------

class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    email: str = Field(pattern=EMAIL_PATTERN, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/register", status_code=201)
def register(req: RegisterRequest, response: Response,
             db: sqlite3.Connection = Depends(get_db)):
    try:
        cur = db.execute("INSERT INTO users (email, name, password_hash) VALUES (?, ?, ?)",
                         (req.email.strip(), req.name.strip(), hash_password(req.password)))
    except sqlite3.IntegrityError:
        raise HTTPException(409, "An account with this email already exists")
    _create_session(db, cur.lastrowid, response)
    return {"id": cur.lastrowid, "name": req.name.strip(), "email": req.email.strip()}


@router.post("/login")
def login(req: LoginRequest, response: Response,
          db: sqlite3.Connection = Depends(get_db)):
    row = db.execute("SELECT id, email, name, password_hash FROM users WHERE email = ?",
                     (req.email.strip(),)).fetchone()
    if row is None or not verify_password(req.password, row["password_hash"]):
        raise HTTPException(401, "Invalid email or password")
    _create_session(db, row["id"], response)
    return {"id": row["id"], "name": row["name"], "email": row["email"]}


@router.post("/logout")
def logout(request: Request, response: Response,
           db: sqlite3.Connection = Depends(get_db)):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        db.execute("DELETE FROM sessions WHERE token_hash = ?", (_token_hash(token),))
    response.delete_cookie(SESSION_COOKIE)
    return {"ok": True}


@router.get("/me")
def me(user: dict = Depends(current_user)):
    return user
