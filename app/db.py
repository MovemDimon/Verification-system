# app/db.py
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

client = AsyncIOMotorClient(settings.DATABASE_URL)
db = client.get_default_database()
transactions = db["transactions"]
