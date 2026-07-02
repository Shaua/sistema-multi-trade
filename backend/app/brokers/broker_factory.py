from .binance_broker import BinanceBroker
from .ib_broker import IBBroker

class BrokerFactory:
    def __init__(self):
        self._binance = BinanceBroker()
        self._ib = IBBroker()

    def get_broker(self, asset: str):
        """Retorna o corretor apropriado com base no ativo."""
        if "BTC" in asset or "ETH" in asset or "USDT" in asset:
            return self._binance
        else:
            # Índices e Commodities
            return self._ib

broker_factory = BrokerFactory()
