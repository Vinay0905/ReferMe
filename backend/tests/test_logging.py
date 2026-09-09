import pytest
from httpx import ASGITransport, AsyncClient
from app.core.logging_config import APP_LOG_PATH, ERRORS_LOG_PATH
from app.main import app


@pytest.mark.asyncio
async def test_request_id_and_response_time_headers():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        assert "x-request-id" in resp.headers
        assert resp.headers["x-request-id"].startswith("req:")
        assert "x-response-time" in resp.headers
        assert resp.headers["x-response-time"].endswith("ms")


@pytest.mark.asyncio
async def test_client_telemetry_beacon():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "level": "ERROR",
            "message": "Test UI component failed to render diagram",
            "url": "http://localhost:3000/topics/morphology",
            "component": "TopicDetailStudio",
            "stack": "Error: mock stack trace at render",
        }
        resp = await client.post("/api/v1/logs/client", json=payload)
        assert resp.status_code == 202
        assert resp.json() == {"status": "recorded"}

        # Verify it was logged into app.log and errors.log
        assert APP_LOG_PATH.exists()
        assert ERRORS_LOG_PATH.exists()

        error_content = ERRORS_LOG_PATH.read_text(encoding="utf-8")
        assert "Test UI component failed to render diagram" in error_content
        assert "TopicDetailStudio" in error_content


@pytest.mark.asyncio
async def test_get_recent_logs_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/logs/recent?lines=20&stream=app")
        assert resp.status_code == 200
        data = resp.json()
        assert "lines" in data
        assert "count" in data
        assert data["file"] == "app.log"
        assert isinstance(data["lines"], list)

        resp_err = await client.get("/api/v1/logs/recent?lines=20&stream=errors")
        assert resp_err.status_code == 200
        data_err = resp_err.json()
        assert data_err["file"] == "errors.log"
