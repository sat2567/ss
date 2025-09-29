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

selected_indices = st.multiselect("Choose indices to plot", options=list(data.keys()), default=list(data.keys()))
all_dates = pd.concat([df.index.to_series() for df in data.values()])
start_date, end_date = st.date_input("Select date range", value=[all_dates.min(), all_dates.max()], min_value=all_dates.min(), max_value=all_dates.max())
ma_windows = st.multiselect("Select Moving Average Windows (days)", options=[5, 10, 20, 50, 100, 200], default=[50])

for name in selected_indices:
    df = data[name]
    df_filtered = df.loc[start_date:end_date].copy()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_filtered.index, y=df_filtered["Close"], mode="lines", name=f"{name} Close"))

    for window in ma_windows:
        col_name = f"MA{window}"
        df_filtered[col_name] = df_filtered["Close"].rolling(window=window).mean()
        fig.add_trace(go.Scatter(x=df_filtered.index, y=df_filtered[col_name], mode="lines", name=f"{name} {window}-Day MA", line=dict(dash='dash')))

    fig.update_layout(title=f"{name} Closing Price with Moving Averages",
                      xaxis_title="Date",
                      yaxis_title="Price",
                      hovermode="x unified",
                      height=400)

    st.plotly_chart(fig, use_container_width=True)
