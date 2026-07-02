import asyncio
from app.brokers.binance_broker import BinanceBroker
async def test():
    b = BinanceBroker()
    price = await b.get_current_price('BTC/USDT')
    print('Price:', price)
    hist = await b.fetch_ohlcv('BTC/USDT', '15m')
    print('Hist length:', len(hist))
asyncio.run(test())
