import asyncio
from dotenv import load_dotenv
load_dotenv()
from app.ai_engine import ai_engine

async def main():
    print("Testing AI Engine...")
    result = await ai_engine.analyze_trade_signal(
        asset="BTC/USD",
        strategy="MomentumBreakoutStrategy",
        signal="LONG",
        market_context={"volatility": "normal", "trend": "bullish", "metric": 0.5}
    )
    print("Result:", result)

if __name__ == "__main__":
    asyncio.run(main())
