import asyncio
import ccxt.async_support as ccxt
import os
from dotenv import load_dotenv

load_dotenv()

async def test_ccxt():
    api_key = os.environ.get('BINANCE_API_KEY', '')
    api_secret = os.environ.get('BINANCE_API_SECRET', '')
    
    # Try using standard binance class
    client = ccxt.binance({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'future', # or swap
        }
    })
    
    client.set_sandbox_mode(True)
    
    try:
        balance = await client.fetch_balance()
        print("Balance fetched successfully!")
        usdt_balance = balance.get('USDT', {}).get('free', 'N/A')
        print(f"USDT Balance: {usdt_balance}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(test_ccxt())
