from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio
from .ai_engine import ai_engine
from .notifications import notifier
from .database import SessionLocal
from .models import Account, Trade

async def send_morning_report():
    print("[Scheduler] Gerando relatório matinal...")
    try:
        db = SessionLocal()
        account = db.query(Account).first()
        open_trades = db.query(Trade).filter(Trade.status == "OPEN").count()
        portfolio_state = {
            "status": "Ativo",
            "balance": account.balance if account else 0.0,
            "open_trades": open_trades
        }
        db.close()
        
        report = await ai_engine.generate_morning_report(portfolio_state)
        await notifier.send_alert("☀️ Relatório Matinal", report, level="INFO")
    except Exception as e:
        print(f"Erro ao gerar relatório matinal: {e}")

async def send_evening_report():
    print("[Scheduler] Gerando relatório noturno...")
    try:
        from datetime import datetime
        db = SessionLocal()
        today = datetime.utcnow().date()
        closed_trades = db.query(Trade).filter(Trade.status == "CLOSED").all()
        day_pnl = sum(
            t.pnl for t in closed_trades
            if t.closed_at and t.closed_at.date() == today and t.pnl
        )
        daily_performance = {"pnl": round(day_pnl, 2)}
        db.close()
        
        report = await ai_engine.generate_evening_report(daily_performance)
        await notifier.send_alert("🌙 Relatório Noturno", report, level="INFO")
    except Exception as e:
        print(f"Erro ao gerar relatório noturno: {e}")

def start_scheduler():
    scheduler = AsyncIOScheduler()
    
    # Executa as 08:00
    scheduler.add_job(
        send_morning_report,
        CronTrigger(hour=8, minute=0),
        id="morning_report_job",
        replace_existing=True
    )
    
    # Executa as 20:00
    scheduler.add_job(
        send_evening_report,
        CronTrigger(hour=20, minute=0),
        id="evening_report_job",
        replace_existing=True
    )
    
    scheduler.start()
    print("[Scheduler] Iniciado. Relatórios agendados para 08:00 e 20:00.")
