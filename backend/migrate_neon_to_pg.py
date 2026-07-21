import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import Base

# Source Neon Database
NEON_URL = "postgresql+psycopg2://neondb_owner:npg_jBWsTLqf5hF9@ep-tiny-dust-advv3wz2.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require"
neon_engine = create_engine(NEON_URL)
NeonSession = sessionmaker(bind=neon_engine)

# Destination Local Postgres Database
# Using localhost since we will run this script on the EC2 host (not inside the container)
# The docker container exposes port 5432 to the host.
LOCAL_PG_URL = "postgresql+psycopg2://trader_user:trader_password@localhost:5432/trader_db"
local_engine = create_engine(LOCAL_PG_URL)
LocalSession = sessionmaker(bind=local_engine)

def migrate():
    print("Creating tables in Local Postgres...")
    Base.metadata.create_all(bind=local_engine)
    
    neon_db = NeonSession()
    local_db = LocalSession()
    
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
            # Drop the table contents on local DB before inserting to prevent unique constraint violations
            local_db.execute(table_schema.delete())
            local_db.commit()
            
            # Insert records
            local_db.execute(table_schema.insert(), [dict(row._mapping) for row in records])
            local_db.commit()
            print(f"Migrated {len(records)} records for {table_name}.")
        else:
            print(f"No records found for {table_name}.")
            
    neon_db.close()
    local_db.close()
    print("Migration completed successfully!")
    
if __name__ == "__main__":
    migrate()
