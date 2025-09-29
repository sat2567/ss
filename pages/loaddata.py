import os
import pandas as pd
import matplotlib.pyplot as plt

# Folder where CSV files are located (one level up from this script)
data_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# File mapping: descriptive names to CSV filenames
files = {
    "NIFTY BANK": "NIFTY BANK-29-09-2024-to-29-09-2025.csv",
    "NIFTY 50": "NIFTY 50-29-09-2024-to-29-09-2025.csv",
    "NIFTY MIDCAP 100": "NIFTY MIDCAP 100-29-09-2024-to-29-09-2025.csv",
    "NIFTY SMALLCAP 100": "NIFTY SMALLCAP 100-29-09-2024-to-29-09-2025.csv"
}

for name, filename in files.items():
    file_path = os.path.join(data_folder, filename)
    if not os.path.isfile(file_path):
        print(f"Warning: File not found: {file_path}")
        continue

    df = pd.read_csv(file_path)

    # Clean columns: strip whitespace and uppercase all names for consistency
    df.columns = df.columns.str.strip().str.upper()

    # Detect the date column (allowing different casings)
    date_col = next((col for col in ["DATE", "Date", "date"] if col in df.columns), None)
    if date_col is None:
        raise ValueError(f"No date column found in file: {filename}")

    # Convert date column to datetime and set as index
    df[date_col] = pd.to_datetime(df[date_col])
    df.set_index(date_col, inplace=True)

    # Verify and calculate moving averages only if CLOSE column exists
    if "CLOSE" not in df.columns:
        print(f"Warning: 'CLOSE' column missing in file {filename}")
        continue

    df["MA50"] = df["CLOSE"].rolling(window=50).mean()
    df["MA200"] = df["CLOSE"].rolling(window=200).mean()

    # Plot Close price with moving averages
    plt.figure(figsize=(12, 6))
    plt.plot(df.index, df["CLOSE"], label=f"{name} Close Price", color="blue")
    plt.plot(df.index, df["MA50"], label="50-day MA", color="orange", linewidth=2)
    plt.plot(df.index, df["MA200"], label="200-day MA", color="red", linewidth=2)
    plt.title(f"{name}: Close Price with 50 & 200-day Moving Averages")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.show()
