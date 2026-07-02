import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import datetime

DATABASE_URL = "postgresql://neondb_owner:npg_jBWsTLqf5hF9@ep-tiny-dust-advv3wz2.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

result = db.execute(text("SELECT id, asset, direction, entry_price, highest_price, stop_loss, status FROM trades WHERE asset='WTI' AND status='OPEN'"))
for row in result:
    print(row._mapping)
