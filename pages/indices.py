import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="🌍 Global Indices Dashboard", layout="wide")

st.title("📈 Global Indices Comparison Dashboard")

# --- INDEX OPTIONS ---
indices = {
    "Gold (COMEX Futures)": "GC=F",
    "S&P 500 (US)": "^GSPC",
    "Dow Jones (US)": "^DJI",
    "Nasdaq (US)": "^IXIC",
    "FTSE 100 (UK)": "^FTSE",
    "DAX (Germany)": "^GDAXI",
    "CAC 40 (France)": "^FCHI",
    "Nikkei 225 (Japan)": "^N225",
    "KOSPI (South Korea)": "^KS11",
    "Hang Seng (Hong Kong)": "^HSI",
    "Shanghai Composite (China)": "000001.SS",
    "Shenzhen Component (China)": "399001.SZ"
}

# --- SIDEBAR FILTERS ---
st.sidebar.header("🔧 Controls")

time_range = st.sidebar.selectbox(
    "Select Time Range",
    ["Last 30 Days", "Last 3 Months", "Last 1 Year", "Last 5 Years"]
)

if time_range == "Last 30 Days":
    start_date = datetime.now() - timedelta(days=30)
elif time_range == "Last 3 Months":
    start_date = datetime.now() - timedelta(days=90)
elif time_range == "Last 1 Year":
    start_date = datetime.now() - timedelta(days=365)
else:
    start_date = datetime.now() - timedelta(days=5 * 365)

selected_indices = st.sidebar.multiselect(
    "Select Indices to Display",
    list(indices.keys()),
    default=["Gold (COMEX Futures)", "S&P 500 (US)", "Nikkei 225 (Japan)"]
)

# --- FETCH DATA ---
@st.cache_data(show_spinner=False)
def fetch_data(symbols, start):
    data = {}
    for name, ticker in symbols.items():
        try:
            df = yf.download(ticker, start=start, progress=False)
            if not df.empty:
                data[name] = df["Close"]
            else:
                st.warning(f"⚠️ No data found for {name}")
        except Exception as e:
            st.warning(f"⚠️ Error fetching {name}: {e}")
    return data

data = fetch_data({k: indices[k] for k in selected_indices}, start_date)

if not data:
    st.error("No data available. Please try selecting different indices.")
    st.stop()

# --- MERGE & CLEAN ---
valid_data = {k: v for k, v in data.items() if v is not None and not v.empty}
df_all = pd.concat(valid_data.values(), axis=1)
df_all.columns = list(valid_data.keys())
df_filtered = df_all.ffill().dropna()

# --- PLOT ---
fig = go.Figure()

for col in df_filtered.columns:
    fig.add_trace(go.Scatter(
        x=df_filtered.index,
        y=df_filtered[col],
        mode="lines",
        name=col,
        hovertemplate="<b>%{text}</b><br>Date: %{x|%b %d, %Y}<br>Value: %{y:.2f}<extra></extra>",
        text=[col] * len(df_filtered)
    ))

# --- STYLE ---
fig.update_layout(
    title=f"Global Indices Performance ({time_range})",
    xaxis_title="Date",
    yaxis_title="Closing Price (normalized)",
    hovermode="x unified",  # temporary
    legend_title="Market Indices",
    template="plotly_white",
    hovermode="closest",  # ✅ show only hovered line!
    height=600
)

st.plotly_chart(fig, use_container_width=True)

# --- FOOTNOTE ---
st.caption("Data source: Yahoo Finance | Updated daily")
