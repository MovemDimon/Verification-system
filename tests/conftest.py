import pytest
from app.config import settings

@pytest.fixture(autouse=True)
def dummy_api_key(monkeypatch):
    monkeypatch.setattr(settings, "API_KEY", "testkey")
    yield

@pytest.fixture(autouse=True)
def fake_redis(monkeypatch):
    import fakeredis
    fake = fakeredis.FakeStrictRedis()
    monkeypatch.setattr("app.verifier.redis", fake)
    yield fake
