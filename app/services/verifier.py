from enum import Enum
import logging
import requests
from fastapi import HTTPException
from app.config import settings
from app.blockchain.evm_client import verify_evm_tx
from app.blockchain.ton_client import verify_ton_tx
from app.db import SessionLocal, Transaction, TxStatus

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
    db = SessionLocal()
    tx = db.query(Transaction).filter_by(idempotency_key=key).first()
    if tx:
        return {'status': tx.status.value, 'tx_hash': payload['tx_hash']}

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

    try:
        if payload['network'] in {NetworkEnum.ETH, NetworkEnum.BSC, NetworkEnum.POLY, NetworkEnum.ARB, NetworkEnum.OPT}:
            ok = verify_evm_tx(
                payload['tx_hash'], payload['sender_wallet'], float(payload['amount']),
                settings.MERCHANT_WALLET_EVM, settings.TX_CONFIRMATIONS
            )
        elif payload['network'] == NetworkEnum.TON:
            ok = verify_ton_tx(
                payload['tx_hash'], payload['sender_wallet'], int(payload['amount']),
                settings.MERCHANT_WALLET_TON
            )
        else:
            raise HTTPException(status_code=400, detail='Unsupported network')
    except Exception as e:
        logger.exception('Verification error')
        tx.status = TxStatus.failed
        db.commit()
        raise

    tx.status = TxStatus.confirmed if ok else TxStatus.failed
    db.commit()

    result = {'status': tx.status.value, 'tx_hash': payload['tx_hash']}
    try:
        requests.post(
            settings.WS_NOTIFY_URL,
            json={'userId': payload['user_id'], 'event': 'payment_result', 'data': result},
            headers={'X-API-KEY': settings.API_KEY},
            timeout=5
        )
    except Exception:
        logger.warning('WS notify failed')

    return result
