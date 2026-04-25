import os
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float,
    Boolean, DateTime, JSON, Text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/roomy.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class InventoryItemDB(Base):
    __tablename__ = "inventory"

    id                  = Column(Integer, primary_key=True, index=True)
    name                = Column(String, nullable=False, index=True)
    brand               = Column(String, nullable=True)           # e.g. Amul, Britannia
    item_type           = Column(String, nullable=True)           # e.g. dairy, produce
    quantity            = Column(Float, nullable=False)
    unit                = Column(String, nullable=False)          # liters, kg, units
    volume_per_unit     = Column(String, nullable=True)           # e.g. "1L", "500ml"
    category            = Column(String, nullable=False)
    agent_owner         = Column(String, nullable=False)
    is_purchasable      = Column(Boolean, default=True)           # False = home-cooked
    container_label     = Column(String, nullable=True)           # "Eric's Dal"
    container_count     = Column(Integer, nullable=True)          # for home-cooked items
    low_stock_threshold = Column(Float, nullable=True)
    reorder_interval_days = Column(Integer, nullable=True)        # routine purchase cadence
    avg_daily_usage     = Column(Float, nullable=True)            # computed from history
    last_updated        = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes               = Column(Text, nullable=True)


class OrderDB(Base):
    __tablename__ = "orders"

    id              = Column(Integer, primary_key=True, index=True)
    platform        = Column(String, nullable=False)
    status          = Column(String, default="pending")
    total_estimated = Column(Float, nullable=True)
    placed_by       = Column(String, default="alfred")
    created_at      = Column(DateTime, default=datetime.utcnow)
    confirmed_at    = Column(DateTime, nullable=True)
    items_json      = Column(JSON, nullable=False)


class AgentEventDB(Base):
    __tablename__ = "agent_events"

    id          = Column(Integer, primary_key=True, index=True)
    agent       = Column(String, nullable=False, index=True)
    event_type  = Column(String, nullable=False)
    payload     = Column(JSON, nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)


class PriceComparisonDB(Base):
    __tablename__ = "price_comparisons"

    id          = Column(Integer, primary_key=True, index=True)
    item_name   = Column(String, nullable=False, index=True)
    platform    = Column(String, nullable=False)
    price       = Column(Float, nullable=False)
    unit        = Column(String, nullable=False)
    fetched_at  = Column(DateTime, default=datetime.utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    print(f"[DB] Initialized at {DATABASE_URL}")
