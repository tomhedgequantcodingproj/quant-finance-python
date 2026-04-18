# Quant Finance Python

A collection of Python tools for quantitative stock analysis, built from scratch. Covers data download, financial metric calculation, signal generation, backtesting, and automated screening.

Built using: `yfinance`, `pandas`, `numpy`, `matplotlib`

---

## Tools

### 1. `stock_analysis.py` — Stock Analysis Class
A reusable `Stock` class that analyses any ticker supported by yfinance.

**Metrics calculated:**
- Total return (%)
- Daily volatility
- Sharpe ratio (risk-adjusted return)
- Best and worst single trading day
- Current SMA crossover signal (BUY / SELL / NEUTRAL)

```python
stock = Stock("AAPL", "2025-01-01", "2026-01-01")
stock.summary()
```

---

### 2. `stock_screener.py` — Automated Stock Screener
Automatically downloads the last 12 months of data for a configurable list of stocks and ranks them by total return, volatility, and Sharpe ratio. Exports results to CSV.

```
─── Best to Worst Total Return ───
  1. LITE        1518.50%
  2. BE          1096.23%
  ...

Results saved to stock_screener.csv
```

---

### 3. `sma_backtester.py` — SMA Crossover Backtester
Backtests a 20/50 day Simple Moving Average crossover strategy on any stock. Tracks every trade, calculates profit per share, and plots the price chart with moving averages.

**Strategy:**
- **BUY** when 20-day SMA crosses above 50-day SMA (Golden Cross)
- **SELL** when 20-day SMA crosses below 50-day SMA (Death Cross)

---

### 4. `volatility_screener.py` — Volatility Screener
Downloads data for a list of stocks and ranks them from least to most volatile, identifying the safest and riskiest options.

---

## Setup

```bash
pip install yfinance pandas matplotlib numpy
```

---

## Notes
- ASX stocks use the `.AX` suffix (e.g. `BHP.AX`)
- US stocks use the raw ticker (e.g. `AAPL`, `MSFT`)
- All tools are configurable by editing the `TICKERS` list at the top of each file
- Not financial advice
