import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# ─── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="Market Performance", page_icon="📈")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@400;700&display=swap');
    :root { 
        --accent: #00f5ff; 
        --bg: #020408; 
        --border: #0d2535;
        --bg-card: #0a1628;
        --pos: #00ff88;
        --neg: #ff3366;
    }
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
    
    /* CUSTOM TABLE STYLING */
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
        font-family: 'Share Tech Mono', monospace;
        font-size: 13px;
    }
    .custom-table th {
        background-color: #0b3d60; /* Standard Blue Header */
        color: #ffffff;            /* White Font */
        padding: 10px;
        text-align: right;
        border: 1px solid var(--border);
        font-weight: bold;
    }
    .custom-table th:first-child {
        text-align: left;
    }
    .custom-table td {
        padding: 8px 10px;
        border: 1px solid var(--border);
        text-align: right;
        background-color: var(--bg-card);
    }
    .custom-table td:first-child {
        text-align: left;
        color: var(--accent);
        font-weight: bold;
    }
    .val-pos { color: var(--pos); }
    .val-neg { color: var(--neg); }
    .val-neu { color: #a0c0d0; }
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
                
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
                
            if 'Close' in data.columns:
                series = data['Close']
                if isinstance(series, pd.DataFrame):
                    series = series.iloc[:, 0]
            else:
                series = data.iloc[:, 0]
                
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
        
        start_val = float(subset.iloc[0])
        end_val = float(subset.iloc[-1])
        
        return ((end_val - start_val) / start_val) * 100
    except Exception:
        return 0.0

def get_last_friday():
    d = datetime.now().date()
    while d.weekday() != 4:  # 4 represents Friday
        d -= timedelta(days=1)
    return d

# ─── MAIN UI ──────────────────────────────────────────────────────────────────
def main():
    st.markdown('<h1 style="font-family:Orbitron; color:#00f5ff;">BHARAT PERFORMANCE TERMINAL</h1>', unsafe_allow_html=True)
    
    last_friday = get_last_friday()
    lf_str = last_friday.strftime("%d-%b")
    
    # 1. DATE CONTROLS
    st.markdown('<div class="section-head">SET PARAMETERS (FOR MAJOR INDICES)</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        s_dt = st.date_input("START DATE", datetime.now() - timedelta(days=30))
    with col2:
        e_dt = st.date_input("END DATE", datetime.now())
    with col3:
        st.info(f"Sector Table is locked to week-over-week ending on Last Friday: {lf_str}") 

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
            if not series.empty:
                idx_rows.append({
                    "Index": name,
                    "Current Level": f"{float(series.iloc[-1]):,.2f}",
                    "1 Week": f"{calc_pct(series, days=7):+.2f}%",
                    "1 Month": f"{calc_pct(series, days=30):+.2f}%",
                    "Custom Range": f"{calc_pct(series, start_dt=s_dt, end_dt=e_dt):+.2f}%"
                })
    
    if idx_rows:
        st.table(pd.DataFrame(idx_rows))
    else:
        st.warning("Data connection issues. Please try refreshing.")

    # 4. SECTORS TABLE (CUSTOM HTML RENDERING)
    st.markdown(f'<div class="section-head">SECTOR ROTATION (ENDING {lf_str.upper()})</div>', unsafe_allow_html=True)
    
    sec_rows = []
    for name, series in sec_dict.items():
        if series.empty: continue
        
        sub_series = series.loc[:str(last_friday)]
        if len(sub_series) < 2: continue
            
        p_0 = float(sub_series.iloc[-1])
        
        # Calculate Monday to Friday logic
        monday_date = last_friday - timedelta(days=4)
        week_data = series.loc[str(monday_date):str(last_friday)]
        
        # Get the first available price in that Monday-Friday window
        p_monday = float(week_data.iloc[0]) if not week_data.empty else None
        
        # Calculate 1 Month back
        month_ago_date = last_friday - timedelta(days=30)
        month_data = series.loc[:str(month_ago_date)]
        p_1m = float(month_data.iloc[-1]) if not month_data.empty else None
        
        def safe_ret(curr, prev):
            if curr is None or prev is None or prev == 0: return "N/A"
            return f"{((curr - prev) / prev) * 100:+.2f}%"

        sec_rows.append({
            "Sector": name,
            lf_str: f"{p_0:,.2f}",
            "1 Week (Mon-Fri)": safe_ret(p_0, p_monday),
            "1 Month": safe_ret(p_0, p_1m)
        })

    if sec_rows:
        df_sec = pd.DataFrame(sec_rows)
        
        # Sort by 1 Week return
        df_sec['sort_col'] = df_sec['1 Week (Mon-Fri)'].apply(lambda x: float(str(x).replace('%', '').replace('+', '')) if x != "N/A" else -999)
        df_sec = df_sec.sort_values("sort_col", ascending=False).drop(columns=['sort_col'])
        
        # Build Custom HTML Table
        html_table = '<table class="custom-table"><thead><tr>'
        for col in df_sec.columns:
            html_table += f'<th>{col}</th>'
        html_table += '</tr></thead><tbody>'
        
        for _, row in df_sec.iterrows():
            html_table += '<tr>'
            for i, col in enumerate(df_sec.columns):
                val = row[col]
                if i == 0 or col == lf_str: # Sector Name or Base Price (No color coding)
                    html_table += f'<td>{val}</td>'
                else:
                    # Color coding logic
                    color_class = "val-neu"
                    if "N/A" not in str(val):
                        try:
                            num = float(str(val).replace('%', '').replace('+', ''))
                            if num > 0: color_class = "val-pos"
                            elif num < 0: color_class = "val-neg"
                        except:
                            pass
                    html_table += f'<td class="{color_class}">{val}</td>'
            html_table += '</tr>'
        html_table += '</tbody></table>'
        
        st.markdown(html_table, unsafe_allow_html=True)
    else:
        st.warning("No sector data found.")

if __name__ == "__main__":
    main()
