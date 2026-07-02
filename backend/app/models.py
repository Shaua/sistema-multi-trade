from sqlalchemy import Column, Integer, BigInteger, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from .database import Base

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    balance = Column(Float, default=100000.0)
    equity = Column(Float, default=100000.0)
    max_drawdown = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)

class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    asset = Column(String, index=True) # e.g., 'BTC/USD', 'US100'
    strategy = Column(String)
    direction = Column(String) # 'LONG' or 'SHORT'
    entry_price = Column(Float)
    highest_price = Column(Float, nullable=True) # Used for trailing stop tracking
    exit_price = Column(Float, nullable=True)
    stop_loss = Column(Float)
    take_profit = Column(Float, nullable=True)
    volume = Column(Float) # Position sizing
    status = Column(String, default="OPEN") # 'OPEN', 'CLOSED'
    pnl = Column(Float, nullable=True)
    reason = Column(String, nullable=True) # IA explanation
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)

class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    asset = Column(String, index=True)
    strategy = Column(String)
    direction = Column(String)
    price = Column(Float)
    ai_confidence = Column(Float, nullable=True)
    ai_reasoning = Column(String, nullable=True)
    is_executed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CandleData(Base):
    __tablename__ = "candle_data"

    id = Column(Integer, primary_key=True, index=True)
    asset = Column(String, index=True)
    timeframe = Column(String)
    timestamp = Column(BigInteger, index=True)  # Unix ms
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    
class SystemSettings(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    max_risk_per_trade = Column(Float, default=0.01)
    trailing_stop_activation = Column(Float, default=1.015)
    trailing_stop_distance = Column(Float, default=0.015)
    ai_confidence_threshold = Column(Float, default=0.5)
    active_assets = Column(String, default="BTC/USDT,ETH/USDT,SOL/USDT,US100,SPX500,XAU/USD")
    strategy_sensitivity = Column(Float, default=0.01)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
