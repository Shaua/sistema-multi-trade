import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path=env_path)

from fastapi import FastAPI, Depends, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import asyncio
import traceback

from .database import engine, Base, get_db
from . import models
from .data_provider import data_provider
from .brokers.broker_factory import broker_factory
from .auth import router as auth_router, get_current_user

# Cria as tabelas do banco
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Multi Asset AI Trader API")

@app.get("/health")
def health_check():
    return {"status": "ok"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_msg = f"Erro não tratado na rota {request.url.path}: {str(exc)}\n\n```python\n{traceback.format_exc()[-1000:]}\n```"
    from .notifications import notifier
    asyncio.create_task(notifier.send_alert("⚠️ Erro Crítico no Sistema", error_msg, level="CRITICAL"))
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

@app.on_event("shutdown")
async def shutdown_event():
    from .notifications import notifier
    await notifier.send_alert("🛑 Sistema Desligado", "O backend do Multi Trade está sendo desligado/inativo.", level="WARNING")

@app.on_event("startup")
async def startup_event():
    # Notificação de Inicialização
    from .notifications import notifier
    asyncio.create_task(notifier.send_alert("🚀 Sistema Iniciado", "O backend do Multi Trade está ativo e online.", level="INFO"))

    # Inicializa conta se não existir
    db = next(get_db())
    account = db.query(models.Account).first()
    if not account:
        account = models.Account(balance=100000.0, equity=100000.0)
        db.add(account)
        db.commit()

    # Inicializa configurações se não existir
    settings = db.query(models.SystemSettings).first()
    if not settings:
        settings = models.SystemSettings(max_risk_per_trade=0.01)
        db.add(settings)
        db.commit()
        
    db.close()

    # Dispara o loop de trading em background
    from .trading_service import trading_loop
    asyncio.create_task(trading_loop())

    # Dispara o scheduler para relatórios
    from .scheduler import start_scheduler
    start_scheduler()


@app.get("/api/dashboard")
def get_dashboard_stats(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    from .trading_service import get_bot_running

    account = db.query(models.Account).first()

    open_trades_count = db.query(models.Trade).filter(models.Trade.status == "OPEN").count()

    # Lucro mensal baseado em trades fechados no mês atual
    current_month = datetime.utcnow().month
    current_year  = datetime.utcnow().year
    closed_trades = db.query(models.Trade).filter(models.Trade.status == "CLOSED").all()
    monthly_profit = sum(
        t.pnl for t in closed_trades
        if t.closed_at and t.closed_at.month == current_month
        and t.closed_at.year == current_year
        and t.pnl
    )

    # Equity Curve dinâmica: agrupa PnL acumulado por dia nos últimos 30 dias
    today = datetime.utcnow().date()
    equity_curve = []
    running_equity = 100000.0  # capital inicial

    for i in range(29, -1, -1):
        day = today - timedelta(days=i)
        day_pnl = sum(
            t.pnl for t in closed_trades
            if t.closed_at and t.closed_at.date() == day and t.pnl
        )
        running_equity += day_pnl
        equity_curve.append({
            "date": day.strftime("%d/%m"),
            "equity": round(running_equity, 2)
        })

    return {
        "balance": account.balance if account else 0.0,
        "monthly_profit": round(monthly_profit, 4),
        "current_drawdown": account.max_drawdown if account else 0.0,
        "open_trades": open_trades_count,
        "equity_curve": equity_curve,
        "bot_running": get_bot_running(),
    }


@app.post("/api/bot/toggle")
def toggle_bot(current_user: str = Depends(get_current_user)):
    """Liga ou desliga o loop de trading."""
    from .trading_service import set_bot_running, get_bot_running
    new_state = not get_bot_running()
    set_bot_running(new_state)
    status = "RUNNING" if new_state else "PAUSED"
    print(f"[API] Bot {status}")
    return {"bot_running": new_state, "status": status}

@app.post("/api/bot/panic")
async def panic_button(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """Fecha todas as posições imediatamente e pausa o bot."""
    from .trading_service import set_bot_running
    from .brokers.order_manager import order_manager
    from .brokers.broker_factory import broker_factory
    from .notifications import notifier

    # 1. Pausar o robô
    set_bot_running(False)
    
    # 2. Buscar trades abertos
    open_trades = db.query(models.Trade).filter(models.Trade.status == "OPEN").all()
    closed_count = 0

    # 3. Fechar tudo
    for trade in open_trades:
        try:
            # Mandar ordem na corretora
            await order_manager.close_position(trade.asset, trade.direction, trade.volume)
            
            # Puxar preço para salvar no DB
            broker = broker_factory.get_broker(trade.asset)
            current_price = await broker.get_current_price(trade.asset)
            
            trade.status = "CLOSED"
            trade.closed_at = datetime.utcnow()
            trade.exit_price = current_price

            price_diff = trade.exit_price - trade.entry_price
            if trade.direction == "SHORT":
                price_diff = -price_diff
            trade.pnl = round(price_diff * trade.volume, 4)
            closed_count += 1
        except Exception as e:
            print(f"Erro ao fechar {trade.asset} no pânico: {e}")

    db.commit()

    # 4. Notificar
    asyncio.create_task(notifier.send_alert(
        title="🚨 BOTÃO DE PÂNICO ACIONADO 🚨",
        message=f"O robô foi pausado e {closed_count} posições foram fechadas a mercado imediatamente.",
        level="CRITICAL"
    ))

    return {"message": "Panic Mode ativado", "closed_trades": closed_count, "bot_running": False}

@app.post("/api/trades/close/{trade_id}")
async def close_trade(trade_id: int, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """Fecha manualmente uma posição específica."""
    from .brokers.order_manager import order_manager
    from .brokers.broker_factory import broker_factory
    from .notifications import notifier

    trade = db.query(models.Trade).filter(models.Trade.id == trade_id, models.Trade.status == "OPEN").first()
    if not trade:
        return {"error": "Trade não encontrado ou já fechado"}

    try:
        # Mandar ordem na corretora
        await order_manager.close_position(trade.asset, trade.direction, trade.volume)
        
        # Puxar preço para salvar no DB
        broker = broker_factory.get_broker(trade.asset)
        current_price = await broker.get_current_price(trade.asset)
        
        trade.status = "CLOSED"
        trade.closed_at = datetime.utcnow()
        trade.exit_price = current_price

        price_diff = trade.exit_price - trade.entry_price
        if trade.direction == "SHORT":
            price_diff = -price_diff
        trade.pnl = round(price_diff * trade.volume, 4)

        db.commit()

        # Notificar
        asyncio.create_task(notifier.send_alert(
            title="🛑 POSIÇÃO FECHADA MANUALMENTE 🛑",
            message=f"{trade.asset} ({trade.direction}) foi fechada pelo usuário. PnL: ${trade.pnl}",
            level="INFO"
        ))

        return {"message": "Trade fechado com sucesso", "pnl": trade.pnl}
    except Exception as e:
        print(f"Erro ao fechar {trade.asset} manualmente: {e}")
        return {"error": str(e)}

@app.get("/api/markets")
async def get_markets(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """Retorna os trades abertos com preço atual e PnL em tempo real."""
    trades = db.query(models.Trade).filter(models.Trade.status == "OPEN").all()

    from .trading_service import _last_valid_price

    result = []
    for t in trades:
        try:
            broker = broker_factory.get_broker(t.asset)
            current_price = await broker.get_current_price(t.asset)
            if current_price == 0.0:
                current_price = _last_valid_price.get(t.asset, t.entry_price or 0.0)
        except Exception:
            current_price = _last_valid_price.get(t.asset, t.entry_price or 0.0)

        # PnL flutuante em tempo real
        if t.entry_price and t.volume:
            price_diff = current_price - t.entry_price
            if t.direction == "SHORT":
                price_diff = -price_diff
            live_pnl = round(price_diff * t.volume, 4)
            if live_pnl == 0.0:
                live_pnl = 0.0
        else:
            live_pnl = 0.0

        result.append({
            "id": t.id,
            "asset": t.asset,
            "strategy": t.strategy,
            "direction": t.direction,
            "status": "Comprado" if t.direction == "LONG" else "Vendido",
            "entry_price": t.entry_price,
            "stop_loss": t.stop_loss,
            "take_profit": t.take_profit,
            "volume": t.volume,
            "price": f"$ {current_price:,.4f}",
            "metric": f"PnL: $ {live_pnl:,.4f}",
            "reason": t.reason,
        })
    return result


@app.get("/api/trades/history")
def get_trade_history(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """Histórico dos últimos 50 trades fechados."""
    trades = db.query(models.Trade).filter(
        models.Trade.status == "CLOSED"
    ).order_by(models.Trade.closed_at.desc()).limit(50).all()
    return trades

@app.delete("/api/trades/cleanup_bugged")
def cleanup_bugged_trades(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """Remove operações abertas bugadas onde o SL/TP foi calculado errado."""
    open_trades = db.query(models.Trade).filter(models.Trade.status == "OPEN").all()
    count = 0
    for t in open_trades:
        # Se a diferença percentual entre o preço de entrada e o SL for maior que 20%, provavelmente foi erro
        if t.entry_price and t.stop_loss:
            diff_pct = abs(t.entry_price - t.stop_loss) / t.entry_price
            if diff_pct > 0.2:  # Mais de 20% de diferença é absurdo
                db.delete(t)
                count += 1
    db.commit()
    return {"message": f"{count} trades bugados foram removidos com sucesso."}

@app.delete("/api/trades/{trade_id}")
def delete_trade(trade_id: int, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """Deleta um trade do histórico."""
    trade = db.query(models.Trade).filter(models.Trade.id == trade_id).first()
    if not trade:
        return {"error": "Trade não encontrado"}
    db.delete(trade)
    db.commit()
    return {"message": "Trade deletado com sucesso"}

@app.get("/api/risk")
def get_risk_metrics(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """Métricas de risco do sistema."""
    from .risk_engine import RiskEngine
    engine = RiskEngine()
    
    account = db.query(models.Account).first()
    max_dd = account.max_drawdown if account else 0.0
    protection_level = engine.check_drawdown_protection(max_dd)
    
    return {
        "max_risk_per_trade": engine.max_risk_per_trade,
        "max_drawdown": max_dd,
        "protection_level": protection_level,
        "correlation_matrix": engine.correlation_matrix
    }

from pydantic import BaseModel

class SettingsUpdate(BaseModel):
    binance_api_key: str = None
    binance_api_secret: str = None
    gemini_api_key: str = None
    telegram_bot_token: str = None
    max_risk_per_trade: float = None
    trailing_stop_activation: float = None
    trailing_stop_distance: float = None
    ai_confidence_threshold: float = None
    active_assets: str = None
    strategy_sensitivity: float = None

@app.get("/api/settings")
def get_settings(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """Retorna as configurações atuais"""
    import os
    settings = db.query(models.SystemSettings).first()
    return {
        "binance_api_key": os.getenv("BINANCE_API_KEY", ""),
        "binance_api_secret": os.getenv("BINANCE_API_SECRET", ""),
        "gemini_api_key": os.getenv("GEMINI_API_KEY", ""),
        "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
        "max_risk_per_trade": settings.max_risk_per_trade if settings else 0.01,
        "trailing_stop_activation": settings.trailing_stop_activation if settings else 1.015,
        "trailing_stop_distance": settings.trailing_stop_distance if settings else 0.015,
        "ai_confidence_threshold": settings.ai_confidence_threshold if settings else 0.5,
        "active_assets": settings.active_assets if settings else "BTC/USDT,ETH/USDT,SOL/USDT,US100,SPX500,XAU/USD",
        "strategy_sensitivity": settings.strategy_sensitivity if settings and hasattr(settings, 'strategy_sensitivity') else 0.01
    }

@app.post("/api/settings")
def update_settings(payload: SettingsUpdate, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """Atualiza as configurações (DB e .env)"""
    print("Iniciando update_settings...")
    import os
    from dotenv import set_key
    
    # Path para o .env no diretório pai do backend (onde fica o venv, ou dentro do backend)
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    
    if payload.binance_api_key is not None and payload.binance_api_key != "":
        set_key(env_path, "BINANCE_API_KEY", payload.binance_api_key)
        os.environ["BINANCE_API_KEY"] = payload.binance_api_key
    if payload.binance_api_secret is not None and payload.binance_api_secret != "":
        set_key(env_path, "BINANCE_API_SECRET", payload.binance_api_secret)
        os.environ["BINANCE_API_SECRET"] = payload.binance_api_secret
    if payload.gemini_api_key is not None and payload.gemini_api_key != "":
        set_key(env_path, "GEMINI_API_KEY", payload.gemini_api_key)
        os.environ["GEMINI_API_KEY"] = payload.gemini_api_key
    if payload.telegram_bot_token is not None and payload.telegram_bot_token != "":
        set_key(env_path, "TELEGRAM_BOT_TOKEN", payload.telegram_bot_token)
        os.environ["TELEGRAM_BOT_TOKEN"] = payload.telegram_bot_token

    if any(x is not None for x in [
        payload.max_risk_per_trade, payload.trailing_stop_activation, 
        payload.trailing_stop_distance, payload.ai_confidence_threshold, payload.active_assets,
        payload.strategy_sensitivity
    ]):
        print("Consultando DB para settings...")
        settings = db.query(models.SystemSettings).first()
        print("Settings encontradas:", settings)
        if not settings:
            settings = models.SystemSettings()
            db.add(settings)
        
        if payload.max_risk_per_trade is not None:
            settings.max_risk_per_trade = payload.max_risk_per_trade
        if payload.trailing_stop_activation is not None:
            settings.trailing_stop_activation = payload.trailing_stop_activation
        if payload.trailing_stop_distance is not None:
            settings.trailing_stop_distance = payload.trailing_stop_distance
        if payload.ai_confidence_threshold is not None:
            settings.ai_confidence_threshold = payload.ai_confidence_threshold
        if payload.active_assets is not None:
            settings.active_assets = payload.active_assets
        if payload.strategy_sensitivity is not None:
            settings.strategy_sensitivity = payload.strategy_sensitivity
            
        db.commit()
        print("DB commit realizado.")

    print("Retornando sucesso.")
    return {"message": "Configurações atualizadas com sucesso"}

class BacktestRequest(BaseModel):
    asset: str
    days: int
    initial_balance: float = 10000.0

@app.post("/api/backtest")
async def run_backtest(req: BacktestRequest, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """Roda um backtest num ativo usando os Candles salvos"""
    from .backtest import BacktestEngine
    engine = BacktestEngine(db)
    result = await engine.run_backtest(req.asset, req.days, req.initial_balance)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
