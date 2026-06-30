"""FastAPI application entry point.

Run from the ``backend/`` directory:
    uvicorn app.main:app --reload
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.init_db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (swap for Alembic migrations in production).
    init_db()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)



@app.get("/", tags=["health"])
def root() -> dict:
    return {"status": "ok", "service": settings.PROJECT_NAME, "docs": "/docs"}