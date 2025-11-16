"""
Elliott Wave Theory Implementation
Includes: 5-3 Wave Pattern Detection, Fibonacci Relationships, ICT Integration
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class WaveType(Enum):
    """Elliott Wave types"""
    IMPULSE = "Impulse"      # 5-wave motive
    CORRECTIVE = "Corrective"  # 3-wave corrective


class WaveLabel(Enum):
    """Wave labels"""
    WAVE_1 = 1
    WAVE_2 = 2
    WAVE_3 = 3
    WAVE_4 = 4
    WAVE_5 = 5
    WAVE_A = "A"
    WAVE_B = "B"
    WAVE_C = "C"


@dataclass
class Wave:
    """Individual wave structure"""
    label: WaveLabel
    start_idx: int
    end_idx: int
    start_price: float
    end_price: float
    wave_type: WaveType
    is_bullish: bool
    degree: int  # Wave degree (1=primary, 2=intermediate, etc.)


@dataclass
class WavePattern:
    """Complete wave pattern (5-wave or 3-wave)"""
    waves: List[Wave]
    pattern_type: WaveType
    is_bullish: bool
    start_idx: int
    end_idx: int
    degree: int


@dataclass
class ElliottWaveCount:
    """Complete Elliott Wave count"""
    impulse_wave: Optional[WavePattern]
    corrective_wave: Optional[WavePattern]
    current_wave: Optional[Wave]
    probability: float  # Confidence score 0-1


class ElliottWaveAnalyzer:
    """
    Elliott Wave Theory analysis and pattern detection
    """

    def __init__(self, min_wave_ratio: float = 0.382, max_wave_ratio: float = 2.618):
        """
        Initialize Elliott Wave analyzer

        Args:
            min_wave_ratio: Minimum acceptable wave ratio
            max_wave_ratio: Maximum acceptable wave ratio
        """
        self.min_wave_ratio = min_wave_ratio
        self.max_wave_ratio = max_wave_ratio

        # Fibonacci relationships for wave validation
        self.wave_2_retracement = [0.5, 0.618, 0.786]
        self.wave_3_extension = [1.618, 2.0, 2.618]
        self.wave_4_retracement = [0.236, 0.382, 0.5]
        self.wave_5_projection = [0.618, 1.0, 1.618]

    def detect_impulse_wave(self, df: pd.DataFrame, swing_points: List[Tuple[int, float, bool]]
                           ) -> Optional[WavePattern]:
        """
        Detect 5-wave impulse pattern

        Args:
            df: DataFrame with OHLCV data
            swing_points: List of (index, price, is_high) tuples

        Returns:
            WavePattern if valid impulse detected, None otherwise
        """
        if len(swing_points) < 6:
            return None

        # Try to identify 5-wave structure
        for i in range(len(swing_points) - 5):
            points = swing_points[i:i+6]

            # Check if this could be a 5-wave impulse
            # Pattern should alternate: low-high-low-high-low-high (bullish)
            # or high-low-high-low-high-low (bearish)

            # Bullish impulse check
            if not points[0][2] and points[1][2] and not points[2][2] and points[3][2] and not points[4][2] and points[5][2]:
                waves = self._create_impulse_waves(points, is_bullish=True)
                if self._validate_impulse_waves(waves):
                    return WavePattern(
                        waves=waves,
                        pattern_type=WaveType.IMPULSE,
                        is_bullish=True,
                        start_idx=points[0][0],
                        end_idx=points[5][0],
                        degree=1
                    )

            # Bearish impulse check
            elif points[0][2] and not points[1][2] and points[2][2] and not points[3][2] and points[4][2] and not points[5][2]:
                waves = self._create_impulse_waves(points, is_bullish=False)
                if self._validate_impulse_waves(waves):
                    return WavePattern(
                        waves=waves,
                        pattern_type=WaveType.IMPULSE,
                        is_bullish=False,
                        start_idx=points[0][0],
                        end_idx=points[5][0],
                        degree=1
                    )

        return None

    def _create_impulse_waves(self, points: List[Tuple[int, float, bool]], is_bullish: bool) -> List[Wave]:
        """Create wave objects for impulse pattern"""
        waves = []

        wave_labels = [WaveLabel.WAVE_1, WaveLabel.WAVE_2, WaveLabel.WAVE_3,
                      WaveLabel.WAVE_4, WaveLabel.WAVE_5]

        for i, label in enumerate(wave_labels):
            waves.append(Wave(
                label=label,
                start_idx=points[i][0],
                end_idx=points[i+1][0],
                start_price=points[i][1],
                end_price=points[i+1][1],
                wave_type=WaveType.IMPULSE,
                is_bullish=is_bullish if i % 2 == 0 else not is_bullish,
                degree=1
            ))

        return waves

    def _validate_impulse_waves(self, waves: List[Wave]) -> bool:
        """
        Validate impulse waves against Elliott Wave rules

        Rules:
        1. Wave 2 cannot retrace more than 100% of Wave 1
        2. Wave 3 cannot be the shortest wave
        3. Wave 4 cannot overlap with Wave 1
        """
        if len(waves) != 5:
            return False

        wave1 = waves[0]
        wave2 = waves[1]
        wave3 = waves[2]
        wave4 = waves[3]
        wave5 = waves[4]

        # Calculate wave sizes
        wave1_size = abs(wave1.end_price - wave1.start_price)
        wave2_size = abs(wave2.end_price - wave2.start_price)
        wave3_size = abs(wave3.end_price - wave3.start_price)
        wave4_size = abs(wave4.end_price - wave4.start_price)
        wave5_size = abs(wave5.end_price - wave5.start_price)

        # Rule 1: Wave 2 cannot retrace more than 100% of Wave 1
        wave2_retracement = wave2_size / wave1_size
        if wave2_retracement > 1.0:
            return False

        # Rule 2: Wave 3 cannot be the shortest
        if wave3_size < wave1_size and wave3_size < wave5_size:
            return False

        # Rule 3: Wave 4 cannot overlap with Wave 1 (in price)
        if wave1.is_bullish:
            if wave4.end_price < wave1.end_price:
                return False
        else:
            if wave4.end_price > wave1.end_price:
                return False

        return True

    def check_fibonacci_relationships(self, waves: List[Wave]) -> Dict[str, float]:
        """
        Check Fibonacci relationships in wave pattern

        Args:
            waves: List of Wave objects

        Returns:
            Dictionary of relationship scores
        """
        scores = {}

        if len(waves) >= 3:
            wave1 = waves[0]
            wave2 = waves[1]
            wave3 = waves[2]

            wave1_size = abs(wave1.end_price - wave1.start_price)
            wave2_size = abs(wave2.end_price - wave2.start_price)
            wave3_size = abs(wave3.end_price - wave3.start_price)

            # Wave 2 retracement of Wave 1
            wave2_retrace_ratio = wave2_size / wave1_size
            scores['wave2_retracement'] = self._score_fibonacci_match(
                wave2_retrace_ratio, self.wave_2_retracement
            )

            # Wave 3 extension of Wave 1
            wave3_extension_ratio = wave3_size / wave1_size
            scores['wave3_extension'] = self._score_fibonacci_match(
                wave3_extension_ratio, self.wave_3_extension
            )

        if len(waves) >= 5:
            wave4 = waves[3]
            wave5 = waves[4]

            wave3_size = abs(wave3.end_price - wave3.start_price)
            wave4_size = abs(wave4.end_price - wave4.start_price)
            wave5_size = abs(wave5.end_price - wave5.start_price)

            # Wave 4 retracement of Wave 3
            wave4_retrace_ratio = wave4_size / wave3_size
            scores['wave4_retracement'] = self._score_fibonacci_match(
                wave4_retrace_ratio, self.wave_4_retracement
            )

            # Wave 5 projection
            wave5_projection_ratio = wave5_size / wave1_size
            scores['wave5_projection'] = self._score_fibonacci_match(
                wave5_projection_ratio, self.wave_5_projection
            )

        return scores

    def _score_fibonacci_match(self, ratio: float, targets: List[float]) -> float:
        """Score how well a ratio matches Fibonacci targets"""
        min_distance = min(abs(ratio - target) for target in targets)

        # Convert distance to score (0-1, where 1 is perfect match)
        if min_distance < 0.05:
            return 1.0
        elif min_distance < 0.1:
            return 0.8
        elif min_distance < 0.15:
            return 0.6
        elif min_distance < 0.2:
            return 0.4
        else:
            return 0.2

    def identify_current_wave(self, pattern: WavePattern, current_idx: int) -> Optional[Wave]:
        """
        Identify which wave is currently forming

        Args:
            pattern: WavePattern object
            current_idx: Current data index

        Returns:
            Current Wave or None
        """
        for wave in pattern.waves:
            if wave.start_idx <= current_idx <= wave.end_idx:
                return wave

        # If beyond pattern, might be starting new wave
        if current_idx > pattern.end_idx:
            last_wave = pattern.waves[-1]
            if pattern.pattern_type == WaveType.IMPULSE:
                # After wave 5, expect corrective wave
                return None
            else:
                # After corrective, expect new impulse
                return None

        return None

    def detect_corrective_wave(self, df: pd.DataFrame, swing_points: List[Tuple[int, float, bool]]
                              ) -> Optional[WavePattern]:
        """
        Detect 3-wave corrective pattern (A-B-C)

        Args:
            df: DataFrame with OHLCV data
            swing_points: List of (index, price, is_high) tuples

        Returns:
            WavePattern if valid correction detected, None otherwise
        """
        if len(swing_points) < 4:
            return None

        # Try to identify 3-wave structure
        for i in range(len(swing_points) - 3):
            points = swing_points[i:i+4]

            # Bullish correction: high-low-high-low
            if points[0][2] and not points[1][2] and points[2][2] and not points[3][2]:
                waves = self._create_corrective_waves(points, is_bullish=False)
                if self._validate_corrective_waves(waves):
                    return WavePattern(
                        waves=waves,
                        pattern_type=WaveType.CORRECTIVE,
                        is_bullish=False,
                        start_idx=points[0][0],
                        end_idx=points[3][0],
                        degree=1
                    )

            # Bearish correction: low-high-low-high
            elif not points[0][2] and points[1][2] and not points[2][2] and points[3][2]:
                waves = self._create_corrective_waves(points, is_bullish=True)
                if self._validate_corrective_waves(waves):
                    return WavePattern(
                        waves=waves,
                        pattern_type=WaveType.CORRECTIVE,
                        is_bullish=True,
                        start_idx=points[0][0],
                        end_idx=points[3][0],
                        degree=1
                    )

        return None

    def _create_corrective_waves(self, points: List[Tuple[int, float, bool]], is_bullish: bool) -> List[Wave]:
        """Create wave objects for corrective pattern"""
        waves = []

        wave_labels = [WaveLabel.WAVE_A, WaveLabel.WAVE_B, WaveLabel.WAVE_C]

        for i, label in enumerate(wave_labels):
            waves.append(Wave(
                label=label,
                start_idx=points[i][0],
                end_idx=points[i+1][0],
                start_price=points[i][1],
                end_price=points[i+1][1],
                wave_type=WaveType.CORRECTIVE,
                is_bullish=is_bullish if i % 2 == 0 else not is_bullish,
                degree=1
            ))

        return waves

    def _validate_corrective_waves(self, waves: List[Wave]) -> bool:
        """Validate corrective waves"""
        if len(waves) != 3:
            return False

        # Basic validation: wave C should be in same direction as wave A
        waveA = waves[0]
        waveC = waves[2]

        return waveA.is_bullish == waveC.is_bullish

    def integrate_with_smc(self, wave: Wave, smc_data: Dict) -> Dict:
        """
        Integrate Elliott Wave with Smart Money Concepts

        Args:
            wave: Current Wave object
            smc_data: Dictionary of SMC analysis results

        Returns:
            Integration analysis
        """
        integration = {
            'wave': wave.label.value,
            'smc_alignment': []
        }

        # Wave 1: Initial Smart Money Move
        if wave.label == WaveLabel.WAVE_1:
            integration['smc_alignment'].append({
                'concept': 'Smart Money Accumulation',
                'description': 'Initial institutional entry',
                'look_for': ['Order Blocks', 'Volume spike']
            })

        # Wave 2: The Retail Trap (Liquidity Sweep & Golden Pocket)
        elif wave.label == WaveLabel.WAVE_2:
            integration['smc_alignment'].append({
                'concept': 'Liquidity Sweep',
                'description': 'Stop hunt before continuation',
                'look_for': ['Liquidity sweep', 'Golden Pocket entry', 'FVG formation']
            })

        # Wave 3: The Institutional Impulse (BOS & Volume)
        elif wave.label == WaveLabel.WAVE_3:
            integration['smc_alignment'].append({
                'concept': 'Break of Structure',
                'description': 'Strong institutional impulse',
                'look_for': ['BOS', 'High volume', 'Multiple FVGs']
            })

        # Wave 4: Smart Money Distribution
        elif wave.label == WaveLabel.WAVE_4:
            integration['smc_alignment'].append({
                'concept': 'Distribution Zone',
                'description': 'Reaccumulation/distribution',
                'look_for': ['Consolidation', 'Order blocks', 'Lower volume']
            })

        # Wave 5: Retail FOMO and Exit Zone
        elif wave.label == WaveLabel.WAVE_5:
            integration['smc_alignment'].append({
                'concept': 'Retail FOMO / Smart Money Exit',
                'description': 'Distribution to late buyers',
                'look_for': ['Exhaustion', 'Divergence', 'Liquidity grab preparation']
            })

        return integration

    def calculate_wave_probability(self, waves: List[Wave], df: pd.DataFrame,
                                   smc_data: Dict) -> float:
        """
        Calculate probability score for wave count

        Args:
            waves: List of Wave objects
            df: DataFrame with OHLCV data
            smc_data: SMC analysis data

        Returns:
            Probability score 0-1
        """
        scores = []

        # Check Fibonacci relationships
        fib_scores = self.check_fibonacci_relationships(waves)
        if fib_scores:
            avg_fib_score = np.mean(list(fib_scores.values()))
            scores.append(avg_fib_score * 0.4)  # 40% weight

        # Check volume pattern (Wave 3 should have highest volume)
        if len(waves) >= 3:
            wave3 = waves[2]
            wave3_volume = df.iloc[wave3.start_idx:wave3.end_idx]['volume'].mean()
            total_avg_volume = df['volume'].mean()

            volume_score = min(1.0, wave3_volume / (total_avg_volume * 1.5))
            scores.append(volume_score * 0.3)  # 30% weight

        # Check SMC alignment
        if smc_data and 'market_structure' in smc_data:
            # More BOS events = higher probability
            bos_count = sum(1 for event in smc_data['market_structure']
                          if event['type'].value == 'Break of Structure')
            smc_score = min(1.0, bos_count / 3)
            scores.append(smc_score * 0.3)  # 30% weight

        return np.mean(scores) if scores else 0.5

    def find_wave_entry_points(self, pattern: WavePattern) -> List[Dict]:
        """
        Identify optimal entry points based on wave structure

        Args:
            pattern: WavePattern object

        Returns:
            List of entry point recommendations
        """
        entries = []

        # Wave 2 entry (after retracement)
        if len(pattern.waves) >= 2:
            wave2 = pattern.waves[1]
            entries.append({
                'wave': 'Wave 2',
                'type': 'Retracement Entry',
                'price': wave2.end_price,
                'index': wave2.end_idx,
                'quality': 'High',
                'notes': 'Entry at 61.8-78.6% retracement of Wave 1'
            })

        # Wave 4 entry (for Wave 5)
        if len(pattern.waves) >= 4:
            wave4 = pattern.waves[3]
            entries.append({
                'wave': 'Wave 4',
                'type': 'Retracement Entry',
                'price': wave4.end_price,
                'index': wave4.end_idx,
                'quality': 'Medium',
                'notes': 'Entry at 23.6-38.2% retracement of Wave 3'
            })

        return entries
