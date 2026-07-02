import os
import sys

# Garante que as variáveis de ambiente sejam lidas do .env
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(dotenv_path=env_path)

from app.database import SessionLocal
from app.models import Trade, Account

def clear_history():
    db = SessionLocal()
    try:
        # Deletar todos os trades
        deleted_trades = db.query(Trade).delete()
        
        # Resetar a conta para o estado inicial
        account = db.query(Account).first()
        if account:
            account.balance = 100000.0
            account.equity = 100000.0
            account.max_drawdown = 0.0
        
        db.commit()
        print(f"Sucesso! {deleted_trades} operações foram excluídas da nuvem.")
        print("A conta foi resetada para o capital inicial (100k).")
    except Exception as e:
        print(f"Erro ao excluir histórico: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    clear_history()
