import ccxt.async_support as ccxt
import os
from .base_broker import BaseBroker

class BybitBroker(BaseBroker):
    def __init__(self):
        # Em produção, pegar de os.environ
        api_key = os.environ.get('BYBIT_API_KEY', '')
        api_secret = os.environ.get('BYBIT_API_SECRET', '')
        
        self.client = ccxt.bybit({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'linear', # Contratos derivativos USDT (linear)
            }
        })
        
        # Modo Paper Trading (Testnet) Ativado!
        self.client.set_sandbox_mode(True)

    async def get_account_balance(self) -> float:
        try:
            if not self.client.apiKey:
                return 100000.0 # Mock fallback se nao tiver chave
                
            balance = await self.client.fetch_balance()
            # Retornar o saldo livre de USDT para contratos lineares
            usdt_balance = balance.get('USDT', {}).get('free', 100000.0)
            return float(usdt_balance)
        except Exception as e:
            print(f"[Bybit] Erro ao buscar saldo: {e}")
            return 100000.0 # Mock fallback

    async def get_current_price(self, symbol: str) -> float:
        try:
            # Formatar symbol para Bybit (ex: BTC/USD -> BTC/USDT:USDT)
            bybit_sym = symbol.replace("USD", "USDT") + ":USDT" if "USD" in symbol else symbol
            
            ticker = await self.client.fetch_ticker(bybit_sym)
            return float(ticker['last'])
        except Exception as e:
            print(f"[Bybit] Erro ao buscar preço de {symbol}: {e}")
            return 65000.0 # Mock fallback

    async def place_market_order(self, symbol: str, side: str, volume: float) -> dict:
        print(f"[Bybit Testnet] Executando ordem {side} a Mercado. Ativo: {symbol}, Volume: {volume}")
        bybit_sym = symbol.replace("USD", "USDT") + ":USDT" if "USD" in symbol else symbol
        
        if not self.client.apiKey:
            # Fallback se nao tiver chaves
            return {"status": "FILLED", "order_id": "BYBIT_MOCK_123", "avg_price": await self.get_current_price(symbol)}
            
        try:
            ccxt_side = 'buy' if side.upper() == 'BUY' else 'sell'
            order = await self.client.create_market_order(bybit_sym, ccxt_side, volume)
            
            return {
                "status": "FILLED", 
                "order_id": order.get('id', 'N/A'),
                "avg_price": float(order.get('average', order.get('price', await self.get_current_price(symbol))))
            }
        except Exception as e:
            print(f"[Bybit Testnet] Erro ao enviar ordem de mercado: {e}")
            return {"status": "ERROR", "order_id": "N/A", "avg_price": 0.0}

    async def place_stop_loss(self, symbol: str, side: str, stop_price: float, volume: float) -> dict:
        print(f"[Bybit Testnet] Posicionando Stop Loss {side} em {stop_price} para {symbol}")
        bybit_sym = symbol.replace("USD", "USDT") + ":USDT" if "USD" in symbol else symbol
        
        if not self.client.apiKey:
            return {"status": "NEW", "order_id": "BYBIT_MOCK_124"}
            
        try:
            ccxt_side = 'buy' if side.upper() == 'BUY' else 'sell'
            # Simples stop order em ccxt
            order = await self.client.create_order(bybit_sym, 'stop', ccxt_side, volume, stop_price, {'stopPrice': stop_price})
            
            return {
                "status": "NEW", 
                "order_id": order.get('id', 'N/A')
            }
        except Exception as e:
            print(f"[Bybit Testnet] Erro ao enviar stop loss: {e}")
            return {"status": "ERROR", "order_id": "N/A"}
