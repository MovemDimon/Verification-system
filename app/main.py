from fastapi import FastAPI, Header, HTTPException
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel, Field
from app.services.verifier import verify
from app.config import settings

app = FastAPI(openapi_prefix="/api/v1")
api_key_header = APIKeyHeader(name='X-API-KEY')

class TransactionPayload(BaseModel):
    user_id: str = Field(..., example="12345")
    currency: str = Field(..., example="USDT")
    network: str = Field(..., example="Ethereum")
    amount: float = Field(..., example=5.0)
    merchant_wallet: str
    sender_wallet: str
    tx_hash: str

@app.post('/transaction')
async def verify_transaction(
    payload: TransactionPayload,
    api_key: str = Header(...)
):
    if api_key != settings.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return await verify(payload.dict())
