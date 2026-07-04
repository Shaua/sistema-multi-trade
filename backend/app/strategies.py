from typing import Dict, Any
from .indicators import calculate_sma, calculate_donchian_channel, calculate_ema, calculate_rsi, calculate_atr
import random
class BaseStrategy:
    def __init__(self, asset: str, timeframe: str):
        self.asset = asset
        self.timeframe = timeframe

    async def analyze(self, current_price: float, historical_data: list) -> Dict[str, Any]:
        """Analisa os dados e retorna um sinal de compra/venda ou neutro."""
        raise NotImplementedError("As estratégias devem implementar o método analyze.")

class MeanReversionStrategy(BaseStrategy):
    """
    Estratégia para Nasdaq e S&P 500 (15m).
    Lógica: Identificar movimentos extremos afastados da média móvel.
    """
    def __init__(self, asset: str, sensitivity: float = 0.01):
        super().__init__(asset, "1h")
        self.moving_average = 0.0
        self.deviation_threshold = sensitivity
        self.ma_period = 20

    async def analyze(self, current_price: float, historical_data: list) -> Dict[str, Any]:
        if not historical_data or len(historical_data) < self.ma_period:
            return {
                "asset": self.asset,
                "strategy": "Mean Reversion",
                "signal": "NEUTRAL",
                "price": current_price,
                "metric": "Aguardando dados suficientes"
            }
        
        closes = [candle[4] for candle in historical_data]
        highs = [candle[2] for candle in historical_data]
        lows = [candle[3] for candle in historical_data]

        self.moving_average = calculate_sma(closes, self.ma_period)
        rsi = calculate_rsi(closes, 14)
        atr = calculate_atr(highs, lows, closes, 14)
        
        if self.moving_average == 0.0:
            # Fallback
            self.moving_average = current_price

        distance = (current_price - self.moving_average) / self.moving_average

        signal = "NEUTRAL"
        
        # Confirmação de reversão usando os dois últimos candles fechados
        last_close = historical_data[-2][4] if len(historical_data) > 1 else current_price
        prev_close = historical_data[-3][4] if len(historical_data) > 2 else last_close

        suggested_sl = None
        suggested_tp = None

        if distance < -self.deviation_threshold and last_close > prev_close and rsi < 35:
            signal = "LONG" # Preço muito abaixo da média, subindo E sobrevendido
            suggested_sl = round(current_price - (2 * atr), 6) if atr > 0 else None
            suggested_tp = round(current_price + (4 * atr), 6) if atr > 0 else None
        elif distance > self.deviation_threshold and last_close < prev_close and rsi > 65:
            signal = "SHORT" # Preço muito acima da média, caindo E sobrecomprado
            suggested_sl = round(current_price + (2 * atr), 6) if atr > 0 else None
            suggested_tp = round(current_price - (4 * atr), 6) if atr > 0 else None

        return {
            "asset": self.asset,
            "strategy": "Mean Reversion",
            "signal": signal,
            "price": current_price,
            "metric": f"Dist. MA: {round(distance * 100, 2)}% | RSI: {round(rsi, 2)}",
            "suggested_sl": suggested_sl,
            "suggested_tp": suggested_tp,
            "suggested_context": {
                "volatility": f"ATR: {round(atr, 4)}",
                "trend": "oversold (reversal)" if signal == "LONG" else "overbought (reversal)",
                "metric": f"Distance: {round(distance * 100, 2)}%, RSI: {round(rsi, 2)}"
            }
        }

