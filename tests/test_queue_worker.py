import os
import sys
# اضافه کردن ریشهٔ پروژه به path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

import json
from app.services.verifier import enqueue_verify
from app.db import SessionLocal, Transaction, TxStatus

def test_enqueue_and_db_insert(fake_redis):
    payload = {
        "user_id": "u1",
        "tx_hash": "h"*64,
        "amount": 1.0,
        "network": "Ethereum",
        "sender_wallet": "0x.."
    }
    # enqueue
    enqueue_verify(payload)
    assert fake_redis.llen("tx_queue") == 1
    data = json.loads(fake_redis.lpop("tx_queue"))
    assert data == payload

    # شبیه‌سازی insert اولیه در DB
    db = SessionLocal()
    tx = Transaction(
        idempotency_key=f"{payload['user_id']}_{payload['tx_hash']}",
        user_id=payload['user_id'],
        tx_hash=payload['tx_hash'],
        network=payload['network'],
        sender_wallet=payload['sender_wallet'],
        amount=payload['amount']
    )
    db.add(tx)
    db.commit()

    fetched = db.query(Transaction).filter_by(idempotency_key=tx.idempotency_key).first()
    assert fetched.status == TxStatus.pending
