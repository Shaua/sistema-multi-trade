from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from .models import CandleData
from .strategies import MomentumBreakoutStrategy, MeanReversionStrategy, TrendFollowingStrategy

class BacktestEngine:
    def __init__(self, db: Session):
        self.db = db

    async def run_backtest(self, asset: str, days: int, initial_balance: float = 10000.0) -> dict:
        # Tratamento de erro de digitação do usuário para ativos comuns
        asset = asset.upper().strip()
        if asset == "XAU": asset = "XAU/USD"
        if asset == "BTC": asset = "BTC/USDT"
        if asset == "ETH": asset = "ETH/USDT"
        if asset == "SOL": asset = "SOL/USDT"
        if asset == "SPX" or asset == "SP500": asset = "SPX500"
        if asset == "NASDAQ" or asset == "NDX": asset = "US100"

        cutoff = datetime.utcnow() - timedelta(days=days)
        cutoff_ms = int(cutoff.timestamp() * 1000)
        
        # Puxa candles do banco, ordenados do mais antigo pro mais novo
        candles = self.db.query(CandleData).filter(
            CandleData.asset == asset,
            CandleData.timestamp >= cutoff_ms
        ).order_by(CandleData.timestamp.asc()).all()

        historical_data = []
        if len(candles) < 60:
            from .brokers.broker_factory import broker_factory
            try:
                broker = broker_factory.get_broker(asset)
                # Tenta puxar o limite máximo de candles da API para ter bastante histórico (ex: 1000 horas)
                api_candles = await broker.fetch_ohlcv(asset, "1h", limit=1000)
                if api_candles:
                    for c in api_candles:
                        # [timestamp, open, high, low, close, volume]
                        if int(c[0]) >= cutoff_ms:
                            historical_data.append([c[0], c[1], c[2], c[3], c[4], c[5]])
            except Exception as e:
                print(f"Erro puxando do broker no backtest: {e}")
                pass
        else:
            for c in candles:
                historical_data.append([c.timestamp, c.open, c.high, c.low, c.close, c.volume])
        
        if not historical_data:
            return {"error": "Nenhum dado histórico encontrado para o período/ativo especificado."}

        # Buscar sensibilidade da estratégia
        from .models import SystemSettings
        settings = self.db.query(SystemSettings).first()
        sensitivity = settings.strategy_sensitivity if settings and hasattr(settings, 'strategy_sensitivity') else 0.01

        # Determina a estratégia com base no ativo, assim como no trading_service
        strategy = None
        if asset in ["US100", "SPX500"]:
            strategy = MeanReversionStrategy(asset, sensitivity)
        elif asset in ["XAU/USD", "WTI"]:
            strategy = TrendFollowingStrategy(asset, sensitivity)
        else:
            strategy = MomentumBreakoutStrategy(asset, sensitivity)

        balance = initial_balance
        equity_curve = []
        trades = []
        
        # Estado atual da posição
        open_position = None
        
        # SL e TP hardcoded temporariamente para a simulação, idealmente puxaria das configurações
        # Para simplificar, assumimos que 1 unidade = 100% da banca
        # Stop e Gain simulam 2% de risco
        
        # Janela deslizante de 60 candles para simular o contexto "histórico" daquele momento
        # A estratégia requer no mínimo 26 a 50 candles para calcular EMA50 / MACD
        min_candles = 60
        if len(historical_data) < min_candles:
            return {"error": "Dados insuficientes para calcular indicadores (mínimo 60 candles)."}

        for i in range(min_candles, len(historical_data)):
            window = historical_data[i-min_candles:i+1]
            current_candle = historical_data[i]
            current_price = current_candle[4] # close
            ts = current_candle[0]
            dt = datetime.utcfromtimestamp(ts/1000).strftime('%Y-%m-%d %H:%M:%S')
            
            # Se já estivermos posicionados, avaliamos saída
            if open_position:
                direction = open_position["direction"]
                entry = open_position["entry"]
                sl = open_position["sl"]
                tp = open_position["tp"]
                
                closed = False
                exit_price = current_price
                
                # Checa SL e TP (usando a variação do candle inteiro para ser conservador no SL)
                high = current_candle[2]
                low = current_candle[3]
                
                if direction == "LONG":
                    if low <= sl:
                        closed = True
                        exit_price = sl
                    elif high >= tp:
                        closed = True
                        exit_price = tp
                else:
                    if high >= sl:
                        closed = True
                        exit_price = sl
                    elif low <= tp:
                        closed = True
                        exit_price = tp
                        
                if closed:
                    pnl = (exit_price - entry) / entry if direction == "LONG" else (entry - exit_price) / entry
                    profit = balance * pnl * 10 # 10x leverage simulado
                    balance += profit
                    
                    trades.append({
                        "entry_time": open_position["entry_time"],
                        "exit_time": dt,
                        "direction": direction,
                        "entry_price": entry,
                        "exit_price": exit_price,
                        "pnl": profit
                    })
                    open_position = None
            else:
                # Importante: o backtest aqui será síncrono. O `strategy.analyze` é async por causa do IB_Broker,
                # mas os cálculos em si (talib/pandas) são síncronos. 
                # Como strategy.analyze() faz `await broker.fetch_ohlcv` internamente se a gente não passar.
                # Espera, no código atual `strategy.analyze` recebe historical_data.
                # E retorna {"signal": "LONG", "metric": ...}. O AI_engine é mockado no backtest.
                result = await strategy.analyze(current_price, window)
                
                signal = result.get("signal", "NEUTRAL")
                
                # Mock da Inteligência artificial (Aprova automático 100%)
                if signal != "NEUTRAL":
                    open_position = {
                        "direction": signal,
                        "entry": current_price,
                        "entry_time": dt,
                        "sl": current_price * 0.98 if signal == "LONG" else current_price * 1.02,
                        "tp": current_price * 1.04 if signal == "LONG" else current_price * 0.96
                    }
            
            equity_curve.append({
                "date": dt,
                "equity": balance
            })

        # Fechar qualquer trade aberto no final
        if open_position:
             entry = open_position["entry"]
             direction = open_position["direction"]
             exit_price = historical_data[-1][4]
             pnl = (exit_price - entry) / entry if direction == "LONG" else (entry - exit_price) / entry
             profit = balance * pnl * 10
             balance += profit
             trades.append({
                  "entry_time": open_position["entry_time"],
                  "exit_time": "FECHAMENTO_FINAL",
                  "direction": direction,
                  "entry_price": entry,
                  "exit_price": exit_price,
                  "pnl": profit
             })

        return {
            "initial_balance": initial_balance,
            "final_balance": round(balance, 2),
            "trades": trades,
            "equity_curve": equity_curve,
            "total_trades": len(trades),
            "win_rate": round(sum(1 for t in trades if t["pnl"] > 0) / len(trades) * 100, 2) if trades else 0.0
        }
