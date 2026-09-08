import pytest
from mongomock_motor import AsyncMongoMockClient
from app.db import mongo


@pytest.fixture(autouse=True)
def mock_mongo(monkeypatch):
    """Sets up an in-memory Mongo mock client for fast, isolated testing without Atlas credentials."""
    client = AsyncMongoMockClient()
    db = client["referme_neet_test"]
    monkeypatch.setattr(mongo.db_context, "client", client)
    monkeypatch.setattr(mongo.db_context, "db", db)
    return db
