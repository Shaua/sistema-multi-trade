import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from app.models import Base

# Source Neon Database
NEON_URL = os.environ.get("DATABASE_URL")
if NEON_URL and NEON_URL.startswith("postgres://"):
    NEON_URL = NEON_URL.replace("postgres://", "postgresql+psycopg2://", 1)
elif NEON_URL and NEON_URL.startswith("postgresql://"):
    NEON_URL = NEON_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

neon_engine = create_engine(NEON_URL)
NeonSession = sessionmaker(bind=neon_engine)

# Destination SQLite Database
SQLITE_URL = "sqlite:///./trader.db"
sqlite_engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
SqliteSession = sessionmaker(bind=sqlite_engine)

def migrate():
    print("Creating tables in SQLite...")
    # Drop first if exists to ensure clean slate
    Base.metadata.drop_all(bind=sqlite_engine)
    Base.metadata.create_all(bind=sqlite_engine)
    
    neon_db = NeonSession()
    sqlite_db = SqliteSession()
    
    tables = [
        ("accounts", Base.metadata.tables["accounts"]),
        ("system_settings", Base.metadata.tables["system_settings"]),
        ("trades", Base.metadata.tables["trades"]),
        ("signals", Base.metadata.tables["signals"]),
        ("candle_data", Base.metadata.tables["candle_data"]),
    ]
    
    for table_name, table_schema in tables:
        print(f"Migrating table {table_name}...")
        records = neon_db.execute(table_schema.select()).fetchall()
        if records:
            sqlite_db.execute(table_schema.insert(), [dict(row._mapping) for row in records])
            sqlite_db.commit()
            print(f"Migrated {len(records)} records for {table_name}.")
        else:
            print(f"No records found for {table_name}.")
            
    neon_db.close()
    sqlite_db.close()
    print("Migration completed successfully!")
    
if __name__ == "__main__":
    migrate()
