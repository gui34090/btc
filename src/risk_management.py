"""
Risk Management and Backtesting Framework
Position sizing, risk controls, and performance metrics
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from signal_generator import TradingSignal, SignalType


class TradeStatus(Enum):
    """Trade status"""
    OPEN = "OPEN"
    CLOSED_WIN = "CLOSED_WIN"
    CLOSED_LOSS = "CLOSED_LOSS"
    CLOSED_BE = "CLOSED_BE"


@dataclass
class Trade:
    """Individual trade record"""
    signal: TradingSignal
    entry_time: pd.Timestamp
    entry_price: float
    position_size: float
    stop_loss: float
    take_profit: float
    exit_time: Optional[pd.Timestamp] = None
    exit_price: Optional[float] = None
    profit_loss: Optional[float] = None
    profit_loss_pct: Optional[float] = None
    status: TradeStatus = TradeStatus.OPEN
    r_multiple: Optional[float] = None  # R-multiple (profit/risk)


@dataclass
class PerformanceMetrics:
    """Trading performance metrics"""
    total_trades: int
    winning_trades: int
    losing_trades: int
    breakeven_trades: int
    win_rate: float
    profit_factor: float
    total_profit: float
    total_loss: float
    net_profit: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    avg_r_multiple: float
    max_consecutive_wins: int
    max_consecutive_losses: int
    max_drawdown: float
    max_drawdown_pct: float
    sharpe_ratio: float
    expectancy: float


class RiskManager:
    """
    Manage trading risk and position sizing
    """

    def __init__(self, config: Dict):
        """
        Initialize risk manager

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.risk_config = config.get('RISK_MANAGEMENT', {})

        self.default_risk_per_trade = self.risk_config.get('default_risk_per_trade', 0.01)
        self.max_risk_per_trade = self.risk_config.get('max_risk_per_trade', 0.02)
        self.min_rr_ratio = self.risk_config.get('min_risk_reward_ratio', 2.0)
        self.max_concurrent_trades = self.risk_config.get('max_concurrent_trades', 3)

    def calculate_position_size(self, account_balance: float, entry_price: float,
                               stop_loss: float, risk_pct: Optional[float] = None) -> float:
        """
        Calculate position size based on risk parameters

        Args:
            account_balance: Current account balance
            entry_price: Entry price
            stop_loss: Stop loss price
            risk_pct: Risk percentage (optional, uses default if not provided)

        Returns:
            Position size in base currency
        """
        risk_pct = risk_pct or self.default_risk_per_trade
        risk_pct = min(risk_pct, self.max_risk_per_trade)

        # Amount willing to risk
        risk_amount = account_balance * risk_pct

        # Distance to stop loss
        stop_distance = abs(entry_price - stop_loss)

        # Position size
        if stop_distance > 0:
            position_size = risk_amount / stop_distance
        else:
            position_size = 0

        return position_size

    def validate_signal(self, signal: TradingSignal) -> Tuple[bool, str]:
        """
        Validate if signal meets risk management criteria

        Args:
            signal: TradingSignal to validate

        Returns:
            Tuple of (is_valid, reason)
        """
        # Check risk/reward ratio
        if signal.risk_reward_ratio < self.min_rr_ratio:
            return False, f"R:R ratio {signal.risk_reward_ratio:.2f} below minimum {self.min_rr_ratio}"

        # Check stop loss is set
        if signal.stop_loss == 0 or signal.stop_loss == signal.entry_price:
            return False, "Invalid stop loss"

        # Check take profit is set
        if signal.take_profit_1 == 0:
            return False, "No take profit set"

        # Check direction consistency
        if signal.signal_type == SignalType.BUY:
            if signal.stop_loss >= signal.entry_price:
                return False, "Stop loss must be below entry for BUY"
            if signal.take_profit_1 <= signal.entry_price:
                return False, "Take profit must be above entry for BUY"
        else:  # SELL
            if signal.stop_loss <= signal.entry_price:
                return False, "Stop loss must be above entry for SELL"
            if signal.take_profit_1 >= signal.entry_price:
                return False, "Take profit must be below entry for SELL"

        return True, "Valid"


