import yfinance as yf
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

indices = {
    "Gold (COMEX Futures)": "GC=F",
    "S&P 500": "^GSPC",
    "Dow Jones": "^DJI",
    "Nasdaq": "^IXIC",
    "Shanghai Composite": "000001.SS",
    "Shenzhen Component": "399001.SZ"
}

data = []

st.title("Weekly Close Prices of Indices (5 years)")

for name, symbol in indices.items():
    df = yf.download(symbol, period="5y", interval="1wk", auto_adjust=True)
    if not df.empty:
        df = df[["Close"]].rename(columns={"Close": name})
        data.append(df)
        
    else:
        st.warning(f"❌ No data for {name}")

if data:
    df_all = pd.concat(data, axis=1)
    csv_data = df_all.to_csv().encode("utf-8")
    st.download_button(
        label="📥 Download merged data as CSV",
        data=csv_data,
        file_name="weekly_indices.csv",
        mime="text/csv",
    )
    
    fig, ax = plt.subplots(figsize=(14, 8))
    for col in df_all.columns:
        ax.plot(df_all.index, df_all[col], label=col)
    ax.set_title("Weekly Close Prices of Indices (5 years)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price")
    ax.legend()
    ax.grid(True)

    st.pyplot(fig)
else:
    st.error("⚠️ No data downloaded. Please check tickers.")
