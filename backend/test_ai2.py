import asyncio, os, json
from dotenv import load_dotenv
load_dotenv('C:/Users/Shau/Documents/Sistema 3 Multi Trade/backend/.env')
from app.ai_engine import ai_engine
async def t():
    res = await ai_engine.analyze_trade_signal('BTC/USDT', 'Trend Following', 'LONG', {'trend': 'UP', 'metric': 'Test'})
    print(json.dumps(res))
asyncio.run(t())
