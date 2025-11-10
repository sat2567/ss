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

# Function to extract data
def extract_data():
    current_year = datetime.now().year
    data_dict = {}
    for index in indices:
        data_list = []
        for year in range(current_year - 5, current_year + 1):
            start = datetime(year, 1, 1)
            end = datetime(year, 12, 31)
            if end > datetime.now():
                end = datetime.now()
            start_str = start.strftime('%d-%b-%Y')
            end_str = end.strftime('%d-%b-%Y')
            data = ns.index_history(index, start_str, end_str)
            data_list.append(data)
        data = pd.concat(data_list, ignore_index=True)
        data = data.drop_duplicates(subset=['HistoricalDate'])
        data['Date'] = pd.to_datetime(data['HistoricalDate'], format='%d %b %Y')
        data = data.set_index('Date').sort_index()
        data_dict[index] = data
    return data_dict

# Sidebar options for moving averages
st.sidebar.header("📉 Chart Options")
show_ma50 = st.sidebar.checkbox("Show 50-day MA", value=False)
show_ma200 = st.sidebar.checkbox("Show 200-day MA", value=False)

# Extract + plot button
if st.button("📈 Extract and Plot Data"):
    st.write("Fetching data... Please wait ⏳")
    data_dict = extract_data()
    st.session_state['data'] = data_dict
    st.success("Data fetched successfully!")

    # Combine data
    combined_df = pd.DataFrame()
    for index, df in data_dict.items():
        combined_df[f"{index.replace(' ', '_')}_CLOSE"] = df['CLOSE']

    # Calculate moving averages only if selected
    if show_ma50:
        for col in combined_df.columns:
            combined_df[f"{col}_MA50"] = combined_df[col].rolling(window=50).mean()

    if show_ma200:
        for col in combined_df.columns:
            combined_df[f"{col}_MA200"] = combined_df[col].rolling(window=200).mean()

    # Plot
    fig, ax = plt.subplots(figsize=(14, 8))

    for col in combined_df.columns:
        if 'CLOSE' in col:
            ax.plot(combined_df.index, combined_df[col], label=col.replace('_', ' '))
        elif 'MA50' in col and show_ma50:
            ax.plot(combined_df.index, combined_df[col], linestyle='--', label=col.replace('_', ' '))
        elif 'MA200' in col and show_ma200:
            ax.plot(combined_df.index, combined_df[col], linestyle=':', label=col.replace('_', ' '))

    ax.set_xlabel('Date')
    ax.set_ylabel('Index Value')
    ax.set_title('Nifty Indices CLOSE Prices' + 
                 (' with Moving Averages' if (show_ma50 or show_ma200) else ''))
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)
