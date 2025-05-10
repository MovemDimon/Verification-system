import requests
import time
from app.config import settings

def verify_ton_tx(tx_hash: str, sender: str, amount: int, merchant: str) -> bool:
    last_lt = 0
    start = time.time()
    attempts = 0
    while time.time() - start < settings.TX_TIMEOUT_SECONDS and attempts < 5:
        attempts += 1
        params = {"account": merchant, "limit": 50, "to_lt": last_lt}
        headers = {"X-API-Key": settings.TON_API_KEY}
        try:
            resp = requests.post(
                f"{settings.TON_API_URL}getTransactions",
                json=params, headers=headers, timeout=10
            )
        except requests.RequestException:
            time.sleep(5)
            continue
        txs = resp.json().get('transactions', [])
        if not txs:
            time.sleep(5)
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
        last_lt = txs[-1]['utime']
    return False
