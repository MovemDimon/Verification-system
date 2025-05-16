from dotenv import load_dotenv
load_dotenv(dotenv_path=".env.test")
from pydantic import BaseSettings, AnyUrl, validator
import re

class Settings(BaseSettings):
    # Merchant wallets
    MERCHANT_WALLET_EVM: str
    MERCHANT_WALLET_TON: str

    # RPC URLs per EVM network (comma-separated)
    EVM_RPC_URL_ETH: str
    EVM_RPC_URL_BSC: str
    EVM_RPC_URL_POLY: str
    EVM_RPC_URL_ARB: str
    EVM_RPC_URL_OPT: str

    # WebSocket URLs per EVM network
    EVM_WS_URL_ETH: AnyUrl
    EVM_WS_URL_BSC: AnyUrl
    EVM_WS_URL_POLY: AnyUrl
    EVM_WS_URL_ARB: AnyUrl
    EVM_WS_URL_OPT: AnyUrl

    # TON
    TON_API_URL: AnyUrl
    TON_API_KEY: str

    # Contracts
    USDT_CONTRACT_EVM: str

    # WebSocket notify
    WS_NOTIFY_URL: AnyUrl

    # Transaction verification
    TX_CONFIRMATIONS: int = 12
    TX_TIMEOUT_SECONDS: int = 300

    # API authentication
    API_KEY: str

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: AnyUrl

    # Security
    SECRET_KEY: str

    class Config:
        env_file = ".env"

    @validator('MERCHANT_WALLET_EVM')
    def validate_evm_address(cls, v):
        if not re.match(r'^0x[a-fA-F0-9]{40}$', v):
            raise ValueError('Invalid EVM address')
        return v

    @validator('MERCHANT_WALLET_TON')
    def validate_ton_address(cls, v):
        if not v.startswith('EQ'):
            raise ValueError('Invalid TON address')
        return v

settings = Settings()

# Helper: split comma lists
def _split(urls: str):
    return [u.strip() for u in urls.split(",") if u.strip()]

RPC_URLS = {
    'Ethereum': _split(settings.EVM_RPC_URL_ETH),
    'BSC':      _split(settings.EVM_RPC_URL_BSC),
    'Polygon':  _split(settings.EVM_RPC_URL_POLY),
    'Arbitrum': _split(settings.EVM_RPC_URL_ARB),
    'Optimism': _split(settings.EVM_RPC_URL_OPT),
}

WS_URLS = {
    'Ethereum': settings.EVM_WS_URL_ETH,
    'BSC':      settings.EVM_WS_URL_BSC,
    'Polygon':  settings.EVM_WS_URL_POLY,
    'Arbitrum': settings.EVM_WS_URL_ARB,
    'Optimism': settings.EVM_WS_URL_OPT,
}

def get_working_rpc(network: str) -> str:
    from web3 import Web3
    for url in RPC_URLS.get(network, []):
        try:
            if Web3(Web3.HTTPProvider(url)).isConnected():
                return url
        except:
            continue
    raise RuntimeError(f"No available RPC for {network}")

def get_ws_url(network: str) -> str:
    ws = WS_URLS.get(network)
    if not ws:
        raise ValueError(f"No WS URL for {network}")
    return ws
