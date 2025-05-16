import os
import sys
import json
import pytest

# اضافه کردن ریشهٔ پروژه به path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

from app.services.verifier import enqueue_verify
from app.db import SessionLocal, Transaction, TxStatus

@pytest.mark.asyncio
async def test_enqueue_and_db_insert(fake_redis):
    payload = {
        "user_id": "u1",
        "tx_hash": "h"*64,
        "amount": 1.0,
        "network": "Ethereum",
        "sender_wallet": "0x.."
    }

    # enqueue در صف Redis
    await enqueue_verify(payload)

    # بررسی اینکه صف 1 آیتم دارد
    length = await fake_redis.llen("tx_queue")
    assert length == 1

    # خواندن و بررسی محتوا
    raw_data = await fake_redis.lpop("tx_queue")
    data = json.loads(raw_data)
    assert data == payload

    # شبیه‌سازی insert اولیه در DB
    db = SessionLocal()
    try:
        tx = Transaction(
            idempotency_key=f"{payload['user_id']}_{payload['tx_hash']}",
            user_id=payload['user_id'],
            tx_hash=payload['tx_hash'],
            network=payload['network'],
            sender_wallet=payload['sender_wallet'],
            amount=payload['amount'],
            status=TxStatus.pending
        )
        db.add(tx)
        db.commit()

        fetched = db.query(Transaction).filter_by(idempotency_key=tx.idempotency_key).first()
        assert fetched.status == TxStatus.pending
    finally:
        db.close()
