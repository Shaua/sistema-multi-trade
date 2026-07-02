from abc import ABC, abstractmethod

class BaseBroker(ABC):
    @abstractmethod
    async def get_account_balance(self) -> float:
        pass

    @abstractmethod
    async def get_current_price(self, symbol: str) -> float:
        pass

    @abstractmethod
    async def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 50) -> list:
        pass

    @abstractmethod
    async def place_market_order(self, symbol: str, side: str, volume: float) -> dict:
        pass

    @abstractmethod
    async def place_stop_loss(self, symbol: str, side: str, stop_price: float, volume: float) -> dict:
        pass
