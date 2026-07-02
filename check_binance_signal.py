import asyncio
from backend.app.brokers.binance_broker import BinanceBroker
from backend.app.strategies import MomentumBreakoutStrategy

async def main():
    b = BinanceBroker()
    p = await b.get_current_price('BTC/USDT')
    print(f"Price: {p}")
    h = await b.fetch_ohlcv('BTC/USDT', '5m', 60)
    print(f"Candles fetched: {len(h)}")
    s = MomentumBreakoutStrategy('BTC/USDT', 0.01)
    res = await s.analyze(p, h)
    print(f"Strategy result: {res}")
    await b.close()

if __name__ == "__main__":
    asyncio.run(main())
