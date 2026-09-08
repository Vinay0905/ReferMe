import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.health import router as health_router
from app.api.v1.ingest import router as ingest_router
from app.config import get_settings
from app.db.indexes import create_indexes
from app.db.mongo import close_mongo_connection, connect_to_mongo

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
logger = logging.getLogger(__name__)


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
    allow_origins=["*"],  # Restrict appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health_router, prefix=settings.API_V1_STR, tags=["Health"])
app.include_router(health_router, tags=["Health Root"])  # Allows top-level /health & /ready
app.include_router(ingest_router, prefix=settings.API_V1_STR)
