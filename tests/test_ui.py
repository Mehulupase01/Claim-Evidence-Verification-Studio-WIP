import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_reviewer_workspace_and_assets_are_served() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        page = await client.get("/")
        styles = await client.get("/assets/styles.css")
        script = await client.get("/assets/app.js")
        sample = await client.get("/samples/sample_report.txt")

    assert page.status_code == 200
    assert "Check a claim against its source" in page.text
    assert 'id="review-form"' in page.text
    assert "Content-Security-Policy" in page.headers
    assert styles.status_code == 200
    assert "--navy" in styles.text
    assert script.status_code == 200
    assert "textContent = evidence.text" in script.text
    assert sample.status_code == 200
    assert "revenue 27 percent" in sample.text
