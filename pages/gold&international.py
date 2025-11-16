import yfinance as yf
import pandas as pd
import streamlit as st
import plotly.graph_objs as go
# ------------------------
# 🌍 Global Market Summary Table (Static)
# ------------------------
st.subheader("🌍 Global Market Summary (as of 14 Nov 2025)")

summary_data = {
    "Asset / Index": [
        "Gold (USD per troy oz)",
        "South Korea (KOSPI)",
        "Japan (Nikkei 225)",
        "Europe (Stoxx 600)",
        "USA (S&P 500)",
        "USA (Dow Jones)"
    ],
    "Current Level (Approx.)": [
        "$4,133 (Nov 14, 2025)",     # [web:44]
        "4,012 (Nov 14, 2025)",      # [web:57]
        "50,377 (Nov 14, 2025)",     # [web:58]
        "574.8 (Nov 14, 2025)",      # [web:63]
        "6,734 (Nov 14, 2025)",      # [web:68][web:77]
        "47,147 (Nov 14, 2025)"      # [web:69][web:78]
    ],
    "1-Week % Change": [
        "+0.06%",    # Gold moved up from ~$4,109 to $4,133 [web:44]
        "-2.72%",    # KOSPI fell from ~4,122 to 4,012 [web:57]
        "-1.2%",     # Nikkei fell from ~51,000 to 50,377 [web:58]
        "+0.35%",    # Stoxx 600 rose from ~572.8 to 574.8 [web:63]
        "-0.85%",    # S&P 500 fell from ~6,792 to 6,734 [web:68][web:77]
        "-0.47%"     # Dow Jones dropped from ~47,368 to 47,147 [web:69][web:78]
    ],
    "1-Month % Change": [
        "+0.6%",     # Gold [web:44]
        "+9.8%",     # KOSPI [web:57]
        "+6.3%",     # Nikkei [web:58]
        "+3.7%",     # Stoxx 600 [web:63]
        "+2.1%",     # S&P 500 [web:68]
        "+2.4%"      # Dow Jones [web:69]
    ]
}

summary_df = pd.DataFrame(summary_data)

st.dataframe(summary_df, use_container_width=True)

# ------------------------
# 🌍 Major Global Indices
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

# Normalization and index selection
normalize = st.checkbox("Normalize Prices (Start = 100)", value=True)

# ------------------------
# 📥 Download Data
# ------------------------
data = {}

for name, symbol in indices.items():
    df = yf.download(symbol, period=period, interval=interval, auto_adjust=True, progress=False)
    if not df.empty:
        df = df[["Close"]].rename(columns={"Close": name})
        data[name] = df
    else:
        st.warning(f"⚠️ No data for {name}")

if not data:
    st.error("❌ No data downloaded. Please check your connection or tickers.")
    st.stop()

# Combine all data
df_all = pd.concat(data.values(), axis=1)
df_all.columns = list(data.keys())  # ✅ ensure column names are plain strings
df_all.dropna(how='all', inplace=True)

# ------------------------
# 🔍 Select Which Indices to Display
# ------------------------
selected_indices = st.multiselect(
    "Select Indices to Display",
    options=list(df_all.columns),
    default=list(df_all.columns)
)

df_filtered = df_all[selected_indices]

# Normalize if checked
if normalize:
    df_filtered = df_filtered / df_filtered.iloc[0] * 100

# ------------------------
# 💾 CSV Download
# ------------------------
csv_data = df_filtered.to_csv().encode("utf-8")
st.download_button(
    label=f"📥 Download {selected_period} data as CSV",
    data=csv_data,
    file_name=f"indices_{selected_period.replace(' ', '_').lower()}.csv",
    mime="text/csv",
)

# ------------------------
# 📊 Interactive Plotly Chart
# ------------------------
fig = go.Figure()

for col in df_filtered.columns:
    fig.add_trace(go.Scatter(
        x=df_filtered.index,
        y=df_filtered[col],
        mode='lines',
        name=col,  # ✅ string, not tuple
        hovertemplate=(
            f"<b>{col}</b><br>" +
            "Date: %{x|%Y-%m-%d}<br>" +
            "Price: %{y:.2f}<extra></extra>"
        )
    ))

fig.update_layout(
    title=f"Global Indices ({selected_period})",
    xaxis_title="Date",
    yaxis_title="Normalized Price (Start=100)" if normalize else "Price",
    hovermode="x unified",
    height=650,
    template="plotly_white",
    legend=dict(orientation="h", y=-0.2)
)

st.plotly_chart(fig, use_container_width=True)
