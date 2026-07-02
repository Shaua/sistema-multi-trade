import os
import sys
from dotenv import load_dotenv
from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from app.database import engine

def migrate_postgres():
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE system_settings ADD COLUMN strategy_sensitivity FLOAT DEFAULT 0.01"))
        print("Coluna strategy_sensitivity adicionada com sucesso no PostgreSQL.")
    except Exception as e:
        print("Erro na migração do PostgreSQL (talvez a coluna já exista):", e)

if __name__ == "__main__":
    migrate_postgres()
