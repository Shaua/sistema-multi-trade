from typing import Dict, Any
from .indicators import calculate_sma, calculate_donchian_channel, calculate_ema
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
        super().__init__(asset, "15m")
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
        self.moving_average = calculate_sma(closes, self.ma_period)
        
        if self.moving_average == 0.0:
            # Fallback
            self.moving_average = current_price

        distance = (current_price - self.moving_average) / self.moving_average

        signal = "NEUTRAL"
        if distance < -self.deviation_threshold:
            signal = "LONG" # Preço muito abaixo da média -> Comprar (Reversão para cima)
        elif distance > self.deviation_threshold:
            signal = "SHORT" # Preço muito acima da média -> Vender (Reversão para baixo)

        return {
            "asset": self.asset,
            "strategy": "Mean Reversion",
            "signal": signal,
            "price": current_price,
            "metric": f"Distância Média: {round(distance * 100, 2)}%"
        }

class MomentumBreakoutStrategy(BaseStrategy):
    """
    Estratégia para Bitcoin (1h).
    Lógica real: Calcula a máxima e mínima dos últimos 20 candles (Canal de Donchian simplificado).
    Se o preço atual romper a máxima, com volume acima da média, envia sinal LONG.
    Se perder a mínima, envia SHORT.
    """
    def __init__(self, asset: str, sensitivity: float = 0.01):
        super().__init__(asset, "5m")
        # Menor sensibilidade (0.005) -> mais agressivo -> menor lookback
        # Base = 20 para 0.01
        self.lookback_period = max(5, int(20 * (sensitivity / 0.01)))
        self.sensitivity = sensitivity

    async def analyze(self, current_price: float, historical_data: list) -> Dict[str, Any]:
        signal = "NEUTRAL"
        resistance = 0.0
        support = 0.0
        metric_str = "Aguardando dados"

        # historical_data format: [ [ts, open, high, low, close, vol], ... ]
        if historical_data and len(historical_data) >= self.lookback_period + 1:
            # Pegar todos exceto o último candle (que ainda não fechou) para o cálculo do canal
            highs = [candle[2] for candle in historical_data[:-1]]
            lows = [candle[3] for candle in historical_data[:-1]]
            
            resistance, support = calculate_donchian_channel(highs, lows, self.lookback_period)
            
            # Precisamos dos volumes dos ultimos N candles, incluindo o ultimo fechado
            recent_candles = historical_data[-(self.lookback_period+1):]
            volumes = [candle[5] for candle in recent_candles]
            
            avg_volume = sum(volumes[:-1]) / len(volumes[:-1]) if len(volumes) > 1 else 0
            last_closed_volume = historical_data[-2][5] if len(historical_data) > 1 else 0
            
            metric_str = f"Res: {round(resistance, 2)} / Sup: {round(support, 2)}"
            # Condição de rompimento com Filtro de Distância / Pullback
            # O preço precisa ter rompido, mas não pode estar distante mais de 1.0% do rompimento para evitar comprar topo extremo
            if current_price > resistance:
                if current_price <= resistance * 1.01:
                    signal = "LONG"
                else:
                    metric_str += f" (Rompimento LONG distante)"
            elif current_price < support:
                if current_price >= support * 0.99:
                    signal = "SHORT"
                else:
                    metric_str += f" (Rompimento SHORT distante)"

        return {
            "asset": self.asset,
            "strategy": "Momentum Breakout",
            "signal": signal,
            "price": current_price,
            "metric": metric_str
        }

class TrendFollowingStrategy(BaseStrategy):
    """
    Estratégia para Ouro e Petróleo (4h).
    Lógica: Seguir a tendência macro usando EMA50 e gatilho de entrada via EMA20 (Pullback/Cruzamento).
    """
    def __init__(self, asset: str, sensitivity: float = 0.01):
        super().__init__(asset, "15m")
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
