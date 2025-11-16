"""
Fibonacci Analysis Implementation
Includes: Retracement, Extensions, Premium/Discount Arrays, Golden Pocket, Time Zones
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import timedelta


@dataclass
class FibonacciLevel:
    """Fibonacci level with price and percentage"""
    level: float      # 0.0 to 1.0 (or extension > 1.0)
    price: float
    label: str
    zone_type: str    # 'discount', 'equilibrium', 'premium', 'extension'


@dataclass
class FibonacciRetracement:
    """Complete Fibonacci retracement structure"""
    start_price: float
    end_price: float
    start_idx: int
    end_idx: int
    is_bullish: bool
    levels: List[FibonacciLevel]


@dataclass
class FibonacciExtension:
    """Fibonacci extension structure for profit targets"""
    base_price: float
    entry_price: float
    levels: List[FibonacciLevel]
    is_bullish: bool


@dataclass
class GoldenPocket:
    """The Golden Pocket zone (61.8% - 70.5%)"""
    top: float
    bottom: float
    mid: float  # 70.5% level
    zone_type: str  # 'buy' or 'sell'


class FibonacciAnalysis:
    """
    Comprehensive Fibonacci analysis for trading
    """

    def __init__(self, retracement_levels: List[float] = None,
                 extension_levels: List[float] = None):
        """
        Initialize Fibonacci analysis

        Args:
            retracement_levels: List of Fibonacci retracement levels
            extension_levels: List of Fibonacci extension levels
        """
        self.retracement_levels = retracement_levels or [0.0, 0.236, 0.382, 0.5, 0.618, 0.705, 0.786, 1.0]
        self.extension_levels = extension_levels or [1.272, 1.414, 1.618, 2.0, 2.618]

        # ICT Premium/Discount classification
        self.discount_zone = [0.0, 0.236, 0.382]
        self.equilibrium = [0.5]
        self.premium_zone = [0.618, 0.705, 0.786, 1.0]
        self.ote_zone = [0.618, 0.705, 0.786]  # Optimal Trade Entry

    def calculate_retracement(self, start_price: float, end_price: float,
                             start_idx: int, end_idx: int) -> FibonacciRetracement:
        """
        Calculate Fibonacci retracement levels

        Args:
            start_price: Starting price (swing low for bullish, swing high for bearish)
            end_price: Ending price (swing high for bullish, swing low for bearish)
            start_idx: Starting index
            end_idx: Ending index

        Returns:
            FibonacciRetracement object
        """
        is_bullish = end_price > start_price
        price_range = abs(end_price - start_price)

        levels = []

        for level in self.retracement_levels:
            if is_bullish:
                # For bullish moves, retracement levels go down from the high
                price = end_price - (price_range * level)
            else:
                # For bearish moves, retracement levels go up from the low
                price = end_price + (price_range * level)

            # Classify the zone
            if level in self.discount_zone:
                zone_type = 'discount'
            elif level in self.equilibrium:
                zone_type = 'equilibrium'
            elif level in self.premium_zone:
                zone_type = 'premium'
            else:
                zone_type = 'other'

            label = self._get_level_label(level)

            levels.append(FibonacciLevel(
                level=level,
                price=price,
                label=label,
                zone_type=zone_type
            ))

        return FibonacciRetracement(
            start_price=start_price,
            end_price=end_price,
            start_idx=start_idx,
            end_idx=end_idx,
            is_bullish=is_bullish,
            levels=levels
        )

    def calculate_extensions(self, base_price: float, peak_price: float,
                            entry_price: float, is_bullish: bool) -> FibonacciExtension:
        """
        Calculate Fibonacci extension levels for profit targets

        Args:
            base_price: Base of the move (swing low for bullish)
            peak_price: Peak of the move (swing high for bullish)
            entry_price: Entry price (retracement level)
            is_bullish: True for bullish, False for bearish

        Returns:
            FibonacciExtension object
        """
        base_range = abs(peak_price - base_price)
        levels = []

        for ext_level in self.extension_levels:
            if is_bullish:
                price = entry_price + (base_range * ext_level)
            else:
                price = entry_price - (base_range * ext_level)

            label = f"{ext_level:.1%}" if ext_level < 2 else f"{ext_level:.2f}"

            levels.append(FibonacciLevel(
                level=ext_level,
                price=price,
                label=label,
                zone_type='extension'
            ))

        return FibonacciExtension(
            base_price=base_price,
            entry_price=entry_price,
            levels=levels,
            is_bullish=is_bullish
        )

    def get_golden_pocket(self, retracement: FibonacciRetracement) -> GoldenPocket:
        """
        Extract the Golden Pocket zone (61.8% - 78.6%)

        Args:
            retracement: FibonacciRetracement object

        Returns:
            GoldenPocket object
        """
        # Find 61.8% and 78.6% levels
        level_618 = next((l for l in retracement.levels if abs(l.level - 0.618) < 0.001), None)
        level_705 = next((l for l in retracement.levels if abs(l.level - 0.705) < 0.001), None)
        level_786 = next((l for l in retracement.levels if abs(l.level - 0.786) < 0.001), None)

        if not all([level_618, level_786, level_705]):
            raise ValueError("Required Fibonacci levels not found")

        if retracement.is_bullish:
            # For bullish, higher price is top
            top = level_618.price
            bottom = level_786.price
            zone_type = 'buy'
        else:
            # For bearish, higher price is top
            top = level_786.price
            bottom = level_618.price
            zone_type = 'sell'

        return GoldenPocket(
            top=top,
            bottom=bottom,
            mid=level_705.price,
            zone_type=zone_type
        )

    def get_ote_zone(self, retracement: FibonacciRetracement) -> Tuple[float, float]:
        """
        Get Optimal Trade Entry (OTE) zone boundaries

        Args:
            retracement: FibonacciRetracement object

        Returns:
            Tuple of (top, bottom) prices for OTE zone
        """
        ote_levels = [l for l in retracement.levels if l.level in self.ote_zone]

        if not ote_levels:
            return None, None

        prices = [l.price for l in ote_levels]

        return max(prices), min(prices)

    def is_in_premium(self, current_price: float, retracement: FibonacciRetracement) -> bool:
        """
        Check if current price is in premium zone

        Args:
            current_price: Current market price
            retracement: FibonacciRetracement object

        Returns:
            True if in premium zone
        """
        if retracement.is_bullish:
            # Premium is upper portion (lower retracement levels)
            level_618 = next((l.price for l in retracement.levels if abs(l.level - 0.618) < 0.001), None)
            return current_price >= level_618 if level_618 else False
        else:
            # For bearish, premium is lower portion
            level_618 = next((l.price for l in retracement.levels if abs(l.level - 0.618) < 0.001), None)
            return current_price <= level_618 if level_618 else False

    def is_in_discount(self, current_price: float, retracement: FibonacciRetracement) -> bool:
        """
        Check if current price is in discount zone

        Args:
            current_price: Current market price
            retracement: FibonacciRetracement object

        Returns:
            True if in discount zone
        """
        if retracement.is_bullish:
            # Discount is lower portion (higher retracement levels)
            level_618 = next((l.price for l in retracement.levels if abs(l.level - 0.618) < 0.001), None)
            return current_price <= level_618 if level_618 else False
        else:
            # For bearish, discount is upper portion
            level_618 = next((l.price for l in retracement.levels if abs(l.level - 0.618) < 0.001), None)
            return current_price >= level_618 if level_618 else False

    def is_in_golden_pocket(self, current_price: float, golden_pocket: GoldenPocket) -> bool:
        """
        Check if price is within the Golden Pocket zone

        Args:
            current_price: Current market price
            golden_pocket: GoldenPocket object

        Returns:
            True if price is in the Golden Pocket
        """
        return golden_pocket.bottom <= current_price <= golden_pocket.top

    def calculate_nested_fibonacci(self, df: pd.DataFrame, swing_points: List[Tuple[int, float]],
                                   timeframes: List[str]) -> Dict[str, List[FibonacciRetracement]]:
        """
        Calculate nested Fibonacci levels across multiple timeframes

        Args:
            df: DataFrame with OHLCV data
            swing_points: List of (index, price) tuples for swing points
            timeframes: List of timeframe labels

        Returns:
            Dictionary of timeframe -> list of retracements
        """
        nested_fibs = {}

        # For each timeframe, calculate Fibonacci levels
        # This creates the "Russian Doll" effect where multiple Fib levels align
        for tf in timeframes:
            retracements = []

            # Find significant swings for this timeframe
            # (In practice, you'd resample data or use different swing detection)
            for i in range(len(swing_points) - 1):
                start_idx, start_price = swing_points[i]
                end_idx, end_price = swing_points[i + 1]

                fib = self.calculate_retracement(start_price, end_price, start_idx, end_idx)
                retracements.append(fib)

            nested_fibs[tf] = retracements

        return nested_fibs

    def find_fibonacci_confluence(self, nested_fibs: Dict[str, List[FibonacciRetracement]],
                                  current_price: float, tolerance: float = 0.001) -> List[Dict]:
        """
        Find price levels where multiple Fibonacci levels align (confluence)

        Args:
            nested_fibs: Dictionary of timeframe -> retracements
            current_price: Current market price
            tolerance: Price tolerance for confluence (as % of price)

        Returns:
            List of confluence zones with details
        """
        confluence_zones = []

        # Collect all Fibonacci levels from all timeframes
        all_levels = []
        for tf, retracements in nested_fibs.items():
            for ret in retracements:
                for level in ret.levels:
                    all_levels.append({
                        'timeframe': tf,
                        'price': level.price,
                        'level': level.level,
                        'zone_type': level.zone_type
                    })

        # Find clusters of levels
        all_levels.sort(key=lambda x: x['price'])

        i = 0
        while i < len(all_levels):
            cluster = [all_levels[i]]
            base_price = all_levels[i]['price']

            # Find all levels within tolerance
            j = i + 1
            while j < len(all_levels):
                if abs(all_levels[j]['price'] - base_price) / base_price <= tolerance:
                    cluster.append(all_levels[j])
                    j += 1
                else:
                    break

            # If we have confluence (2+ levels), record it
            if len(cluster) >= 2:
                avg_price = np.mean([c['price'] for c in cluster])
                confluence_zones.append({
                    'price': avg_price,
                    'count': len(cluster),
                    'timeframes': list(set(c['timeframe'] for c in cluster)),
                    'zone_types': list(set(c['zone_type'] for c in cluster)),
                    'strength': len(cluster) * len(set(c['timeframe'] for c in cluster))
                })

            i = j if j > i + 1 else i + 1

        # Sort by strength
        confluence_zones.sort(key=lambda x: x['strength'], reverse=True)

        return confluence_zones

    def calculate_fibonacci_time_zones(self, df: pd.DataFrame, start_idx: int) -> List[int]:
        """
        Calculate Fibonacci time zones for potential reversal timing

        Args:
            df: DataFrame with OHLCV data
            start_idx: Starting index for time zone calculation

        Returns:
            List of indices where Fibonacci time zones occur
        """
        # Fibonacci sequence for time zones: 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144...
        fib_sequence = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233]

        time_zones = []

        for fib_number in fib_sequence:
            zone_idx = start_idx + fib_number
            if zone_idx < len(df):
                time_zones.append(zone_idx)
            else:
                break

        return time_zones

    def _get_level_label(self, level: float) -> str:
        """Get label for Fibonacci level"""
        labels = {
            0.0: "0%",
            0.236: "23.6%",
            0.382: "38.2%",
            0.5: "50%",
            0.618: "61.8%",
            0.705: "70.5%",
            0.786: "78.6%",
            1.0: "100%"
        }
        return labels.get(level, f"{level:.1%}")

    def get_profit_targets(self, entry_price: float, fib_extension: FibonacciExtension,
                          risk_amount: float) -> List[Dict]:
        """
        Calculate profit targets with risk/reward ratios

        Args:
            entry_price: Entry price
            fib_extension: FibonacciExtension object
            risk_amount: Amount risked on trade

        Returns:
            List of profit targets with R:R ratios
        """
        targets = []

        for level in fib_extension.levels:
            profit = abs(level.price - entry_price)
            rr_ratio = profit / risk_amount if risk_amount > 0 else 0

            targets.append({
                'level': level.label,
                'price': level.price,
                'profit': profit,
                'rr_ratio': rr_ratio
            })

        return targets
