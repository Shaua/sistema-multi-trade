import sqlite3
import pprint

conn = sqlite3.connect('c:/Users/Shau/Documents/Sistema 3 Multi Trade/backend/trader.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Check open trades
cur.execute("SELECT * FROM trades WHERE status='OPEN'")
open_trades = cur.fetchall()
print(f"Open trades: {len(open_trades)}")
for t in open_trades:
    print(dict(t))
