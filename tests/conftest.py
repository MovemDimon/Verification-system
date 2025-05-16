# tests/conftest.py

import os, sys
import pytest
from app.db import Base, engine

@pytest.fixture(scope="session", autouse=True)
def create_test_db():
    Base.metadata.create_all(bind=engine)

# مسیر ریشه را اضافه می‌کنیم
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

# ست کردن ENV‌ها
DUMMY_ENV = {
    "MERCHANT_WALLET_EVM": "0x" + "0"*40,
    "MERCHANT_WALLET_TON": "EQ" + "A"*48,
    "EVM_RPC_URL_ETH": "http://localhost",
    "EVM_RPC_URL_BSC": "http://localhost",
    "EVM_RPC_URL_POLY": "http://localhost",
    "EVM_RPC_URL_ARB": "http://localhost",
    "EVM_RPC_URL_OPT": "http://localhost",
    "EVM_WS_URL_ETH": "ws://localhost",
    "EVM_WS_URL_BSC": "ws://localhost",
    "EVM_WS_URL_POLY": "ws://localhost",
    "EVM_WS_URL_ARB": "ws://localhost",
    "EVM_WS_URL_OPT": "ws://localhost",
    "TON_API_URL": "http://localhost",
    "TON_API_KEY": "dummy",
    "USDT_CONTRACT_EVM": "0x" + "1"*40,
    "WS_NOTIFY_URL": "http://localhost",
    "TX_CONFIRMATIONS": "1",
    "TX_TIMEOUT_SECONDS": "1",
    "API_KEY": "testkey",
    "DATABASE_URL": "sqlite:///:memory:",
    "REDIS_URL": "redis://localhost:6379/0",
    "SECRET_KEY": "secret",
}

for k, v in DUMMY_ENV.items():
    os.environ.setdefault(k, v)

from app.config import settings
import pytest

# اصلاح شده: monkeypatch کردن get_redis به جای redis
@pytest.fixture(autouse=True)
def fake_redis(monkeypatch):
    import fakeredis.aioredis
    fake = fakeredis.aioredis.FakeRedis()

    import app.services.verifier as verifier
    monkeypatch.setattr(verifier, "get_redis", lambda: fake)
    return fake
