import asyncio
from datetime import datetime
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential
from .database import SessionLocal
from .models import Trade, Account, Signal
from .ai_engine import ai_engine
from .risk_engine import RiskEngine
from .brokers.order_manager import order_manager
from .brokers.broker_factory import broker_factory
from .strategies import MomentumBreakoutStrategy, MeanReversionStrategy, TrendFollowingStrategy
from .notifications import notifier

risk_engine = RiskEngine()

# Estado global do bot (pode ser controlado via API)
_bot_running = True

def set_bot_running(state: bool):
    global _bot_running
    _bot_running = state

def get_bot_running() -> bool:
    return _bot_running

_last_valid_price = {}


async def trading_loop():
    """
    Loop principal de automação do trading, agora com tratamento de erros (Tenacity).
    """
    while True:
        await asyncio.sleep(15)  # Ciclo a cada 15 segundos

        if not _bot_running:
            print("[TradingLoop] Bot pausado. Aguardando...")
            continue

        db = SessionLocal()
        try:
            from .models import SystemSettings
            settings = db.query(SystemSettings).first()
            if not settings:
                settings = SystemSettings() # Defaults
            
            account = db.query(Account).first()
            if not account:
                continue

            # ── 1. Sincronizar saldo real com a Binance Testnet ──────────────
            try:
                binance = broker_factory.get_broker("BTC/USD")
                async for attempt in AsyncRetrying(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)):
                    with attempt:
                        real_balance = await binance.get_account_balance()
                
                account.balance = real_balance
                account.equity = real_balance
                db.commit()
            except Exception as e:
                print(f"[TradingLoop] Erro ao sincronizar saldo: {e}")
                real_balance = account.balance  # Fallback

            # ── 2. Gerenciar trades abertos (TP / SL) ────────────────────────
            open_trades = db.query(Trade).filter(Trade.status == "OPEN").all()
            for trade in open_trades:
                try:
                    broker = broker_factory.get_broker(trade.asset)
                    async for attempt in AsyncRetrying(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)):
                        with attempt:
                            current_price = await broker.get_current_price(trade.asset)

                    # Filtro Anti-Spike
                    last_price = _last_valid_price.get(trade.asset)
                    if last_price:
                        price_diff_pct = abs(current_price - last_price) / last_price
                        if price_diff_pct > 0.05:
                            print(f"[Anti-Spike] Spike detectado em {trade.asset}. Preço saltou de {last_price} para {current_price}. Ignorando tick.")
                            continue
                    _last_valid_price[trade.asset] = current_price

                    should_close = False

                    # Lógica de Trailing Stop
                    if trade.highest_price is None:
                        trade.highest_price = trade.entry_price

                    if trade.direction == "LONG":
                        if current_price > trade.highest_price:
                            trade.highest_price = current_price
                        
                        trigger_distance = trade.entry_price * settings.trailing_stop_activation
                        if trade.highest_price >= trigger_distance:
                            new_sl = round(trade.highest_price * (1.0 - settings.trailing_stop_distance), 6)
                            if new_sl > trade.stop_loss:
                                print(f"[Trailing Stop] LONG {trade.asset} SL movido de {trade.stop_loss} para {new_sl:.6f}")
                                trade.stop_loss = new_sl
                                asyncio.create_task(notifier.send_alert(
                                    title="Trailing Stop Acionado 📈",
                                    message=f"Ativo: {trade.asset}\nDireção: LONG\nNova Proteção (SL): $ {trade.stop_loss:,.2f}",
                                    level="INFO"
                                ))

                        if current_price <= trade.stop_loss:
                            should_close = True
                            print(f"[SL] Fechando LONG {trade.asset} @ {current_price} (SL: {trade.stop_loss})")
                        elif trade.take_profit and current_price >= trade.take_profit:
                            should_close = True
                            print(f"[TP] Fechando LONG {trade.asset} @ {current_price} (TP: {trade.take_profit})")
                    elif trade.direction == "SHORT":
                        if current_price < trade.highest_price:
                            trade.highest_price = current_price

                        trigger_distance = trade.entry_price * (2.0 - settings.trailing_stop_activation)
                        if trade.highest_price <= trigger_distance:
                            new_sl = round(trade.highest_price * (1.0 + settings.trailing_stop_distance), 6)
                            if new_sl < trade.stop_loss:
                                print(f"[Trailing Stop] SHORT {trade.asset} SL movido de {trade.stop_loss} para {new_sl:.6f}")
                                trade.stop_loss = new_sl
                                asyncio.create_task(notifier.send_alert(
                                    title="Trailing Stop Acionado 📉",
                                    message=f"Ativo: {trade.asset}\nDireção: SHORT\nNova Proteção (SL): $ {trade.stop_loss:,.2f}",
                                    level="INFO"
                                ))

                        if current_price >= trade.stop_loss:
                            should_close = True
                            print(f"[SL] Fechando SHORT {trade.asset} @ {current_price} (SL: {trade.stop_loss})")
                        elif trade.take_profit and current_price <= trade.take_profit:
                            should_close = True
                            print(f"[TP] Fechando SHORT {trade.asset} @ {current_price} (TP: {trade.take_profit})")

                    # Hard Stop (-3% of equity)
                    floating_diff = current_price - trade.entry_price if trade.direction == "LONG" else trade.entry_price - current_price
                    floating_pnl = floating_diff * trade.volume
                    if (floating_pnl / account.equity) <= -0.03:
                        should_close = True
                        print(f"[Hard Stop] Prejuízo de -3% atingido em {trade.asset}. Fechando imediatamente @ {current_price}.")
                        asyncio.create_task(notifier.send_alert(
                            title="Hard Stop Acionado 🚨",
                            message=f"Ativo: {trade.asset}\nDireção: {trade.direction}\nPrejuízo excedeu -3% da banca.",
                            level="WARNING"
                        ))

                    if should_close:
                        async for attempt in AsyncRetrying(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)):
                            with attempt:
                                await order_manager.close_position(trade.asset, trade.direction, trade.volume)

                        trade.status = "CLOSED"
                        trade.closed_at = datetime.utcnow()
                        trade.exit_price = current_price

                        price_diff = trade.exit_price - trade.entry_price
                        if trade.direction == "SHORT":
                            price_diff = -price_diff

                        trade.pnl = round(price_diff * trade.volume, 4)

                        action_type = "Gain" if trade.pnl > 0 else "Loss"
                        alert_level = "SUCCESS" if trade.pnl > 0 else "WARNING"
                        asyncio.create_task(notifier.send_alert(
                            title=f"Trade Fechado ({action_type})",
                            message=f"Ativo: {trade.asset}\nDireção: {trade.direction}\nSaída: $ {trade.exit_price:,.2f}\nPnL: $ {trade.pnl:,.2f}",
                            level=alert_level
                        ))
                
                except Exception as e:
                    print(f"[TradingLoop] Erro ao processar trade aberto {trade.asset}: {e}")

            db.commit()

            # ── 3. Avaliar estratégias ativas ───────────
            if len(open_trades) < 15:
                ativos = [a.strip() for a in settings.active_assets.split(",") if a.strip()]
                sensitivity = settings.strategy_sensitivity if hasattr(settings, 'strategy_sensitivity') else 0.01

                estrategias_ativas = []
                for a in ativos:
                    if a in ["US100", "SPX500"]:
                        estrategias_ativas.append(MeanReversionStrategy(a, sensitivity))
                    elif a in ["XAU/USD", "WTI"]:
                        estrategias_ativas.append(TrendFollowingStrategy(a, sensitivity))
                    else:
                        estrategias_ativas.append(MomentumBreakoutStrategy(a, sensitivity))
                        estrategias_ativas.append(MeanReversionStrategy(a, sensitivity))

                for strategy in estrategias_ativas:
                    try:
                        if len(open_trades) >= 15:
                            break

                        if any(t.asset == strategy.asset for t in open_trades):
                            continue

                        broker = broker_factory.get_broker(strategy.asset)
                        
                        async for attempt in AsyncRetrying(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)):
                            with attempt:
                                current_price = await broker.get_current_price(strategy.asset)
                                historical_data = await broker.fetch_ohlcv(strategy.asset, strategy.timeframe, limit=300)

                        # Filtro Anti-Spike
                        last_price = _last_valid_price.get(strategy.asset)
                        if last_price:
                            price_diff_pct = abs(current_price - last_price) / last_price
                            if price_diff_pct > 0.05:
                                print(f"[Anti-Spike] Spike detectado em {strategy.asset} durante análise. Ignorando tick.")
                                continue
                        _last_valid_price[strategy.asset] = current_price

                        if historical_data and len(historical_data) > 1:
                            last_closed = historical_data[-2]
                            from .models import CandleData
                            ts = int(last_closed[0])
                            existing_candle = db.query(CandleData).filter(
                                CandleData.asset == strategy.asset,
                                CandleData.timeframe == strategy.timeframe,
                                CandleData.timestamp == ts
                            ).first()
                            if not existing_candle:
                                db.add(CandleData(
                                    asset=strategy.asset,
                                    timeframe=strategy.timeframe,
                                    timestamp=ts,
                                    open=float(last_closed[1]),
                                    high=float(last_closed[2]),
                                    low=float(last_closed[3]),
                                    close=float(last_closed[4]),
                                    volume=float(last_closed[5])
                                ))

                        analysis_result = await strategy.analyze(current_price, historical_data)
                        signal = analysis_result["signal"]

                        if signal != "NEUTRAL":
                            now = datetime.utcnow()
                            cooldown_key = f"{strategy.asset}_{strategy.__class__.__name__}_{signal}"
                            
                            # Use global dictionary for cooldowns since strategy instances are recreated
                            global _ai_cooldowns
                            if '_ai_cooldowns' not in globals():
                                _ai_cooldowns = {}
                                
                            last_check = _ai_cooldowns.get(cooldown_key)
                            
                            # Cooldown de 15 minutos para o mesmo sinal no mesmo ativo para evitar spam na IA e overtrading
                            if last_check and (now - last_check).total_seconds() < 900:
                                continue

                            _ai_cooldowns[cooldown_key] = now

                            print(f"[{strategy.__class__.__name__}] {strategy.asset} | Preço: {current_price:.2f} | Sinal: {signal} | {analysis_result['metric']}")
                            
                            protection = risk_engine.check_drawdown_protection(account.max_drawdown)
                            if protection != "LEVEL_3_PROTECTION":
                                async for attempt in AsyncRetrying(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)):
                                    with attempt:
                                        analysis = await ai_engine.analyze_trade_signal(
                                            asset=strategy.asset,
                                            strategy=strategy.__class__.__name__,
                                            signal=signal,
                                            market_context=analysis_result.get("suggested_context", {
                                                "volatility": "normal",
                                                "trend": "bullish" if signal == "LONG" else "bearish",
                                                "metric": analysis_result["metric"]
                                            })
                                        )
                                        
                                # Pausa de 4.1 segundos garantida após cada chamada à IA para NUNCA estourar
                                # o limite de 15 requisições por minuto da camada gratuita (60s / 15 = 4s).
                                await asyncio.sleep(4.1)

                                confidence = analysis.get("grau_confianca", 0.0)
                                print(f"[IA - {strategy.asset}] Confiança: {confidence:.0%} | Risco: {analysis.get('nivel_risco')}")

                                if confidence >= settings.ai_confidence_threshold:
                                    suggested_sl = analysis_result.get("suggested_sl")
                                    suggested_tp = analysis_result.get("suggested_tp")
                                    
                                    if suggested_sl is not None and suggested_tp is not None:
                                        stop_loss = suggested_sl
                                        take_profit = suggested_tp
                                    else:
                                        sl_distance_pct = 0.02
                                        tp_distance_pct = 0.04
                                        if signal == "LONG":
                                            stop_loss  = round(current_price * (1 - sl_distance_pct), 6)
                                            take_profit = round(current_price * (1 + tp_distance_pct), 6)
                                        else:
                                            stop_loss  = round(current_price * (1 + sl_distance_pct), 6)
                                            take_profit = round(current_price * (1 - tp_distance_pct), 6)

                                    reduction = risk_engine.check_correlation_exposure(
                                        strategy.asset,
                                        [t.asset for t in open_trades]
                                    )
                                    
                                    risk_amount = real_balance * settings.max_risk_per_trade
                                    sl_distance_points = abs(current_price - stop_loss)
                                    raw_volume = risk_amount / sl_distance_points if sl_distance_points > 0 else 0
                                    volume = max(round(raw_volume * reduction, 3), 0.001)

                                    print(f"[Ordem] {signal} {strategy.asset} | Vol: {volume} | SL: {stop_loss} | TP: {take_profit}")

                                    async for attempt in AsyncRetrying(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)):
                                        with attempt:
                                            order_res = await order_manager.execute_trade(
                                                strategy.asset, signal, volume, stop_loss
                                            )

                                    if order_res.get("status") != "ERROR":
                                        entry_price = order_res.get("avg_price", current_price)

                                        new_trade = Trade(
                                            asset=strategy.asset,
                                            strategy=strategy.__class__.__name__,
                                            direction=signal,
                                            entry_price=round(entry_price, 6),
                                            stop_loss=stop_loss,
                                            take_profit=take_profit,
                                            volume=volume,
                                            status="OPEN",
                                            reason=analysis.get("motivo_entrada") or "Aprovado via IA"
                                        )
                                        db.add(new_trade)
                                        open_trades.append(new_trade)
                                        print(f"[Trade] Nova posição aberta: {signal} {volume} {strategy.asset} @ {entry_price:.2f}")

                                        asyncio.create_task(notifier.send_alert(
                                            title="Nova Posição Aberta",
                                            message=f"Ativo: {strategy.asset}\nDireção: {signal}\nPreço: $ {entry_price:,.2f}\nVolume: {volume}\nSL: $ {stop_loss} | TP: $ {take_profit}\nMotivo: {new_trade.reason}",
                                            level="INFO"
                                        ))

                                else:
                                    motivo = analysis.get("motivo_entrada") or "Sinal rejeitado pela IA"
                                    
                                    new_signal = Signal(
                                        asset=strategy.asset,
                                        strategy=strategy.__class__.__name__,
                                        direction=signal,
                                        price=current_price,
                                        ai_confidence=confidence,
                                        ai_reasoning=motivo,
                                        is_executed=False
                                    )
                                    db.add(new_signal)

                                    if "Limites esgotados" in motivo:
                                        asyncio.create_task(notifier.send_alert(
                                            title="Operação Cancelada (IA)",
                                            message=f"Ativo: {strategy.asset}\nDireção: {signal}\nPreço: $ {current_price:,.2f}\nMotivo: Limites da IA esgotados. A operação foi cancelada por segurança e registrada no dashboard.",
                                            level="WARNING"
                                        ))
                                    else:
                                        print(f"[Signal] {signal} {strategy.asset} rejeitado. Motivo: {motivo}")
                    except Exception as e:
                        print(f"[TradingLoop] Erro ao analisar ativo {strategy.asset}: {e}")

                    # Pequena pausa para evitar sobrecarga de requisições concorrentes nas APIs (Rate Limit por segundo)
                    await asyncio.sleep(0.5)

            db.commit()

        except Exception as e:
            print(f"[TradingLoop] ERRO FATAL: {e}")
            import traceback
            traceback.print_exc()
            db.rollback()
        finally:
            db.close()
