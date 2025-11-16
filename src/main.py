"""
Main Application - BTC/USDT Smart Money Chart
Institutional-grade trading system with live charts and signal generation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime

# Import configuration
import config

# Import all modules
from data_processing import DataProcessor
from smart_money_concepts import SmartMoneyConcepts
from fibonacci_analysis import FibonacciAnalysis
from elliott_wave import ElliottWaveAnalyzer
from signal_generator import SignalGenerator
from chart_visualizer import ChartVisualizer
from risk_management import RiskManager, Backtester


class BTCSmartMoneyChart:
    """
    Main application class for BTC/USDT Smart Money Chart
    """

    def __init__(self):
        """Initialize the trading system"""
        # Set up logging
        logging.basicConfig(
            level=getattr(logging, config.LOGGING['level']),
            format=config.LOGGING['format'],
            handlers=[
                logging.FileHandler(config.LOGGING['file']),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing BTC Smart Money Chart System...")

        # Initialize components
        self.data_processor = DataProcessor(
            symbol=config.SYMBOL,
            base_url=config.API_SETTINGS['base_url']
        )

        self.signal_generator = SignalGenerator(config.__dict__)
        self.chart_visualizer = ChartVisualizer(config.__dict__)
        self.risk_manager = RiskManager(config.__dict__)
        self.backtester = Backtester(config.__dict__)

        self.logger.info("System initialized successfully!")

    def run_analysis(self, timeframe: str = '15m', lookback: int = 500) -> Dict:
        """
        Run complete analysis on BTC/USDT

        Args:
            timeframe: Timeframe to analyze
            lookback: Number of candles to fetch

        Returns:
            Dictionary with analysis results
        """
        self.logger.info(f"Running analysis on {timeframe} timeframe...")

        # Fetch data
        df = self.data_processor.fetch_historical_data(interval=timeframe, limit=lookback)

        if df.empty:
            self.logger.error("Failed to fetch data")
            return {}

        # Prepare features
        df = self.data_processor.prepare_features(df, config.TRADING_SESSIONS)

        # Fetch higher timeframe for context
        htf_timeframe = config.TIMEFRAMES.get('htf', '4h')
        htf_df = self.data_processor.fetch_historical_data(interval=htf_timeframe, limit=200)

        if not htf_df.empty:
            htf_df = self.data_processor.prepare_features(htf_df, config.TRADING_SESSIONS)

        # Run SMC analysis
        smc = SmartMoneyConcepts(
            swing_lookback=config.SMC_SETTINGS['swing_lookback'],
            ob_lookback=config.SMC_SETTINGS['ob_lookback'],
            fvg_min_size=config.SMC_SETTINGS['fvg_min_size'],
            liquidity_threshold=config.SMC_SETTINGS['liquidity_threshold']
        )
        smc_analysis = smc.analyze_all(df)

        self.logger.info(f"Found {len(smc_analysis['swing_highs'])} swing highs, "
                        f"{len(smc_analysis['swing_lows'])} swing lows")
        self.logger.info(f"Detected {len(smc_analysis['order_blocks'])} order blocks, "
                        f"{len(smc_analysis['fvgs'])} FVGs")
        self.logger.info(f"Identified {len(smc_analysis['liquidity_sweeps'])} liquidity sweeps")

        # Generate Fibonacci retracements
        swing_highs = smc_analysis['swing_highs']
        swing_lows = smc_analysis['swing_lows']

        fib_analyzer = FibonacciAnalysis(
            retracement_levels=config.FIBONACCI_RETRACEMENT,
            extension_levels=config.FIBONACCI_EXTENSION
        )

        fib_retracements = []
        # Generate bullish retracements
        for i in range(len(swing_lows) - 1):
            for j in range(i + 1, min(i + 5, len(swing_lows))):
                low = swing_lows[i]
                highs_between = [h for h in swing_highs if low.index < h.index < swing_lows[j].index]
                if highs_between:
                    high = max(highs_between, key=lambda h: h.price)
                    fib = fib_analyzer.calculate_retracement(
                        low.price, high.price, low.index, high.index
                    )
                    fib_retracements.append(fib)

        self.logger.info(f"Generated {len(fib_retracements)} Fibonacci retracements")

        # Detect Elliott Wave patterns
        wave_analyzer = ElliottWaveAnalyzer(
            min_wave_ratio=config.ELLIOTT_WAVE['min_wave_ratio'],
            max_wave_ratio=config.ELLIOTT_WAVE['max_wave_ratio']
        )

        swing_points = [(s.index, s.price, s.is_high) for s in swing_highs + swing_lows]
        swing_points.sort(key=lambda x: x[0])

        wave_pattern = wave_analyzer.detect_impulse_wave(df, swing_points)

        if wave_pattern:
            self.logger.info(f"Detected {len(wave_pattern.waves)}-wave "
                           f"{'bullish' if wave_pattern.is_bullish else 'bearish'} pattern")

        # Generate trading signals
        self.logger.info("Generating trading signals...")
        signals = self.signal_generator.generate_signals(df, htf_df if not htf_df.empty else None)

        self.logger.info(f"Generated {len(signals)} trading signals")

        # Count by quality
        high_quality = sum(1 for s in signals if s.quality.value == 'HIGH')
        medium_quality = sum(1 for s in signals if s.quality.value == 'MEDIUM')
        low_quality = sum(1 for s in signals if s.quality.value == 'LOW')

        self.logger.info(f"Signal Quality: HIGH={high_quality}, MEDIUM={medium_quality}, LOW={low_quality}")

        return {
            'df': df,
            'htf_df': htf_df,
            'smc_analysis': smc_analysis,
            'fib_retracements': fib_retracements,
            'wave_pattern': wave_pattern,
            'signals': signals
        }

    def create_chart(self, analysis_results: Dict) -> None:
        """
        Create and display the chart

        Args:
            analysis_results: Results from run_analysis()
        """
        self.logger.info("Creating chart visualization...")

        fig = self.chart_visualizer.create_live_chart(
            df=analysis_results['df'],
            smc_data=analysis_results['smc_analysis'],
            fib_retracements=analysis_results['fib_retracements'],
            signals=analysis_results['signals'],
            wave_pattern=analysis_results['wave_pattern']
        )

        # Save to HTML
        output_file = 'btc_smart_money_chart.html'
        fig.write_html(output_file)
        self.logger.info(f"Chart saved to {output_file}")

        # Show in browser
        fig.show()

    def run_backtest(self, timeframe: str = '15m', lookback: int = 1000) -> None:
        """
        Run backtest on historical data

        Args:
            timeframe: Timeframe to backtest
            lookback: Number of candles to use
        """
        self.logger.info("=" * 60)
        self.logger.info("STARTING BACKTEST")
        self.logger.info("=" * 60)

        # Get analysis results
        analysis_results = self.run_analysis(timeframe=timeframe, lookback=lookback)

        if not analysis_results:
            self.logger.error("Analysis failed, cannot run backtest")
            return

        df = analysis_results['df']
        signals = analysis_results['signals']

        # Run backtest
        self.logger.info(f"\nBacktesting {len(signals)} signals on {len(df)} candles...")

        trades, metrics = self.backtester.run_backtest(df, signals)

        # Print results
        self.backtester.print_performance_report(metrics)

        # Show example trades
        if trades:
            self.logger.info("\n" + "=" * 60)
            self.logger.info("EXAMPLE TRADES")
            self.logger.info("=" * 60)

            for i, trade in enumerate(trades[:5], 1):
                self.logger.info(f"\nTrade {i}:")
                self.logger.info(f"  Type: {trade.signal.signal_type.value}")
                self.logger.info(f"  Entry: ${trade.entry_price:.2f} @ {trade.entry_time}")
                self.logger.info(f"  Exit: ${trade.exit_price:.2f} @ {trade.exit_time}")
                self.logger.info(f"  P&L: ${trade.profit_loss:.2f} ({trade.profit_loss_pct:.2f}%)")
                self.logger.info(f"  R-Multiple: {trade.r_multiple:.2f}R")
                self.logger.info(f"  Status: {trade.status.value}")
                self.logger.info(f"  Confluence: {trade.signal.confluence_score} - "
                               f"{', '.join(trade.signal.confluence_factors[:3])}")

    def run_live(self, timeframe: str = '15m', update_interval: int = 60) -> None:
        """
        Run live chart with periodic updates

        Args:
            timeframe: Timeframe to display
            update_interval: Update interval in seconds
        """
        self.logger.info("=" * 60)
        self.logger.info("STARTING LIVE MODE")
        self.logger.info("=" * 60)

        try:
            while True:
                # Get latest analysis
                analysis_results = self.run_analysis(timeframe=timeframe)

                if not analysis_results:
                    self.logger.warning("Analysis failed, retrying in 60 seconds...")
                    time.sleep(60)
                    continue

                # Create and save chart
                self.create_chart(analysis_results)

                # Show latest signals
                signals = analysis_results['signals']
                if signals:
                    latest_signals = sorted(signals, key=lambda s: s.timestamp, reverse=True)[:5]

                    self.logger.info("\n" + "=" * 60)
                    self.logger.info("LATEST SIGNALS")
                    self.logger.info("=" * 60)

                    for signal in latest_signals:
                        self.logger.info(f"\n{signal.signal_type.value} @ ${signal.entry_price:.2f}")
                        self.logger.info(f"  Quality: {signal.quality.value}")
                        self.logger.info(f"  Time: {signal.timestamp}")
                        self.logger.info(f"  Stop Loss: ${signal.stop_loss:.2f}")
                        self.logger.info(f"  Take Profit: ${signal.take_profit_2:.2f}")
                        self.logger.info(f"  R:R Ratio: {signal.risk_reward_ratio:.2f}")
                        self.logger.info(f"  Confluence: {signal.confluence_score}")
                        self.logger.info(f"  Factors: {', '.join(signal.confluence_factors[:3])}")

                # Get current price
                current_price = self.data_processor.get_latest_price()
                if current_price:
                    self.logger.info(f"\nCurrent BTC/USDT Price: ${current_price:,.2f}")

                # Wait for next update
                self.logger.info(f"\nNext update in {update_interval} seconds...")
                self.logger.info("Press Ctrl+C to stop")
                time.sleep(update_interval)

        except KeyboardInterrupt:
            self.logger.info("\nLive mode stopped by user")

    def quick_scan(self) -> None:
        """Quick scan for current market conditions and signals"""
        self.logger.info("Running quick market scan...")

        analysis_results = self.run_analysis(timeframe='15m', lookback=300)

        if not analysis_results:
            return

        signals = analysis_results['signals']
        df = analysis_results['df']

        # Get current price
        current_price = df.iloc[-1]['close']

        self.logger.info("\n" + "=" * 60)
        self.logger.info("QUICK MARKET SCAN RESULTS")
        self.logger.info("=" * 60)
        self.logger.info(f"\nCurrent Price: ${current_price:,.2f}")

        # Check for active signals near current price
        active_signals = [s for s in signals
                         if abs(s.entry_price - current_price) / current_price < 0.01]

        if active_signals:
            self.logger.info(f"\n{len(active_signals)} ACTIVE SIGNALS near current price:")
            for signal in active_signals:
                self.logger.info(f"\n  {signal.signal_type.value} - {signal.quality.value}")
                self.logger.info(f"  Entry: ${signal.entry_price:.2f}")
                self.logger.info(f"  Confluence Factors: {', '.join(signal.confluence_factors)}")
        else:
            self.logger.info("\nNo active signals near current price")

        self.logger.info("=" * 60)


def main():
    """Main entry point"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║   BTC/USDT INSTITUTIONAL-GRADE SMART MONEY CHART SYSTEM     ║
    ║                                                              ║
    ║   Features:                                                  ║
    ║   • Smart Money Concepts (Liquidity, OB, FVG)               ║
    ║   • Fibonacci Golden Pocket & Extensions                    ║
    ║   • Elliott Wave Pattern Detection                          ║
    ║   • Multi-Timeframe Confluence Signals                      ║
    ║   • Risk Management & Backtesting                           ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    # Initialize system
    system = BTCSmartMoneyChart()

    # Menu
    print("\nSelect Mode:")
    print("1. Run Analysis & Show Chart")
    print("2. Run Backtest")
    print("3. Live Mode (Auto-update)")
    print("4. Quick Scan")
    print("5. Exit")

    choice = input("\nEnter choice (1-5): ").strip()

    if choice == '1':
        timeframe = input("Enter timeframe (5m/15m/1h/4h) [default: 15m]: ").strip() or '15m'
        results = system.run_analysis(timeframe=timeframe)
        if results:
            system.create_chart(results)

    elif choice == '2':
        timeframe = input("Enter timeframe (5m/15m/1h/4h) [default: 15m]: ").strip() or '15m'
        system.run_backtest(timeframe=timeframe)

    elif choice == '3':
        timeframe = input("Enter timeframe (5m/15m/1h/4h) [default: 15m]: ").strip() or '15m'
        update_interval = input("Update interval in seconds [default: 60]: ").strip()
        update_interval = int(update_interval) if update_interval else 60
        system.run_live(timeframe=timeframe, update_interval=update_interval)

    elif choice == '4':
        system.quick_scan()

    elif choice == '5':
        print("Goodbye!")
        return

    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
