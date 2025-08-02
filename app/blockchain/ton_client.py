# app/blockchain/ton_client.py
import asyncio
import httpx
from app.config import settings

async def verify_ton_tx_async(tx_hash: str, sender: str, amount: int, merchant: str) -> bool:
    last_lt = 0
    start = asyncio.get_event_loop().time()
    attempts = 0

    async with httpx.AsyncClient(timeout=10) as client:
        while asyncio.get_event_loop().time() - start < settings.TX_TIMEOUT_SECONDS and attempts < 5:
            attempts += 1

            params = {
                "account": merchant,
                "limit": 50,
                "to_lt": last_lt
            }

            headers = {
                "X-API-Key": settings.TON_API_KEY
            }

            try:
                resp = await client.get(
                    f"{settings.TON_API_URL}getTransactions",
                    params=params,
                    headers=headers
                )
            except httpx.RequestError:
                await asyncio.sleep(5)
                continue

            data = resp.json()
            txs = data.get('transactions', [])
            if not txs:
                await asyncio.sleep(5)
                continue

            for tx in txs:
                if tx.get('id') == tx_hash and tx.get('in_msg'):
                    msg = tx['in_msg']
                    if (
                        msg.get('source') == sender and
                        int(msg.get('value', 0)) == amount and
                        msg.get('destination') == merchant
                    ):
                        return True

            last_lt = txs[-1].get('utime', last_lt)

    return False
