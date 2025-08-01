# app/services/verifier.py
import logging
from app.config import settings
from app.db import transactions
from enum import Enum
from app.blockchain.evm_client import verify_evm_tx_async
from app.blockchain.ton_client import verify_ton_tx_async

logger = logging.getLogger(__name__)

class NetworkEnum(str, Enum):
    ETH = 'Ethereum'
    BSC = 'BSC'
    POLY = 'Polygon'
    ARB = 'Arbitrum'
    OPT = 'Optimism'
    TON = 'TON'

async def verify(payload: dict) -> dict:
    key = f"{payload['user_id']}_{payload['tx_hash']}"

    existing = await transactions.find_one({"idempotency_key": key})
    if existing and existing.get("status") != "pending":
        return {"status": existing["status"], "tx_hash": payload["tx_hash"]}

    if not existing:
        tx_data = {
            "idempotency_key": key,
            "user_id": payload["user_id"],
            "tx_hash": payload["tx_hash"],
            "network": payload["network"],
            "sender_wallet": payload["sender_wallet"],
            "amount": payload["amount"],
            "status": "pending",
            "attempts": 0
        }
        await transactions.insert_one(tx_data)

    success = False
    try:
        if payload["network"] == "TON":
            success = await verify_ton_tx_async(
                tx_hash=payload["tx_hash"],
                sender=payload["sender_wallet"],
                amount=int(payload["amount"]),
                merchant=settings.MERCHANT_WALLET_TON
            )
        else:
            success = await verify_evm_tx_async(
                tx_hash=payload["tx_hash"],
                sender=payload["sender_wallet"],
                amount_usdt=payload["amount"],
                merchant=settings.MERCHANT_WALLET_EVM,
                confirmations=settings.TX_CONFIRMATIONS,
                network=payload["network"]
            )
    except Exception as e:
        logger.error(f"❌ Error during verification: {e}")
        success = False

    status = "confirmed" if success else "failed"
    await transactions.update_one(
        {"idempotency_key": key},
        {"$set": {"status": status}}
    )

    return {"status": status, "tx_hash": payload["tx_hash"]}
