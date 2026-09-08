# Phase 1: Backend Scaffolding, Data Modeling & Storage Layer

This guide provides step-by-step instructions and complete code to set up the backend foundation for the **ALLEN NEET Test ↔ Topic Intelligence System**.

Follow the steps in order.

---

## Directory Structure to Create

Inside `/Users/mast/Documents/VInayPrograming/ReferMe`, set up the following folder structure:

```text
ReferMe/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       └── health.py
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── mongo.py
│   │   │   └── indexes.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── common.py
│   │   │   ├── test.py
│   │   │   ├── topic.py
│   │   │   ├── relationship.py
│   │   │   ├── artifact.py
│   │   │   └── ingestion.py
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── test_repo.py
│   │   │   ├── topic_repo.py
│   │   │   ├── test_topic_repo.py
│   │   │   └── artifact_repo.py
│   │   └── storage/
│   │       ├── __init__.py
│   │       ├── base.py
│   │       └── local.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   └── test_models_and_repos.py
│   ├── .env.example
│   ├── .gitignore
│   └── requirements.txt
```

---

## Step 1: Environment & Dependency Setup

### 1.1 Activate conda environment
In your terminal, activate your existing conda environment:

```bash
conda activate all
cd /Users/mast/Documents/VInayPrograming/ReferMe/backend
```

### 1.2 Create `backend/requirements.txt`

```text
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.8.0
pydantic-settings>=2.4.0
motor>=3.6.0
pymongo>=4.9.0
httpx>=0.27.0
pdfplumber>=0.11.0
pypdf>=4.3.0
python-multipart>=0.0.9

# Testing
pytest>=8.3.0
pytest-asyncio>=0.24.0
mongomock-motor>=0.0.31
```

Install requirements:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 1.3 Create `backend/.gitignore`

```text
venv/
__pycache__/
*.pyc
.env
.pytest_cache/
storage_data/
*.log
.DS_Store
```

### 1.4 Create `backend/.env.example` and `backend/.env`

**`backend/.env.example`**:
```ini
ENVIRONMENT=development
PROJECT_NAME="ALLEN NEET Test ↔ Topic Intelligence System"
API_V1_STR="/api/v1"

# MongoDB Atlas URI (Replace with your actual Atlas connection string)
MONGODB_URI="mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority"
MONGODB_DB_NAME="referme_neet_dev"

# Storage configuration
STORAGE_PROVIDER="local"
LOCAL_STORAGE_DIR="./storage_data"

# Ingestion settings
DEFAULT_PAGE_SIZE=25
MAX_CONCURRENT_REQUESTS=3
REQUEST_TIMEOUT_SECONDS=30
```

Copy it to `.env`:
```bash
cp .env.example .env
```
> **Note**: Update `MONGODB_URI` in `.env` with your real MongoDB Atlas connection string.

---

## Step 2: Configuration (`backend/app/config.py`)

Create `backend/app/config.py`:

```python
from functools import lru_cache
from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "ALLEN NEET Test ↔ Topic Intelligence System"
    API_V1_STR: str = "/api/v1"

    # MongoDB
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "referme_neet_dev"

    # Storage
    STORAGE_PROVIDER: Literal["local", "gridfs", "s3"] = "local"
    LOCAL_STORAGE_DIR: str = "./storage_data"

    # Ingestion
    DEFAULT_PAGE_SIZE: int = 25
    MAX_CONCURRENT_REQUESTS: int = 3
    REQUEST_TIMEOUT_SECONDS: int = 30

    @property
    def storage_path(self) -> Path:
        path = Path(self.LOCAL_STORAGE_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

---

## Step 3: Pydantic Domain Models

### 3.1 Common Types (`backend/app/models/common.py`)

```python
from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Any
from pydantic import BaseModel, BeforeValidator, Field


def py_object_id_validator(val: Any) -> str:
    if val is None:
        return ""
    return str(val)


PyObjectId = Annotated[str, BeforeValidator(py_object_id_validator)]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class BaseMongoModel(BaseModel):
    id: PyObjectId = Field(default="", alias="_id")

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {datetime: lambda dt: dt.isoformat()},
    }


