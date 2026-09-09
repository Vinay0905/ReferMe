import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.v1.artifacts import router as artifacts_router
from app.api.v1.health import router as health_router
from app.api.v1.ingest import router as ingest_router
from app.api.v1.logs import router as logs_router
from app.api.v1.questions import router as questions_router
from app.api.v1.tests import router as tests_router
from app.api.v1.topics import router as topics_router
from app.config import get_settings
from app.core.logging_config import setup_central_logging
from app.db.indexes import create_indexes
from app.db.mongo import close_mongo_connection, connect_to_mongo
from app.middleware.logging_middleware import LoggingMiddleware

# Initialize centralized logging (Console + logs/app.log + logs/errors.log)
setup_central_logging()
logger = logging.getLogger("referme.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect Mongo and ensure indexes
    await connect_to_mongo()
    await create_indexes()
    yield
    # Shutdown: Close connection pool
    await close_mongo_connection()


settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTTP Access Logging & Latency Tracking Middleware
app.add_middleware(LoggingMiddleware)


# Global Exception Handler with Request ID tracking
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    req_id = getattr(request.state, "request_id", "unknown")
    logger.error(
        f"[{req_id}] Global unhandled error on {request.method} {request.url.path}: {exc}",
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred.",
            "error_id": req_id,
        },
        headers={"X-Request-ID": req_id},
    )


# Include Routers
app.include_router(health_router, prefix=settings.API_V1_STR, tags=["Health"])
app.include_router(health_router, tags=["Health Root"])  # Allows top-level /health & /ready
app.include_router(tests_router, prefix=settings.API_V1_STR)
app.include_router(topics_router, prefix=settings.API_V1_STR)
app.include_router(questions_router, prefix=settings.API_V1_STR)
app.include_router(artifacts_router, prefix=settings.API_V1_STR)
app.include_router(ingest_router, prefix=settings.API_V1_STR)
app.include_router(logs_router, prefix=settings.API_V1_STR)
