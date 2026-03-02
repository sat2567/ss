import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# ─── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="Advanced Market Performance", page_icon="🛡️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@400;700&display=swap');
    :root { --accent: #00f5ff; --bg: #020408; --panel: #0a1628; }
    .stApp { background: var(--bg); color: #e2f4ff; font-family: 'Share Tech Mono', monospace; }
    .section-head {
        font-family: 'Orbitron', sans-serif;
        color: var(--accent);
        border-left: 3px solid var(--accent);
        padding-left: 10px;
        margin: 20px 0 10px;
        font-size: 14px;
        letter-spacing: 2px;
    }
</style>
""", unsafe_allow_html=True)

# ─── TICKERS (Updated with Next 50 and Defence) ────────────────────────────────
INDICES = {
    "NIFTY 50": "^NSEI",
    "NIFTY NEXT 50": "^NSMIDCP", # Often represented as Junior Nifty
    "NIFTY BANK": "^NSEBANK",
    "NIFTY MIDCAP 100": "^CNXMID",
    "NIFTY IT": "^CNXIT",
    "SENSEX": "^BSESN"
}

SECTORS = {
    "Defence": "NIFTY_DEFENCE.NS", # Custom ticker for Defense index
    "Auto": "^CNXAUTO",
    "Pharma": "^CNXPHARMA",
    "Consumption": "^CNXCONSUMP",
    "Energy": "^CNXENERGY",
    "Infrastructure": "^CNXINFRA",
    "Realty": "^CNXREALTY",
    "FMCG": "^CNXFMCG",
    "Metal": "^CNXMETAL"
}

# ─── DATA FETCHING ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def get_market_data(tickers):
    # Using a slightly longer period to ensure we have enough data for lookbacks
    data = yf.download(list(tickers.values()), period="2y", interval="1d", auto_adjust=True, progress=False)
    
    # Handle single ticker vs multi-ticker dataframes
    if len(tickers) > 1:
        return {name: data['Close'][ticker].dropna() for name, ticker in tickers.items()}
    else:
        name = list(tickers.keys())[0]
        return {name: data['Close'].dropna()}

def calc_pct(series, start_date=None, end_date=None, days=None):
    try:
        if days:
            # Trailing days lookback
            cutoff = series.index.max() - timedelta(days=days)
            subset = series.loc[series.index >= cutoff]
        elif start_date and end_date:
            # Date range lookback
            subset = series.loc[str(start_date):str(end_dt)]
        else:
            return 0.0

        if len(subset) < 2: return 0.0
        val_start = subset.iloc[0]
        val_end = subset.iloc[-1]
        return ((val_end - val_start) / val_start) * 100
    except Exception:
        return 0.0

# ─── MAIN UI ──────────────────────────────────────────────────────────────────
def main():
    st.markdown('<h1 style="font-family:Orbitron; color:#00f5ff;">BHARAT PERIODIC PERFORMANCE</h1>', unsafe_allow_html=True)
    
    # 1. DATE CONTROLS
    st.markdown('<div class="section-head">SET DATE PARAMETERS</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        global start_dt
        start_dt = st.date_input("START DATE", datetime.now() - timedelta(days=30))
    with col2:
        global end_dt
        end_dt = st.date_input("END DATE", datetime.now())
    with col3:
        st.info("The tables show 1-Week/1-Month trailing data alongside your Custom Date Range.")

    # 2. FETCH DATA
    with st.spinner("Fetching data for Indices and Sectors..."):
        idx_data = get_market_data(INDICES)
        sec_data = get_market_data(SECTORS)

    # 3. MAJOR INDICES TABLE
    st.markdown('<div class="section-head">MAJOR NIFTY INDICES</div>', unsafe_allow_html=True)
    
    idx_results = []
    for name, series in idx_data.items():
        idx_results.append({
            "Index Name": name,
            "1 Week": f"{calc_pct(series, days=7):+.2f}%",
            "1 Month": f"{calc_pct(series, days=30):+.2f}%",
            "Custom Range": f"{calc_pct(series, start_date=start_dt, end_date=end_dt):+.2f}%",
            "LTP": f"{series.iloc[-1]:,.2f}"
        })
    st.table(pd.DataFrame(idx_results))

    # 4. EXPANDED SECTOR PERFORMANCE TABLE
    st.markdown('<div class="section-head">SECTOR PERFORMANCE (INCL. DEFENCE & GROWTH)</div>', unsafe_allow_html=True)
    
    sec_results = []
    for name, series in sec_data.items():
        w1_val = calc_pct(series, days=7)
        sec_results.append({
            "Sector": name,
            "1 Week (%)": w1_val,
            "1 Month (%)": calc_pct(series, days=30),
            "Custom Range (%)": calc_pct(series, start_date=start_dt, end_date=end_dt)
        })
    
    df_sec = pd.DataFrame(sec_results).sort_values("1 Week (%)", ascending=False)
    
    # Formatting for better readability
    df_disp = df_sec.copy()
    for col in ["1 Week (%)", "1 Month (%)", "Custom Range (%)"]:
        df_disp[col] = df_disp[col].apply(lambda x: f"{x:+.2f}%")
        
    st.dataframe(df_disp, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()
