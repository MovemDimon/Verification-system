from pydantic import BaseSettings, AnyUrl, validator
import re

class Settings(BaseSettings):
    # Merchant wallets
    MERCHANT_WALLET_EVM: str
    MERCHANT_WALLET_TON: str

    # RPC / API endpoints
    EVM_RPC_URL: AnyUrl
    TON_API_URL: AnyUrl
    TON_API_KEY: str

    # Contract addresses
    USDT_CONTRACT_EVM: str

    # WebSocket notification
    WS_NOTIFY_URL: AnyUrl

    # Transaction verification params
    TX_CONFIRMATIONS: int = 12
    TX_TIMEOUT_SECONDS: int = 300

    # HTTP API auth
    API_KEY: str

    # Database URL
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
