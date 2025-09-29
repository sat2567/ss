import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# Mapping descriptive names to raw GitHub URLs of CSV files
files = {
    "NIFTY BANK": "https://raw.githubusercontent.com/sat2567/ss/my-new-branch/NIFTY%20BANK-29-09-2024-to-29-09-2025.csv",
    "NIFTY 50": "https://raw.githubusercontent.com/sat2567/ss/my-new-branch/NIFTY%2050-29-09-2024-to-29-09-2025.csv",
    "NIFTY MIDCAP 100": "https://raw.githubusercontent.com/sat2567/ss/my-new-branch/NIFTY%20MIDCAP%20100-29-09-2024-to-29-09-2025.csv",
    "NIFTY SMALLCAP 100": "https://raw.githubusercontent.com/sat2567/ss/my-new-branch/NIFTY%20SMALLCAP%20100-29-09-2024-to-29-09-2025.csv"
}

for name, url in files.items():
    st.write(f"Loading data for {name}...")
    
    try:
        df = pd.read_csv(url)
    except Exception as e:
        st.error(f"Failed to load {name}: {e}")
        continue

    # Clean columns
    df.columns = df.columns.str.strip().str.upper()

    # Identify date column
    date_col = next((col for col in ["DATE", "Date", "date"] if col in df.columns), None)
    if date_col is None:
        st.error(f"No date column in {name} data")
        continue
    
    df[date_col] = pd.to_datetime(df[date_col])
    df.set_index(date_col, inplace=True)

    if "CLOSE" not in df.columns:
        st.error(f"CLOSE column missing in {name} data")
        continue

    df["MA50"] = df["CLOSE"].rolling(window=50).mean()
    df["MA200"] = df["CLOSE"].rolling(window=200).mean()

    st.line_chart(df[["CLOSE", "MA50", "MA200"]], height=400, width=700)
