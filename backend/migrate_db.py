import os
import sys
from sqlalchemy import text
from dotenv import load_dotenv

# Load env
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from app.database import engine

def migrate():
    with engine.connect() as conn:
        try:
            # Check if column exists
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='trades' AND column_name='highest_price'"))
            if not result.fetchone():
                print("Adicionando coluna highest_price...")
                conn.execute(text("ALTER TABLE trades ADD COLUMN highest_price FLOAT"))
                # Preencher dados antigos
                conn.execute(text("UPDATE trades SET highest_price = entry_price WHERE highest_price IS NULL"))
                conn.commit()
                print("Migração concluída.")
            else:
                print("Coluna highest_price já existe.")
        except Exception as e:
            print("Erro na migração:", e)

if __name__ == "__main__":
    migrate()
