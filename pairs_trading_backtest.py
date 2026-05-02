import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
# -----------------------------------------------------------------------------------
# Config
TICKER1 = "RIO.AX"
TICKER2 = "BHP.AX"
START = "2024-04-01"
END = "2026-04-01"
ZSCORE_ENTRY = 2      # enter trade when z-score exceeds this threshold
ZSCORE_EXIT = 0.5     # exit trade when z-score returns within this range of zero
WINDOW = 30           # rolling window for z-score calculation
# -----------------------------------------------------------------------------------
#  Downloads price data 
df1 = yf.download(TICKER1, start=START, end=END, progress=False)
df2 = yf.download(TICKER2, start=START, end=END, progress=False)

close1 = df1["Close"].squeeze()
close2 = df2["Close"].squeeze()

#  Normalises prices to start at 1.0 so they're directly comparable  
normalised1 = close1 / close1.iloc[0]
normalised2 = close2 / close2.iloc[0]

# Calculates spread and rolling z-score 
# Spread measures the divergence
spread = normalised1 - normalised2

# Z-score measures how many standard deviations the spread is from its rolling mean
# High z-score = TICKER1 expensive relative to TICKER2
# Low z-score  = TICKER2 expensive relative to TICKER1
spread_mean = spread.rolling(window=WINDOW).mean()
spread_std = spread.rolling(window=WINDOW).std()
z_score = (spread - spread_mean) / spread_std

# Builds signals DataFrame 
signals = pd.DataFrame()
signals["rio"] = close1
signals["bhp"] = close2
signals["z_score"] = z_score
signals["normalised1"] = normalised1
signals["normalised2"] = normalised2

# Backtest 
# Strategies:
#   z > +2 → short RIO, long BHP (RIO expensive relative to BHP)
#   z < -2 → short BHP, long RIO (BHP expensive relative to RIO)
#   |z| < 0.5 → exit (spread has converged back to mean)
in_position = False
position_direction = None
entry_rio = None
entry_bhp = None
total_profit = 0
trade_profits = []

print(f"\n--- Trade Log ({TICKER1} vs {TICKER2}) ---")
for date, row in signals.iterrows():
    # Entry RIO expensive relative to BHP
    if row["z_score"] > ZSCORE_ENTRY and not in_position:
        entry_rio = row["rio"]
        entry_bhp = row["bhp"]
        in_position = True
        position_direction = "long_bhp"

    # Entry BHP expensive relative to RIO 
    elif row["z_score"] < -ZSCORE_ENTRY and not in_position:
        entry_rio = row["rio"]
        entry_bhp = row["bhp"]
        in_position = True
        position_direction = "long_rio"

    # Exit spread has converged
    elif in_position and abs(row["z_score"]) < ZSCORE_EXIT:
        if position_direction == "long_bhp":
            profit = (entry_rio - row["rio"]) + (row["bhp"] - entry_bhp)
        elif position_direction == "long_rio":
            profit = (entry_bhp - row["bhp"]) + (row["rio"] - entry_rio)
        total_profit += profit
        trade_profits.append(profit)
        print(f"{date.date()} | Profit: ${profit:+.2f}")
        in_position = False

# Summary 
print(f"\n--- Backtest Summary ---")
print(f"Total Trades:   {len(trade_profits)}")
print(f"Total Profit:   ${total_profit:.2f}")
print(f"Average Profit: ${total_profit / len(trade_profits):.2f} per trade")

# Kelly Criterion 
def kelly_criterion(trade_profits):
    wins = [p for p in trade_profits if p > 0]
    losses = [abs(p) for p in trade_profits if p < 0]
    if not trade_profits or not wins or not losses:
        print("Not enough data for Kelly Criterion.")
        return
    win_rate = len(wins) / len(trade_profits)
    avg_win = sum(wins) / len(wins)
    avg_loss = sum(losses) / len(losses)
    kelly = win_rate - ((1 - win_rate) / (avg_win / avg_loss))
    print(f"Win Rate:       {win_rate:.2%}")
    print(f"Avg Win:        ${avg_win:.2f}")
    print(f"Avg Loss:       ${avg_loss:.2f}")
    print(f"Kelly %:        {kelly:.2%}")
    if kelly > 0.25:
        print("Verdict: Strong bet.")
    elif kelly > 0:
        print("Verdict: Modest bet.")
    else:
        print("Verdict: Don't trade this strategy.")

kelly_criterion(trade_profits)