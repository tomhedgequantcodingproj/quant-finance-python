import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
# -----------------------------------------------------------------------------------------------
# Config 
TICKER = "YAL.AX"
YEARS = 4  # total period to analyse
# -----------------------------------------------------------------------------------------------

# Calculate start, midpoint and end dates to automatically split the data into in-sample and out-of-sample
end = datetime.today()
start = end - timedelta(days=365 * YEARS)
midpoint = start + timedelta(days=365 * YEARS // 2)  # halfway point

# convert to strings for yfinance
start_str = start.strftime("%Y-%m-%d")
mid_str = midpoint.strftime("%Y-%m-%d")
end_str = end.strftime("%Y-%m-%d")


# Download data 
def run_backtest(ticker, start, end, label):
    df = yf.download(ticker, start=start, end=end, progress=False)
    close = df["Close"].squeeze()  # extract close prices as a plain Series
    
    sma20 = close.rolling(window=20).mean()  # average of last 20 days — short term trend
    sma50 = close.rolling(window=50).mean()  # average of last 50 days — long term trend

    # Build signals DataFrame 
    signals = pd.DataFrame()
    signals["close"] = close
    signals["sma20"] = sma20
    signals["sma50"] = sma50

    # signal = 1 when sma20 is above sma50 (uptrend), 0 when below (downtrend)
    signals["signal"] = 0
    signals.loc[signals["sma20"] > signals["sma50"], "signal"] = 1

    # diff() detects when signal changes — +1 is golden cross (buy), -1 is death cross (sell)
    signals["crossover"] = signals["signal"].diff()

    # Backtest loop 
    buy_price = None
    in_position = False
    total_profit = 0
    trade_profits = []

    for date, row in signals.iterrows():
        # golden cross — buy if not already holding
        if row["crossover"] == 1 and not in_position:
            buy_price = row["close"]
            stop_loss = buy_price * (1 - 0.02)
            take_profit = buy_price * (1 + 0.03)
            in_position = True

        # take profit hit
        elif in_position and row["close"] >= take_profit:
            profit = row["close"] - buy_price
            total_profit += profit
            trade_profits.append(profit)
            in_position = False

        # death cross — sell if holding
        elif row["crossover"] == -1 and in_position:
            profit = row["close"] - buy_price
            total_profit += profit
            trade_profits.append(profit)
            in_position = False

        # stop loss hit
        elif in_position and row["close"] <= stop_loss:
            profit = row["close"] - buy_price
            total_profit += profit
            trade_profits.append(profit)
            in_position = False

    # Results 
    def kelly_criterion(trade_profits):
        wins = [p for p in trade_profits if p > 0]
        losses = [abs(p) for p in trade_profits if p < 0]
        if not trade_profits or not wins or not losses:
            return 0.0
        win_rate = len(wins) / len(trade_profits)
        avg_win = sum(wins) / len(wins)
        avg_loss = sum(losses) / len(losses)
        return win_rate - ((1 - win_rate) / (avg_win / avg_loss))

    kelly = kelly_criterion(trade_profits)

    print(f"Total Trades:  {len(trade_profits)}")
    print(f"Total Profit:  ${total_profit:.2f}")
    print(f"Kelly %:       {kelly:.2%}")

    return total_profit, kelly

run_backtest(TICKER, start_str, mid_str, "IN SAMPLE")
run_backtest(TICKER, mid_str, end_str, "OUT OF SAMPLE")
