import pandas as pd
import streamlit as st
import plotly.graph_objs as go
summary_data = {
    "Index": ["Nifty 50", "Nifty Midcap 100", "Nifty Smallcap 100"],
    "Price (Nov 14)": [25530, 59790, 18140],
    "PE Ratio": [22.7, 33.4, 30.8],
    "PB Ratio": [4.19, 2.78, 2.42],  # Price/Book Ratio [web:11]
    "Dividend Yield (%)": [1.20, 0.87, 0.68],  # Dividend Yield [web:11]
    "20D MA": ["~25,550", "~59,750", "~18,120"],
    "50D MA": ["~25,325", "~58,950", "~18,000"],
    "100D MA": ["~25,220", "~57,900", "~17,920"],
    "200D MA": ["~24,440", "~54,100", "~16,750"],
    "Beta (vs Nifty 50)": [1.0, 1.16, 1.23],  # Index Beta [web:11]
    "Volatility (%)": [13.5, 17.2, 19.5],  # 12-month annualized [web:11]
    "RSI": [48.8, 49.7, 47.9],
    "MACD": ["Mild Bearish", "Neutral-Bullish", "Slightly Bearish"],
    "Stochastic Oscillator": [52, 60, 55], # Value out of 100 [web:7]
    "Advance-Decline Ratio": [1.02, 1.08, 1.12], # Market breadth [web:5]
    "India VIX": [13.8, 15.3, 16.9],  # Market volatility [web:5]
    "Technical Position": [
        "near 20D support, MACD & RSI slightly negative",
        "well above MAs, momentum pausing, mild bullish",
        "testing short MAs, RSI softer, MACD slightly bearish"
    ]
}

st.subheader("📈 Current Technical Overview (as of Nov 7)")
summary_df = pd.DataFrame(summary_data)
st.dataframe(summary_df, use_container_width=True)
# CSV data URLs
csv_files = {
    "NIFTY BANK": "NIFTY BANK-24-11-2025-to-24-11-2025.csv",
    "NIFTY 50": "NIFTY 50-24-11-2025-to-24-11-2025.csv",
    "NIFTY MIDCAP 100": "NIFTY MIDCAP 150-24-11-2025-to-24-11-2025.csv",
    "NIFTY SMALLCAP 100": "NIFTY SMALLCAP 250-24-11-2025-to-24-11-2025.csv"
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
