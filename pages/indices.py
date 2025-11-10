import streamlit as st
import pandas as pd
import nsepython as ns
from datetime import datetime
import matplotlib.pyplot as plt

st.set_page_config(page_title="Nifty Indices Dashboard", layout="wide")
st.title("📊 Nifty Indices Data Extraction & Visualization")

# Define indices
indices = ['NIFTY 50', 'NIFTY MIDCAP 150', 'NIFTY SMALLCAP 250']

# --------------------------
# 🔹 Function to extract data
# --------------------------
def extract_data():
    current_year = datetime.now().year
    data_dict = {}

    with st.spinner("Extracting data... Please wait (takes a few minutes)"):
        for index in indices:
            st.write(f"📥 Fetching data for **{index}**...")
            data_list = []

            for year in range(current_year - 5, current_year + 1):
                start = datetime(year, 1, 1)
                end = datetime(year, 12, 31)
                if end > datetime.now():
                    end = datetime.now()

                start_str = start.strftime('%d-%b-%Y')
                end_str = end.strftime('%d-%b-%Y')

                try:
                    data = ns.index_history(index, start_str, end_str)
                    if not data.empty:
                        data_list.append(data)
                except Exception as e:
                    st.warning(f"⚠️ Failed to fetch {index} for {year}: {e}")

            if data_list:
                df = pd.concat(data_list, ignore_index=True)
                df.drop_duplicates(subset=['HistoricalDate'], inplace=True)
                df['Date'] = pd.to_datetime(df['HistoricalDate'], format='%d %b %Y')
                df.set_index('Date', inplace=True)
                df.sort_index(inplace=True)
                data_dict[index] = df
            else:
                st.warning(f"⚠️ No data retrieved for {index}")

    return data_dict

# --------------------------
# 🔘 Button triggers extraction & plotting
# --------------------------
if st.button("🚀 Extract & Plot Data"):
    data_dict = extract_data()

    if not data_dict:
        st.error("❌ No data extracted. Please try again.")
        st.stop()

    st.session_state['data'] = data_dict
    st.success("✅ Data extracted successfully!")

    # --------------------------
    # 📈 Visualization
    # --------------------------
    combined_df = pd.DataFrame()
    for index, df in data_dict.items():
        combined_df[f"{index.replace(' ', '_')}_CLOSE"] = df['CLOSE']

    # Calculate Moving Averages
    for col in combined_df.columns:
        combined_df[f"{col}_MA50"] = combined_df[col].rolling(window=50).mean()
        combined_df[f"{col}_MA200"] = combined_df[col].rolling(window=200).mean()

    st.write("### 📊 Combined Data Preview")
    st.dataframe(combined_df.tail())

    # --------------------------
    # Plotting
    # --------------------------
    st.write("### 📉 Combined Chart with Moving Averages")
    fig, ax = plt.subplots(figsize=(14, 8))

    for col in combined_df.columns:
        if 'CLOSE' in col:
            ax.plot(combined_df.index, combined_df[col], label=col, linewidth=2)
        elif 'MA50' in col:
            ax.plot(combined_df.index, combined_df[col], linestyle='--', label=col, alpha=0.7)
        elif 'MA200' in col:
            ax.plot(combined_df.index, combined_df[col], linestyle=':', label=col, alpha=0.7)

    ax.set_xlabel('Date')
    ax.set_ylabel('Index Value')
    ax.set_title('Nifty Indices with 50-day & 200-day Moving Averages')
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

    # --------------------------
    # 💾 CSV Download buttons
    # --------------------------
    st.write("### 📂 Download Data")
    for index, df in data_dict.items():
        csv = df.to_csv().encode('utf-8')
        st.download_button(
            label=f"⬇️ Download {index} Data (CSV)",
            data=csv,
            file_name=f"{index.replace(' ', '_')}_last_5_years.csv",
            mime='text/csv'
        )

# --------------------------
# 🧠 If data already extracted, show cached chart
# --------------------------
elif 'data' in st.session_state:
    st.info("ℹ️ Using previously extracted data.")
    data_dict = st.session_state['data']

    combined_df = pd.DataFrame()
    for index, df in data_dict.items():
        combined_df[f"{index.replace(' ', '_')}_CLOSE"] = df['CLOSE']

    for col in combined_df.columns:
        combined_df[f"{col}_MA50"] = combined_df[col].rolling(window=50).mean()
        combined_df[f"{col}_MA200"] = combined_df[col].rolling(window=200).mean()

    st.write("### 📉 Combined Chart with Moving Averages (Cached)")
    fig, ax = plt.subplots(figsize=(14, 8))
    for col in combined_df.columns:
        if 'CLOSE' in col:
            ax.plot(combined_df.index, combined_df[col], label=col)
        elif 'MA50' in col:
            ax.plot(combined_df.index, combined_df[col], linestyle='--', label=col)
        elif 'MA200' in col:
            ax.plot(combined_df.index, combined_df[col], linestyle=':', label=col)
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)
else:
    st.write("👉 Click **'Extract & Plot Data'** to start.")
