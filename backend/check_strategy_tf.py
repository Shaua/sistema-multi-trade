import asyncio
from app.brokers.binance_broker import BinanceBroker
from app.strategies import TrendFollowingStrategy
async def test():
    b = BinanceBroker()
    asset = 'BTC/USDT'
    price = await b.get_current_price(asset)
    hist_15m = await b.fetch_ohlcv(asset, '15m', 300)
    strat_tf = TrendFollowingStrategy(asset, 0.05)
    res_tf = await strat_tf.analyze(price, hist_15m)
    print('TrendFollowing:', res_tf)
asyncio.run(test())
