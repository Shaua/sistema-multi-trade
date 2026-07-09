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

def calculate_rsi(closes: List[float], period: int = 14) -> float:
    """Calcula o Índice de Força Relativa (RSI)."""
    if len(closes) < period + 1:
        return 50.0
    s = pd.Series(closes)
    delta = s.diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1])

def calculate_atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
    """Calcula o Average True Range (ATR)."""
    if len(closes) < period + 1:
        return 0.0
    df = pd.DataFrame({'high': highs, 'low': lows, 'close': closes})
    df['prev_close'] = df['close'].shift(1)
    df['tr1'] = df['high'] - df['low']
    df['tr2'] = (df['high'] - df['prev_close']).abs()
    df['tr3'] = (df['low'] - df['prev_close']).abs()
    df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
    atr = df['tr'].rolling(window=period).mean()
    atr = atr.fillna(0)
    return float(atr.iloc[-1])

def calculate_adx(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
    """Calcula o Average Directional Index (ADX)."""
    if len(closes) < period * 2:
        return 0.0
    
    df = pd.DataFrame({'high': highs, 'low': lows, 'close': closes})
    df['prev_close'] = df['close'].shift(1)
    
    df['tr1'] = df['high'] - df['low']
    df['tr2'] = (df['high'] - df['prev_close']).abs()
    df['tr3'] = (df['low'] - df['prev_close']).abs()
    df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
    
    df['up_move'] = df['high'] - df['high'].shift(1)
    df['down_move'] = df['low'].shift(1) - df['low']
    
    df['plus_dm'] = 0.0
    df.loc[(df['up_move'] > df['down_move']) & (df['up_move'] > 0), 'plus_dm'] = df['up_move']
    
    df['minus_dm'] = 0.0
    df.loc[(df['down_move'] > df['up_move']) & (df['down_move'] > 0), 'minus_dm'] = df['down_move']
    
    df['atr'] = df['tr'].ewm(alpha=1/period, adjust=False).mean()
    
    df['plus_di'] = 100 * (df['plus_dm'].ewm(alpha=1/period, adjust=False).mean() / df['atr'])
    df['minus_di'] = 100 * (df['minus_dm'].ewm(alpha=1/period, adjust=False).mean() / df['atr'])
    
    df['dx'] = 100 * (abs(df['plus_di'] - df['minus_di']) / (df['plus_di'] + df['minus_di']))
    df['adx'] = df['dx'].ewm(alpha=1/period, adjust=False).mean()
    
    df = df.fillna(0)
    return float(df['adx'].iloc[-1])