class Backtester:
    """
    Backtest trading signals and calculate performance metrics
    """

    def __init__(self, config: Dict):
        """
        Initialize backtester

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.backtest_config = config.get('BACKTEST_SETTINGS', {})
        self.risk_manager = RiskManager(config)

        self.initial_capital = self.backtest_config.get('initial_capital', 10000)
        self.commission_rate = self.backtest_config.get('commission_rate', 0.001)
        self.slippage = self.backtest_config.get('slippage', 0.0005)

    def run_backtest(self, df: pd.DataFrame, signals: List[TradingSignal]) -> Tuple[List[Trade], PerformanceMetrics]:
        """
        Run backtest on historical data

        Args:
            df: DataFrame with OHLCV data
            signals: List of trading signals

        Returns:
            Tuple of (trades, performance_metrics)
        """
        trades = []
        account_balance = self.initial_capital
        equity_curve = [self.initial_capital]
        open_trades = []

        # Sort signals by timestamp
        signals = sorted(signals, key=lambda s: s.timestamp)

        for signal in signals:
            # Validate signal
            is_valid, reason = self.risk_manager.validate_signal(signal)
            if not is_valid:
                continue

            # Check if we can open new trade (max concurrent trades)
            if len(open_trades) >= self.risk_manager.max_concurrent_trades:
                continue

            # Calculate position size
            position_size = self.risk_manager.calculate_position_size(
                account_balance,
                signal.entry_price,
                signal.stop_loss
            )

            if position_size <= 0:
                continue

            # Apply slippage to entry
            if signal.signal_type == SignalType.BUY:
                actual_entry = signal.entry_price * (1 + self.slippage)
            else:
                actual_entry = signal.entry_price * (1 - self.slippage)

            # Calculate commission
            commission = position_size * actual_entry * self.commission_rate

            # Create trade
            trade = Trade(
                signal=signal,
                entry_time=signal.timestamp,
                entry_price=actual_entry,
                position_size=position_size,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit_2,  # Use TP2 as main target
                status=TradeStatus.OPEN
            )

            open_trades.append(trade)

            # Simulate trade until exit
            self._simulate_trade_exit(trade, df, signal.index)

            # Calculate P&L
            if trade.exit_price:
                if signal.signal_type == SignalType.BUY:
                    pnl = (trade.exit_price - trade.entry_price) * position_size
                else:
                    pnl = (trade.entry_price - trade.exit_price) * position_size

                # Subtract commissions
                exit_commission = position_size * trade.exit_price * self.commission_rate
                pnl -= (commission + exit_commission)

                trade.profit_loss = pnl
                trade.profit_loss_pct = (pnl / (trade.entry_price * position_size)) * 100

                # Calculate R-multiple
                risk = abs(trade.entry_price - trade.stop_loss) * position_size
                trade.r_multiple = pnl / risk if risk > 0 else 0

                # Update account balance
                account_balance += pnl
                equity_curve.append(account_balance)

                # Determine trade status
                if pnl > 0:
                    trade.status = TradeStatus.CLOSED_WIN
                elif pnl < 0:
                    trade.status = TradeStatus.CLOSED_LOSS
                else:
                    trade.status = TradeStatus.CLOSED_BE

            trades.append(trade)
            open_trades.remove(trade)

        # Calculate performance metrics
        metrics = self._calculate_metrics(trades, equity_curve)

        return trades, metrics

    def _simulate_trade_exit(self, trade: Trade, df: pd.DataFrame, start_idx: int):
        """
        Simulate trade exit based on price action

        Args:
            trade: Trade object
            df: DataFrame with price data
            start_idx: Starting index for simulation
        """
        signal_type = trade.signal.signal_type

        # Look ahead up to 100 candles for exit
        for i in range(start_idx + 1, min(start_idx + 100, len(df))):
            candle = df.iloc[i]

            # Check if stop loss hit
            if signal_type == SignalType.BUY:
                if candle['low'] <= trade.stop_loss:
                    trade.exit_time = df.index[i]
                    trade.exit_price = trade.stop_loss * (1 - self.slippage)  # Slippage on exit
                    return

                # Check if take profit hit
                if candle['high'] >= trade.take_profit:
                    trade.exit_time = df.index[i]
                    trade.exit_price = trade.take_profit * (1 - self.slippage)
                    return

            else:  # SELL
                if candle['high'] >= trade.stop_loss:
                    trade.exit_time = df.index[i]
                    trade.exit_price = trade.stop_loss * (1 + self.slippage)
                    return

                if candle['low'] <= trade.take_profit:
                    trade.exit_time = df.index[i]
                    trade.exit_price = trade.take_profit * (1 + self.slippage)
                    return

        # If no exit found, close at last available price
        if trade.exit_price is None:
            last_candle = df.iloc[min(start_idx + 99, len(df) - 1)]
            trade.exit_time = df.index[min(start_idx + 99, len(df) - 1)]
            trade.exit_price = last_candle['close']

    def _calculate_metrics(self, trades: List[Trade], equity_curve: List[float]) -> PerformanceMetrics:
        """
        Calculate performance metrics

        Args:
            trades: List of completed trades
            equity_curve: List of account balance over time

        Returns:
            PerformanceMetrics object
        """
        if not trades:
            return PerformanceMetrics(
                total_trades=0, winning_trades=0, losing_trades=0, breakeven_trades=0,
                win_rate=0, profit_factor=0, total_profit=0, total_loss=0, net_profit=0,
                avg_win=0, avg_loss=0, largest_win=0, largest_loss=0, avg_r_multiple=0,
                max_consecutive_wins=0, max_consecutive_losses=0,
                max_drawdown=0, max_drawdown_pct=0, sharpe_ratio=0, expectancy=0
            )

        # Separate winning and losing trades
        winning_trades = [t for t in trades if t.status == TradeStatus.CLOSED_WIN]
        losing_trades = [t for t in trades if t.status == TradeStatus.CLOSED_LOSS]
        breakeven_trades = [t for t in trades if t.status == TradeStatus.CLOSED_BE]

        total_trades = len(trades)
        win_count = len(winning_trades)
        loss_count = len(losing_trades)
        be_count = len(breakeven_trades)

        # Win rate
        win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0

        # Profit/Loss
        total_profit = sum(t.profit_loss for t in winning_trades)
        total_loss = abs(sum(t.profit_loss for t in losing_trades))
        net_profit = total_profit - total_loss

        # Profit factor
        profit_factor = (total_profit / total_loss) if total_loss > 0 else float('inf')

        # Average win/loss
        avg_win = (total_profit / win_count) if win_count > 0 else 0
        avg_loss = (total_loss / loss_count) if loss_count > 0 else 0

        # Largest win/loss
        largest_win = max((t.profit_loss for t in winning_trades), default=0)
        largest_loss = min((t.profit_loss for t in losing_trades), default=0)

        # Average R-multiple
        r_multiples = [t.r_multiple for t in trades if t.r_multiple is not None]
        avg_r_multiple = np.mean(r_multiples) if r_multiples else 0

        # Consecutive wins/losses
        max_consecutive_wins = self._calculate_max_consecutive(trades, TradeStatus.CLOSED_WIN)
        max_consecutive_losses = self._calculate_max_consecutive(trades, TradeStatus.CLOSED_LOSS)

        # Drawdown
        max_dd, max_dd_pct = self._calculate_max_drawdown(equity_curve)

        # Sharpe ratio
        sharpe_ratio = self._calculate_sharpe_ratio(equity_curve)

        # Expectancy
        expectancy = (win_rate / 100 * avg_win) - ((1 - win_rate / 100) * avg_loss)

        return PerformanceMetrics(
            total_trades=total_trades,
            winning_trades=win_count,
            losing_trades=loss_count,
            breakeven_trades=be_count,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_profit=total_profit,
            total_loss=total_loss,
            net_profit=net_profit,
            avg_win=avg_win,
            avg_loss=avg_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            avg_r_multiple=avg_r_multiple,
            max_consecutive_wins=max_consecutive_wins,
            max_consecutive_losses=max_consecutive_losses,
            max_drawdown=max_dd,
            max_drawdown_pct=max_dd_pct,
            sharpe_ratio=sharpe_ratio,
            expectancy=expectancy
        )

    def _calculate_max_consecutive(self, trades: List[Trade], status: TradeStatus) -> int:
        """Calculate maximum consecutive trades of given status"""
        max_consecutive = 0
        current_consecutive = 0

        for trade in trades:
            if trade.status == status:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0

        return max_consecutive

    def _calculate_max_drawdown(self, equity_curve: List[float]) -> Tuple[float, float]:
        """Calculate maximum drawdown"""
        if not equity_curve or len(equity_curve) < 2:
            return 0, 0

        peak = equity_curve[0]
        max_dd = 0
        max_dd_pct = 0

        for value in equity_curve:
            if value > peak:
                peak = value

            dd = peak - value
            dd_pct = (dd / peak * 100) if peak > 0 else 0

            max_dd = max(max_dd, dd)
            max_dd_pct = max(max_dd_pct, dd_pct)

        return max_dd, max_dd_pct

    def _calculate_sharpe_ratio(self, equity_curve: List[float], risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        if len(equity_curve) < 2:
            return 0

        returns = np.diff(equity_curve) / equity_curve[:-1]

        if len(returns) == 0 or np.std(returns) == 0:
            return 0

        excess_returns = returns - (risk_free_rate / 252)  # Daily risk-free rate
        sharpe = np.mean(excess_returns) / np.std(returns) * np.sqrt(252)

        return sharpe

    def print_performance_report(self, metrics: PerformanceMetrics):
        """
        Print detailed performance report

        Args:
            metrics: PerformanceMetrics object
        """
        print("=" * 60)
        print("BACKTEST PERFORMANCE REPORT")
        print("=" * 60)
        print(f"\nTotal Trades: {metrics.total_trades}")
        print(f"Winning Trades: {metrics.winning_trades}")
        print(f"Losing Trades: {metrics.losing_trades}")
        print(f"Breakeven Trades: {metrics.breakeven_trades}")
        print(f"Win Rate: {metrics.win_rate:.2f}%")
        print(f"\nProfit Factor: {metrics.profit_factor:.2f}")
        print(f"Net Profit: ${metrics.net_profit:.2f}")
        print(f"Total Profit: ${metrics.total_profit:.2f}")
        print(f"Total Loss: ${metrics.total_loss:.2f}")
        print(f"\nAverage Win: ${metrics.avg_win:.2f}")
        print(f"Average Loss: ${metrics.avg_loss:.2f}")
        print(f"Largest Win: ${metrics.largest_win:.2f}")
        print(f"Largest Loss: ${metrics.largest_loss:.2f}")
        print(f"\nAverage R-Multiple: {metrics.avg_r_multiple:.2f}R")
        print(f"Expectancy: ${metrics.expectancy:.2f}")
        print(f"\nMax Consecutive Wins: {metrics.max_consecutive_wins}")
        print(f"Max Consecutive Losses: {metrics.max_consecutive_losses}")
        print(f"\nMax Drawdown: ${metrics.max_drawdown:.2f} ({metrics.max_drawdown_pct:.2f}%)")
        print(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
        print("=" * 60)
