import random
import asyncio
from datetime import datetime
from typing import Dict

class MockDataProvider:
    def __init__(self):
        self.market_data = {
            "BTC/USD": {"price": 64000.0, "volatility": 0.02, "trend": "UP"},
            "US100": {"price": 18500.0, "volatility": 0.015, "trend": "NEUTRAL"},
            "SPX500": {"price": 5200.0, "volatility": 0.012, "trend": "NEUTRAL"},
            "XAU/USD": {"price": 2350.0, "volatility": 0.008, "trend": "DOWN"},
            "WTI": {"price": 82.50, "volatility": 0.025, "trend": "UP"},
        }

    async def get_current_price(self, asset: str) -> float:
        """Retorna preço atual simulado com pequeno ruído"""
        if asset not in self.market_data:
            raise ValueError(f"Asset {asset} not found")
        
        base_price = self.market_data[asset]["price"]
        volatility = self.market_data[asset]["volatility"]
        
        # Simula uma variação aleatória de preço
        noise = random.uniform(-volatility, volatility)
        current_price = base_price * (1 + noise)
        
        # Atualiza o preço base ligeiramente
        self.market_data[asset]["price"] = current_price
        
        return round(current_price, 2)

    async def get_atr(self, asset: str, period: int = 14) -> float:
        """Simula um valor de ATR (Average True Range)"""
        if asset not in self.market_data:
            raise ValueError(f"Asset {asset} not found")
            
        base_price = self.market_data[asset]["price"]
        volatility = self.market_data[asset]["volatility"]
        
        # O ATR simulado é proporcional ao preço e volatilidade
        simulated_atr = base_price * volatility * 0.5 
        return round(simulated_atr, 4)

data_provider = MockDataProvider()
