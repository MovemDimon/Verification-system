from enum import Enum
import json, logging, time
import requests, asyncio
from fastapi import HTTPException
from app.config import settings, get_working_rpc
from app.blockchain.evm_client import verify_evm_tx
from app.blockchain.ton_client import verify_ton_tx
from app.db import SessionLocal, Transaction, TxStatus
import aioredis

logger = logging.getLogger(__name__)

class NetworkEnum(str, Enum):
    ETH = 'Ethereum'
    BSC = 'BSC'
    POLY = 'Polygon'
    ARB = 'Arbitrum'
    OPT = 'Optimism'
    TON = 'TON'

redis = aioredis.from_url(settings.REDIS_URL)

async def enqueue_verify(payload: dict):
    """به‌جای اجرای مستقیم، بسته را به صف Redis بفرست."""
    await redis.lpush("tx_queue", json.dumps(payload))

async def get_cached(key: str):
    return await redis.get(key)

async def set_cached(key: str, value: str, ttl: int = 60):
    await redis.set(key, value, ex=ttl)

async def verify(payload: dict) -> dict:
    key = f"{payload['user_id']}_{payload['tx_hash']}"
    # 1) کش: اگر همین الان چک شده
    cached = await get_cached(key)
    if cached:
        return json.loads(cached)

    db = SessionLocal()
    tx = db.query(Transaction).filter_by(idempotency_key=key).first()
    if tx:
        result = {'status': tx.status.value, 'tx_hash': payload['tx_hash']}
        await set_cached(key, json.dumps(result))
        return result

    # 2) ذخیره اولیه
    tx = Transaction(
        idempotency_key=key,
        user_id=payload['user_id'],
        tx_hash=payload['tx_hash'],
        network=payload['network'],
        sender_wallet=payload['sender_wallet'],
        amount=payload['amount'],
        status=TxStatus.pending
    )
    db.add(tx); db.commit()

    # 3) enqueue و برگرداندن pending
    await enqueue_verify(payload)
    return {'status': 'pending', 'tx_hash': payload['tx_hash']}
