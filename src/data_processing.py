"""
Data Processing and Feature Engineering
Handles data acquisition, processing, and session timing
"""

import pandas as pd
import numpy as np
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import time
import logging


class DataProcessor:
    """
    Handle data acquisition and processing for BTC/USDT
    """

    def __init__(self, symbol: str = 'BTCUSDT', base_url: str = 'https://api.binance.com'):
        """
        Initialize data processor

        Args:
            symbol: Trading pair symbol
            base_url: Binance API base URL
        """
        self.symbol = symbol
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)

    def fetch_historical_data(self, interval: str = '15m', limit: int = 500) -> pd.DataFrame:
        """
        Fetch historical OHLCV data from Binance

        Args:
            interval: Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Number of candles to fetch (max 1000)

        Returns:
            DataFrame with OHLCV data
        """
        endpoint = f"{self.base_url}/api/v3/klines"

        params = {
            'symbol': self.symbol,
            'interval': interval,
            'limit': min(limit, 1000)
        }

        try:
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Convert to DataFrame
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])

            # Convert types
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')

            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)

            df['trades'] = df['trades'].astype(int)

            # Set timestamp as index
            df.set_index('timestamp', inplace=True)

            self.logger.info(f"Fetched {len(df)} candles for {self.symbol} ({interval})")

            return df[['open', 'high', 'low', 'close', 'volume', 'trades']]

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching data: {e}")
            return pd.DataFrame()

    def fetch_multi_timeframe_data(self, timeframes: List[str], limit: int = 500) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple timeframes

        Args:
            timeframes: List of timeframe strings
            limit: Number of candles per timeframe

        Returns:
            Dictionary of timeframe -> DataFrame
        """
        data = {}

        for tf in timeframes:
            df = self.fetch_historical_data(interval=tf, limit=limit)
            if not df.empty:
                data[tf] = df
                time.sleep(0.1)  # Rate limiting

        return data

    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Average True Range (ATR)

        Args:
            df: DataFrame with OHLC data
            period: ATR period

        Returns:
            Series with ATR values
        """
        high = df['high']
        low = df['low']
        close = df['close']

        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        return atr

    def calculate_volume_profile(self, df: pd.DataFrame, bins: int = 50) -> Dict:
        """
        Calculate volume profile for price levels

        Args:
            df: DataFrame with OHLCV data
            bins: Number of price bins

        Returns:
            Dictionary with volume profile data
        """
        price_range = df['high'].max() - df['low'].min()
        bin_size = price_range / bins

        # Create price bins
        min_price = df['low'].min()
        price_bins = [min_price + (i * bin_size) for i in range(bins + 1)]

        # Accumulate volume in each bin
        volume_at_price = np.zeros(bins)

        for idx, row in df.iterrows():
            # Distribute volume across bins touched by this candle
            low_bin = int((row['low'] - min_price) / bin_size)
            high_bin = int((row['high'] - min_price) / bin_size)

            low_bin = max(0, min(low_bin, bins - 1))
            high_bin = max(0, min(high_bin, bins - 1))

            # Distribute volume evenly across bins
            bins_touched = high_bin - low_bin + 1
            volume_per_bin = row['volume'] / bins_touched

            for b in range(low_bin, high_bin + 1):
                if b < bins:
                    volume_at_price[b] += volume_per_bin

        # Find POC (Point of Control) - highest volume level
        poc_bin = np.argmax(volume_at_price)
        poc_price = price_bins[poc_bin] + (bin_size / 2)

        # Find Value Area (70% of volume)
        total_volume = volume_at_price.sum()
        va_volume_target = total_volume * 0.7

        # Start from POC and expand
        va_bins = [poc_bin]
        va_volume = volume_at_price[poc_bin]

        lower_bin = poc_bin - 1
        upper_bin = poc_bin + 1

        while va_volume < va_volume_target and (lower_bin >= 0 or upper_bin < bins):
            lower_vol = volume_at_price[lower_bin] if lower_bin >= 0 else 0
            upper_vol = volume_at_price[upper_bin] if upper_bin < bins else 0

            if lower_vol > upper_vol and lower_bin >= 0:
                va_bins.append(lower_bin)
                va_volume += lower_vol
                lower_bin -= 1
            elif upper_bin < bins:
                va_bins.append(upper_bin)
                va_volume += upper_vol
                upper_bin += 1
            else:
                break

        va_low = price_bins[min(va_bins)]
        va_high = price_bins[max(va_bins) + 1]

        return {
            'poc_price': poc_price,
            'value_area_high': va_high,
            'value_area_low': va_low,
            'price_bins': price_bins,
            'volume_at_price': volume_at_price
        }

    def detect_session_timing(self, timestamp: pd.Timestamp, session_config: Dict) -> Dict:
        """
        Detect trading session timing (London/NY Opens)

        Args:
            timestamp: Current timestamp
            session_config: Session configuration from config

        Returns:
            Dictionary with session info
        """
        # Convert to UTC
        utc_time = timestamp.tz_localize('UTC') if timestamp.tz is None else timestamp.tz_convert('UTC')

        hour = utc_time.hour
        minute = utc_time.minute

        # Check London Open (8:00 UTC)
        london_open = session_config.get('london_open', {'hour': 8, 'minute': 0})
        london_window = session_config.get('session_window_minutes', 120)

        london_open_time = utc_time.replace(hour=london_open['hour'], minute=london_open['minute'], second=0)
        is_london_open = abs((utc_time - london_open_time).total_seconds() / 60) <= london_window

        # Check NY Open (13:30 UTC)
        ny_open = session_config.get('ny_open', {'hour': 13, 'minute': 30})

        ny_open_time = utc_time.replace(hour=ny_open['hour'], minute=ny_open['minute'], second=0)
        is_ny_open = abs((utc_time - ny_open_time).total_seconds() / 60) <= london_window

        return {
            'is_london_open': is_london_open,
            'is_ny_open': is_ny_open,
            'is_session_open': is_london_open or is_ny_open,
            'current_hour_utc': hour,
            'current_minute_utc': minute
        }

    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add technical indicators to DataFrame

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with added indicators
        """
        df = df.copy()

        # ATR
        df['atr'] = self.calculate_atr(df, period=14)

        # Volume indicators
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']

        # Price indicators
        df['hl2'] = (df['high'] + df['low']) / 2
        df['hlc3'] = (df['high'] + df['low'] + df['close']) / 3
        df['ohlc4'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4

        # Candle patterns
        df['body'] = abs(df['close'] - df['open'])
        df['upper_wick'] = df['high'] - df[['open', 'close']].max(axis=1)
        df['lower_wick'] = df[['open', 'close']].min(axis=1) - df['low']
        df['is_bullish'] = (df['close'] > df['open']).astype(int)

        # Range
        df['range'] = df['high'] - df['low']
        df['range_ma'] = df['range'].rolling(window=20).mean()

        return df

    def align_timeframes(self, ltf_df: pd.DataFrame, htf_df: pd.DataFrame) -> pd.DataFrame:
        """
        Align lower timeframe with higher timeframe data

        Args:
            ltf_df: Lower timeframe DataFrame
            htf_df: Higher timeframe DataFrame

        Returns:
            LTF DataFrame with HTF indicators
        """
        ltf_df = ltf_df.copy()

        # For each LTF candle, find corresponding HTF candle
        ltf_df['htf_trend'] = 0

        for idx in ltf_df.index:
            # Find HTF candle that contains this LTF timestamp
            htf_candle = htf_df[htf_df.index <= idx].iloc[-1] if len(htf_df[htf_df.index <= idx]) > 0 else None

            if htf_candle is not None:
                # Determine HTF trend
                if htf_candle['close'] > htf_candle['open']:
                    ltf_df.loc[idx, 'htf_trend'] = 1  # Bullish
                else:
                    ltf_df.loc[idx, 'htf_trend'] = -1  # Bearish

        return ltf_df

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and validate data

        Args:
            df: DataFrame to clean

        Returns:
            Cleaned DataFrame
        """
        df = df.copy()

        # Remove duplicates
        df = df[~df.index.duplicated(keep='first')]

        # Sort by index
        df = df.sort_index()

        # Remove any NaN in OHLCV
        df = df.dropna(subset=['open', 'high', 'low', 'close', 'volume'])

        # Validate OHLC relationships
        df = df[(df['high'] >= df['low']) &
                (df['high'] >= df['open']) &
                (df['high'] >= df['close']) &
                (df['low'] <= df['open']) &
                (df['low'] <= df['close'])]

        return df

    def resample_data(self, df: pd.DataFrame, target_timeframe: str) -> pd.DataFrame:
        """
        Resample data to different timeframe

        Args:
            df: DataFrame with OHLCV data
            target_timeframe: Target timeframe (e.g., '1h', '4h')

        Returns:
            Resampled DataFrame
        """
        resampled = df.resample(target_timeframe).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum',
            'trades': 'sum'
        }).dropna()

        return resampled

    def get_latest_price(self) -> Optional[float]:
        """
        Get latest price from Binance

        Returns:
            Current price or None
        """
        endpoint = f"{self.base_url}/api/v3/ticker/price"

        params = {'symbol': self.symbol}

        try:
            response = requests.get(endpoint, params=params, timeout=5)
            response.raise_for_status()

            data = response.json()
            return float(data['price'])

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching latest price: {e}")
            return None

    def prepare_features(self, df: pd.DataFrame, session_config: Dict) -> pd.DataFrame:
        """
        Prepare all features for analysis

        Args:
            df: DataFrame with OHLCV data
            session_config: Session timing configuration

        Returns:
            DataFrame with all features
        """
        # Add technical indicators
        df = self.add_technical_indicators(df)

        # Add session timing
        df['is_session_open'] = df.apply(
            lambda row: self.detect_session_timing(row.name, session_config)['is_session_open'],
            axis=1
        )

        # Clean data
        df = self.clean_data(df)

        return df
