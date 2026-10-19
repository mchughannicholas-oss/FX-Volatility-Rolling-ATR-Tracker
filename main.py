import streamlit as st
import matplotlib.pyplot as plt
from core_analytics import fetch_and_process_fx_data

# Page Configuration
st.set_page_config(
    page_title="FX Volatility & ATR Tracker",
    page_icon="📈",
    layout="wide"
)

st.title("📈 FX Volatility & Rolling ATR Tracker")
st.markdown("Analyze currency pair volatility, ATR percentiles, and regime shifts in real time.")

# Sidebar Controls
st.sidebar.header("Market Controls")
ticker_choice = st.sidebar.selectbox("Currency Pair", ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X"])
period_choice = st.sidebar.selectbox("Historical Lookback", ["1y", "2y", "5y"], index=1)

# Cached Data Pipeline (prevents reloading on every click)
@st.cache_data(ttl=3600)
def load_data(ticker, period):
    return fetch_and_process_fx_data(ticker, period)

with st.spinner("Fetching and processing market data..."):
    df = load_data(ticker_choice, period_choice)

# Latest Analytics Summary Cards
latest = df.iloc[-1]
col1, col2, col3, col4 = st.columns(4)

col1.metric("Latest Close", f"{float(latest['Close']):.4f}")
col2.metric("14-Day ATR", f"{float(latest['ATR']):.4f}")
col3.metric("Volatility Regime", str(latest["Volatility_Regime"]))
col4.metric("ATR Ratio (5/50)", f"{float(latest['ATR_Ratio']):.2f}")

# Display Raw Head Data Expandable Section
with st.expander("View Recent Analytics Table"):
    st.dataframe(df[["Close", "ATR", "Volatility_Pct", "ATR_Percentile", "Volatility_Regime", "ATR_Ratio"]].tail(10))

# Plotting Price vs ATR
st.subheader("Price Action & Volatility Regime Visualization")
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

ax1.plot(df.index, df["Close"], label=f"{ticker_choice} Close", color="#1f77b4")
ax1.set_title(f"{ticker_choice} Price vs. Rolling ATR Volatility")
ax1.set_ylabel("Price")
ax1.grid(True, alpha=0.3)
ax1.legend(loc="upper left")

ax2.plot(df.index, df["ATR"], label="14-Day Wilder's ATR", color="#ff7f0e")
ax2.set_title("14-Period Average True Range (ATR)")
ax2.set_xlabel("Date")
ax2.set_ylabel("ATR Range")
ax2.grid(True, alpha=0.3)
ax2.legend(loc="upper left")

plt.tight_layout()
st.pyplot(fig)

