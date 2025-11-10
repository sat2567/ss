import streamlit as st
import pandas as pd
import nsepython as ns
from datetime import datetime
import plotly.graph_objects as go

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
# ⚙️ Fetching Function
# -------------------------
indices = {
    "NIFTY 50": ["NIFTY 50"],
    "NIFTY MIDCAP 150": ["NIFTY MIDCAP 150", "NIFTY MIDCAP 100"],
    "NIFTY SMALLCAP 250": ["NIFTY SMALLCAP 250", "NIFTY SMALLCAP 100", "NIFTY SMLCAP 100"]
}

def fetch_index_data(index_names):
    """Tries multiple possible index names from NSEPython"""
    current_year = datetime.now().year
    all_data = []
    for name in index_names:
        for year in range(current_year - 5, current_year + 1):
            start = datetime(year, 1, 1)
            end = min(datetime(year, 12, 31), datetime.now())
            start_str, end_str = start.strftime('%d-%b-%Y'), end.strftime('%d-%b-%Y')

            try:
                data = ns.index_history(name, start_str, end_str)
                if data is not None and not data.empty:
                    all_data.append(data)
            except Exception:
                continue
        if all_data:
            break

    if not all_data:
        return None

    df = pd.concat(all_data, ignore_index=True).drop_duplicates(subset=['HistoricalDate'])
    df['Date'] = pd.to_datetime(df['HistoricalDate'], format='%d %b %Y')
    df = df.set_index('Date').sort_index()
    df['CLOSE'] = pd.to_numeric(df['CLOSE'], errors='coerce')
    return df[['CLOSE']]

def extract_all_data():
    """Fetch and merge data for all indices."""
    data_dict = {}
    for label, names in indices.items():
        df = fetch_index_data(names)
        if df is not None and not df.empty:
            data_dict[label] = df.rename(columns={'CLOSE': label})

    if not data_dict:
        return pd.DataFrame()

    combined = pd.concat(data_dict.values(), axis=1).sort_index()
    combined = combined.resample('D').ffill()
    combined = combined.dropna(how='all')
    return combined

# -------------------------
# 📉 Sidebar Options
# -------------------------
st.sidebar.header("📉 Chart Options")
show_ma50 = st.sidebar.checkbox("Show 50-day MA", value=False)
show_ma200 = st.sidebar.checkbox("Show 200-day MA", value=False)

# -------------------------
# 📈 Extract & Plot
# -------------------------
if st.button("📈 Extract and Plot Data"):
    st.write("Fetching data... Please wait ⏳")
    df = extract_all_data()

    if df.empty:
        st.error("❌ No valid data retrieved. Try again later.")
        st.stop()

    st.success("Data fetched successfully!")

    # Add moving averages
    if show_ma50:
        for col in df.columns:
            df[f"{col}_MA50"] = df[col].rolling(50).mean()
    if show_ma200:
        for col in df.columns:
            df[f"{col}_MA200"] = df[col].rolling(200).mean()

    # -------------------------
    # 📊 Plotly Interactive Chart
    # -------------------------
    fig = go.Figure()

    base_colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    for i, col in enumerate([c for c in df.columns if not ('MA' in c)]):
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df[col],
            mode='lines',
            name=col,
            line=dict(width=2, color=base_colors[i % len(base_colors)]),
            hovertemplate=f"{col}<br>Date: %{x|%d-%b-%Y}<br>Value: %{y:.2f}<extra></extra>"
        ))

    # Moving averages
    if show_ma50:
        for col in [c for c in df.columns if 'MA50' in c]:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[col],
                mode='lines',
                name=col,
                line=dict(width=1.5, dash='dot'),
                hovertemplate=f"{col}<br>Date: %{x|%d-%b-%Y}<br>Value: %{y:.2f}<extra></extra>"
            ))
    if show_ma200:
        for col in [c for c in df.columns if 'MA200' in c]:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[col],
                mode='lines',
                name=col,
                line=dict(width=1.5, dash='dash'),
                hovertemplate=f"{col}<br>Date: %{x|%d-%b-%Y}<br>Value: %{y:.2f}<extra></extra>"
            ))

    title_suffix = []
    if show_ma50: title_suffix.append("50D MA")
    if show_ma200: title_suffix.append("200D MA")

    fig.update_layout(
        title=f"Nifty Indices Closing Prices{' with ' + ' & '.join(title_suffix) if title_suffix else ''}",
        xaxis_title="Date",
        yaxis_title="Index Value",
        hovermode="x unified",
        template="plotly_white",
        legend=dict(x=0, y=1.1, orientation="h"),
        height=700
    )

    st.plotly_chart(fig, use_container_width=True)
