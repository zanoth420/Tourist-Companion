"""Tourist Companion API.

One process serves everything:

  pip install -r requirements.txt
  uvicorn main:app --app-dir api --port 8000

  /api/plan, /api/places, /api/presets   planning (see planning.py)
  /api/auth/*                            register / login / logout / me
  /api/trips                             saved trips (per user)
  /                                      the website (static)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import config
import auth
import db
import planning
import trips


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="Tourist Companion API", lifespan=lifespan)
app.include_router(planning.router)
app.include_router(auth.router)
app.include_router(trips.router)

# mounted last so /api/* wins; html=True serves index.html at /
app.mount("/", StaticFiles(directory=config.SITE_DIR, html=True), name="site")
