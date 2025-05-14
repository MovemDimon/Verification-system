import time, asyncio
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.exceptions import TransactionNotFound
from app.config import settings, get_working_rpc, get_ws_url

contract_abi = [
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
]

async def wait_for_transfer_ws(tx_hash: str, sender: str, merchant: str, timeout: int, network: str) -> bool:
    """Subscribe to Transfer events via WebSocket."""
    w3 = Web3(Web3.WebsocketProvider(get_ws_url(network)))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    contract = w3.eth.contract(address=Web3.toChecksumAddress(settings.USDT_CONTRACT_EVM), abi=contract_abi)
    event_filter = contract.events.Transfer.createFilter(
        fromBlock="latest",
        argument_filters={"from": sender, "to": merchant}
    )
    start = time.time()
    while time.time() - start < timeout:
        entries = event_filter.get_new_entries()
        for ev in entries:
            if ev.transactionHash.hex() == tx_hash:
                return True
        await asyncio.sleep(1)
    return False

def verify_evm_tx(tx_hash: str, sender: str, amount_usdt: float, merchant: str, confirmations: int, network: str) -> bool:
    """Atomic verification: first try WS subscription, fallback to HTTP polling."""
    # WS-based first
    try:
        loop = asyncio.new_event_loop()
        return loop.run_until_complete(
            wait_for_transfer_ws(tx_hash, sender, merchant, settings.TX_TIMEOUT_SECONDS, network)
        )
    except Exception:
        pass

    # Fallback to HTTP polling
    w3 = Web3(Web3.HTTPProvider(get_working_rpc(network)))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    contract = w3.eth.contract(address=Web3.toChecksumAddress(settings.USDT_CONTRACT_EVM), abi=contract_abi)
    amount_units = int(amount_usdt * 10**6)
    start = time.time()
    attempts = 0

    while time.time() - start < settings.TX_TIMEOUT_SECONDS and attempts < confirmations:
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
