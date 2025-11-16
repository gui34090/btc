"""
Smart Money Concepts (SMC) Implementation
Includes: Liquidity Sweep, FVG, Order Blocks, Market Structure (BOS/ChoCh)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class TrendDirection(Enum):
    """Market trend direction"""
    BULLISH = 1
    BEARISH = -1
    NEUTRAL = 0


class MarketStructure(Enum):
    """Market structure events"""
    BOS = "Break of Structure"      # Continuation
    CHOCH = "Change of Character"   # Reversal


@dataclass
class SwingPoint:
    """Swing high or low point"""
    index: int
    price: float
    time: pd.Timestamp
    is_high: bool  # True for swing high, False for swing low


@dataclass
class OrderBlock:
    """Order Block structure"""
    start_idx: int
    end_idx: int
    high: float
    low: float
    is_bullish: bool
    volume: float
    strength: float  # 0-1 score


@dataclass
class FairValueGap:
    """Fair Value Gap structure"""
    start_idx: int
    end_idx: int
    top: float
    bottom: float
    is_bullish: bool
    size: float
    filled: bool = False


@dataclass
class LiquiditySweep:
    """Liquidity sweep event"""
    index: int
    price: float
    swept_level: float
    is_high_sweep: bool  # True if swept high, False if swept low
    reversal_confirmed: bool


class SmartMoneyConcepts:
    """
    Comprehensive Smart Money Concepts implementation
    """

    def __init__(self, swing_lookback: int = 5, ob_lookback: int = 20,
                 fvg_min_size: float = 0.001, liquidity_threshold: float = 0.002):
        self.swing_lookback = swing_lookback
        self.ob_lookback = ob_lookback
        self.fvg_min_size = fvg_min_size
        self.liquidity_threshold = liquidity_threshold

    def detect_swing_points(self, df: pd.DataFrame) -> Tuple[List[SwingPoint], List[SwingPoint]]:
        """
        Detect swing highs and swing lows

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Tuple of (swing_highs, swing_lows)
        """
        swing_highs = []
        swing_lows = []

        lookback = self.swing_lookback

        for i in range(lookback, len(df) - lookback):
            # Check for swing high
            is_swing_high = True
            current_high = df.iloc[i]['high']

            for j in range(1, lookback + 1):
                if df.iloc[i - j]['high'] >= current_high or df.iloc[i + j]['high'] >= current_high:
                    is_swing_high = False
                    break

            if is_swing_high:
                swing_highs.append(SwingPoint(
                    index=i,
                    price=current_high,
                    time=df.iloc[i]['timestamp'] if 'timestamp' in df.columns else df.index[i],
                    is_high=True
                ))

            # Check for swing low
            is_swing_low = True
            current_low = df.iloc[i]['low']

            for j in range(1, lookback + 1):
                if df.iloc[i - j]['low'] <= current_low or df.iloc[i + j]['low'] <= current_low:
                    is_swing_low = False
                    break

            if is_swing_low:
                swing_lows.append(SwingPoint(
                    index=i,
                    price=current_low,
                    time=df.iloc[i]['timestamp'] if 'timestamp' in df.columns else df.index[i],
                    is_high=False
                ))

        return swing_highs, swing_lows

    def detect_market_structure(self, df: pd.DataFrame, swing_highs: List[SwingPoint],
                                swing_lows: List[SwingPoint]) -> List[Dict]:
        """
        Detect Break of Structure (BOS) and Change of Character (ChoCh)

        Args:
            df: DataFrame with OHLCV data
            swing_highs: List of swing high points
            swing_lows: List of swing low points

        Returns:
            List of market structure events
        """
        events = []
        trend = TrendDirection.NEUTRAL

        all_swings = sorted(swing_highs + swing_lows, key=lambda x: x.index)

        for i in range(1, len(all_swings)):
            prev_swing = all_swings[i - 1]
            curr_swing = all_swings[i]

            # Bullish BOS: Break above previous swing high in uptrend
            if curr_swing.is_high and not prev_swing.is_high:
                if i >= 2:
                    prev_high = next((s for s in reversed(all_swings[:i]) if s.is_high), None)
                    if prev_high and curr_swing.price > prev_high.price:
                        if trend == TrendDirection.BULLISH:
                            events.append({
                                'type': MarketStructure.BOS,
                                'index': curr_swing.index,
                                'price': curr_swing.price,
                                'direction': TrendDirection.BULLISH
                            })
                        else:
                            events.append({
                                'type': MarketStructure.CHOCH,
                                'index': curr_swing.index,
                                'price': curr_swing.price,
                                'direction': TrendDirection.BULLISH
                            })
                            trend = TrendDirection.BULLISH

            # Bearish BOS: Break below previous swing low in downtrend
            elif not curr_swing.is_high and prev_swing.is_high:
                if i >= 2:
                    prev_low = next((s for s in reversed(all_swings[:i]) if not s.is_high), None)
                    if prev_low and curr_swing.price < prev_low.price:
                        if trend == TrendDirection.BEARISH:
                            events.append({
                                'type': MarketStructure.BOS,
                                'index': curr_swing.index,
                                'price': curr_swing.price,
                                'direction': TrendDirection.BEARISH
                            })
                        else:
                            events.append({
                                'type': MarketStructure.CHOCH,
                                'index': curr_swing.index,
                                'price': curr_swing.price,
                                'direction': TrendDirection.BEARISH
                            })
                            trend = TrendDirection.BEARISH

        return events

    def detect_order_blocks(self, df: pd.DataFrame) -> List[OrderBlock]:
        """
        Detect Order Blocks (OB)
        An OB is the last opposing candle before a strong move

        Args:
            df: DataFrame with OHLCV data

        Returns:
            List of Order Blocks
        """
        order_blocks = []

        for i in range(self.ob_lookback, len(df) - 1):
            # Bullish Order Block: Last down candle before strong up move
            if df.iloc[i]['close'] < df.iloc[i]['open']:  # Bearish candle
                # Check for strong bullish move after
                next_candles_bullish = 0
                total_move = 0

                for j in range(i + 1, min(i + 6, len(df))):
                    if df.iloc[j]['close'] > df.iloc[j]['open']:
                        next_candles_bullish += 1
                        total_move += df.iloc[j]['close'] - df.iloc[j]['open']

                avg_volume = df['volume'].iloc[i-10:i].mean()
                volume_surge = df.iloc[i+1]['volume'] > avg_volume * 1.5 if i+1 < len(df) else False

                if next_candles_bullish >= 3 and volume_surge:
                    strength = min(1.0, (total_move / df.iloc[i]['close']) * 100)
                    order_blocks.append(OrderBlock(
                        start_idx=i,
                        end_idx=i,
                        high=df.iloc[i]['high'],
                        low=df.iloc[i]['low'],
                        is_bullish=True,
                        volume=df.iloc[i+1]['volume'] if i+1 < len(df) else df.iloc[i]['volume'],
                        strength=strength
                    ))

            # Bearish Order Block: Last up candle before strong down move
            elif df.iloc[i]['close'] > df.iloc[i]['open']:  # Bullish candle
                next_candles_bearish = 0
                total_move = 0

                for j in range(i + 1, min(i + 6, len(df))):
                    if df.iloc[j]['close'] < df.iloc[j]['open']:
                        next_candles_bearish += 1
                        total_move += df.iloc[j]['open'] - df.iloc[j]['close']

                avg_volume = df['volume'].iloc[i-10:i].mean()
                volume_surge = df.iloc[i+1]['volume'] > avg_volume * 1.5 if i+1 < len(df) else False

                if next_candles_bearish >= 3 and volume_surge:
                    strength = min(1.0, (total_move / df.iloc[i]['close']) * 100)
                    order_blocks.append(OrderBlock(
                        start_idx=i,
                        end_idx=i,
                        high=df.iloc[i]['high'],
                        low=df.iloc[i]['low'],
                        is_bullish=False,
                        volume=df.iloc[i+1]['volume'] if i+1 < len(df) else df.iloc[i]['volume'],
                        strength=strength
                    ))

        return order_blocks

    def detect_fvg(self, df: pd.DataFrame) -> List[FairValueGap]:
        """
        Detect Fair Value Gaps (FVG)
        FVG occurs when there's a gap between candle 1's high/low and candle 3's low/high

        Args:
            df: DataFrame with OHLCV data

        Returns:
            List of Fair Value Gaps
        """
        fvgs = []

        for i in range(2, len(df)):
            # Bullish FVG: Gap between candle[i-2].high and candle[i].low
            if df.iloc[i-2]['high'] < df.iloc[i]['low']:
                gap_size = (df.iloc[i]['low'] - df.iloc[i-2]['high']) / df.iloc[i]['close']

                if gap_size >= self.fvg_min_size:
                    fvgs.append(FairValueGap(
                        start_idx=i-2,
                        end_idx=i,
                        top=df.iloc[i]['low'],
                        bottom=df.iloc[i-2]['high'],
                        is_bullish=True,
                        size=gap_size,
                        filled=False
                    ))

            # Bearish FVG: Gap between candle[i-2].low and candle[i].high
            elif df.iloc[i-2]['low'] > df.iloc[i]['high']:
                gap_size = (df.iloc[i-2]['low'] - df.iloc[i]['high']) / df.iloc[i]['close']

                if gap_size >= self.fvg_min_size:
                    fvgs.append(FairValueGap(
                        start_idx=i-2,
                        end_idx=i,
                        top=df.iloc[i-2]['low'],
                        bottom=df.iloc[i]['high'],
                        is_bullish=False,
                        size=gap_size,
                        filled=False
                    ))

        return fvgs

    def detect_liquidity_sweeps(self, df: pd.DataFrame, swing_highs: List[SwingPoint],
                                swing_lows: List[SwingPoint]) -> List[LiquiditySweep]:
        """
        Detect liquidity sweeps (stop hunts)

        Args:
            df: DataFrame with OHLCV data
            swing_highs: List of swing high points
            swing_lows: List of swing low points

        Returns:
            List of liquidity sweep events
        """
        sweeps = []

        # Check for high sweeps (taking out resistance/buy stops)
        for swing in swing_highs:
            # Look for price action after the swing high
            for i in range(swing.index + 1, min(swing.index + 20, len(df))):
                # Price swept above the swing high
                if df.iloc[i]['high'] > swing.price * (1 + self.liquidity_threshold):
                    # Check for reversal (close back below)
                    reversal = df.iloc[i]['close'] < swing.price

                    # Additional confirmation: next few candles move down
                    if reversal and i + 3 < len(df):
                        moves_down = sum(1 for j in range(i+1, min(i+4, len(df)))
                                       if df.iloc[j]['close'] < df.iloc[j-1]['close'])
                        reversal_confirmed = moves_down >= 2
                    else:
                        reversal_confirmed = reversal

                    sweeps.append(LiquiditySweep(
                        index=i,
                        price=df.iloc[i]['high'],
                        swept_level=swing.price,
                        is_high_sweep=True,
                        reversal_confirmed=reversal_confirmed
                    ))
                    break

        # Check for low sweeps (taking out support/sell stops)
        for swing in swing_lows:
            for i in range(swing.index + 1, min(swing.index + 20, len(df))):
                if df.iloc[i]['low'] < swing.price * (1 - self.liquidity_threshold):
                    reversal = df.iloc[i]['close'] > swing.price

                    if reversal and i + 3 < len(df):
                        moves_up = sum(1 for j in range(i+1, min(i+4, len(df)))
                                     if df.iloc[j]['close'] > df.iloc[j-1]['close'])
                        reversal_confirmed = moves_up >= 2
                    else:
                        reversal_confirmed = reversal

                    sweeps.append(LiquiditySweep(
                        index=i,
                        price=df.iloc[i]['low'],
                        swept_level=swing.price,
                        is_high_sweep=False,
                        reversal_confirmed=reversal_confirmed
                    ))
                    break

        return sweeps

    def analyze_all(self, df: pd.DataFrame) -> Dict:
        """
        Perform complete Smart Money Concepts analysis

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Dictionary containing all SMC components
        """
        # Detect all components
        swing_highs, swing_lows = self.detect_swing_points(df)
        market_structure = self.detect_market_structure(df, swing_highs, swing_lows)
        order_blocks = self.detect_order_blocks(df)
        fvgs = self.detect_fvg(df)
        liquidity_sweeps = self.detect_liquidity_sweeps(df, swing_highs, swing_lows)

        return {
            'swing_highs': swing_highs,
            'swing_lows': swing_lows,
            'market_structure': market_structure,
            'order_blocks': order_blocks,
            'fvgs': fvgs,
            'liquidity_sweeps': liquidity_sweeps
        }
