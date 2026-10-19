import pandas as pd
import yfinance as yf

def fetch_and_process_fx_data(ticker: str = "EURUSD=X", period: str = "2y") -> pd.DataFrame:
    # 1. Data Ingestion
    df = yf.download(ticker, period=period, interval="1d")

    # Flatten MultiIndex columns if present
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)

    # Drop volume column cleanly
    if "Volume" in df.columns:
        df = df.drop(columns=["Volume"])

    # 2. Calculate ATR & True Range
    high = df["High"]
    low = df["Low"]
    prev_close = df["Close"].shift(1)

    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()

    df["True_Range"] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # 14-day Wilder's ATR
    period_atr = 14
    df["ATR"] = (
        df["True_Range"]
        .ewm(alpha=1 / period_atr, min_periods=period_atr, adjust=False)
        .mean()
    )

    df["Volatility_Pct"] = (df["ATR"] / df["Close"]) * 100

    # 3. Volatility Percentile Rank & Regime Detection
    rank_window = 252
    df["ATR_Percentile"] = (
        df["ATR"]
        .rolling(window=rank_window, min_periods=rank_window)
        .rank(pct=True)
        * 100
    )

    def categorize_regime(pct):
        if pd.isna(pct):
            return "Insufficient Data"
        elif pct >= 80:
            return "High Volatility"
        elif pct <= 20:
            return "Volatility Squeeze"
        else:
            return "Normal Volatility"

    df["Volatility_Regime"] = df["ATR_Percentile"].apply(categorize_regime)

    # 4. Volatility Ratio Analysis (Short-term vs. Long-term ATR)
    df["ATR_5"] = (
        df["True_Range"]
        .ewm(alpha=1 / 5, min_periods=5, adjust=False)
        .mean()
    )
    df["ATR_50"] = (
        df["True_Range"]
        .ewm(alpha=1 / 50, min_periods=50, adjust=False)
        .mean()
    )
    df["ATR_Ratio"] = df["ATR_5"] / df["ATR_50"]

    return df