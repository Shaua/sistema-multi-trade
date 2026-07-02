from datetime import datetime
import asyncio
import os
import urllib.request
import urllib.parse
import json

class NotificationSystem:
    def __init__(self):
        self.channels = ["Console", "Telegram"] # "WhatsApp", "Email" seriam adicionados aqui
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

    async def send_alert(self, title: str, message: str, level: str = "INFO"):
        """
        Envia notificação para os canais configurados.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        alert_body = f"[{timestamp}] [{level}] {title}\n{message}\n"
        
        # Simula o envio
        print(f"--- NOVA NOTIFICAÇÃO ---\n{alert_body}------------------------")
        
        # Envio para o Telegram
        if self.telegram_token and self.telegram_chat_id:
            try:
                await asyncio.to_thread(self._send_telegram, title, message, level)
            except Exception as e:
                print(f"Erro no envio assíncrono para o Telegram: {e}")

    def _send_telegram(self, title: str, message: str, level: str):
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        text = f"*{level}*: {title}\n{message}"
        data = {
            "chat_id": self.telegram_chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as response:
                pass # sucesso
        except urllib.error.HTTPError as e:
            error_msg = e.read().decode('utf-8') if hasattr(e, 'read') else str(e)
            print(f"Erro ao enviar notificação pro Telegram: HTTP {e.code} - {error_msg}")
        except Exception as e:
            print(f"Erro ao enviar notificação pro Telegram: {e}")

notifier = NotificationSystem()
