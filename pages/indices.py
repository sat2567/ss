import streamlit as st
import pandas as pd
import nsepython as ns
from datetime import datetime
import matplotlib.pyplot as plt

st.set_page_config(page_title="Nifty Indices Dashboard", layout="wide")
st.title("📊 Nifty Indices Dashboard")

# -------------------------
# 🧾 Static Technical Table
# -------------------------
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
    ],
}

st.subheader("📈 Current Technical Overview (as of Nov 7)")
summary_df = pd.DataFrame(summary_data)
st.dataframe(summary_df, use_container_width=True)

# -------------------------
# 🧮 Chart Section
# -------------------------
indices = ['NIFTY 50', 'NIFTY MIDCAP 150', 'NIFTY SMALLCAP 250']

def extract_data():
    """Fetch and merge last 5 years of data for given indices."""
    current_year = datetime.now().year
    data_dict = {}

    for index in indices:
        data_list = []
        for year in range(current_year - 5, current_year + 1):
            start = datetime(year, 1, 1)
            end = min(datetime(year, 12, 31), datetime.now())
            start_str, end_str = start.strftime('%d-%b-%Y'), end.strftime('%d-%b-%Y')

            try:
                data = ns.index_history(index, start_str, end_str)
                if not data.empty:
                    data_list.append(data)
            except Exception:
                continue

        if data_list:
            df = pd.concat(data_list, ignore_index=True)
            df = df.drop_duplicates(subset=['HistoricalDate'])
            df['Date'] = pd.to_datetime(df['HistoricalDate'], format='%d %b %Y')
            df = df.set_index('Date').sort_index()

            # ✅ Ensure numeric values
            df['CLOSE'] = pd.to_numeric(df['CLOSE'], errors='coerce')
            df = df[['CLOSE']].rename(columns={'CLOSE': index})
            data_dict[index] = df

    # Combine all indices and clean
    combined = pd.concat(data_dict.values(), axis=1).sort_index()
    combined = combined.resample('D').ffill()  # fill missing days
    combined = combined.apply(pd.to_numeric, errors='coerce')  # ensure all numeric
    combined = combined.dropna(how='all')  # drop completely empty rows
    return combined

# Sidebar options
st.sidebar.header("📉 Chart Options")
show_ma50 = st.sidebar.checkbox("Show 50-day MA", value=False)
show_ma200 = st.sidebar.checkbox("Show 200-day MA", value=False)

# Extract + plot
if st.button("📈 Extract and Plot Data"):
    st.write("Fetching data... Please wait ⏳")
    df = extract_data()

    if df.empty:
        st.error("❌ No valid data retrieved. Try again later.")
        st.stop()

    st.success("Data fetched successfully!")

    # Add moving averages if selected
    if show_ma50:
        for col in df.columns:
            df[f"{col}_MA50"] = df[col].rolling(50).mean()
    if show_ma200:
        for col in df.columns:
            df[f"{col}_MA200"] = df[col].rolling(200).mean()

    # Plot
    fig, ax = plt.subplots(figsize=(14, 8))
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']

    # Plot base lines
    for i, col in enumerate([c for c in df.columns if not ('MA' in c)]):
        ax.plot(df.index, df[col], label=col, linewidth=2, color=colors[i % len(colors)])

    # Plot moving averages
    if show_ma50:
        for col in [c for c in df.columns if 'MA50' in c]:
            ax.plot(df.index, df[col], linestyle='--', label=col, alpha=0.8)
    if show_ma200:
        for col in [c for c in df.columns if 'MA200' in c]:
            ax.plot(df.index, df[col], linestyle=':', label=col, alpha=0.8)

    ax.set_xlabel('Date')
    ax.set_ylabel('Index Value')
    title_suffix = []
    if show_ma50: title_suffix.append("50D MA")
    if show_ma200: title_suffix.append("200D MA")
    ax.set_title("Nifty Indices Closing Prices" + (f" with {' & '.join(title_suffix)}" if title_suffix else ""))
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(True, alpha=0.3)

    st.pyplot(fig)
