"""
Signal Generation Engine
Integrates SMC, Fibonacci, Elliott Wave for high-probability trade signals
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from smart_money_concepts import SmartMoneyConcepts, TrendDirection, MarketStructure
from fibonacci_analysis import FibonacciAnalysis, FibonacciRetracement
from elliott_wave import ElliottWaveAnalyzer, WaveLabel


class SignalType(Enum):
    """Signal types"""
    BUY = "BUY"
    SELL = "SELL"


class SignalQuality(Enum):
    """Signal quality levels"""
    HIGH = "HIGH"       # 5+ confluence factors
    MEDIUM = "MEDIUM"   # 3-4 confluence factors
    LOW = "LOW"         # 2 confluence factors


@dataclass
class TradingSignal:
    """Complete trading signal"""
    timestamp: pd.Timestamp
    index: int
    signal_type: SignalType
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    quality: SignalQuality
    confluence_score: int
    confluence_factors: List[str]
    risk_reward_ratio: float
    notes: str


class SignalGenerator:
    """
    Generate high-probability trading signals using confluence of multiple factors
    """

    def __init__(self, config: Dict):
        """
        Initialize signal generator

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.smc = SmartMoneyConcepts(
            swing_lookback=config.get('SMC_SETTINGS', {}).get('swing_lookback', 5),
            ob_lookback=config.get('SMC_SETTINGS', {}).get('ob_lookback', 20),
            fvg_min_size=config.get('SMC_SETTINGS', {}).get('fvg_min_size', 0.001),
            liquidity_threshold=config.get('SMC_SETTINGS', {}).get('liquidity_threshold', 0.002)
        )

        self.fib_analyzer = FibonacciAnalysis(
            retracement_levels=config.get('FIBONACCI_RETRACEMENT', [0.0, 0.236, 0.382, 0.5, 0.618, 0.705, 0.786, 1.0]),
            extension_levels=config.get('FIBONACCI_EXTENSION', [1.272, 1.414, 1.618, 2.0, 2.618])
        )

        self.wave_analyzer = ElliottWaveAnalyzer(
            min_wave_ratio=config.get('ELLIOTT_WAVE', {}).get('min_wave_ratio', 0.382),
            max_wave_ratio=config.get('ELLIOTT_WAVE', {}).get('max_wave_ratio', 2.618)
        )

        self.min_confluence_score = config.get('SIGNAL_SETTINGS', {}).get('min_confluence_score', 3)
        self.require_htf_alignment = config.get('SIGNAL_SETTINGS', {}).get('require_htf_alignment', True)
        self.require_session_timing = config.get('SIGNAL_SETTINGS', {}).get('require_session_timing', False)

    def generate_signals(self, df: pd.DataFrame, htf_df: Optional[pd.DataFrame] = None) -> List[TradingSignal]:
        """
        Generate trading signals from price data

        Args:
            df: Primary timeframe DataFrame
            htf_df: Higher timeframe DataFrame (optional)

        Returns:
            List of TradingSignal objects
        """
        signals = []

        # Run SMC analysis
        smc_analysis = self.smc.analyze_all(df)

        # Detect swing points for Fibonacci
        swing_highs = smc_analysis['swing_highs']
        swing_lows = smc_analysis['swing_lows']

        # Generate Fibonacci retracements
        fib_retracements = self._generate_fibonacci_retracements(swing_highs, swing_lows, df)

        # Detect Elliott Wave patterns
        swing_points = [(s.index, s.price, s.is_high) for s in swing_highs + swing_lows]
        swing_points.sort(key=lambda x: x[0])

        wave_pattern = self.wave_analyzer.detect_impulse_wave(df, swing_points)

        # Analyze each potential signal point
        for i in range(max(50, self.smc.swing_lookback * 2), len(df) - 1):
            # Skip if we already have a signal at this index
            if any(sig.index == i for sig in signals):
                continue

            # Check for LONG signal
            long_signal = self._check_long_signal(
                df, i, smc_analysis, fib_retracements, wave_pattern, htf_df
            )

            if long_signal:
                signals.append(long_signal)

            # Check for SHORT signal
            short_signal = self._check_short_signal(
                df, i, smc_analysis, fib_retracements, wave_pattern, htf_df
            )

            if short_signal:
                signals.append(short_signal)

        return signals

    def _check_long_signal(self, df: pd.DataFrame, idx: int, smc_analysis: Dict,
                          fib_retracements: List[FibonacciRetracement],
                          wave_pattern, htf_df: Optional[pd.DataFrame]) -> Optional[TradingSignal]:
        """
        Check for LONG signal at given index

        Args:
            df: DataFrame
            idx: Current index
            smc_analysis: SMC analysis results
            fib_retracements: List of Fibonacci retracements
            wave_pattern: Elliott Wave pattern
            htf_df: Higher timeframe DataFrame

        Returns:
            TradingSignal or None
        """
        confluence_factors = []
        current_price = df.iloc[idx]['close']
        timestamp = df.index[idx]

        # 1. Check HTF alignment (bullish trend)
        if htf_df is not None and self.require_htf_alignment:
            htf_current = htf_df[htf_df.index <= timestamp].iloc[-1] if len(htf_df[htf_df.index <= timestamp]) > 0 else None
            if htf_current is None or htf_current['close'] <= htf_current['open']:
                return None  # HTF not bullish
            confluence_factors.append("HTF Bullish Trend")

        # 2. Check for liquidity sweep (sweep low then reverse up)
        liquidity_sweeps = smc_analysis['liquidity_sweeps']
        recent_sweep = next((s for s in liquidity_sweeps
                           if not s.is_high_sweep and s.reversal_confirmed and abs(s.index - idx) <= 5),
                          None)
        if recent_sweep:
            confluence_factors.append("Liquidity Sweep (Low)")

        # 3. Check for Order Block (bullish OB)
        order_blocks = smc_analysis['order_blocks']
        ob_at_price = next((ob for ob in order_blocks
                          if ob.is_bullish and ob.low <= current_price <= ob.high
                          and abs(ob.start_idx - idx) <= 20),
                         None)
        if ob_at_price:
            confluence_factors.append(f"Bullish Order Block (Strength: {ob_at_price.strength:.2f})")

        # 4. Check for Fair Value Gap (FVG)
        fvgs = smc_analysis['fvgs']
        fvg_at_price = next((fvg for fvg in fvgs
                           if fvg.is_bullish and not fvg.filled
                           and fvg.bottom <= current_price <= fvg.top
                           and abs(fvg.end_idx - idx) <= 20),
                          None)
        if fvg_at_price:
            confluence_factors.append("Fair Value Gap (Bullish)")

        # 5. Check Fibonacci - in discount zone or golden pocket
        active_fib = next((fib for fib in fib_retracements
                         if fib.is_bullish and fib.end_idx <= idx <= fib.end_idx + 50),
                        None)

        if active_fib:
            if self.fib_analyzer.is_in_discount(current_price, active_fib):
                confluence_factors.append("Fibonacci Discount Zone")

                golden_pocket = self.fib_analyzer.get_golden_pocket(active_fib)
                if self.fib_analyzer.is_in_golden_pocket(current_price, golden_pocket):
                    confluence_factors.append("Golden Pocket Entry")

        # 6. Check Elliott Wave - Wave 2 or Wave 4 entry
        if wave_pattern and wave_pattern.is_bullish:
            current_wave = self.wave_analyzer.identify_current_wave(wave_pattern, idx)
            if current_wave and current_wave.label in [WaveLabel.WAVE_2, WaveLabel.WAVE_4]:
                confluence_factors.append(f"Elliott Wave {current_wave.label.value} Entry")

        # 7. Check Market Structure (BOS/ChoCh bullish)
        market_structure = smc_analysis['market_structure']
        recent_structure = next((ms for ms in market_structure
                               if ms['direction'] == TrendDirection.BULLISH
                               and abs(ms['index'] - idx) <= 10),
                              None)
        if recent_structure:
            confluence_factors.append(f"{recent_structure['type'].value} - Bullish")

        # 8. Check Volume confirmation
        if idx > 20:
            avg_volume = df['volume'].iloc[idx-20:idx].mean()
            if df.iloc[idx]['volume'] > avg_volume * 1.5:
                confluence_factors.append("Volume Confirmation")

        # 9. Check session timing (optional)
        if self.require_session_timing and 'is_session_open' in df.columns:
            if df.iloc[idx]['is_session_open']:
                confluence_factors.append("Session Open (London/NY)")
            elif self.require_session_timing:
                return None  # Must be during session

        # Calculate confluence score
        confluence_score = len(confluence_factors)

        # Check if meets minimum requirements
        if confluence_score < self.min_confluence_score:
            return None

        # Calculate stop loss and take profits
        atr = df.iloc[idx]['atr'] if 'atr' in df.columns else (df.iloc[idx]['high'] - df.iloc[idx]['low']) * 2

        # Stop loss below recent swing low or liquidity sweep level
        swing_lows_recent = [s.price for s in smc_analysis['swing_lows'] if s.index < idx and idx - s.index <= 20]
        stop_loss = min(swing_lows_recent) if swing_lows_recent else current_price - (atr * 1.5)

        risk = current_price - stop_loss

        # Take profits using Fibonacci extensions
        if active_fib:
            fib_ext = self.fib_analyzer.calculate_extensions(
                active_fib.start_price,
                active_fib.end_price,
                current_price,
                is_bullish=True
            )
            tp1 = fib_ext.levels[0].price  # 127.2%
            tp2 = fib_ext.levels[2].price  # 161.8%
            tp3 = fib_ext.levels[4].price  # 261.8%
        else:
            tp1 = current_price + (risk * 2)
            tp2 = current_price + (risk * 3)
            tp3 = current_price + (risk * 5)

        # Calculate quality
        quality = self._determine_signal_quality(confluence_score)

        # Calculate R:R ratio
        rr_ratio = (tp2 - current_price) / risk if risk > 0 else 0

        return TradingSignal(
            timestamp=timestamp,
            index=idx,
            signal_type=SignalType.BUY,
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit_1=tp1,
            take_profit_2=tp2,
            take_profit_3=tp3,
            quality=quality,
            confluence_score=confluence_score,
            confluence_factors=confluence_factors,
            risk_reward_ratio=rr_ratio,
            notes=f"LONG signal with {confluence_score} confluence factors"
        )

    def _check_short_signal(self, df: pd.DataFrame, idx: int, smc_analysis: Dict,
                           fib_retracements: List[FibonacciRetracement],
                           wave_pattern, htf_df: Optional[pd.DataFrame]) -> Optional[TradingSignal]:
        """
        Check for SHORT signal at given index

        Args:
            df: DataFrame
            idx: Current index
            smc_analysis: SMC analysis results
            fib_retracements: List of Fibonacci retracements
            wave_pattern: Elliott Wave pattern
            htf_df: Higher timeframe DataFrame

        Returns:
            TradingSignal or None
        """
        confluence_factors = []
        current_price = df.iloc[idx]['close']
        timestamp = df.index[idx]

        # 1. Check HTF alignment (bearish trend)
        if htf_df is not None and self.require_htf_alignment:
            htf_current = htf_df[htf_df.index <= timestamp].iloc[-1] if len(htf_df[htf_df.index <= timestamp]) > 0 else None
            if htf_current is None or htf_current['close'] >= htf_current['open']:
                return None  # HTF not bearish
            confluence_factors.append("HTF Bearish Trend")

        # 2. Check for liquidity sweep (sweep high then reverse down)
        liquidity_sweeps = smc_analysis['liquidity_sweeps']
        recent_sweep = next((s for s in liquidity_sweeps
                           if s.is_high_sweep and s.reversal_confirmed and abs(s.index - idx) <= 5),
                          None)
        if recent_sweep:
            confluence_factors.append("Liquidity Sweep (High)")

        # 3. Check for Order Block (bearish OB)
        order_blocks = smc_analysis['order_blocks']
        ob_at_price = next((ob for ob in order_blocks
                          if not ob.is_bullish and ob.low <= current_price <= ob.high
                          and abs(ob.start_idx - idx) <= 20),
                         None)
        if ob_at_price:
            confluence_factors.append(f"Bearish Order Block (Strength: {ob_at_price.strength:.2f})")

        # 4. Check for Fair Value Gap (FVG)
        fvgs = smc_analysis['fvgs']
        fvg_at_price = next((fvg for fvg in fvgs
                           if not fvg.is_bullish and not fvg.filled
                           and fvg.bottom <= current_price <= fvg.top
                           and abs(fvg.end_idx - idx) <= 20),
                          None)
        if fvg_at_price:
            confluence_factors.append("Fair Value Gap (Bearish)")

        # 5. Check Fibonacci - in premium zone or golden pocket
        active_fib = next((fib for fib in fib_retracements
                         if not fib.is_bullish and fib.end_idx <= idx <= fib.end_idx + 50),
                        None)

        if active_fib:
            if self.fib_analyzer.is_in_premium(current_price, active_fib):
                confluence_factors.append("Fibonacci Premium Zone")

                golden_pocket = self.fib_analyzer.get_golden_pocket(active_fib)
                if self.fib_analyzer.is_in_golden_pocket(current_price, golden_pocket):
                    confluence_factors.append("Golden Pocket Entry")

        # 6. Check Elliott Wave
        if wave_pattern and not wave_pattern.is_bullish:
            current_wave = self.wave_analyzer.identify_current_wave(wave_pattern, idx)
            if current_wave and current_wave.label in [WaveLabel.WAVE_2, WaveLabel.WAVE_4]:
                confluence_factors.append(f"Elliott Wave {current_wave.label.value} Entry")

        # 7. Check Market Structure
        market_structure = smc_analysis['market_structure']
        recent_structure = next((ms for ms in market_structure
                               if ms['direction'] == TrendDirection.BEARISH
                               and abs(ms['index'] - idx) <= 10),
                              None)
        if recent_structure:
            confluence_factors.append(f"{recent_structure['type'].value} - Bearish")

        # 8. Check Volume confirmation
        if idx > 20:
            avg_volume = df['volume'].iloc[idx-20:idx].mean()
            if df.iloc[idx]['volume'] > avg_volume * 1.5:
                confluence_factors.append("Volume Confirmation")

        # 9. Check session timing
        if self.require_session_timing and 'is_session_open' in df.columns:
            if df.iloc[idx]['is_session_open']:
                confluence_factors.append("Session Open (London/NY)")
            elif self.require_session_timing:
                return None

        confluence_score = len(confluence_factors)

        if confluence_score < self.min_confluence_score:
            return None

        # Calculate stop loss and take profits
        atr = df.iloc[idx]['atr'] if 'atr' in df.columns else (df.iloc[idx]['high'] - df.iloc[idx]['low']) * 2

        swing_highs_recent = [s.price for s in smc_analysis['swing_highs'] if s.index < idx and idx - s.index <= 20]
        stop_loss = max(swing_highs_recent) if swing_highs_recent else current_price + (atr * 1.5)

        risk = stop_loss - current_price

        if active_fib:
            fib_ext = self.fib_analyzer.calculate_extensions(
                active_fib.start_price,
                active_fib.end_price,
                current_price,
                is_bullish=False
            )
            tp1 = fib_ext.levels[0].price
            tp2 = fib_ext.levels[2].price
            tp3 = fib_ext.levels[4].price
        else:
            tp1 = current_price - (risk * 2)
            tp2 = current_price - (risk * 3)
            tp3 = current_price - (risk * 5)

        quality = self._determine_signal_quality(confluence_score)
        rr_ratio = (current_price - tp2) / risk if risk > 0 else 0

        return TradingSignal(
            timestamp=timestamp,
            index=idx,
            signal_type=SignalType.SELL,
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit_1=tp1,
            take_profit_2=tp2,
            take_profit_3=tp3,
            quality=quality,
            confluence_score=confluence_score,
            confluence_factors=confluence_factors,
            risk_reward_ratio=rr_ratio,
            notes=f"SHORT signal with {confluence_score} confluence factors"
        )

    def _generate_fibonacci_retracements(self, swing_highs, swing_lows, df) -> List[FibonacciRetracement]:
        """Generate Fibonacci retracements from swing points"""
        retracements = []

        # Bullish retracements (low to high)
        for i in range(len(swing_lows) - 1):
            for j in range(i + 1, len(swing_lows)):
                low = swing_lows[i]
                # Find high between these lows
                highs_between = [h for h in swing_highs if low.index < h.index < swing_lows[j].index]
                if highs_between:
                    high = max(highs_between, key=lambda h: h.price)
                    fib = self.fib_analyzer.calculate_retracement(
                        low.price, high.price, low.index, high.index
                    )
                    retracements.append(fib)

        # Bearish retracements (high to low)
        for i in range(len(swing_highs) - 1):
            for j in range(i + 1, len(swing_highs)):
                high = swing_highs[i]
                lows_between = [l for l in swing_lows if high.index < l.index < swing_highs[j].index]
                if lows_between:
                    low = min(lows_between, key=lambda l: l.price)
                    fib = self.fib_analyzer.calculate_retracement(
                        high.price, low.price, high.index, low.index
                    )
                    retracements.append(fib)

        return retracements

    def _determine_signal_quality(self, confluence_score: int) -> SignalQuality:
        """Determine signal quality based on confluence score"""
        thresholds = self.config.get('SIGNAL_SETTINGS', {}).get('signal_quality_thresholds', {
            'high': 5,
            'medium': 3,
            'low': 2
        })

        if confluence_score >= thresholds['high']:
            return SignalQuality.HIGH
        elif confluence_score >= thresholds['medium']:
            return SignalQuality.MEDIUM
        else:
            return SignalQuality.LOW
