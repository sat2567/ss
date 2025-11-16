import pandas as pd
import streamlit as st
import plotly.graph_objs as go
summary_data = {
    "Index": ["Nifty 50", "Nifty Midcap 100", "Nifty Smallcap 100"],
    "Price (Nov 7)": [25492, 59843, 18076],
    "PE Ratio": [22.57, 33.5, 31.0],
    "20D MA": ["~25,520", "~59,700", "~18,150"],
    "50D MA": ["~25,315", "~58,950", "~17,990"],
    "100D MA": ["~25,210", "~57,900", "~17,910"],
    "200D MA": ["~24,440", "~54,100", "~16,750"],
    "RSI": [49.2, 50, 48],
    "MACD": ["Mild Bearish", "Mild Bullish", "Slightly Bearish"],
    "Technical Position": [
        "near 20D/50D support, neutral-bearish",
        "above major MAs, MACD neutral-bullish",
        "near short-term MAs, RSI neutral"
    ]
}

st.subheader("📈 Current Technical Overview (as of Nov 7)")
summary_df = pd.DataFrame(summary_data)
st.dataframe(summary_df, use_container_width=True)
# CSV data URLs
csv_files = {
    "NIFTY BANK": "NIFTY BANK-16-10-2025-to-16-11-2025.csv",
    "NIFTY 50": "NIFTY 50-16-10-2025-to-16-11-2025.csv",
    "NIFTY MIDCAP 100": "NIFTY MIDCAP 150-16-10-2025-to-16-11-2025.csv",
    "NIFTY SMALLCAP 100": "NIFTY SMALLCAP 250-16-10-2025-to-16-11-2025.csv"
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

st.title('Compare Indices: Closing Prices & Moving Averages')

# Find common date range
all_dates = pd.concat([df.index.to_series() for df in csv_data.values()])
min_date, max_date = all_dates.min(), all_dates.max()

start_date, end_date = st.date_input(
    'Select Date Range',
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date,
    key='date_range'
)

# Filter data by selected range
filtered_data = {name: df.loc[start_date:end_date] for name, df in csv_data.items()}

# Select indices and MAs
indices = st.multiselect('Select Indices to Plot', options=list(filtered_data.keys()), default=list(filtered_data.keys()))
ma_windows = st.multiselect('Select Moving Average Windows (days)', options=[10, 20, 50, 100, 200], default=[50, 200])

# Normalization option
normalize_option = st.checkbox('Normalize Prices (Start at 100)', value=True)

# Create a combined chart
fig = go.Figure()

for name in indices:
    df = filtered_data[name].copy()

    # Normalize if selected
    if normalize_option:
        base = df['CLOSE'].iloc[0]
        df['CLOSE_NORM'] = (df['CLOSE'] / base) * 100
        plot_col = 'CLOSE_NORM'
        yaxis_label = 'Normalized Price (Start = 100)'
    else:
        plot_col = 'CLOSE'
        yaxis_label = 'Price'

    # Add main close line
    fig.add_trace(go.Scatter(
        x=df.index, y=df[plot_col],
        mode='lines', name=f'{name} (Close)',
        line=dict(width=2)
    ))

    # Add moving averages
    for window in ma_windows:
        ma_label = f'{name} MA{window}'
        df[ma_label] = df[plot_col].rolling(window=window).mean()
        fig.add_trace(go.Scatter(
            x=df.index, y=df[ma_label],
            mode='lines', name=f'{name} {window}-Day MA',
            line=dict(dash='dash')
        ))

# Layout
fig.update_layout(
    title="Indices Comparison Chart",
    xaxis_title='Date',
    yaxis_title=yaxis_label,
    hovermode='x unified',
    height=600,
    legend=dict(orientation='h', y=-0.2)
)

st.plotly_chart(fig, use_container_width=True)
