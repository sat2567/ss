import pandas as pd
import matplotlib.pyplot as plt

# File names (update paths as required)
files = {
    "NIFTY BANK": "NIFTY BANK-29-09-2024-to-29-09-2025.csv",
    "NIFTY 50": "NIFTY 50-29-09-2024-to-29-09-2025.csv",
    "NIFTY MIDCAP 100": "NIFTY MIDCAP 100-29-09-2024-to-29-09-2025.csv",
    "NIFTY SMALLCAP 100": "NIFTY SMALLCAP 100-29-09-2024-to-29-09-2025.csv"
}

for name, filename in files.items():
    # Load data
    df = pd.read_csv(filename, parse_dates=True)
    # If 'Date' is a column, set as index.
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
    # Ensure we have a 'Close' column
    price_col = 'Close' if 'Close' in df.columns else df.columns[-1]
    
    # Calculate moving averages
    df['MA50'] = df[price_col].rolling(window=50).mean()
    df['MA200'] = df[price_col].rolling(window=200).mean()

    # Plot
    plt.figure(figsize=(12, 6))
    plt.plot(df.index, df[price_col], label=name, color='blue')
    plt.plot(df.index, df['MA50'], label='50-day MA', color='orange', linewidth=2)
    plt.plot(df.index, df['MA200'], label='200-day MA', color='red', linewidth=2)
    plt.title(f"{name} Closing Price & Moving Averages")
    plt.xlabel('Date')
    plt.ylabel('Closing Price')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.show()
