import logging
import traceback
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from app.services.verifier import verify
from app.config import settings

# Configure logging to show errors and tracebacks
logging.basicConfig(level=logging.ERROR)

# Initialize FastAPI with debug mode
app = FastAPI(debug=True)

# Enable CORS to allow preflight requests and cross-origin access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # Or restrict to specific domains
    allow_methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
    allow_headers=["*"],            # Or specify ['api-key', 'Content-Type']
)

class TransactionPayload(BaseModel):
    user_id: str = Field(..., example="12345")
    currency: str = Field(..., example="USDT")
    network: str = Field(..., example="Ethereum")
    amount: float = Field(..., example=5.0)
    merchant_wallet: str
    sender_wallet: str
    tx_hash: str

@app.post('/api/v1/transaction')
async def verify_transaction(
    payload: TransactionPayload,
    api_key: str = Header(..., alias="api-key")
):
    try:
        # Validate API Key
        if api_key != settings.API_KEY:
            raise HTTPException(status_code=403, detail="Invalid API Key")
        # Perform verification
        return await verify(payload.dict())

    except HTTPException:
        # Re-raise HTTP exceptions (e.g., invalid API key)
        raise
    except Exception as e:
        # Log full traceback for debugging
        logging.error("Unhandled exception during transaction verification:\n%s", traceback.format_exc())
        # Return generic internal error
        raise HTTPException(status_code=500, detail="Internal Server Error")
