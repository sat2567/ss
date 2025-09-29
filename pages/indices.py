import yfinance as yf
import pandas as pd
import streamlit as st
import plotly.graph_objs as go

# CSV data URLs
csv_files = {
    "NIFTY BANK": "https://raw.githubusercontent.com/sat2567/ss/my-new-branch/NIFTY%20BANK-29-09-2024-to-29-09-2025.csv",
    "NIFTY 50": "https://raw.githubusercontent.com/sat2567/ss/my-new-branch/NIFTY%2050-29-09-2024-to-29-09-2025.csv",
    "NIFTY MIDCAP 100": "https://raw.githubusercontent.com/sat2567/ss/my-new-branch/NIFTY%20MIDCAP%20100-29-09-2024-to-29-09-2025.csv",
    "NIFTY SMALLCAP 100": "https://raw.githubusercontent.com/sat2567/ss/my-new-branch/NIFTY%20SMALLCAP%20100-29-09-2024-to-29-09-2025.csv"
}

# yfinance symbols
yf_indices = {
    "Gold (COMEX Futures)": "GC=F",
    "S&P 500": "^GSPC",
    "Dow Jones": "^DJI",
    "Nasdaq": "^IXIC",
    "Shanghai Composite": "000001.SS",
    "Shenzhen Component": "399001.SZ"
}

def normalize_csv(df):
    df.columns = df.columns.str.strip().str.upper()
    date_col = next(col for col in ['DATE', 'Date', 'date'] if col in df.columns)
    df[date_col] = pd.to_datetime(df[date_col], dayfirst=True)
    df.set_index(date_col, inplace=True)
    if 'VOLUME' not in df.columns and 'SHARES TRADED' in df.columns:
        df.rename(columns={'SHARES TRADED': 'VOLUME'}, inplace=True)
    if 'CLOSE' not in df.columns:
        close_candidates = [c for c in df.columns if 'CLOSE' in c]
        if close_candidates:
            df.rename(columns={close_candidates[0]: 'CLOSE'}, inplace=True)
    df['CLOSE'] = pd.to_numeric(df['CLOSE'], errors='coerce')
    return df[['CLOSE']].sort_index()

def normalize_yf(df):
    df.rename(columns=str.upper, inplace=True)
    df.index = pd.to_datetime(df.index)
    if 'CLOSE' not in df.columns:
        df['CLOSE'] = pd.NA
    col = df['CLOSE']
    if hasattr(col, 'ndim') and col.ndim > 1:
        df['CLOSE'] = col.iloc[:, 0]
    df['CLOSE'] = pd.to_numeric(df['CLOSE'], errors='coerce')
    return df[['CLOSE']].sort_index()

csv_data = {name: normalize_csv(pd.read_csv(url)) for name, url in csv_files.items()}

yf_data = {}
for name, ticker in yf_indices.items():
    df = yf.download(ticker, period='1y', interval='1wk', auto_adjust=True)
    if not df.empty:
        yf_data[name] = normalize_yf(df)

all_data = {**csv_data, **yf_data}

st.title('Indices Closing Prices & Moving Averages')

all_dates = pd.concat([df.index.to_series() for df in all_data.values()])
min_date, max_date = all_dates.min(), all_dates.max()

start_date, end_date = st.date_input(
    'Select Date Range',
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date,
    key='date_range'
)

filtered_data = {name: df.loc[start_date:end_date] for name, df in all_data.items()}

indices = st.multiselect('Select Indices', options=list(filtered_data.keys()), default=list(filtered_data.keys()))
ma_windows = st.multiselect('Moving Average Windows (days)', options=[10, 20, 50, 100, 200], default=[50, 200])

for name in indices:
    df = filtered_data[name].copy()
    st.subheader(name)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['CLOSE'], mode='lines', name='Close', line=dict(width=2)))

    for window in ma_windows:
        ma_label = f'MA{window}'
        df[ma_label] = df['CLOSE'].rolling(window=window).mean()
        fig.add_trace(go.Scatter(x=df.index, y=df[ma_label], mode='lines', name=f'{window}-Day MA', line=dict(dash='dash')))

    fig.update_layout(xaxis_title='Date', yaxis_title='Price', hovermode='x unified', height=500)
    st.plotly_chart(fig, use_container_width=True)
