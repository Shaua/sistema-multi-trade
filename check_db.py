import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

engine = create_engine('postgresql+psycopg2://trader_user:trader_password@localhost:5432/trader_db')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

result = db.execute(text("SELECT id, asset, status FROM trades WHERE status = 'OPEN';")).fetchall()
for row in result:
    print(row)
