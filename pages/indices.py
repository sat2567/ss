import pandas as pd
import streamlit as st
import plotly.graph_objs as go

# CSV data URLs
csv_files = {
    "NIFTY BANK": "NIFTY BANK-10-10-2025-to-10-11-2025.csv",
    "NIFTY 50": "NIFTY 50-10-10-2025-to-10-11-2025.csv",
    "NIFTY MIDCAP 100": "NIFTY MIDCAP 150-10-10-2025-to-10-11-2025.csv",
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

st.title('Compare Indices: Closing Prices')

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

# Select indices
indices = st.multiselect('Select Indices to Plot', options=list(filtered_data.keys()), default=list(filtered_data.keys()))

# Normalization option
normalize_option = st.checkbox('Normalize Prices (Start at 100)', value=True)
yaxis_label = 'Normalized Price (Start = 100)' if normalize_option else 'Price'

# Create a combined chart
fig = go.Figure()

for name in indices:
    df = filtered_data[name].copy()

    # Normalize if selected
    if normalize_option:
        if not df['CLOSE'].empty:
            base = df['CLOSE'].iloc[0]
            df['CLOSE_NORM'] = (df['CLOSE'] / base) * 100
            plot_col = 'CLOSE_NORM'
        else:
            plot_col = 'CLOSE'
    else:
        plot_col = 'CLOSE'

    # Add main close line
    fig.add_trace(go.Scatter(
        x=df.index, y=df[plot_col],
        mode='lines', name=f'{name} (Close)',
        line=dict(width=2)
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
