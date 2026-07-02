import asyncio
import os
import sys

from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(dotenv_path=env_path)

from app.database import SessionLocal
from app.models import Trade
from app.brokers.order_manager import order_manager

async def run_test_trades():
    print("Iniciando execucao de trades de teste...")
    db = SessionLocal()
    
    try:
        # TESTE 1: Abrindo posição LONG no BTC
        print("\n--- Teste 1: LONG BTC/USDT ---")
        btc_vol = 0.05
        res1 = await order_manager.execute_trade("BTC/USDT", "LONG", btc_vol, stop_loss_price=55000.0)
        print(f"Resposta Binance: {res1}")
        
        if res1.get("status") != "ERROR":
            trade1 = Trade(
                asset="BTC/USDT",
                strategy="ManualTestStrategy",
                direction="LONG",
                entry_price=res1.get("avg_price", 60000.0),
                stop_loss=55000.0,
                take_profit=65000.0,
                volume=btc_vol,
                status="OPEN",
                reason="Teste de integridade do sistema disparado manualmente."
            )
            db.add(trade1)
            print("Trade 1 registrado no banco de dados!")
            
        # TESTE 2: Abrindo posição SHORT no ETH
        print("\n--- Teste 2: SHORT ETH/USDT ---")
        eth_vol = 0.5
        res2 = await order_manager.execute_trade("ETH/USDT", "SHORT", eth_vol, stop_loss_price=4000.0)
        print(f"Resposta Binance: {res2}")
        
        if res2.get("status") != "ERROR":
            trade2 = Trade(
                asset="ETH/USDT",
                strategy="ManualTestStrategy",
                direction="SHORT",
                entry_price=res2.get("avg_price", 3500.0),
                stop_loss=4000.0,
                take_profit=3000.0,
                volume=eth_vol,
                status="OPEN",
                reason="Teste de integridade do sistema disparado manualmente."
            )
            db.add(trade2)
            print("Trade 2 registrado no banco de dados!")
            
        db.commit()
        print("\nTodos os trades de teste foram salvos com sucesso na nuvem!")
        
    except Exception as e:
        print(f"Erro durante os testes: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_test_trades())