class Subject(str, Enum):
    PHYSICS = "Physics"
    CHEMISTRY = "Chemistry"
    BIOLOGY = "Biology"


class ProcessingStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    SYLLABUS_PENDING = "SYLLABUS_PENDING"
    SYLLABUS_FETCHED = "SYLLABUS_FETCHED"
    SYLLABUS_PARSED = "SYLLABUS_PARSED"
    TOPICS_PROCESSED = "TOPICS_PROCESSED"
    QUESTION_PAPER_PENDING = "QUESTION_PAPER_PENDING"
    READY = "READY"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
```

### 3.2 Test Model (`backend/app/models/test.py`)

```python
from datetime import datetime
from typing import Optional
from pydantic import Field
from app.models.common import BaseMongoModel, ProcessingStatus, utc_now


class TestModel(BaseMongoModel):
    external_source: str = "allen"
    external_test_id: str
    name: str
    date: Optional[str] = None  # YYYY-MM-DD or raw string from card (e.g. "13 Sep")
    duration_minutes: Optional[int] = None
    mode: Optional[str] = None  # e.g., "Offline", "Online"
    status: Optional[str] = None  # e.g., "UPCOMING", "FINAL_RESULT_GENERATED"
    category: Optional[str] = None  # e.g., "DLP", "MINOR", "MAJOR"
    processing_status: ProcessingStatus = ProcessingStatus.DISCOVERED
    has_syllabus: bool = False
    has_question_paper: bool = False
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
```

### 3.3 Topic Model (`backend/app/models/topic.py`)

```python
from datetime import datetime
from typing import List
from pydantic import Field
from app.models.common import BaseMongoModel, Subject, utc_now


class TopicModel(BaseMongoModel):
    subject: Subject
    name: str  # Display name, e.g., "Electric Power"
    canonical_key: str  # Unique key, e.g., "physics:electric-power"
    aliases: List[str] = Field(default_factory=list)
    test_count: int = 0  # Denormalized counter for fast UI rendering
    active: bool = True
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
```

### 3.4 Relationship Model (`backend/app/models/relationship.py`)

```python
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import Field
from app.models.common import BaseMongoModel, Subject, utc_now


class NormalizationMethod(str, Enum):
    DETERMINISTIC = "deterministic"
    ALIAS = "alias"
    MANUAL = "manual"
    AI_SUGGESTED = "ai_suggested"


class TestTopicModel(BaseMongoModel):
    test_id: str  # References tests._id
    external_test_id: str  # For quick index debugging
    topic_id: str  # References topics._id
    canonical_key: str
    subject: Subject
    source_text: str  # Exact wording as parsed from syllabus PDF
    source_section: Optional[str] = None
    syllabus_snapshot_id: Optional[str] = None
    normalization_method: NormalizationMethod = NormalizationMethod.DETERMINISTIC
    normalization_version: str = "v1"
    confidence: float = 1.0
    created_at: datetime = Field(default_factory=utc_now)
```

### 3.5 Artifact Model & Syllabus Snapshot (`backend/app/models/artifact.py`)

```python
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import Field
from app.models.common import BaseMongoModel, utc_now


class ArtifactKind(str, Enum):
    SYLLABUS = "syllabus"
    QUESTION_PAPER = "question_paper"


class ArtifactModel(BaseMongoModel):
    test_id: str  # References tests._id
    external_test_id: str
    kind: ArtifactKind
    source: str = "allen"
    stable_object_key: str  # e.g., "test_12345/syllabus.pdf"
    storage_provider: str = "local"
    storage_key: str  # File path or S3 key
    sha256: str
    content_type: str = "application/pdf"
    size_bytes: int
    language: str = "en"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class SyllabusSnapshotModel(BaseMongoModel):
    test_id: str
    external_test_id: str
    artifact_id: Optional[str] = None
    content_hash: str
    parser_version: str = "v1"
    raw_sections: List[Dict[str, Any]] = Field(default_factory=list)
    extracted_at: datetime = Field(default_factory=utc_now)
    created_at: datetime = Field(default_factory=utc_now)
```

### 3.6 Ingestion Job Model (`backend/app/models/ingestion.py`)

```python
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from app.models.common import BaseMongoModel, utc_now


