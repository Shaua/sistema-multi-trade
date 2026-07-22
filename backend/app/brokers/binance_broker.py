import os
import time
import hmac
import hashlib
import aiohttp
from .base_broker import BaseBroker

_DEMO_BASE = 'https://demo-fapi.binance.com'


def _sign(secret: str, query_string: str) -> str:
    return hmac.new(
        secret.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


class BinanceBroker(BaseBroker):
    """
    Broker para Binance Demo Trading (Futuros USD-M).
    Usa aiohttp diretamente para evitar problemas do ccxt com endpoints sapi
    que nao existem no ambiente Demo (demo-fapi.binance.com).
    """

    def __init__(self):
        super().__init__()
        self._session: aiohttp.ClientSession | None = None
        self._symbol_precisions: dict[str, int] = {}

    @property
    def _api_key(self):
        return os.environ.get('BINANCE_API_KEY', '')

    @property
    def _api_secret(self):
        return os.environ.get('BINANCE_API_SECRET', '')

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _public_get(self, path: str, params: dict | None = None) -> dict | list:
        session = await self._get_session()
        url = f'{_DEMO_BASE}{path}'
        async with session.get(url, params=params or {}) as resp:
            return await resp.json()

    async def _private_get(self, path: str, params: dict | None = None) -> dict | list:
        session = await self._get_session()
        ts = int(time.time() * 1000)
        p = dict(params or {})
        p['timestamp'] = ts
        qs = '&'.join(f'{k}={v}' for k, v in p.items())
        p['signature'] = _sign(self._api_secret, qs)
        headers = {'X-MBX-APIKEY': self._api_key}
        url = f'{_DEMO_BASE}{path}'
        async with session.get(url, params=p, headers=headers) as resp:
            return await resp.json()

    async def _private_post(self, path: str, params: dict | None = None) -> dict | list:
        session = await self._get_session()
        ts = int(time.time() * 1000)
        p = dict(params or {})
        p['timestamp'] = ts
        qs = '&'.join(f'{k}={v}' for k, v in p.items())
        p['signature'] = _sign(self._api_secret, qs)
        headers = {'X-MBX-APIKEY': self._api_key}
        url = f'{_DEMO_BASE}{path}'
        async with session.post(url, params=p, headers=headers) as resp:
            return await resp.json()

    async def _private_delete(self, path: str, params: dict | None = None) -> dict | list:
        session = await self._get_session()
        ts = int(time.time() * 1000)
        p = dict(params or {})
        p['timestamp'] = ts
        qs = '&'.join(f'{k}={v}' for k, v in p.items())
        p['signature'] = _sign(self._api_secret, qs)
        headers = {'X-MBX-APIKEY': self._api_key}
        url = f'{_DEMO_BASE}{path}'
        async with session.delete(url, params=p, headers=headers) as resp:
            return await resp.json()

    # ── Interface publica ────────────────────────────────────────────────

    async def get_account_balance(self) -> float:
        try:
            if not self._api_key:
                return 100000.0

            data = await self._private_get('/fapi/v2/balance')
            for asset in data:
                if asset.get('asset') == 'USDT':
                    return float(asset.get('availableBalance', 100000.0))
            return 100000.0
        except Exception as e:
            print(f"[Binance Demo] Erro ao buscar saldo: {e}")
            return 100000.0

    async def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 50) -> list:
        try:
            sym = symbol.replace("/", "")
            if sym.endswith("USD"):
                sym = sym + "T"
            data = await self._public_get('/fapi/v1/klines', {
                'symbol': sym,
                'interval': timeframe,
                'limit': limit,
            })
            if isinstance(data, dict) and 'code' in data:
                return [] # Ignora erro de símbolo inválido
            
            # Binance klines: [ts, open, high, low, close, vol, ...]
            return [
                [int(k[0]), float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])]
                for k in data
            ]
        except Exception as e:
            print(f"[Binance Demo] Erro ao buscar OHLCV de {symbol}: {e}")
            return []

    async def get_current_price(self, symbol: str) -> float:
        try:
            sym = symbol.replace("/", "")
            if sym.endswith("USD"):
                sym = sym + "T"
            data = await self._public_get('/fapi/v1/ticker/price', {'symbol': sym})
            if isinstance(data, dict):
                if 'code' in data or 'price' not in data:
                    return 0.0
                return float(data['price'])
            # Se for lista ou string ou algo inesperado
            return 0.0
        except Exception as e:
            print(f"[Binance Demo] Erro ao buscar preco de {symbol}: {e}")
            return 0.0

    async def _load_exchange_info(self):
        try:
            data = await self._public_get('/fapi/v1/exchangeInfo')
            if isinstance(data, dict) and 'symbols' in data:
                for s in data['symbols']:
                    self._symbol_precisions[s['symbol']] = s.get('quantityPrecision', 2)
        except Exception as e:
            print(f"[Binance Demo] Erro ao buscar exchangeInfo: {e}")

    async def place_market_order(self, symbol: str, side: str, volume: float) -> dict:
        print(f"[Binance Demo] Ordem {side} a Mercado | {symbol} | Vol: {volume}")
        sym = symbol.replace("/", "")
        if sym.endswith("USD"):
            sym = sym + "T"

        if not self._api_key:
            return {"status": "FILLED", "order_id": "DEMO_MOCK_123", "avg_price": await self.get_current_price(symbol)}

        if not self._symbol_precisions:
            await self._load_exchange_info()

        precision = self._symbol_precisions.get(sym, 2)
        qty = round(float(volume), precision)
        if precision == 0:
            qty = int(qty)

        try:
            data = await self._private_post('/fapi/v1/order', {
                'symbol': sym,
                'side': 'BUY' if side.upper() in ('BUY', 'LONG') else 'SELL',
                'type': 'MARKET',
                'quantity': qty,
            })
            if 'code' in data:
                raise Exception(f"Binance error {data['code']}: {data.get('msg')}")
            avg_p = float(data.get('avgPrice') or 0.0)
            if avg_p == 0.0:
                avg_p = float(data.get('price') or 0.0)
            if avg_p == 0.0:
                avg_p = await self.get_current_price(symbol)

            return {
                "status": "FILLED",
                "order_id": str(data.get('orderId', 'N/A')),
                "avg_price": avg_p
            }
        except Exception as e:
            print(f"[Binance Demo] Erro ao enviar ordem de mercado: {e}")
            return {"status": "ERROR", "order_id": "N/A", "avg_price": 0.0}

    async def place_stop_loss(self, symbol: str, side: str, stop_price: float, volume: float) -> dict:
        print(f"[Binance Demo] Stop Loss {side} em {stop_price} para {symbol}")
        sym = symbol.replace("/", "")
        if sym.endswith("USD"):
            sym = sym + "T"

        if not self._api_key:
            return {"status": "NEW", "order_id": "DEMO_MOCK_124"}

        try:
            data = await self._private_post('/fapi/v1/order', {
                'symbol': sym,
                'side': 'SELL' if side.upper() in ('BUY', 'LONG') else 'BUY',
                'type': 'STOP_MARKET',
                'stopPrice': round(float(stop_price), 2),
                'quantity': round(float(volume), 2),
                'closePosition': 'false',
            })
            if 'code' in data:
                raise Exception(f"Binance error {data['code']}: {data.get('msg')}")
            return {"status": "NEW", "order_id": str(data.get('orderId', 'N/A'))}
        except Exception as e:
            print(f"[Binance Demo] Erro ao enviar stop loss: {e}")
            return {"status": "ERROR", "order_id": "N/A"}

    async def close(self):
        """Fechar sessao aiohttp ao encerrar o broker."""
        if self._session and not self._session.closed:
            await self._session.close()
