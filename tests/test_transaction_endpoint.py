import os
import sys
# اضافه کردن ریشه پروژه به path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_verify_endpoint_pending_and_idempotent():
    payload = {
        "user_id": "user1",
        "currency": "USDT",
        "network": "Ethereum",
        "amount": 1.0,
        "merchant_wallet": "0x" + "0"*40,
        "sender_wallet": "0x" + "1"*40,
        "tx_hash": "a"*64
    }
    # بار اول => pending
    r1 = client.post("/api/v1/transaction",
                     json=payload,
                     headers={"api-key": "testkey"})

    print(">>>", r1.status_code, r1.json()) 

    assert r1.status_code == 200
    assert r1.json()["status"] == "pending"

    # بار دوم => idempotent
    r2 = client.post("/api/v1/transaction",
                     json=payload,
                     headers={"api-key": "testkey"})
    assert r2.status_code == 200
    assert r2.json()["status"] in ("pending", "confirmed", "failed")
