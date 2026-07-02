import os
from dotenv import load_dotenv
load_dotenv()
from app.database import SessionLocal
from app.models import SystemSettings, Trade
db = SessionLocal()
s = db.query(SystemSettings).first()
if s:
    print(f'Threshold: {s.ai_confidence_threshold}')
else:
    print('No settings found')
    
from app.trading_service import get_bot_running
print(f'Bot Running state (memory): {get_bot_running()}')

open_trades = db.query(Trade).filter(Trade.status == "OPEN").count()
print(f'Open trades: {open_trades}')
db.close()