class IngestionStatus(str, Enum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"


class IngestionJobModel(BaseMongoModel):
    status: IngestionStatus = IngestionStatus.RUNNING
    start_time: datetime = Field(default_factory=utc_now)
    end_time: Optional[datetime] = None
    discovered_count: int = 0
    succeeded_count: int = 0
    partial_count: int = 0
    failed_count: int = 0
    error_summary: List[Dict[str, str]] = Field(default_factory=list)
    parser_version: str = "v1"
```

---

## Step 4: MongoDB Atlas Connection & Indexes

### 4.1 Connection Manager (`backend/app/db/mongo.py`)

Create `backend/app/db/mongo.py`:

```python
import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import get_settings

logger = logging.getLogger(__name__)


class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None


db_context = MongoDB()


async def connect_to_mongo():
    settings = get_settings()
    logger.info("Connecting to MongoDB Atlas...")
    db_context.client = AsyncIOMotorClient(
        settings.MONGODB_URI,
        serverSelectionTimeoutMS=5000
    )
    db_context.db = db_context.client[settings.MONGODB_DB_NAME]
    # Ping to verify connection
    await db_context.db.command("ping")
    logger.info(f"Connected to MongoDB Atlas: {settings.MONGODB_DB_NAME}")


async def close_mongo_connection():
    if db_context.client:
        logger.info("Closing MongoDB connection...")
        db_context.client.close()
        logger.info("MongoDB connection closed.")


def get_database() -> AsyncIOMotorDatabase:
    if db_context.db is None:
        raise RuntimeError("Database is not initialized. Call connect_to_mongo first.")
    return db_context.db
```

### 4.2 Index Provisioning (`backend/app/db/indexes.py`)

Create `backend/app/db/indexes.py`:

```python
import logging
from pymongo import ASCENDING, IndexModel
from app.db.mongo import get_database

logger = logging.getLogger(__name__)


async def create_indexes():
    """Idempotently provisions all required MongoDB compound & unique indexes."""
    db = get_database()
    logger.info("Creating MongoDB indexes...")

    # tests: unique external source + ID, date index, status index
    await db["tests"].create_indexes([
        IndexModel([("external_source", ASCENDING), ("external_test_id", ASCENDING)], unique=True, name="idx_tests_external_unique"),
        IndexModel([("date", ASCENDING)], name="idx_tests_date"),
        IndexModel([("processing_status", ASCENDING)], name="idx_tests_status")
    ])

    # topics: unique canonical_key, subject + name
    await db["topics"].create_indexes([
        IndexModel([("canonical_key", ASCENDING)], unique=True, name="idx_topics_canonical_key_unique"),
        IndexModel([("subject", ASCENDING), ("name", ASCENDING)], name="idx_topics_subject_name")
    ])

    # test_topics: unique (test_id, topic_id), topic_id lookup, test_id lookup
    await db["test_topics"].create_indexes([
        IndexModel([("test_id", ASCENDING), ("topic_id", ASCENDING)], unique=True, name="idx_test_topics_unique"),
        IndexModel([("topic_id", ASCENDING)], name="idx_test_topics_by_topic"),
        IndexModel([("test_id", ASCENDING)], name="idx_test_topics_by_test"),
        IndexModel([("canonical_key", ASCENDING)], name="idx_test_topics_canonical_key"),
        IndexModel([("subject", ASCENDING)], name="idx_test_topics_subject")
    ])

    # artifacts: unique (source, stable_object_key, kind), test_id + kind
    await db["artifacts"].create_indexes([
        IndexModel([("source", ASCENDING), ("stable_object_key", ASCENDING), ("kind", ASCENDING)], unique=True, name="idx_artifacts_unique_key"),
        IndexModel([("test_id", ASCENDING), ("kind", ASCENDING)], name="idx_artifacts_test_kind")
    ])

    # syllabus_snapshots: test_id, content_hash
    await db["syllabus_snapshots"].create_indexes([
        IndexModel([("test_id", ASCENDING)], name="idx_snapshots_test_id"),
        IndexModel([("content_hash", ASCENDING)], name="idx_snapshots_hash")
    ])

    logger.info("MongoDB indexes successfully created.")
```

---

## Step 5: Abstract Artifact Storage Interface & Local Provider

### 5.1 Abstract Base (`backend/app/storage/base.py`)

```python
from abc import ABC, abstractmethod
from typing import BinaryIO, Optional


class ArtifactStorage(ABC):
    """Abstract interface for storing and retrieving PDF artifacts."""

    @abstractmethod
    async def save(self, key: str, content: bytes, content_type: str = "application/pdf") -> str:
        """Saves content bytes under a logical key. Returns the permanent storage identifier/path."""
        pass

    @abstractmethod
    async def get(self, storage_key: str) -> Optional[bytes]:
        """Retrieves content bytes for a stored artifact."""
        pass

    @abstractmethod
    async def exists(self, storage_key: str) -> bool:
        """Checks if artifact exists."""
        pass

    @abstractmethod
    async def delete(self, storage_key: str) -> bool:
        """Deletes artifact if present."""
        pass
```

### 5.2 Local File Storage Provider (`backend/app/storage/local.py`)

```python
import hashlib
from pathlib import Path
from typing import Optional
from app.config import get_settings
from app.storage.base import ArtifactStorage


class LocalArtifactStorage(ArtifactStorage):
    """Stores binary PDF artifacts on the local filesystem."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or get_settings().storage_path

    async def save(self, key: str, content: bytes, content_type: str = "application/pdf") -> str:
        # Sanitize relative path
        safe_key = key.lstrip("/")
        target_path = self.base_dir / safe_key
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(content)
        return str(target_path.resolve())

    async def get(self, storage_key: str) -> Optional[bytes]:
        path = Path(storage_key)
        if not path.exists():
            return None
        return path.read_bytes()

    async def exists(self, storage_key: str) -> bool:
        return Path(storage_key).exists()

    async def delete(self, storage_key: str) -> bool:
        path = Path(storage_key)
        if path.exists():
            path.unlink()
            return True
        return False


def get_storage_provider() -> ArtifactStorage:
    settings = get_settings()
    if settings.STORAGE_PROVIDER == "local":
        return LocalArtifactStorage()
    raise NotImplementedError(f"Storage provider '{settings.STORAGE_PROVIDER}' not implemented yet.")
```

---

## Step 6: Repository Layer

### 6.1 Base Repository (`backend/app/repositories/base.py`)

```python
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import BaseModel
from app.db.mongo import get_database

T = TypeVar("T", bound=BaseModel)


class BaseRepository(Generic[T]):
    def __init__(self, collection_name: str, model_cls: Type[T]):
        self.collection_name = collection_name
        self.model_cls = model_cls

    @property
    def collection(self) -> AsyncIOMotorCollection:
        return get_database()[self.collection_name]

    async def get_by_id(self, doc_id: str) -> Optional[T]:
        from bson import ObjectId
        query = {"_id": ObjectId(doc_id) if ObjectId.is_valid(doc_id) else doc_id}
        doc = await self.collection.find_one(query)
        if doc:
            return self.model_cls(**doc)
        return None

    async def insert(self, entity: T) -> str:
        doc = entity.model_dump(by_alias=True, exclude={"id"})
        result = await self.collection.insert_one(doc)
        return str(result.inserted_id)

    async def find_all(self, filter_query: Dict[str, Any] = None, skip: int = 0, limit: int = 50) -> List[T]:
        cursor = self.collection.find(filter_query or {}).skip(skip).limit(limit)
        items = []
        async for doc in cursor:
            items.append(self.model_cls(**doc))
        return items
```

### 6.2 Test Repository (`backend/app/repositories/test_repo.py`)

```python
from typing import Optional
from app.models.test import TestModel
from app.repositories.base import BaseRepository


class TestRepository(BaseRepository[TestModel]):
    def __init__(self):
        super().__init__("tests", TestModel)

    async def get_by_external_id(self, external_source: str, external_test_id: str) -> Optional[TestModel]:
        doc = await self.collection.find_one({
            "external_source": external_source,
            "external_test_id": external_test_id
        })
        if doc:
            return self.model_cls(**doc)
        return None

    async def upsert(self, test: TestModel) -> str:
        doc = test.model_dump(by_alias=True, exclude={"id"})
        result = await self.collection.update_one(
            {
                "external_source": test.external_source,
                "external_test_id": test.external_test_id
            },
            {"$set": doc},
            upsert=True
        )
        if result.upserted_id:
            return str(result.upserted_id)
        existing = await self.get_by_external_id(test.external_source, test.external_test_id)
        return str(existing.id) if existing else ""
```

### 6.3 Topic Repository (`backend/app/repositories/topic_repo.py`)

```python
from typing import Optional
from app.models.topic import TopicModel
from app.repositories.base import BaseRepository


class TopicRepository(BaseRepository[TopicModel]):
    def __init__(self):
        super().__init__("topics", TopicModel)

    async def get_by_canonical_key(self, canonical_key: str) -> Optional[TopicModel]:
        doc = await self.collection.find_one({"canonical_key": canonical_key})
        if doc:
            return self.model_cls(**doc)
        return None

    async def upsert_canonical(self, topic: TopicModel) -> str:
        """Upserts a topic by canonical_key. Preserves existing test_count."""
        existing = await self.get_by_canonical_key(topic.canonical_key)
        if existing:
            return str(existing.id)
        doc = topic.model_dump(by_alias=True, exclude={"id"})
        result = await self.collection.insert_one(doc)
        return str(result.inserted_id)

    async def increment_test_count(self, topic_id: str, count: int = 1):
        from bson import ObjectId
        query = {"_id": ObjectId(topic_id) if ObjectId.is_valid(topic_id) else topic_id}
        await self.collection.update_one(query, {"$inc": {"test_count": count}})
```

### 6.4 TestTopic Relationship Repository (`backend/app/repositories/test_topic_repo.py`)

```python
from typing import List
from app.models.relationship import TestTopicModel
from app.repositories.base import BaseRepository


class TestTopicRepository(BaseRepository[TestTopicModel]):
    def __init__(self):
        super().__init__("test_topics", TestTopicModel)

    async def find_by_test_id(self, test_id: str) -> List[TestTopicModel]:
        return await self.find_all({"test_id": test_id}, limit=500)

    async def find_by_topic_id(self, topic_id: str, skip: int = 0, limit: int = 50) -> List[TestTopicModel]:
        return await self.find_all({"topic_id": topic_id}, skip=skip, limit=limit)

    async def replace_for_test(self, test_id: str, relationships: List[TestTopicModel]):
        """Idempotently replaces all topic relations for a test (e.g. after re-parsing)."""
        await self.collection.delete_many({"test_id": test_id})
        if relationships:
            docs = [r.model_dump(by_alias=True, exclude={"id"}) for r in relationships]
            await self.collection.insert_many(docs)
```

### 6.5 Artifact Repository (`backend/app/repositories/artifact_repo.py`)

```python
from typing import Optional
from app.models.artifact import ArtifactKind, ArtifactModel
from app.repositories.base import BaseRepository


class ArtifactRepository(BaseRepository[ArtifactModel]):
    def __init__(self):
        super().__init__("artifacts", ArtifactModel)

    async def get_by_test_and_kind(self, test_id: str, kind: ArtifactKind) -> Optional[ArtifactModel]:
        doc = await self.collection.find_one({"test_id": test_id, "kind": kind.value})
        if doc:
            return self.model_cls(**doc)
        return None

    async def upsert_artifact(self, artifact: ArtifactModel) -> str:
        doc = artifact.model_dump(by_alias=True, exclude={"id"})
        result = await self.collection.update_one(
            {
                "source": artifact.source,
                "stable_object_key": artifact.stable_object_key,
                "kind": artifact.kind.value
            },
            {"$set": doc},
            upsert=True
        )
        if result.upserted_id:
            return str(result.upserted_id)
        existing = await self.collection.find_one({
            "source": artifact.source,
            "stable_object_key": artifact.stable_object_key,
            "kind": artifact.kind.value
        })
        return str(existing["_id"]) if existing else ""
```

---

## Step 7: FastAPI App & Health Endpoints

### 7.1 Health Endpoints (`backend/app/api/v1/health.py`)

Create `backend/app/api/v1/health.py`:

```python
from fastapi import APIRouter, HTTPException, status
from app.db.mongo import get_database

router = APIRouter()


@router.get("/health", summary="Basic health check")
async def health():
    return {"status": "ok", "service": "referme-neet-backend"}


@router.get("/ready", summary="Readiness check for database connectivity")
async def ready():
    try:
        db = get_database()
        await db.command("ping")
        return {"status": "ready", "database": "connected"}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database not reachable: {str(exc)}"
        )
```

### 7.2 FastAPI Main (`backend/app/main.py`)

Create `backend/app/main.py`:

```python
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.health import router as health_router
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
app.include_router(health_router, tags=["Health Root"])  # For top-level /health
```

---

## Step 8: Verification & Automated Test

### 8.1 Create `backend/tests/conftest.py`

```python
import pytest
from mongomock_motor import AsyncMongoMockClient
from app.db import mongo


@pytest.fixture(autouse=True)
def mock_mongo(monkeypatch):
    client = AsyncMongoMockClient()
    db = client["referme_neet_test"]
    monkeypatch.setattr(mongo.db_context, "client", client)
    monkeypatch.setattr(mongo.db_context, "db", db)
    return db
```

### 8.2 Create `backend/tests/test_models_and_repos.py`

```python
import pytest
from app.models.common import ProcessingStatus, Subject
from app.models.relationship import TestTopicModel
from app.models.test import TestModel
from app.models.topic import TopicModel
from app.repositories.test_repo import TestRepository
from app.repositories.test_topic_repo import TestTopicRepository
from app.repositories.topic_repo import TopicRepository
from app.storage.local import LocalArtifactStorage


@pytest.mark.asyncio
async def test_test_repo_upsert():
    repo = TestRepository()
    test = TestModel(
        external_source="allen",
        external_test_id="test_9999",
        name="MINOR TEST 1",
        mode="Offline",
        processing_status=ProcessingStatus.DISCOVERED,
    )
    test_id = await repo.upsert(test)
    assert test_id != ""

    fetched = await repo.get_by_external_id("allen", "test_9999")
    assert fetched is not None
    assert fetched.name == "MINOR TEST 1"


@pytest.mark.asyncio
async def test_topic_and_relationship():
    topic_repo = TopicRepository()
    rel_repo = TestTopicRepository()

    topic = TopicModel(
        subject=Subject.PHYSICS,
        name="Electric Current",
        canonical_key="physics:electric-current",
    )
    topic_id = await topic_repo.upsert_canonical(topic)
    assert topic_id != ""

    rel = TestTopicModel(
        test_id="test_internal_1",
        external_test_id="test_9999",
        topic_id=topic_id,
        canonical_key="physics:electric-current",
        subject=Subject.PHYSICS,
        source_text="Current Electricity - Electric Current",
    )
    await rel_repo.replace_for_test("test_internal_1", [rel])

    results = await rel_repo.find_by_topic_id(topic_id)
    assert len(results) == 1
    assert results[0].canonical_key == "physics:electric-current"


@pytest.mark.asyncio
async def test_local_storage(tmp_path):
    storage = LocalArtifactStorage(base_dir=tmp_path)
    sample_pdf_bytes = b"%PDF-1.4 test sample"
    saved_path = await storage.save("test_9999/syllabus.pdf", sample_pdf_bytes)

    assert await storage.exists(saved_path)
    content = await storage.get(saved_path)
    assert content == sample_pdf_bytes
```

---

## Step 9: Running & Verifying

### Run tests:
```bash
cd /Users/mast/Documents/VInayPrograming/ReferMe/backend
pytest
```
Expected output:
```text
=== 3 passed in 0.xx s ===
```

### Run live server:
```bash
uvicorn app.main:app --reload --port 8000
```

Open in browser / curl:
- `curl http://localhost:8000/health` → `{"status":"ok","service":"referme-neet-backend"}`
- `curl http://localhost:8000/ready` → `{"status":"ready","database":"connected"}`
- Interactive Swagger docs: `http://localhost:8000/docs`

---

## Next Step
Once you have executed these steps and verified `pytest` and `/health`, we will proceed to **Phase 2: PDF Parsing & Topic Processing Engine**.
