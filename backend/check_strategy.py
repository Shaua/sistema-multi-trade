import asyncio
from app.brokers.binance_broker import BinanceBroker
from app.strategies import MomentumBreakoutStrategy, MeanReversionStrategy
async def test():
    b = BinanceBroker()
    asset = 'BTC/USDT'
    price = await b.get_current_price(asset)
    hist_5m = await b.fetch_ohlcv(asset, '5m', 300)
    hist_15m = await b.fetch_ohlcv(asset, '15m', 300)
    strat_mom = MomentumBreakoutStrategy(asset, 0.05)
    res_mom = await strat_mom.analyze(price, hist_5m)
    print('Momentum:', res_mom)
    strat_mr = MeanReversionStrategy(asset, 0.05)
    res_mr = await strat_mr.analyze(price, hist_15m)
    print('MeanReversion:', res_mr)
asyncio.run(test())
