import yfinance as yf
import asyncio
from .base_broker import BaseBroker
import pandas as pd
import math

class YFinanceBroker(BaseBroker):
    def __init__(self):
        # Mapeamento de ativos internos para símbolos do Yahoo Finance
        self.symbol_map = {
            "SPX500": "^GSPC",
            "US100": "^NDX",
            "XAU/USD": "GC=F",
            "WTI": "CL=F",
            "BTC/USD": "BTC-USD",
            "ETH/USD": "ETH-USD",
            "SOL/USD": "SOL-USD"
        }

    def _get_yf_symbol(self, symbol: str) -> str:
        return self.symbol_map.get(symbol, symbol)

    async def get_current_price(self, symbol: str) -> float:
        """Busca o preço atual de mercado no Yahoo Finance de forma assíncrona (thread)."""
        yf_symbol = self._get_yf_symbol(symbol)
        
        def fetch():
            ticker = yf.Ticker(yf_symbol)
            # Tenta pegar dados intradiários recentes
            data = ticker.history(period="1d", interval="1m")
            if not data.empty:
                return float(data['Close'].iloc[-1])
            # Fallback se mercado fechado / sem dados de 1m
            data = ticker.history(period="5d")
            if not data.empty:
                return float(data['Close'].iloc[-1])
            return 0.0

        try:
            # Roda num thread para não bloquear o event loop do asyncio
            price = await asyncio.to_thread(fetch)
            if math.isnan(price) or price <= 0:
                print(f"[YFinance] Aviso: Preço inválido para {symbol} ({yf_symbol})")
                return 0.0
            return price
        except Exception as e:
            print(f"[YFinance] Erro ao buscar preço de {symbol}: {e}")
            return 0.0

    async def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 60) -> list:
        """
        Busca candles históricos.
        Retorno padrão esperado pelo bot: [[timestamp, open, high, low, close, volume], ...]
        """
        yf_symbol = self._get_yf_symbol(symbol)
        
        # Mapeamento do timeframe do bot para o Yahoo Finance
        # yfinance suporta: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
        tf_map = {
            "1m": "1m",
            "5m": "5m",
            "15m": "15m",
            "1h": "1h",
            "4h": "1h", # Fallback pois yf nao tem 4h exato sem resampling manual
            "1d": "1d"
        }
        yf_tf = tf_map.get(timeframe, "15m")

        # Periodo dinâmico baseado no limite pedido para economizar tempo
        period = "5d"
        if yf_tf == "1m": period = "5d"
        elif yf_tf in ["5m", "15m", "30m"]: period = "1mo"
        elif yf_tf in ["1h", "60m"]: period = "1mo"
        else: period = "1y"

        def fetch():
            ticker = yf.Ticker(yf_symbol)
            data = ticker.history(period=period, interval=yf_tf)
            if data.empty:
                return []
            
            # Formatar no padrão do bot
            ohlcv_list = []
            # yfinance index é datetime
            for index, row in data.tail(limit).iterrows():
                # Converter index para timestamp unix milissegundos
                ts = int(index.timestamp() * 1000)
                ohlcv_list.append([
                    ts,
                    float(row['Open']),
                    float(row['High']),
                    float(row['Low']),
                    float(row['Close']),
                    float(row['Volume'])
                ])
            return ohlcv_list

        try:
            return await asyncio.to_thread(fetch)
        except Exception as e:
            print(f"[YFinance] Erro ao buscar OHLCV de {symbol}: {e}")
            return []

    # ── MÉTODOS DE EXECUÇÃO (MOCKADOS POIS O YFINANCE NÃO OPERA) ───

    async def place_market_order(self, symbol: str, side: str, volume: float) -> dict:
        print(f"[Yahoo Finance Mock] Executando ordem {side} a Mercado. Ativo: {symbol}, Lotes: {volume}")
        current_price = await self.get_current_price(symbol)
        return {"status": "FILLED", "order_id": "YF_MOCK_123", "avg_price": current_price}

    async def place_stop_loss(self, symbol: str, side: str, stop_price: float, volume: float) -> dict:
        print(f"[Yahoo Finance Mock] Posicionando Stop Loss {side} em {stop_price} para {symbol}")
        return {"status": "NEW", "order_id": "YF_MOCK_SL"}
