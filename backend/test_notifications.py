import asyncio
import os
import sys

# Adiciona o diretório atual ao path para poder importar app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
# Carrega as variáveis de ambiente antes de importar o notifier
load_dotenv()

from app.notifications import notifier

async def main():
    print("Enviando notificações de teste para o Telegram...")
    
    await notifier.send_alert(
        title="Teste de Conexão",
        message="A integração com o Telegram foi configurada com sucesso!",
        level="INFO"
    )
    
    await asyncio.sleep(1)
    
    await notifier.send_alert(
        title="Alerta de Risco Simulado",
        message="Drawdown atingiu o limite configurado de 5%. Todas as posições foram protegidas.",
        level="WARNING"
    )

    await asyncio.sleep(1)
    
    await notifier.send_alert(
        title="Nova Operação (Simulação)",
        message="Compra de 0.5 BTC a $60,000 efetuada com sucesso na Binance.",
        level="SUCCESS"
    )
    
    print("Notificações enviadas! Verifique seu Telegram.")

if __name__ == "__main__":
    asyncio.run(main())
