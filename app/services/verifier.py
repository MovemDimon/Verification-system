import json, logging
from fastapi import HTTPException
from app.config import settings
from app.db import SessionLocal, Transaction, TxStatus
import aioredis
from enum import Enum
import asyncio

from app.blockchain.evm_client import verify_evm_tx
from app.blockchain.ton_client import verify_ton_tx

logger = logging.getLogger(__name__)

# تابع تولید Redis – برای تست قابل override است
def get_redis():
    return aioredis.from_url(settings.REDIS_URL)

class NetworkEnum(str, Enum):
    ETH = 'Ethereum'
    BSC = 'BSC'
    POLY = 'Polygon'
    ARB = 'Arbitrum'
    OPT = 'Optimism'
    TON = 'TON'

async def enqueue_verify(payload: dict):
    redis = get_redis()
    await redis.lpush("tx_queue", json.dumps(payload))

async def get_cached(key: str):
    redis = get_redis()
    return await redis.get(key)

async def set_cached(key: str, value: str, ttl: int = 60):
    redis = get_redis()
    await redis.set(key, value, ex=ttl)

async def verify(payload: dict) -> dict:
    key = f"{payload['user_id']}_{payload['tx_hash']}"
    cached = await get_cached(key)
    if cached:
        return json.loads(cached)

    db = SessionLocal()
    try:
        tx = db.query(Transaction).filter_by(idempotency_key=key).first()
        if tx:
            result = {'status': tx.status.value, 'tx_hash': payload['tx_hash']}
            await set_cached(key, json.dumps(result))
            return result

        tx = Transaction(
            idempotency_key=key,
            user_id=payload['user_id'],
            tx_hash=payload['tx_hash'],
            network=payload['network'],
            sender_wallet=payload['sender_wallet'],
            amount=payload['amount'],
            status=TxStatus.pending
        )
        db.add(tx)
        db.commit()

        await enqueue_verify(payload)
        return {'status': 'pending', 'tx_hash': payload['tx_hash']}
    finally:
        db.close()
