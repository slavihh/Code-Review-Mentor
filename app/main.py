# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.db import Base, engine
from app.api.submissions import router as submissions_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield
    finally:
        # Shutdown
        await engine.dispose()

app = FastAPI(
    lifespan=lifespan,
    title="Code Review Mentor",
    description="A FastAPI app for code submissions and AI feedback",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(submissions_router)

@app.get("/")
async def root():
    return {"message": "Hello from Code Review Mentor 🚀"}
