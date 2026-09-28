import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import yfinance as yf

# =====================================================================
# 1. Data Ingestion and API Selection
# =====================================================================
# Define the currency pairs and time period
currency_pairs = ["EURUSD=X"]

# Download 2 years of daily data (2y provides enough history for 252-day percentiles)
df = yf.download(currency_pairs, period="2y", interval="1d")

# Flatten MultiIndex columns returned by yfinance if present
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.droplevel(1)

# Drop volume column cleanly
if "Volume" in df.columns:
    df = df.drop(columns=["Volume"])

# Display OHLC data
print("--- HEAD DATA ---")
print(df.head())

# Check for missing values
print("\n--- MISSING VALUES CHECK ---")
print(df.isnull().sum())


# =====================================================================
# 2. Calculate ATR (Average True Range) & Data Architecture
# =====================================================================
high = df["High"]
low = df["Low"]
prev_close = df["Close"].shift(1)

# The 3 components of True Range
tr1 = high - low
tr2 = (high - prev_close).abs()
tr3 = (low - prev_close).abs()

# The True Range is the maximum of the three components for each row
df["True_Range"] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

# 14-day Wilder's ATR
period = 14
df["ATR"] = (
    df["True_Range"]
    .ewm(alpha=1 / period, min_periods=period, adjust=False)
    .mean()
)

# Normalizing Volatility (% of Spot Price)
df["Volatility_Pct"] = (df["ATR"] / df["Close"]) * 100


# =====================================================================
# 3. Key Analytical Features to Build
# =====================================================================

# Feature 3A: Volatility Percentile Rank & Regime Detection
rank_window = 252  # 252 trading days = 1 calendar year

df["ATR_Percentile"] = (
    df["ATR"]
    .rolling(window=rank_window, min_periods=rank_window)
    .rank(pct=True)
    * 100
)


def categorize_regime(pct):
    if pd.isna(pct):
        return None
    elif pct >= 80:
        return "High Volatility"
    elif pct <= 20:
        return "Volatility Squeeze"
    else:
        return "Normal Volatility"


df["Volatility_Regime"] = df["ATR_Percentile"].apply(categorize_regime)

# Feature 3B: Volatility Ratio Analysis (Short-term vs. Long-term ATR)
atr_short_period = 5
atr_long_period = 50

df["ATR_5"] = (
    df["True_Range"]
    .ewm(alpha=1 / atr_short_period, min_periods=atr_short_period, adjust=False)
    .mean()
)

df["ATR_50"] = (
    df["True_Range"]
    .ewm(alpha=1 / atr_long_period, min_periods=atr_long_period, adjust=False)
    .mean()
)

# Ratio > 1.0 = Volatility Expansion | Ratio < 1.0 = Volatility Contraction
df["ATR_Ratio"] = df["ATR_5"] / df["ATR_50"]

# Output key metrics
print("\n--- LATEST ANALYTICS OUTPUT ---")
print(
    df[
        [
            "Close",
            "ATR",
            "Volatility_Pct",
            "ATR_Percentile",
            "Volatility_Regime",
            "ATR_Ratio",
        ]
    ].tail(10)
)


# =====================================================================
# 4. Code Architecture & Project Design (Visual Plot Output)
# =====================================================================
# Plotting Price vs ATR and Volatility Regimes
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

# Top Chart: EUR/USD Price
ax1.plot(df.index, df["Close"], label="EUR/USD Close", color="blue")
ax1.set_title("EUR/USD Price vs. Rolling ATR Volatility")
ax1.set_ylabel("Price")
ax1.grid(True)
ax1.legend(loc="upper left")

# Bottom Chart: 14-Day ATR
ax2.plot(df.index, df["ATR"], label="14-Day ATR", color="orange")
ax2.set_title("14-Period Average True Range (ATR)")
ax2.set_xlabel("Date")
ax2.set_ylabel("ATR Range")
ax2.grid(True)
ax2.legend(loc="upper left")

plt.tight_layout()
plt.show()

