# tests/conftest.py

import os, sys

# 1) مسیر ریشه را اضافه می‌کنیم برای import صحیح
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
)

# 2) تمام ENVهای مورد نیاز را در top-level ست می‌کنیم
DUMMY_ENV = {
    "MERCHANT_WALLET_EVM": "0x" + "0"*40,
    "MERCHANT_WALLET_TON":   "EQ" + "A"*48,
    "EVM_RPC_URL_ETH":       "http://localhost",
    "EVM_RPC_URL_BSC":       "http://localhost",
    "EVM_RPC_URL_POLY":      "http://localhost",
    "EVM_RPC_URL_ARB":       "http://localhost",
    "EVM_RPC_URL_OPT":       "http://localhost",
    "EVM_WS_URL_ETH":        "ws://localhost",
    "EVM_WS_URL_BSC":        "ws://localhost",
    "EVM_WS_URL_POLY":       "ws://localhost",
    "EVM_WS_URL_ARB":        "ws://localhost",
    "EVM_WS_URL_OPT":        "ws://localhost",
    "TON_API_URL":           "http://localhost",
    "TON_API_KEY":           "dummy",
    "USDT_CONTRACT_EVM":     "0x" + "1"*40,
    "WS_NOTIFY_URL":         "http://localhost",
    "TX_CONFIRMATIONS":      "1",
    "TX_TIMEOUT_SECONDS":    "1",
    "API_KEY":               "testkey",
    "DATABASE_URL":          "sqlite:///:memory:",
    "REDIS_URL":             "redis://localhost:6379/0",
    "SECRET_KEY":            "secret",
}

for k, v in DUMMY_ENV.items():
    os.environ.setdefault(k, v)

# 3) حالا که ENV ست شد، می‌توانیم settings را import کنیم
from app.config import settings

import pytest

# 4) fixture برای fake Redis
@pytest.fixture(autouse=True)
def fake_redis(monkeypatch):
    import fakeredis
    fake = fakeredis.FakeStrictRedis()
    monkeypatch.setattr("app.verifier.redis", fake)
    return fake
