import yfinance as yf
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# ------------------------
# 📊 Major Global Indices
# ------------------------
indices = {
    "Gold (COMEX Futures)": "GC=F",
    "S&P 500 (US)": "^GSPC",
    "Dow Jones (US)": "^DJI",
    "Nasdaq (US)": "^IXIC",
    "FTSE 100 (UK)": "^FTSE",
    "DAX (Germany)": "^GDAXI",
    "CAC 40 (France)": "^FCHI",
    "Nikkei 225 (Japan)": "^N225",
    "KOSPI (South Korea)": "^KS11",
    "Hang Seng (Hong Kong)": "^HSI",
    "Shanghai Composite (China)": "000001.SS",
    "Shenzhen Component (China)": "399001.SZ"
}

# ------------------------
# 🕒 Streamlit App Layout
# ------------------------
st.title("📈 Global Indices Comparison Dashboard")

# Time period selection
period_options = {
    "Last 30 Days": ("30d", "1d"),
    "Last 3 Months": ("3mo", "1d"),
    "Last 1 Year": ("1y", "1wk"),
    "Last 5 Years": ("5y", "1wk"),
}
selected_period = st.selectbox("Select Time Range", list(period_options.keys()))
period, interval = period_options[selected_period]

normalize = st.checkbox("Normalize Prices (Start = 100)", value=True)

# ------------------------
# 📥 Download Data
# ------------------------
data = []

for name, symbol in indices.items():
    df = yf.download(symbol, period=period, interval=interval, auto_adjust=True, progress=False)
    if not df.empty:
        df = df[["Close"]].rename(columns={"Close": name})
        data.append(df)
    else:
        st.warning(f"⚠️ No data for {name}")

# ------------------------
# 🧮 Combine and Normalize
# ------------------------
if data:
    df_all = pd.concat(data, axis=1)
    df_all.dropna(how='all', inplace=True)

    if normalize:
        df_all = df_all / df_all.iloc[0] * 100

    # ------------------------
    # 💾 Download Button
    # ------------------------
    csv_data = df_all.to_csv().encode("utf-8")
    st.download_button(
        label=f"📥 Download {selected_period} data as CSV",
        data=csv_data,
        file_name=f"indices_{selected_period.replace(' ', '_').lower()}.csv",
        mime="text/csv",
    )

    # ------------------------
    # 📊 Plot
    # ------------------------
    fig, ax = plt.subplots(figsize=(14, 8))
    for col in df_all.columns:
        ax.plot(df_all.index, df_all[col], label=col)

    ax.set_title(f"Global Indices ({selected_period})", fontsize=16)
    ax.set_xlabel("Date")
    ax.set_ylabel("Normalized Price (Start=100)" if normalize else "Price")
    ax.legend(fontsize=8, loc='upper left')
    ax.grid(True, linestyle='--', alpha=0.6)

    st.pyplot(fig)

else:
    st.error("❌ No data downloaded. Please check internet connection or tickers.")
