"""
Teste completo do BinanceBroker com Binance Demo Trading (Futuros USD-M).
"""
import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

# Simular o broker sem importar o modulo app completo
import time, hmac, hashlib, aiohttp

DEMO_BASE   = 'https://demo-fapi.binance.com'
API_KEY     = os.environ.get('BINANCE_API_KEY', '')
API_SECRET  = os.environ.get('BINANCE_API_SECRET', '')

def sign(qs: str) -> str:
    return hmac.new(API_SECRET.encode(), qs.encode(), hashlib.sha256).hexdigest()

async def main():
    print("=== Teste Binance Demo Trading (Futuros) ===\n")

    async with aiohttp.ClientSession() as s:

        # [1] Preco publico
        print("[1] Preco BTC/USDT...")
        async with s.get(f"{DEMO_BASE}/fapi/v1/ticker/price", params={"symbol": "BTCUSDT"}) as r:
            d = await r.json()
            print(f"    SUCESSO! Preco: {d['price']}\n")

        # [2] Saldo
        print("[2] Saldo da conta Demo...")
        ts = int(time.time() * 1000)
        qs = f"timestamp={ts}"
        sig = sign(qs)
        async with s.get(f"{DEMO_BASE}/fapi/v2/balance",
                         params={"timestamp": ts, "signature": sig},
                         headers={"X-MBX-APIKEY": API_KEY}) as r:
            data = await r.json()
            for asset in data:
                if asset.get('asset') == 'USDT':
                    print(f"    SUCESSO! Saldo USDT disponivel: {asset['availableBalance']}")
                    print(f"    Saldo total USDT: {asset['balance']}\n")
                    break

        # [3] OHLCV BTC 1h (5 candles)
        print("[3] OHLCV BTC/USDT 1h (ultimos 5 candles)...")
        async with s.get(f"{DEMO_BASE}/fapi/v1/klines",
                         params={"symbol": "BTCUSDT", "interval": "1h", "limit": 5}) as r:
            klines = await r.json()
            print(f"    SUCESSO! Recebidos {len(klines)} candles.")
            ts_last = klines[-1][0]
            print(f"    Ultimo close: {klines[-1][4]}\n")

    print("=== Tudo funcionando! Binance Demo conectada com sucesso. ===")

if __name__ == "__main__":
    asyncio.run(main())
