import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.core.db import Base, engine, init_mongo, close_mongo
from app.api.submissions import router as submissions_router
from app.api.ai import router as ai_router

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up application...")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    init_mongo()

    try:
        yield
    finally:
        logger.info("Shutting down application...")

        await engine.dispose()
        close_mongo()


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

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error at {request.url.path}")  # full traceback
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error"
        },
    )
