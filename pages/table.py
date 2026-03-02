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
    "NIFTY NEXT 50": "NIFTYJR.NS", 
    "NIFTY BANK": "^NSEBANK",
    "NIFTY MIDCAP 100": "^CRSMID",
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
    output = {}
    for name, ticker in tickers.items():
        try:
            data = yf.download(ticker, period="2y", interval="1d", auto_adjust=True, progress=False)
            if data.empty:
                continue
                
            # FIX: Flatten multi-level columns if they exist (yfinance >= 0.2.40)
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
                
            # FIX: Extract the Close column and ensure it is strictly a 1D Series
            if 'Close' in data.columns:
                series = data['Close']
                if isinstance(series, pd.DataFrame):
                    series = series.iloc[:, 0]
            else:
                series = data.iloc[:, 0]
                
            # .squeeze() forcefully reduces 1-column DataFrames to a Series
            output[name] = series.squeeze().dropna()
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
        
        # FIX: Force extraction of pure python floats to avoid TypeError
        start_val = float(subset.iloc[0])
        end_val = float(subset.iloc[-1])
        
        return ((end_val - start_val) / start_val) * 100
    except Exception:
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
        st.write("") 

    # 2. FETCH DATA
    with st.spinner("Accessing Real-time Market Data..."):
        idx_dict = get_market_data(INDICES)
        sec_dict = get_market_data(SECTORS)

    # 3. INDICES TABLE
    st.markdown('<div class="section-head">MAJOR INDICES</div>', unsafe_allow_html=True)
    idx_rows = []
    
    display_order = ["NIFTY 50", "NIFTY NEXT 50", "NIFTY BANK", "NIFTY MIDCAP 100", "SENSEX"]
    
    for name in display_order:
        if name in idx_dict:
            series = idx_dict[name]
            # Extra safety check to ensure series isn't empty
            if not series.empty:
                idx_rows.append({
                    "Index": name,
                    "1 Week": f"{calc_pct(series, days=7):+.2f}%",
                    "1 Month": f"{calc_pct(series, days=30):+.2f}%",
                    "Custom Range": f"{calc_pct(series, start_dt=s_dt, end_dt=e_dt):+.2f}%",
                    "LTP": f"{float(series.iloc[-1]):,.2f}" # Forced float here as well
                })
    
    if idx_rows:
        st.table(pd.DataFrame(idx_rows))
    else:
        st.warning("Data connection issues. Please try refreshing.")

    # 4. SECTORS TABLE
    st.markdown('<div class="section-head">SECTOR PERFORMANCE</div>', unsafe_allow_html=True)
    sec_rows = []
    for name, series in sec_dict.items():
        if not series.empty:
            sec_rows.append({
                "Sector": name,
                "1 Week (%)": calc_pct(series, days=7),
                "1 Month (%)": calc_pct(series, days=30),
                "Custom Range (%)": calc_pct(series, start_dt=s_dt, end_dt=e_dt)
            })
    
    if sec_rows:
        df_sec = pd.DataFrame(sec_rows).sort_values("1 Week (%)", ascending=False)
        # Apply formatting
        for col in ["1 Week (%)", "1 Month (%)", "Custom Range (%)"]:
            df_sec[col] = df_sec[col].apply(lambda x: f"{x:+.2f}%")
        st.dataframe(df_sec, use_container_width=True, hide_index=True)
    else:
        st.warning("No sector data found.")

if __name__ == "__main__":
    main()
