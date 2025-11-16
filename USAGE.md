# Usage Guide

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### Option 1: Using the run script
```bash
python run.py
```

### Option 2: Direct execution
```bash
python src/main.py
```

## Modes of Operation

### 1. Analysis & Chart Mode
Analyzes historical data and generates an interactive chart with all signals and indicators.

```python
from src.main import BTCSmartMoneyChart

system = BTCSmartMoneyChart()
results = system.run_analysis(timeframe='15m', lookback=500)
system.create_chart(results)
```

### 2. Backtest Mode
Tests the strategy on historical data and provides performance metrics.

```python
system = BTCSmartMoneyChart()
system.run_backtest(timeframe='15m', lookback=1000)
```

Expected output:
- Total trades
- Win rate
- Profit factor
- Maximum drawdown
- Sharpe ratio
- Detailed trade statistics

### 3. Live Mode
Continuously updates the chart with live data.

```python
system = BTCSmartMoneyChart()
system.run_live(timeframe='15m', update_interval=60)
```

### 4. Quick Scan
Quick market scan for current conditions and active signals.

```python
system = BTCSmartMoneyChart()
system.quick_scan()
```

## Understanding the Signals

### Signal Quality Levels

**HIGH Quality (5+ confluence factors)**
- Best probability setups
- Multiple confirmations aligned
- Recommended for trading

**MEDIUM Quality (3-4 confluence factors)**
- Good probability setups
- Some confirmations present
- Consider with caution

**LOW Quality (2 confluence factors)**
- Lower probability
- Minimal confirmation
- Not recommended for live trading

### Confluence Factors

The system checks for these confluence factors:

1. **HTF Trend Alignment** - Higher timeframe confirms direction
2. **Liquidity Sweep** - Stop hunt detected and confirmed reversal
3. **Order Block** - Price in institutional order block zone
4. **Fair Value Gap** - Price in unfilled FVG
5. **Fibonacci Zone** - Price in discount/premium or golden pocket
6. **Elliott Wave** - Wave 2 or Wave 4 retracement entry
7. **Market Structure** - BOS or ChoCh confirmation
8. **Volume Confirmation** - Above-average volume
9. **Session Timing** - London or NY session open

### Reading the Chart

**Colors:**
- Green: Bullish elements (bullish OBs, FVGs, buy signals)
- Red: Bearish elements (bearish OBs, FVGs, sell signals)
- Orange: Fibonacci levels
- Purple: Equilibrium (50%)
- Gold: Golden Pocket (61.8-78.6%)

**Markers:**
- Triangle Up (Green): Buy signal
- Triangle Down (Red): Sell signal
- 💰: Liquidity sweep
- Circles: Swing highs/lows

## Configuration

Edit `config.py` to customize:

### Trading Pair
```python
SYMBOL = 'BTCUSDT'
```

### Timeframes
```python
TIMEFRAMES = {
    'primary': '15m',
    'htf': '4h',
    'ltf': '5m',
}
```

### Risk Management
```python
RISK_MANAGEMENT = {
    'default_risk_per_trade': 0.01,  # 1% risk
    'min_risk_reward_ratio': 2.0,     # Minimum 1:2 RR
    'max_concurrent_trades': 3,
}
```

### Signal Filters
```python
SIGNAL_SETTINGS = {
    'min_confluence_score': 3,
    'require_htf_alignment': True,
    'require_session_timing': False,
}
```

## Example Workflow

### For Day Trading

1. **Morning Scan** (before London/NY open)
```python
system.quick_scan()
```

2. **Generate Signals** on 5m or 15m
```python
results = system.run_analysis(timeframe='5m')
```

3. **Monitor Live** during trading sessions
```python
system.run_live(timeframe='5m', update_interval=30)
```

### For Swing Trading

1. **Daily Analysis** on 1h or 4h
```python
results = system.run_analysis(timeframe='4h')
system.create_chart(results)
```

2. **Review Backtest** performance
```python
system.run_backtest(timeframe='4h', lookback=2000)
```

## Understanding Output Files

### Chart File (btc_smart_money_chart.html)
- Interactive Plotly chart
- Pan, zoom, hover for details
- Can be shared or embedded

### Log File (btc_smart_money.log)
- Detailed execution logs
- Error messages
- Analysis results

## Tips for Best Results

1. **Wait for Confluence** - Don't trade signals with less than 3 confluence factors
2. **Check HTF First** - Always verify higher timeframe trend
3. **Trade Session Opens** - Best setups occur during London/NY opens
4. **Use Risk Management** - Never risk more than 1-2% per trade
5. **Backtest First** - Verify strategy performance before live trading
6. **Golden Pocket Priority** - Highest probability entries in 61.8-78.6% zone
7. **Volume Matters** - Confirm breakouts with volume spikes
8. **Respect Market Structure** - Trade with BOS, be cautious on ChoCh

## Troubleshooting

### No signals generated
- Lower `min_confluence_score` in config
- Set `require_htf_alignment` to False
- Increase `lookback` period

### Chart not displaying
- Check internet connection (for Binance API)
- Verify Plotly installation
- Check browser compatibility

### API errors
- Verify Binance API is accessible
- Check rate limits
- Retry after delay

## Performance Optimization

For faster analysis:
- Reduce lookback periods
- Use higher timeframes
- Limit number of Fibonacci retracements
- Disable session timing requirement

## Next Steps

1. **Backtest Thoroughly** - Test on at least 1000 candles
2. **Paper Trade** - Simulate trades before going live
3. **Track Results** - Keep a trading journal
4. **Optimize Settings** - Fine-tune confluence requirements
5. **Stay Disciplined** - Follow the signals, manage risk

## Support

For issues or questions:
- Review logs in `btc_smart_money.log`
- Check configuration settings
- Verify data connectivity
- Consult strategy documentation in README.md
