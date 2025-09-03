import logging
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.core.db import Base, engine
from app.api.submissions import router as submissions_router
from app.api.ai import router as ai_router
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("app")


mongo_client: AsyncIOMotorClient | None = None
mongo_db: AsyncIOMotorDatabase | None = None

MONGO_URL: str = os.getenv("MONGO_URL", "mongodb://mongo:27017")
MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "codereview")

@asynccontextmanager
async def lifespan(app: FastAPI):
    global mongo_client, mongo_db

    logger.info("Starting up application...")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    mongo_client = AsyncIOMotorClient(MONGO_URL)
    mongo_db = mongo_client[MONGO_DB_NAME]
    logger.info("MongoDB client initialized")

    try:
        yield
    finally:
        logger.info("Shutting down application...")

        await engine.dispose()
        mongo_client.close()
        logger.info("MongoDB client closed")


app = FastAPI(
    lifespan=lifespan,
    title="Code Review Mentor",
    description="A FastAPI app for code submissions and AI feedback",
    version="0.1.0",
)


# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Routers ---
app.include_router(submissions_router)
app.include_router(ai_router)


# --- Global error handler ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error at {request.url.path}")  # full traceback
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error"
        },  # don’t leak stack traces to clients
    )
