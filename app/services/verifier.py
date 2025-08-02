import logging
import traceback
from enum import Enum

from app.config import settings
from app.db import transactions

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
    try:
        existing = await transactions.find_one({"idempotency_key": key})
        if existing and existing.get("status") != "pending":
            return {"status": existing["status"], "tx_hash": payload["tx_hash"]}

        if not existing:
            await transactions.insert_one({
                "idempotency_key": key,
                "user_id": payload["user_id"],
                "tx_hash": payload["tx_hash"],
                "network": payload["network"],
                "sender_wallet": payload["sender_wallet"],
                "amount": payload["amount"],
                "status": "pending",
                "attempts": 0
            })

        success = False
        try:
            if payload["network"] == "TON":
                from app.blockchain.ton_client import verify_ton_tx_async  # Lazy import
                success = await verify_ton_tx_async(
                    tx_hash=payload["tx_hash"],
                    sender=payload["sender_wallet"],
                    amount=int(payload["amount"]),
                    merchant=settings.MERCHANT_WALLET_TON
                )
            else:
                from app.blockchain.evm_client import verify_evm_tx_async  # Lazy import
                success = await verify_evm_tx_async(
                    tx_hash=payload["tx_hash"],
                    sender=payload["sender_wallet"],
                    amount_usdt=payload["amount"],
                    merchant=settings.MERCHANT_WALLET_EVM,
                    confirmations=settings.TX_CONFIRMATIONS,
                    network=payload["network"]
                )
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"❌ Unhandled exception during transaction verification:\n{tb}")
            success = False

        status = "confirmed" if success else "failed"
        await transactions.update_one(
            {"idempotency_key": key},
            {"$set": {"status": status}}
        )
        return {"status": status, "tx_hash": payload["tx_hash"]}

    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"🔥 Critical error in verify():\n{tb}")
        raise  # بفرست بالا برای لاگ‌گیری بهتر در FastAPI هم
