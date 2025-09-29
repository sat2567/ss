import streamlit as st
import yfinance as yf
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

st.set_page_config(page_title="📈 Indices Analysis", layout="wide")

st.title("📈 Nifty / BSE Indices & Gold Analysis")

indices = {
    "Nifty 50": "^NSEI",
    "Nifty Bank": "^NSEBANK",
    "Nifty Smallcap 100": "^CNXSC",
    "BSE Midcap": "BSE-MIDCAP.BO",
    "BSE Smallcap": "BSE-SMLCAP.BO",
    "Gold (COMEX Futures)": "GC=F"
}

data = []
for name, symbol in indices.items():
    df = yf.download(symbol, period="5y", interval="1wk", auto_adjust=True)
    if not df.empty:
        df = df[["Close"]].rename(columns={"Close": name})
        data.append(df)
        st.success(f"✅ Downloaded {name}")
    else:
        st.error(f"❌ No data for {name}")

if data:
    df_all = pd.concat(data, axis=1)

    # --- User date filter ---
    start_date = st.date_input("Start Date", df_all.index.min().date())
    end_date   = st.date_input("End Date", df_all.index.max().date())

    df_range = df_all.loc[str(start_date):str(end_date)]
    returns = df_range.pct_change().dropna()
    corr_matrix = returns.corr()

    # --- Correlation Heatmap ---
    st.subheader("Correlation Heatmap of Weekly Returns")
    fig, ax = plt.subplots(figsize=(8,6))
    sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", vmin=-1, vmax=1, linewidths=0.5, ax=ax)
    st.pyplot(fig)

    # --- Moving Averages ---
    st.subheader("Moving Averages (50 & 200 Weeks)")
    for col in df_all.columns:
        df = df_all[[col]].dropna().copy()
        df["MA50"] = df[col].rolling(50).mean()
        df["MA200"] = df[col].rolling(200).mean()

        fig, ax = plt.subplots(figsize=(10,5))
        ax.plot(df.index, df[col], label=col, color="blue")
        ax.plot(df.index, df["MA50"], label="50-week MA", color="orange", linewidth=2)
        ax.plot(df.index, df["MA200"], label="200-week MA", color="red", linewidth=2)
        ax.set_title(f"{col} with 50 & 200-week MAs", fontsize=14)
        ax.legend()
        ax.grid(True, linestyle="--", alpha=0.6)
        st.pyplot(fig)

    # --- Download CSV ---
    st.download_button(
        label="📥 Download Weekly Data as CSV",
        data=df_all.to_csv().encode("utf-8"),
        file_name="weekly_indices.csv",
        mime="text/csv"
    )
