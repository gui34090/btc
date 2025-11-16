"""
Chart Visualization with Plotly
Real-time interactive chart with SMC, Fibonacci, Elliott Wave overlays
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime

from smart_money_concepts import OrderBlock, FairValueGap, LiquiditySweep, SwingPoint
from fibonacci_analysis import FibonacciRetracement, FibonacciExtension
from elliott_wave import WavePattern
from signal_generator import TradingSignal, SignalType, SignalQuality


class ChartVisualizer:
    """
    Create interactive charts with all trading concepts visualized
    """

    def __init__(self, config: Dict):
        """
        Initialize chart visualizer

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.colors = config.get('CHART_SETTINGS', {}).get('color_scheme', {})

    def create_live_chart(self, df: pd.DataFrame, smc_data: Dict,
                         fib_retracements: List[FibonacciRetracement],
                         signals: List[TradingSignal],
                         wave_pattern: Optional[WavePattern] = None) -> go.Figure:
        """
        Create complete live chart with all indicators

        Args:
            df: DataFrame with OHLCV data
            smc_data: SMC analysis results
            fib_retracements: List of Fibonacci retracements
            signals: List of trading signals
            wave_pattern: Elliott Wave pattern (optional)

        Returns:
            Plotly Figure object
        """
        # Create subplots: price chart + volume
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3],
            subplot_titles=('BTC/USDT - Smart Money Concepts', 'Volume')
        )

        # 1. Add candlestick chart
        self._add_candlestick(fig, df, row=1, col=1)

        # 2. Add volume bars
        self._add_volume(fig, df, row=2, col=1)

        # 3. Add SMC components
        self._add_order_blocks(fig, df, smc_data.get('order_blocks', []), row=1, col=1)
        self._add_fvgs(fig, df, smc_data.get('fvgs', []), row=1, col=1)
        self._add_swing_points(fig, df, smc_data.get('swing_highs', []),
                              smc_data.get('swing_lows', []), row=1, col=1)
        self._add_liquidity_sweeps(fig, df, smc_data.get('liquidity_sweeps', []), row=1, col=1)
        self._add_market_structure(fig, df, smc_data.get('market_structure', []), row=1, col=1)

        # 4. Add Fibonacci levels
        self._add_fibonacci_levels(fig, df, fib_retracements, row=1, col=1)

        # 5. Add Elliott Wave labels
        if wave_pattern:
            self._add_elliott_wave(fig, df, wave_pattern, row=1, col=1)

        # 6. Add trading signals
        self._add_signals(fig, df, signals, row=1, col=1)

        # Update layout
        fig.update_layout(
            title={
                'text': 'BTC/USDT - Institutional Grade Smart Money Chart',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20, 'color': '#ffffff'}
            },
            template='plotly_dark',
            xaxis_rangeslider_visible=False,
            height=900,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor='rgba(0,0,0,0.5)'
            ),
            hovermode='x unified',
            plot_bgcolor='#0d1117',
            paper_bgcolor='#0d1117'
        )

        # Update axes
        fig.update_xaxes(gridcolor='#1f2937', showgrid=True)
        fig.update_yaxes(gridcolor='#1f2937', showgrid=True)

        return fig

    def _add_candlestick(self, fig: go.Figure, df: pd.DataFrame, row: int, col: int):
        """Add candlestick chart"""
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='BTC/USDT',
                increasing_line_color=self.colors.get('bullish', '#26a69a'),
                decreasing_line_color=self.colors.get('bearish', '#ef5350')
            ),
            row=row, col=col
        )

    def _add_volume(self, fig: go.Figure, df: pd.DataFrame, row: int, col: int):
        """Add volume bars"""
        colors = ['#26a69a' if df.iloc[i]['close'] >= df.iloc[i]['open']
                 else '#ef5350' for i in range(len(df))]

        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df['volume'],
                name='Volume',
                marker_color=colors,
                showlegend=False
            ),
            row=row, col=col
        )

    def _add_order_blocks(self, fig: go.Figure, df: pd.DataFrame,
                         order_blocks: List[OrderBlock], row: int, col: int):
        """Add Order Blocks to chart"""
        for ob in order_blocks[-10:]:  # Show last 10 OBs
            if ob.start_idx >= len(df):
                continue

            x_start = df.index[ob.start_idx]
            x_end = df.index[min(ob.end_idx + 20, len(df) - 1)]

            color = self.colors.get('ob_bullish', 'rgba(38, 166, 154, 0.3)') if ob.is_bullish \
                   else self.colors.get('ob_bearish', 'rgba(239, 83, 80, 0.3)')

            fig.add_shape(
                type="rect",
                x0=x_start, x1=x_end,
                y0=ob.low, y1=ob.high,
                fillcolor=color,
                line=dict(color=color, width=1),
                row=row, col=col
            )

            # Add label
            fig.add_annotation(
                x=x_start,
                y=ob.high if ob.is_bullish else ob.low,
                text=f"OB {'↑' if ob.is_bullish else '↓'}",
                showarrow=False,
                font=dict(size=10, color='white'),
                bgcolor=color,
                row=row, col=col
            )

    def _add_fvgs(self, fig: go.Figure, df: pd.DataFrame,
                  fvgs: List[FairValueGap], row: int, col: int):
        """Add Fair Value Gaps to chart"""
        for fvg in fvgs[-15:]:  # Show last 15 FVGs
            if fvg.start_idx >= len(df):
                continue

            x_start = df.index[fvg.start_idx]
            x_end = df.index[min(fvg.end_idx + 30, len(df) - 1)]

            color = self.colors.get('fvg_bullish', 'rgba(38, 166, 154, 0.2)') if fvg.is_bullish \
                   else self.colors.get('fvg_bearish', 'rgba(239, 83, 80, 0.2)')

            fig.add_shape(
                type="rect",
                x0=x_start, x1=x_end,
                y0=fvg.bottom, y1=fvg.top,
                fillcolor=color,
                line=dict(color=color, width=1, dash='dot'),
                row=row, col=col
            )

            # Add label
            fig.add_annotation(
                x=x_start,
                y=(fvg.top + fvg.bottom) / 2,
                text=f"FVG",
                showarrow=False,
                font=dict(size=9, color='white'),
                bgcolor=color,
                row=row, col=col
            )

    def _add_swing_points(self, fig: go.Figure, df: pd.DataFrame,
                         swing_highs: List[SwingPoint],
                         swing_lows: List[SwingPoint], row: int, col: int):
        """Add swing high/low points"""
        # Swing highs
        if swing_highs:
            x_highs = [df.index[s.index] for s in swing_highs if s.index < len(df)]
            y_highs = [s.price for s in swing_highs if s.index < len(df)]

            fig.add_trace(
                go.Scatter(
                    x=x_highs,
                    y=y_highs,
                    mode='markers',
                    name='Swing High',
                    marker=dict(
                        symbol='triangle-down',
                        size=10,
                        color='#ef5350',
                        line=dict(color='white', width=1)
                    )
                ),
                row=row, col=col
            )

        # Swing lows
        if swing_lows:
            x_lows = [df.index[s.index] for s in swing_lows if s.index < len(df)]
            y_lows = [s.price for s in swing_lows if s.index < len(df)]

            fig.add_trace(
                go.Scatter(
                    x=x_lows,
                    y=y_lows,
                    mode='markers',
                    name='Swing Low',
                    marker=dict(
                        symbol='triangle-up',
                        size=10,
                        color='#26a69a',
                        line=dict(color='white', width=1)
                    )
                ),
                row=row, col=col
            )

    def _add_liquidity_sweeps(self, fig: go.Figure, df: pd.DataFrame,
                             sweeps: List[LiquiditySweep], row: int, col: int):
        """Add liquidity sweep markers"""
        for sweep in sweeps[-10:]:
            if sweep.index >= len(df):
                continue

            x = df.index[sweep.index]
            y = sweep.price

            color = '#ff0000' if sweep.is_high_sweep else '#00ff00'
            symbol = 'x' if sweep.is_high_sweep else 'x'

            fig.add_trace(
                go.Scatter(
                    x=[x],
                    y=[y],
                    mode='markers+text',
                    name=f"Liquidity Sweep {'High' if sweep.is_high_sweep else 'Low'}",
                    marker=dict(symbol=symbol, size=15, color=color),
                    text=['💰'],
                    textposition='top center',
                    showlegend=False
                ),
                row=row, col=col
            )

    def _add_market_structure(self, fig: go.Figure, df: pd.DataFrame,
                             market_structure: List[Dict], row: int, col: int):
        """Add market structure (BOS/ChoCh) annotations"""
        for ms in market_structure[-10:]:
            if ms['index'] >= len(df):
                continue

            x = df.index[ms['index']]
            y = ms['price']

            is_bullish = ms['direction'].value == 1
            text = ms['type'].value

            fig.add_annotation(
                x=x,
                y=y,
                text=text,
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor='#26a69a' if is_bullish else '#ef5350',
                font=dict(size=10, color='white'),
                bgcolor='#26a69a' if is_bullish else '#ef5350',
                row=row, col=col
            )

    def _add_fibonacci_levels(self, fig: go.Figure, df: pd.DataFrame,
                             fib_retracements: List[FibonacciRetracement],
                             row: int, col: int):
        """Add Fibonacci retracement levels"""
        # Show only the most recent/relevant retracements
        for fib in fib_retracements[-3:]:
            if fib.start_idx >= len(df) or fib.end_idx >= len(df):
                continue

            x_start = df.index[fib.start_idx]
            x_end = df.index[min(fib.end_idx + 50, len(df) - 1)]

            # Draw Fibonacci levels
            for level in fib.levels:
                # Special styling for key levels
                if abs(level.level - 0.618) < 0.01 or abs(level.level - 0.705) < 0.01:
                    # Golden Pocket levels
                    line_color = '#ffd700'
                    line_width = 2
                elif abs(level.level - 0.5) < 0.01:
                    # Equilibrium
                    line_color = self.colors.get('equilibrium', '#9c27b0')
                    line_width = 2
                else:
                    line_color = self.colors.get('fibonacci', '#ff9800')
                    line_width = 1

                fig.add_shape(
                    type="line",
                    x0=x_start, x1=x_end,
                    y0=level.price, y1=level.price,
                    line=dict(
                        color=line_color,
                        width=line_width,
                        dash='dash'
                    ),
                    row=row, col=col
                )

                # Add level label
                fig.add_annotation(
                    x=x_end,
                    y=level.price,
                    text=f"{level.label}",
                    showarrow=False,
                    xanchor='left',
                    font=dict(size=9, color=line_color),
                    bgcolor='rgba(0,0,0,0.7)',
                    row=row, col=col
                )

    def _add_elliott_wave(self, fig: go.Figure, df: pd.DataFrame,
                         wave_pattern: WavePattern, row: int, col: int):
        """Add Elliott Wave labels"""
        for wave in wave_pattern.waves:
            if wave.start_idx >= len(df) or wave.end_idx >= len(df):
                continue

            x = df.index[wave.end_idx]
            y = wave.end_price

            fig.add_annotation(
                x=x,
                y=y,
                text=f"Wave {wave.label.value}",
                showarrow=True,
                arrowhead=2,
                font=dict(size=12, color='#00ffff', family='Arial Black'),
                bgcolor='rgba(0, 100, 100, 0.8)',
                bordercolor='#00ffff',
                borderwidth=2,
                row=row, col=col
            )

    def _add_signals(self, fig: go.Figure, df: pd.DataFrame,
                    signals: List[TradingSignal], row: int, col: int):
        """Add buy/sell signal markers"""
        for signal in signals:
            if signal.index >= len(df):
                continue

            x = df.index[signal.index]
            y = signal.entry_price

            # Determine color based on quality
            if signal.quality == SignalQuality.HIGH:
                marker_color = '#00ff00' if signal.signal_type == SignalType.BUY else '#ff0000'
                marker_size = 20
            elif signal.quality == SignalQuality.MEDIUM:
                marker_color = '#ffff00' if signal.signal_type == SignalType.BUY else '#ff8800'
                marker_size = 15
            else:
                marker_color = '#888888'
                marker_size = 12

            symbol = 'triangle-up' if signal.signal_type == SignalType.BUY else 'triangle-down'

            # Add signal marker
            fig.add_trace(
                go.Scatter(
                    x=[x],
                    y=[y],
                    mode='markers+text',
                    name=f"{signal.signal_type.value} - {signal.quality.value}",
                    marker=dict(
                        symbol=symbol,
                        size=marker_size,
                        color=marker_color,
                        line=dict(color='white', width=2)
                    ),
                    text=[signal.signal_type.value],
                    textposition='top center' if signal.signal_type == SignalType.BUY else 'bottom center',
                    textfont=dict(size=10, color='white'),
                    hovertemplate=(
                        f"<b>{signal.signal_type.value} Signal</b><br>"
                        f"Quality: {signal.quality.value}<br>"
                        f"Entry: {signal.entry_price:.2f}<br>"
                        f"Stop Loss: {signal.stop_loss:.2f}<br>"
                        f"TP1: {signal.take_profit_1:.2f}<br>"
                        f"TP2: {signal.take_profit_2:.2f}<br>"
                        f"TP3: {signal.take_profit_3:.2f}<br>"
                        f"R:R: {signal.risk_reward_ratio:.2f}<br>"
                        f"Confluence: {signal.confluence_score}<br>"
                        f"Factors: {', '.join(signal.confluence_factors[:3])}<br>"
                        "<extra></extra>"
                    ),
                    showlegend=False
                ),
                row=row, col=col
            )

            # Add SL/TP lines
            x_end = df.index[min(signal.index + 30, len(df) - 1)]

            # Stop Loss
            fig.add_shape(
                type="line",
                x0=x, x1=x_end,
                y0=signal.stop_loss, y1=signal.stop_loss,
                line=dict(color='red', width=1, dash='dot'),
                row=row, col=col
            )

            # Take Profits
            for i, tp in enumerate([signal.take_profit_1, signal.take_profit_2, signal.take_profit_3]):
                alpha = 0.8 - (i * 0.2)
                fig.add_shape(
                    type="line",
                    x0=x, x1=x_end,
                    y0=tp, y1=tp,
                    line=dict(color=f'rgba(0, 255, 0, {alpha})', width=1, dash='dot'),
                    row=row, col=col
                )

    def update_chart_live(self, fig: go.Figure, new_candle: pd.Series):
        """
        Update chart with new candle data (for live updates)

        Args:
            fig: Existing figure
            new_candle: New candle data

        Returns:
            Updated figure
        """
        # This would update the existing chart with new data
        # Implementation depends on how you want to handle live updates
        pass

    def create_performance_summary(self, signals: List[TradingSignal]) -> go.Figure:
        """
        Create performance summary visualization

        Args:
            signals: List of trading signals

        Returns:
            Plotly Figure with performance metrics
        """
        # Count signals by quality
        quality_counts = {
            'HIGH': sum(1 for s in signals if s.quality == SignalQuality.HIGH),
            'MEDIUM': sum(1 for s in signals if s.quality == SignalQuality.MEDIUM),
            'LOW': sum(1 for s in signals if s.quality == SignalQuality.LOW)
        }

        # Create bar chart
        fig = go.Figure(data=[
            go.Bar(
                x=list(quality_counts.keys()),
                y=list(quality_counts.values()),
                marker_color=['#00ff00', '#ffff00', '#888888']
            )
        ])

        fig.update_layout(
            title='Signal Quality Distribution',
            xaxis_title='Quality',
            yaxis_title='Count',
            template='plotly_dark'
        )

        return fig
