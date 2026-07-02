import os
import sys
from dotenv import load_dotenv
from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from app.database import engine

def fix_postgres_timestamp():
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE candle_data ALTER COLUMN timestamp TYPE BIGINT;"))
        print("Coluna timestamp alterada para BIGINT com sucesso no PostgreSQL.")
    except Exception as e:
        print("Erro ao alterar coluna no PostgreSQL:", e)

if __name__ == "__main__":
    fix_postgres_timestamp()
