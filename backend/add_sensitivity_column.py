import os
import sys
import sqlite3
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

def migrate():
    db_path = "./trader.db"
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("ALTER TABLE system_settings ADD COLUMN strategy_sensitivity FLOAT DEFAULT 0.01")
        conn.commit()
        print("Coluna strategy_sensitivity adicionada com sucesso.")
    except Exception as e:
        print("Erro na migração (talvez a coluna já exista):", e)
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    migrate()
