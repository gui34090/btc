"""
Configuration settings for BTC/USDT Smart Money Chart
"""

# Trading Pair
SYMBOL = 'BTCUSDT'
BASE_CURRENCY = 'BTC'
QUOTE_CURRENCY = 'USDT'

# Timeframe Settings
TIMEFRAMES = {
    'primary': '15m',      # Primary trading timeframe
    'htf': '4h',           # Higher timeframe for context
    'ltf': '5m',           # Lower timeframe for entry
}

# Data Settings
LOOKBACK_PERIODS = {
    '5m': 500,
    '15m': 500,
    '1h': 300,
    '4h': 200,
    '1d': 100,
}

# Fibonacci Levels
FIBONACCI_RETRACEMENT = [0.0, 0.236, 0.382, 0.5, 0.618, 0.705, 0.786, 1.0]
FIBONACCI_EXTENSION = [1.272, 1.414, 1.618, 2.0, 2.618]

# ICT Premium/Discount Arrays
PREMIUM_DISCOUNT_LEVELS = {
    'discount': [0.0, 0.236, 0.382],
    'equilibrium': [0.5],
    'premium': [0.618, 0.705, 0.786, 1.0],
    'ote_zone': [0.618, 0.705, 0.786],  # Optimal Trade Entry
    'golden_pocket': 0.705,
}

# Elliott Wave Settings
ELLIOTT_WAVE = {
    'wave_2_retracement': [0.5, 0.618],
    'wave_3_extension': [1.618, 2.0, 2.618],
    'wave_4_retracement': [0.236, 0.382],
    'wave_5_projection': [0.618, 1.0],
    'min_wave_ratio': 0.382,
    'max_wave_ratio': 2.618,
}

# Smart Money Concepts Settings
SMC_SETTINGS = {
    'swing_lookback': 5,           # Periods for swing high/low detection
    'ob_lookback': 20,             # Lookback for Order Block detection
    'fvg_min_size': 0.001,         # Minimum FVG size (as % of price)
    'liquidity_threshold': 0.002,  # Threshold for liquidity pool identification
    'volume_multiplier': 1.5,      # Volume spike multiplier for confirmation
}

# Session Timing (UTC)
TRADING_SESSIONS = {
    'london_open': {'hour': 8, 'minute': 0},
    'ny_open': {'hour': 13, 'minute': 30},
    'london_close': {'hour': 16, 'minute': 0},
    'ny_close': {'hour': 20, 'minute': 0},
    'session_window_minutes': 120,  # Trade within 2 hours of session open
}

# Signal Generation Settings
SIGNAL_SETTINGS = {
    'min_confluence_score': 3,     # Minimum confluence factors required
    'require_htf_alignment': True, # Require higher timeframe alignment
    'require_session_timing': False, # Optional session timing filter
    'require_volume_confirmation': True,
    'signal_quality_thresholds': {
        'high': 5,    # 5+ confluence factors
        'medium': 3,  # 3-4 confluence factors
        'low': 2,     # 2 confluence factors
    }
}

# Risk Management Settings
RISK_MANAGEMENT = {
    'default_risk_per_trade': 0.01,      # 1% risk per trade
    'max_risk_per_trade': 0.02,          # Maximum 2% risk
    'min_risk_reward_ratio': 2.0,        # Minimum 1:2 RR
    'use_dynamic_stops': True,           # Use ATR-based stops
    'atr_multiplier': 1.5,               # ATR multiplier for stop loss
    'trailing_stop_activation': 1.5,     # Activate trailing stop at 1.5R
    'max_concurrent_trades': 3,          # Maximum simultaneous positions
}

# Backtesting Settings
BACKTEST_SETTINGS = {
    'initial_capital': 10000,
    'commission_rate': 0.001,            # 0.1% commission
    'slippage': 0.0005,                  # 0.05% slippage
    'use_realistic_fills': True,
}

# Chart Visualization Settings
CHART_SETTINGS = {
    'chart_type': 'candlestick',
    'show_volume': True,
    'show_indicators': True,
    'color_scheme': {
        'bullish': '#26a69a',
        'bearish': '#ef5350',
        'fvg_bullish': 'rgba(38, 166, 154, 0.2)',
        'fvg_bearish': 'rgba(239, 83, 80, 0.2)',
        'ob_bullish': 'rgba(38, 166, 154, 0.3)',
        'ob_bearish': 'rgba(239, 83, 80, 0.3)',
        'buy_signal': '#00ff00',
        'sell_signal': '#ff0000',
        'fibonacci': '#ff9800',
        'equilibrium': '#9c27b0',
    },
    'update_interval': 5,  # seconds
}

# API Settings (Binance)
API_SETTINGS = {
    'base_url': 'https://api.binance.com',
    'ws_url': 'wss://stream.binance.com:9443/ws',
    'rate_limit': 1200,  # requests per minute
    'timeout': 10,       # seconds
}

# Logging Settings
LOGGING = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'btc_smart_money.log',
}
