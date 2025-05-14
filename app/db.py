from sqlalchemy import create_engine, Column, Integer, String, Float, Enum as SqlEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import enum

from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class TxStatus(enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    failed = "failed"

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    idempotency_key = Column(String, unique=True, index=True)
    user_id = Column(String, index=True)
    tx_hash = Column(String, index=True)
    network = Column(String)
    sender_wallet = Column(String)
    amount = Column(Float)
    status = Column(SqlEnum(TxStatus), default=TxStatus.pending)
    attempts = Column(Integer, default=0)

Base.metadata.create_all(bind=engine)
