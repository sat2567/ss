import pandas as pd
import streamlit as st
import plotly.graph_objs as go

# GitHub raw URLs of CSV files
files = {
    "NIFTY BANK": "https://raw.githubusercontent.com/sat2567/ss/my-new-branch/NIFTY%20BANK-29-09-2024-to-29-09-2025.csv",
    "NIFTY 50": "https://raw.githubusercontent.com/sat2567/ss/my-new-branch/NIFTY%2050-29-09-2024-to-29-09-2025.csv",
    "NIFTY MIDCAP 100": "https://raw.githubusercontent.com/sat2567/ss/my-new-branch/NIFTY%20MIDCAP%20100-29-09-2024-to-29-09-2025.csv",
    "NIFTY SMALLCAP 100": "https://raw.githubusercontent.com/sat2567/ss/my-new-branch/NIFTY%20SMALLCAP%20100-29-09-2024-to-29-09-2025.csv"
}

all_data = {}

for name, url in files.items():
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip().str.upper()
    date_col = next(c for c in ['DATE', 'Date', 'date'] if c in df.columns)
    df[date_col] = pd.to_datetime(df[date_col])
    df.set_index(date_col, inplace=True)
    df['MA50'] = df['CLOSE'].rolling(window=50).mean()
    df['MA200'] = df['CLOSE'].rolling(window=200).mean()
    all_data[name] = df

st.title("Indices Close Price & Moving Averages Comparison")

min_date = min(df.index.min() for df in all_data.values())
max_date = max(df.index.max() for df in all_data.values())

start_date, end_date = st.date_input("Select Time Frame", value=[min_date, max_date], min_value=min_date, max_value=max_date)

filtered_data = {name: df.loc[start_date:end_date] for name, df in all_data.items()}

selected_indices = st.multiselect("Select Indices to Compare", options=list(filtered_data.keys()), default=list(filtered_data.keys()))

fig = go.Figure()

for name in selected_indices:
    df = filtered_data[name]
    fig.add_trace(go.Scatter(x=df.index, y=df['CLOSE'], mode='lines', name=f"{name} Close"))
    fig.add_trace(go.Scatter(x=df.index, y=df['MA50'], mode='lines', name=f"{name} 50-day MA", line=dict(dash='dash')))
    fig.add_trace(go.Scatter(x=df.index, y=df['MA200'], mode='lines', name=f"{name} 200-day MA", line=dict(dash='dot')))

fig.update_layout(title="Indices Closing Prices & Moving Averages", xaxis_title="Date", yaxis_title="Price", hovermode='x unified')
st.plotly_chart(fig, use_container_width=True)
