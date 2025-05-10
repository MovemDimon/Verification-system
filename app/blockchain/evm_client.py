import time
from web3 import Web3
from web3.exceptions import TransactionNotFound
from app.config import settings

w3 = Web3(Web3.HTTPProvider(settings.EVM_RPC_URL))
contract = w3.eth.contract(
    address=Web3.toChecksumAddress(settings.USDT_CONTRACT_EVM),
    abi=[
        {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "name": "from", "type": "address"},
                {"indexed": True, "name": "to", "type": "address"},
                {"indexed": False, "name": "value", "type": "uint256"},
            ],
            "name": "Transfer",
            "type": "event",
        }
    ],
)

def verify_evm_tx(tx_hash: str, sender: str, amount_usdt: float, merchant: str, confirmations: int) -> bool:
    amount_units = int(amount_usdt * 10**6)  # USDT has 6 decimals
    start = time.time()
    attempts = 0
    while time.time() - start < settings.TX_TIMEOUT_SECONDS and attempts < 5:
        attempts += 1
        try:
            receipt = w3.eth.getTransactionReceipt(tx_hash)
        except TransactionNotFound:
            time.sleep(5)
            continue
        if receipt.status != 1:
            return False
        if w3.eth.blockNumber - receipt.blockNumber < confirmations:
            time.sleep(5)
            continue
        for log in receipt.logs:
            try:
                ev = contract.events.Transfer().processLog(log)
                if (
                    ev['args']['from'].lower() == sender.lower() and
                    ev['args']['to'].lower() == merchant.lower() and
                    ev['args']['value'] == amount_units
                ):
                    return True
            except:
                continue
        return False
    return False
