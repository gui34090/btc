# Institutional-Grade BTC/USDT Live Chart with Smart Money Signals

## Overview
Advanced trading system implementing Smart Money Concepts (SMC), Elliott Wave Theory, and Fibonacci analysis for BTC/USDT trading with real-time visualization and signal generation.

## Core Features

### 1. Smart Money Concepts (SMC)
- **Liquidity Sweep & Reversal Detection**
- **Fair Value Gaps (FVG) Identification**
- **Order Blocks (OB) Detection**
- **Market Structure Analysis (BOS/ChoCh)**
- **Engineered Liquidity & False Breakouts**
- **Run on Stops Detection**

### 2. Fibonacci Analysis
- **Premium/Discount Arrays**
- **Optimal Trade Entry (OTE) Zone (61.8% - 78.6%)**
- **Golden Pocket (70.5% Level)**
- **Fibonacci Extensions (127.2%, 141.4%, 161.8%, 261.8%)**
- **Multi-Timeframe Nested Fibonacci**
- **Fibonacci Time Zones**

### 3. Elliott Wave Theory
- **5-3 Wave Pattern Detection**
- **Wave Fibonacci Relationships**
- **Multi-Timeframe Wave Alignment**
- **Advanced Patterns (Ending Diagonals, Triangles)**
- **Integration with SMC Concepts**

### 4. Signal Generation
- **Confluence Stack Analysis**
- **High-Probability Entry Detection**
- **Signal Quality Classification**
- **Session Timing Filters (London/NY)**
- **Volume Confirmation**

### 5. Risk Management
- **Dynamic Stop Loss Placement**
- **Position Sizing Calculations**
- **Risk/Reward Ratio Analysis**
- **Performance Metrics Tracking**

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage
```python
from src.main import BTCSmartMoneyChart

# Initialize the chart
chart = BTCSmartMoneyChart()

# Start live chart with real-time updates
chart.run_live()
```

### Configuration
Edit `config.py` to customize:
- Timeframe settings
- Fibonacci levels
- Signal thresholds
- Risk management parameters

## Project Structure

```
btc/
├── src/
│   ├── smart_money_concepts.py    # SMC implementation
│   ├── fibonacci_analysis.py      # Fibonacci calculations
│   ├── elliott_wave.py             # Elliott Wave detection
│   ├── data_processing.py          # Data acquisition & processing
│   ├── signal_generator.py         # Signal generation logic
│   ├── chart_visualizer.py         # Plotly chart visualization
│   ├── risk_management.py          # Risk & position management
│   └── main.py                     # Main application
├── config.py                       # Configuration settings
├── requirements.txt                # Dependencies
└── README.md                       # Documentation
```

## Trading Strategies Implemented

### 1.1. Liquidity Sweep & Reversal
Detection of stop hunts followed by rapid reversals at key levels.

### 1.2. Liquidity Grab into FVG
Identification of liquidity grabs that fill into Fair Value Gaps.

### 1.3. Engineered Liquidity & False Breakouts
Recognition of institutional false breakout patterns.

### 1.4. Run on Stops
Detection of cascading stop loss triggers.

## The Perfect Entry Formula

**Signal Components:**
- Liquidity Sweep
- Order Block (OB)
- Fair Value Gap (FVG)
- Market Structure (BOS/ChoCh)
- Session Timing (London/NY Opens)
- Premium/Discount Zone
- Volume Confirmation

## Performance Metrics

The system tracks:
- Win Rate
- Profit Factor
- Maximum Drawdown
- Average Risk/Reward Ratio
- Sharpe Ratio
- Expected Value per Trade

## Disclaimer

This software is for educational and research purposes only. Trading cryptocurrencies carries substantial risk. Always perform your own analysis and never risk more than you can afford to lose.

## License

MIT License
