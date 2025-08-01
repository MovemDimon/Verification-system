import json, logging
from app.config import settings
from app.db import transactions
from enum import Enum

from app.blockchain.evm_client import verify_evm_tx
from app.blockchain.ton_client import verify_ton_tx

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

    # چک کن ببینی قبلاً بررسی شده یا نه
    existing_tx = await transactions.find_one({"idempotency_key": key})
    if existing_tx and existing_tx.get("status") != "pending":
        return {"status": existing_tx["status"], "tx_hash": payload["tx_hash"]}

    # اگر نبود، تراکنش جدید رو ذخیره کن
    if not existing_tx:
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

    # تأیید مستقیم تراکنش
    success = False
    try:
        if payload["network"] == "TON":
            success = verify_ton_tx(
                tx_hash=payload["tx_hash"],
                sender=payload["sender_wallet"],
                amount=int(payload["amount"]),  # ⚠️ مقدار به ton بر حسب nano
                merchant=settings.MERCHANT_WALLET_TON
            )
        else:
            success = verify_evm_tx(
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