class MomentumBreakoutStrategy(BaseStrategy):
    """
    Estratégia para Bitcoin (1h).
    Lógica real: Calcula a máxima e mínima dos últimos 20 candles (Canal de Donchian simplificado).
    Se o preço atual romper a máxima, com volume acima da média, envia sinal LONG.
    Se perder a mínima, envia SHORT.
    """
    def __init__(self, asset: str, sensitivity: float = 0.01):
        super().__init__(asset, "1h")
        # Menor sensibilidade (0.005) -> mais agressivo -> menor lookback
        # Base = 20 para 0.01
        self.lookback_period = max(5, int(20 * (sensitivity / 0.01)))
        self.sensitivity = sensitivity

    async def analyze(self, current_price: float, historical_data: list) -> Dict[str, Any]:
        signal = "NEUTRAL"
        resistance = 0.0
        support = 0.0
        metric_str = "Aguardando dados"
        suggested_sl = None
        suggested_tp = None
        ema200 = 0.0

        # historical_data format: [ [ts, open, high, low, close, vol], ... ]
        if historical_data and len(historical_data) >= max(200, self.lookback_period + 1):
            # Pegar todos exceto o último candle (que ainda não fechou) para o cálculo do canal
            highs = [candle[2] for candle in historical_data[:-1]]
            lows = [candle[3] for candle in historical_data[:-1]]
            closes = [candle[4] for candle in historical_data]
            
            resistance, support = calculate_donchian_channel(highs, lows, self.lookback_period)
            ema200 = calculate_ema(closes, 200)
            
            # Precisamos dos volumes dos ultimos N candles, incluindo o ultimo fechado
            recent_candles = historical_data[-(self.lookback_period+1):]
            volumes = [candle[5] for candle in recent_candles]
            
            avg_volume = sum(volumes[:-1]) / len(volumes[:-1]) if len(volumes) > 1 else 0
            last_closed_volume = historical_data[-2][5] if len(historical_data) > 1 else 0
            
            metric_str = f"Res: {round(resistance, 2)} / Sup: {round(support, 2)}"
            
            # Condição de rompimento com Filtro de Distância / Pullback e Tendência (EMA200)
            if current_price > resistance and current_price > ema200:
                if current_price <= resistance * 1.01:
                    signal = "LONG"
                    # SL no suporte do canal ou no meio do canal, TP projetando a altura do canal
                    channel_height = resistance - support
                    suggested_sl = round(resistance - (channel_height * 0.5), 6) # Meio do canal
                    suggested_tp = round(current_price + (channel_height * 1.5), 6)
                else:
                    metric_str += f" (Rompimento LONG distante)"
            elif current_price < support and current_price < ema200:
                if current_price >= support * 0.99:
                    signal = "SHORT"
                    channel_height = resistance - support
                    suggested_sl = round(support + (channel_height * 0.5), 6) # Meio do canal
                    suggested_tp = round(current_price - (channel_height * 1.5), 6)
                else:
                    metric_str += f" (Rompimento SHORT distante)"

        return {
            "asset": self.asset,
            "strategy": "Momentum Breakout",
            "signal": signal,
            "price": current_price,
            "metric": metric_str,
            "suggested_sl": suggested_sl,
            "suggested_tp": suggested_tp,
            "suggested_context": {
                "volatility": "breakout",
                "trend": f"{'bullish' if current_price > ema200 else 'bearish'} (EMA200: {round(ema200, 2)})",
                "metric": metric_str
            }
        }

class TrendFollowingStrategy(BaseStrategy):
    """
    Estratégia para Ouro e Petróleo (4h).
    Lógica: Seguir a tendência macro usando EMA50 e gatilho de entrada via EMA20 (Pullback/Cruzamento).
    """
    def __init__(self, asset: str, sensitivity: float = 0.01):
        super().__init__(asset, "1h")
        self.trend = "NEUTRAL"
        # Menor = mais agressivo -> médias mais rápidas
        self.ema_macro = max(20, int(50 * (sensitivity / 0.01)))
        self.ema_micro = max(10, int(20 * (sensitivity / 0.01)))

    async def analyze(self, current_price: float, historical_data: list) -> Dict[str, Any]:
        signal = "NEUTRAL"
        
        if not historical_data or len(historical_data) < self.ema_macro + 2:
            return {
                "asset": self.asset,
                "strategy": "Trend Following",
                "signal": signal,
                "price": current_price,
                "metric": "Aguardando dados"
            }

        closes = [candle[4] for candle in historical_data]
        ema50 = calculate_ema(closes, self.ema_macro)
        ema20 = calculate_ema(closes, self.ema_micro)
        
        # Último candle fechado (penúltimo da lista)
        last_close = closes[-2]
        
        if ema20 > ema50:
            self.trend = "UP"
        elif ema20 < ema50:
            self.trend = "DOWN"
        
        # Lógica de Pullback / Crossover simplificada para mais entradas
        if self.trend == "UP":
            # Retomando a alta
            if current_price > ema20:
                signal = "LONG"
        elif self.trend == "DOWN":
            # Retomando a baixa
            if current_price < ema20:
                signal = "SHORT"

        return {
            "asset": self.asset,
            "strategy": "Trend Following",
            "signal": signal,
            "price": current_price,
            "metric": f"Tendência: {self.trend} (EMA50: {round(ema50, 2)})"
        }
