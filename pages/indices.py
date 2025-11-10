import pandas as pd
import streamlit as st
import plotly.graph_objs as go

# CSV data URLs
csv_files = {
    "NIFTY BANK": "NIFTY BANK-10-10-2025-to-10-11-2025.csv",
    "NIFTY 50": "https://github.com/sat2567/ss/blob/my-new-branch/NIFTY%2050-10-10-2025-to-10-11-2025.csv",
    "NIFTY MIDCAP 100": "https://raw.githubusercontent.com/sat2567/ss/my-new-branch/NIFTY%20MIDCAP%20100-29-09-2024-to-29-09-2025.csv",
    "NIFTY SMALLCAP 100": "NIFTY SMALLCAP 250-10-10-2025-to-10-11-2025.csv"
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

# Load and normalize CSV data
csv_data = {name: normalize_csv(pd.read_csv(url)) for name, url in csv_files.items()}

st.title('CSV Indices Closing Prices & Moving Averages')

all_dates = pd.concat([df.index.to_series() for df in csv_data.values()])
min_date, max_date = all_dates.min(), all_dates.max()

start_date, end_date = st.date_input(
    'Select Date Range',
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date,
    key='date_range'
)

filtered_data = {name: df.loc[start_date:end_date] for name, df in csv_data.items()}

indices = st.multiselect('Select Indices to Plot', options=list(filtered_data.keys()), default=list(filtered_data.keys()))
ma_windows = st.multiselect('Select Moving Average Windows (days)', options=[10, 20, 50, 100, 200], default=[50, 200])

for name in indices:
    df = filtered_data[name].copy()
    st.subheader(name)
    fig = go.Figure()
    # Plot Close price
    fig.add_trace(go.Scatter(x=df.index, y=df['CLOSE'], mode='lines', name='Close', line=dict(width=2)))
    # Plot MAs
    for window in ma_windows:
        ma_label = f'MA{window}'
        df[ma_label] = df['CLOSE'].rolling(window=window).mean()
        fig.add_trace(go.Scatter(x=df.index, y=df[ma_label], mode='lines', name=f'{window}-Day MA', line=dict(dash='dash')))
    fig.update_layout(xaxis_title='Date', yaxis_title='Price', hovermode='x unified', height=500)
    st.plotly_chart(fig, use_container_width=True)
