import yfinance as yf
import pandas as pd
import streamlit as st
import plotly.graph_objs as go

# Define pre-existing CSV files raw URLs in GitHub repo
csv_files = {
    "NIFTY BANK": "https://raw.githubusercontent.com/sat2567/ss/my-new-branch/NIFTY%20BANK-29-09-2024-to-29-09-2025.csv",
    "NIFTY 50": "https://raw.githubusercontent.com/sat2567/ss/my-new-branch/NIFTY%2050-29-09-2024-to-29-09-2025.csv",
    "NIFTY MIDCAP 100": "https://raw.githubusercontent.com/sat2567/ss/my-new-branch/NIFTY%20MIDCAP%20100-29-09-2024-to-29-09-2025.csv",
    "NIFTY SMALLCAP 100": "https://raw.githubusercontent.com/sat2567/ss/my-new-branch/NIFTY%20SMALLCAP%20100-29-09-2024-to-29-09-2025.csv"
}

# Define yfinance symbols for additional global indices
yfinance_indices = {
    "Gold (COMEX Futures)": "GC=F",
    "S&P 500": "^GSPC",
    "Dow Jones": "^DJI",
    "Nasdaq": "^IXIC",
    "Shanghai Composite": "000001.SS",
    "Shenzhen Component": "399001.SZ"
}

# Load CSV data
csv_data = {}
for name, url in csv_files.items():
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip().str.upper()
    date_col = next(c for c in ['DATE','Date','date'] if c in df.columns)
    df[date_col] = pd.to_datetime(df[date_col], dayfirst=True)
    df.set_index(date_col, inplace=True)
    csv_data[name] = df

# Download yfinance data
yf_data = {}
for name, symbol in yfinance_indices.items():
    df = yf.download(symbol, period="5y", interval="1wk", auto_adjust=True)
    if not df.empty:
        df = df[["Close"]].rename(columns={"Close": "CLOSE"})
        df.index = pd.to_datetime(df.index)
        yf_data[name] = df

# Combine all datasets into one dict with unified structure ('CLOSE' column)
all_data = {}
# Add CSV data first, ensure 'CLOSE' column exists (NIFTY CSV might have 'CLOSE' column in uppercase)
for name, df in csv_data.items():
    # Ensure closing price column named 'CLOSE'
    if "CLOSE" not in df.columns:
        close_col = next((col for col in df.columns if "CLOSE" in col), None)
        if close_col:
            df.rename(columns={close_col: "CLOSE"}, inplace=True)
        else:
            continue
    all_data[name] = df[["CLOSE"]].copy()

# Add yfinance data
for name, df in yf_data.items():
    all_data[name] = df.copy()

# Streamlit UI
st.title("Combined Indices Close Price & Moving Averages")

# Compute overall min and max dates from all datasets
all_dates = pd.concat([df.index.to_series() for df in all_data.values()])
min_date = all_dates.min()
max_date = all_dates.max()

start_date, end_date = st.date_input("Select Date Range", value=[min_date, max_date], min_value=min_date, max_value=max_date)

filtered_data = {}
for name, df in all_data.items():
    filtered_data[name] = df.loc[start_date:end_date]

# Select indices to compare
selected_indices = st.multiselect("Select Indices to Compare", options=sorted(filtered_data.keys()), default=sorted(filtered_data.keys()))

# Select moving average windows
ma_windows = st.multiselect("Moving Average Window Sizes (days)", options=[10, 20, 50, 100, 200], default=[50, 200])

# Plot combined figure
fig = go.Figure()

for name in selected_indices:
    df = filtered_data[name]
    fig.add_trace(go.Scatter(x=df.index, y=df['CLOSE'], mode='lines', name=f'{name} Close'))
    for window in ma_windows:
        ma_col = f"MA{window}"
        df[ma_col] = df['CLOSE'].rolling(window=window).mean()
        fig.add_trace(go.Scatter(x=df.index, y=df[ma_col], mode='lines', name=f'{name} {window}-Day MA',
                                 line=dict(dash='dash' if window != 200 else 'dot')))

fig.update_layout(
    title="Indices Closing Prices and Moving Averages",
    xaxis_title="Date",
    yaxis_title="Price",
    legend_title="Legend",
    height=700,
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)
