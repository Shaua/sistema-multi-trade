from .base_broker import BaseBroker
import yfinance as yf

class IBBroker(BaseBroker):
    def __init__(self):
        # A API oficial do Interactive Brokers (TWS API) não é nativamente REST 
        # e requer um gateway local rodando (IB Gateway). 
        # Para Paper Trading gratuito sem configuração de infraestrutura pesada,
        # utilizaremos a simulação lógica puxando os dados de preço real via yfinance.
        pass

    async def get_account_balance(self) -> float:
        return 100000.0

    async def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 50) -> list:
        yf_symbol = symbol
        if symbol == "US100": yf_symbol = "NQ=F"
        elif symbol == "SPX500": yf_symbol = "ES=F"
        elif symbol == "XAU/USD": yf_symbol = "GC=F"
        elif symbol == "WTI": yf_symbol = "CL=F"

        try:
            import asyncio
            ticker = yf.Ticker(yf_symbol)
            yf_tf = timeframe
            if timeframe == "4h":
                yf_tf = "1h"
                limit = limit * 4

            history = await asyncio.to_thread(ticker.history, period="1mo", interval=yf_tf)
            if history.empty:
                return []

            history = history.tail(limit)
            ohlcv = []
            for index, row in history.iterrows():
                ts = int(index.timestamp() * 1000)
                ohlcv.append([
                    ts,
                    float(row['Open']),
                    float(row['High']),
                    float(row['Low']),
                    float(row['Close']),
                    float(row['Volume'])
                ])
            return ohlcv
        except Exception as e:
            print(f"[IB/YFinance] Erro ao buscar OHLCV de {symbol}: {e}")
            return []

    async def get_current_price(self, symbol: str) -> float:
        # Mapeamento do nosso símbolo pro yfinance
        yf_symbol = symbol
        if symbol == "US100": yf_symbol = "NQ=F"
        elif symbol == "SPX500": yf_symbol = "ES=F"
        elif symbol == "XAU/USD": yf_symbol = "GC=F"
        elif symbol == "WTI": yf_symbol = "CL=F"

        try:
            import asyncio
            ticker = yf.Ticker(yf_symbol)
            # Pega o último preço de mercado disponível, usando 5d para garantir que pegue o último fechamento válido mesmo em fins de semana
            history = await asyncio.to_thread(ticker.history, period="5d")
            if not history.empty:
                return float(history['Close'].iloc[-1])
            raise ValueError(f"Sem dados de preço para {symbol}")
        except Exception as e:
            print(f"[IB/YFinance] Erro ao buscar preço de {symbol}: {e}")
            raise # Lança o erro em vez de retornar valor mockado para não bugar o SL/TP

    async def place_market_order(self, symbol: str, side: str, volume: float) -> dict:
        print(f"[IB Paper] Executando ordem SIMULADA {side} a Mercado. Ativo: {symbol}, Lotes: {volume}")
        current_price = await self.get_current_price(symbol)
        return {"status": "FILLED", "order_id": "IB_TEST_123", "avg_price": current_price}

    async def place_stop_loss(self, symbol: str, side: str, stop_price: float, volume: float) -> dict:
        print(f"[IB Paper] Posicionando Stop Loss SIMULADO {side} em {stop_price} para {symbol}")
        return {"status": "NEW", "order_id": "IB_TEST_124"}
