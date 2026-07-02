import pandas as pd
from typing import List, Tuple

def calculate_sma(closes: List[float], period: int) -> float:
    """Calcula a Média Móvel Simples (SMA)."""
    if len(closes) < period:
        return 0.0
    return sum(closes[-period:]) / period

def calculate_ema(closes: List[float], period: int) -> float:
    """Calcula a Média Móvel Exponencial (EMA)."""
    if len(closes) < period:
        return 0.0
    s = pd.Series(closes)
    ema = s.ewm(span=period, adjust=False).mean()
    return float(ema.iloc[-1])

def calculate_donchian_channel(highs: List[float], lows: List[float], period: int) -> Tuple[float, float]:
    """Calcula o Canal de Donchian (Maior Alta, Menor Baixa)."""
    if len(highs) < period or len(lows) < period:
        return 0.0, 0.0
    
    recent_highs = highs[-period:]
    recent_lows = lows[-period:]
    
    return max(recent_highs), min(recent_lows)
