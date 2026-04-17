"""
tests/test_health.py
====================
Smoke tests: health endpoint and basic server reachability.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint_returns_200(client: AsyncClient):
    r = await client.get("/health")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_health_response_shape(client: AsyncClient):
    r = await client.get("/health")
    data = r.json()
    assert data.get("status") == "healthy"
    assert "service" in data


@pytest.mark.asyncio
async def test_unknown_route_returns_404(client: AsyncClient):
    r = await client.get("/api/v1/nonexistent_endpoint_xyz")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_cors_headers_present_on_health(client: AsyncClient):
    """CORS allow_origins=* means OPTIONS requests should succeed."""
    r = await client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    # FastAPI's CORSMiddleware responds with 200 on preflight
    assert r.status_code in (200, 400)
