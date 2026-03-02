import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# ─── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="Market Performance", page_icon="📈")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@400;700&display=swap');
    :root { --accent: #00f5ff; --bg: #020408; }
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

# ─── TICKERS ───────────────────────────────────────────────────────────────────
INDICES = {
    "NIFTY 50": "^NSEI",
    "NIFTY NEXT 50": "^NSEJOCKEY", # Alternative: "NIFTYJR.NS"
    "NIFTY BANK": "^NSEBANK",
    "NIFTY MIDCAP 100": "^CNXMID",
    "SENSEX": "^BSESN"
}

SECTORS = {
    "Defence": "NIFTY_DEFENCE.NS", 
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
    # Fetching 2 years of data to be safe
    data = yf.download(list(tickers.values()), period="2y", interval="1d", auto_adjust=True, progress=False)
    
    output = {}
    for name, ticker in tickers.items():
        try:
            # Handle MultiIndex columns if multiple tickers were returned
            if isinstance(data.columns, pd.MultiIndex):
                series = data['Close'][ticker].dropna()
            else:
                series = data['Close'].dropna()
            
            # Only add to output if we actually have data points
            if not series.empty:
                output[name] = series
        except Exception:
            continue
    return output

def calc_pct(series, start_dt=None, end_dt=None, days=None):
    if series is None or series.empty: return 0.0
    try:
        if days:
            cutoff = series.index.max() - timedelta(days=days)
            subset = series.loc[series.index >= cutoff]
        else:
            subset = series.loc[str(start_dt):str(end_dt)]
        
        if len(subset) < 2: return 0.0
        return ((subset.iloc[-1] - subset.iloc[0]) / subset.iloc[0]) * 100
    except:
        return 0.0

# ─── MAIN UI ──────────────────────────────────────────────────────────────────
def main():
    st.markdown('<h1 style="font-family:Orbitron; color:#00f5ff;">BHARAT PERFORMANCE TERMINAL</h1>', unsafe_allow_html=True)
    
    # 1. DATE CONTROLS
    st.markdown('<div class="section-head">SET PARAMETERS</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        s_dt = st.date_input("START DATE", datetime.now() - timedelta(days=30))
    with col2:
        e_dt = st.date_input("END DATE", datetime.now())
    with col3:
        st.write("") # Spacer

    # 2. FETCH DATA
    with st.spinner("Downloading market data..."):
        idx_dict = get_market_data(INDICES)
        sec_dict = get_market_data(SECTORS)

    # 3. INDICES TABLE
    st.markdown('<div class="section-head">MAJOR INDICES</div>', unsafe_allow_html=True)
    idx_rows = []
    for name, series in idx_dict.items():
        # The FIX: Check if series has data before accessing index -1
        if not series.empty:
            idx_rows.append({
                "Index": name,
                "1 Week": f"{calc_pct(series, days=7):+.2f}%",
                "1 Month": f"{calc_pct(series, days=30):+.2f}%",
                "Custom Range": f"{calc_pct(series, start_dt=s_dt, end_dt=e_dt):+.2f}%",
                "LTP": f"{series.iloc[-1]:,.2f}"
            })
    
    if idx_rows:
        st.table(pd.DataFrame(idx_rows))
    else:
        st.warning("No index data found. Please check ticker symbols.")

    # 4. SECTORS TABLE
    st.markdown('<div class="section-head">SECTOR PERFORMANCE</div>', unsafe_allow_html=True)
    sec_rows = []
    for name, series in sec_dict.items():
        if not series.empty:
            w1 = calc_pct(series, days=7)
            sec_rows.append({
                "Sector": name,
                "1 Week (%)": w1,
                "1 Month (%)": calc_pct(series, days=30),
                "Custom Range (%)": calc_pct(series, start_dt=s_dt, end_dt=e_dt)
            })
    
    if sec_rows:
        df_sec = pd.DataFrame(sec_rows).sort_values("1 Week (%)", ascending=False)
        # Apply string formatting for display
        for col in ["1 Week (%)", "1 Month (%)", "Custom Range (%)"]:
            df_sec[col] = df_sec[col].apply(lambda x: f"{x:+.2f}%")
        st.dataframe(df_sec, use_container_width=True, hide_index=True)
    else:
        st.warning("No sector data found.")

if __name__ == "__main__":
    main()
