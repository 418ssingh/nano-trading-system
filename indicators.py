"""
Technical indicators using Pandas/NumPy
Meets: Pandas/NumPy requirement for strategy builders
"""

import pandas as pd
import numpy as np

class Indicators:
    @staticmethod
    def sma(prices: pd.Series, period: int = 20) -> pd.Series:
        """Simple Moving Average - vectorized"""
        return prices.rolling(window=period).mean()
    
    @staticmethod
    def ema(prices: pd.Series, period: int = 20) -> pd.Series:
        """Exponential Moving Average"""
        return prices.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """RSI using vectorized operations"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def macd(prices: pd.Series, fast=12, slow=26, signal=9) -> pd.DataFrame:
        """MACD indicator"""
        ema_fast = Indicators.ema(prices, fast)
        ema_slow = Indicators.ema(prices, slow)
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        return pd.DataFrame({
            'macd': macd_line,
            'signal': signal_line,
            'histogram': macd_line - signal_line
        })
    
    @staticmethod
    def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
        """Generate buy/sell signals (no loops - vectorized)"""
        df = df.copy()
        df['sma_20'] = Indicators.sma(df['close'], 20)
        df['sma_50'] = Indicators.sma(df['close'], 50)
        df['signal'] = 0
        df.loc[df['sma_20'] > df['sma_50'], 'signal'] = 1  # Buy
        df.loc[df['sma_20'] < df['sma_50'], 'signal'] = -1 # Sell
        return df