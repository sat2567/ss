import yfinance as yf
import pandas as pd
import streamlit as st
import plotly.graph_objs as go

indices = {
    "Gold (COMEX Futures)": "GC=F",
    "S&P 500": "^GSPC",
    "Dow Jones": "^DJI",
    "Nasdaq": "^IXIC",
    "Shanghai Composite": "000001.SS",
    "Shenzhen Component": "399001.SZ"
}

# Download data
data = {}
for name, symbol in indices.items():
    df = yf.download(symbol, period="5y", interval="1wk", auto_adjust=True)
    if not df.empty:
        df = df[["Close"]].rename(columns={"Close": "Close"})
        df.index = pd.to_datetime(df.index)
        data[name] = df
        st.success(f"✅ Downloaded {name}")
    else:
        st.warning(f"❌ No data for {name}")

# Select indices to plot
selected_indices = st.multiselect("Choose indices to plot", options=list(data.keys()), default=list(data.keys()))

# Date selection sliders (global min-max over all data)
all_dates = pd.concat([df.index.to_series() for df in data.values()])
min_date = all_dates.min()
max_date = all_dates.max()
start_date, end_date = st.date_input("Select date range", value=[min_date, max_date], min_value=min_date, max_value=max_date)

# Moving average windows to select
ma_windows = st.multiselect("Select Moving Average Windows (days)", options=[5, 10, 20, 50, 100, 200], default=[50])

for name in selected_indices:
    df = data[name]
    df_filtered = df.loc[start_date:end_date]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_filtered.index, y=df_filtered["Close"], mode="lines", name=f"{name} Close"))

    for window in ma_windows:
        col_name = f"MA{window}"
        df_filtered[col_name] = df_filtered
