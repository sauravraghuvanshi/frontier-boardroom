import pytest

from app.main import health


@pytest.mark.asyncio
async def test_health_identifies_the_running_build(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_BUILD_SHA", "test-sha")

    assert await health() == {"status": "ok", "build_sha": "test-sha"}
