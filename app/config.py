from pydantic import BaseSettings, AnyUrl, validator
import re

class Settings(BaseSettings):
    # Merchant wallets
    MERCHANT_WALLET_EVM: str
    MERCHANT_WALLET_TON: str

    # RPC URLs per EVM network
    EVM_RPC_URL_ETH: AnyUrl
    EVM_RPC_URL_BSC: AnyUrl
    EVM_RPC_URL_POLY: AnyUrl
    EVM_RPC_URL_ARB: AnyUrl
    EVM_RPC_URL_OPT: AnyUrl

    # TON
    TON_API_URL: AnyUrl
    TON_API_KEY: str

    # Contracts
    USDT_CONTRACT_EVM: str

    # WebSocket
    WS_NOTIFY_URL: AnyUrl

    # Transaction verification
    TX_CONFIRMATIONS: int = 12
    TX_TIMEOUT_SECONDS: int = 300

    # API authentication
    API_KEY: str

    # Database
    DATABASE_URL: str

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
