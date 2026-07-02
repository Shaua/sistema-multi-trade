import sqlite3
import pandas as pd

conn = sqlite3.connect('trader.db')
query = """
SELECT id, asset, direction, pnl, strategy, reason, closed_at 
FROM trades 
ORDER BY closed_at DESC
"""
df = pd.read_sql_query(query, conn)
print(f'Total trades in DB: {len(df)}')
for idx, row in df.head(10).iterrows():
    print(f"Trade {row['id']} [{row['closed_at']}]: {row['asset']} {row['direction']}, PnL: {row['pnl']}, Strategy: {row['strategy']}")
