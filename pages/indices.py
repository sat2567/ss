import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, date
import numpy as np
import base64

# ─── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    layout="wide",
    page_title="BHARAT MARKETS // TERMINAL",
    page_icon="📡",
    initial_sidebar_state="expanded"
)

# ─── GLOBAL CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Exo+2:wght@300;400;600;700;900&family=Orbitron:wght@400;700;900&display=swap');

:root {
  --bg-base:    #020408;
  --bg-panel:   #060d14;
  --bg-card:    #0a1628;
  --accent-1:   #00f5ff;
  --accent-2:   #ff6b35;
  --accent-3:   #00ff88;
  --accent-4:   #ff3366;
  --accent-5:   #a855f7;
  --text-pri:   #e2f4ff;
  --text-sec:   #7ab3cc;
  --text-dim:   #3a5a70;
  --border:     #0d2535;
}

html, body, .stApp { background: var(--bg-base) !important; font-family: 'Exo 2', sans-serif; color: var(--text-pri); }

.stApp::before {
  content: '';
  position: fixed; top:0; left:0; right:0; bottom:0;
  background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,245,255,0.010) 2px, rgba(0,245,255,0.010) 4px);
  pointer-events: none; z-index: 9999;
}

section[data-testid="stSidebar"] { background: var(--bg-panel) !important; border-right: 1px solid var(--border) !important; }
section[data-testid="stSidebar"] * { color: var(--text-sec) !important; }
section[data-testid="stSidebar"] label { color: var(--accent-1) !important; font-family: 'Share Tech Mono', monospace; font-size: 11px; }

.terminal-header {
  background: linear-gradient(135deg, var(--bg-panel) 0%, #0a1628 100%);
  border: 1px solid var(--border); border-top: 2px solid var(--accent-1);
  border-radius: 0 0 8px 8px; padding: 16px 24px; margin-bottom: 18px; position: relative; overflow: hidden;
}
.terminal-header::after {
  content: ''; position: absolute; top:0; left:0; right:0; height:2px;
  background: linear-gradient(90deg, transparent, var(--accent-1), transparent);
  animation: scanH 3s ease-in-out infinite;
}
@keyframes scanH { 0%,100%{opacity:.3} 50%{opacity:1} }
.terminal-title { font-family:'Orbitron',monospace; font-size:20px; font-weight:900; letter-spacing:4px; color:var(--accent-1); text-shadow:0 0 20px var(--accent-1); margin:0; }
.terminal-subtitle { font-family:'Share Tech Mono',monospace; font-size:10px; color:var(--text-dim); letter-spacing:2px; margin-top:3px; }

.kpi-grid { display:grid; gap:8px; margin-bottom:16px; }
.kpi-card { background:var(--bg-card); border:1px solid var(--border); border-radius:6px; padding:12px 14px; position:relative; overflow:hidden; }
.kpi-card::before { content:''; position:absolute; top:0; left:0; right:0; height:2px; }
.kpi-card.up::before   { background:var(--accent-3); box-shadow:0 0 8px var(--accent-3); }
.kpi-card.down::before { background:var(--accent-4); box-shadow:0 0 8px var(--accent-4); }
.kpi-card.vix::before  { background:var(--accent-5); box-shadow:0 0 8px var(--accent-5); }
.kpi-label { font-family:'Share Tech Mono',monospace; font-size:9px; color:var(--text-dim); letter-spacing:1px; margin-bottom:5px; }
.kpi-value { font-family:'Orbitron',monospace; font-size:16px; font-weight:700; color:var(--text-pri); }
.kpi-delta { font-family:'Share Tech Mono',monospace; font-size:11px; margin-top:3px; }
.kpi-delta.pos { color:var(--accent-3); }
.kpi-delta.neg { color:var(--accent-4); }
.kpi-delta.neu { color:var(--text-dim); }

.section-head { font-family:'Orbitron',monospace; font-size:11px; font-weight:700; letter-spacing:3px; color:var(--accent-1); border-left:3px solid var(--accent-1); padding-left:10px; margin:16px 0 10px; text-transform:uppercase; }

.signal-badge { display:inline-block; padding:2px 8px; border-radius:4px; font-family:'Share Tech Mono',monospace; font-size:10px; font-weight:700; letter-spacing:1px; }
.signal-buy     { background:rgba(0,255,136,.15); color:var(--accent-3); border:1px solid var(--accent-3); }
.signal-sell    { background:rgba(255,51,102,.15); color:var(--accent-4); border:1px solid var(--accent-4); }
.signal-neutral { background:rgba(168,85,247,.15); color:var(--accent-5); border:1px solid var(--accent-5); }
.signal-caution { background:rgba(255,107,53,.15); color:var(--accent-2); border:1px solid var(--accent-2); }

.metric-panel { background:var(--bg-card); border:1px solid var(--border); border-radius:8px; padding:14px 18px; }
.metric-row { display:flex; justify-content:space-between; align-items:center; padding:7px 0; border-bottom:1px solid var(--border); font-family:'Share Tech Mono',monospace; font-size:11px; }
.metric-row:last-child { border-bottom:none; }
.metric-key  { color:var(--text-dim); }
.metric-val  { color:var(--text-pri); font-weight:600; }
.metric-val.green  { color:var(--accent-3); }
.metric-val.red    { color:var(--accent-4); }
.metric-val.cyan   { color:var(--accent-1); }
.metric-val.orange { color:var(--accent-2); }
.metric-val.purple { color:var(--accent-5); }

.stTabs [data-baseweb="tab-list"] { background:var(--bg-panel)!important; border-bottom:1px solid var(--border)!important; gap:4px; }
.stTabs [data-baseweb="tab"] { font-family:'Share Tech Mono',monospace!important; font-size:11px!important; letter-spacing:1px!important; color:var(--text-dim)!important; padding:10px 18px!important; border:none!important; background:transparent!important; }
.stTabs [aria-selected="true"] { color:var(--accent-1)!important; border-bottom:2px solid var(--accent-1)!important; }

.indicator-pill { display:inline-block; padding:3px 9px; border-radius:12px; background:rgba(0,245,255,.08); border:1px solid rgba(0,245,255,.25); font-family:'Share Tech Mono',monospace; font-size:10px; color:var(--accent-1); margin:2px; }

.chart-clean-label { font-family:'Share Tech Mono',monospace; font-size:10px; color:var(--text-dim); letter-spacing:1px; margin-bottom:6px; }

#MainMenu, footer, header { visibility:hidden; }
.block-container { padding-top:.8rem!important; }
</style>
""", unsafe_allow_html=True)

# ─── TICKERS ───────────────────────────────────────────────────────────────────
INDEX_TICKERS = {
    "NIFTY 50":     "^NSEI",
    "NIFTY BANK":   "^NSEBANK",
    "NIFTY MIDCAP": "^NSMIDCP",
    "NIFTY IT":     "^CNXIT",
    "SENSEX":       "^BSESN",
    "INDIA VIX":    "^INDIAVIX",
}

SECTOR_TICKERS = {
    "Bank":   "^NSEBANK",
    "IT":     "^CNXIT",
    "Auto":   "^CNXAUTO",
    "Pharma": "^CNXPHARMA",
    "FMCG":   "^CNXFMCG",
    "Metal":  "^CNXMETAL",
    "Energy": "^CNXENERGY",
    "Realty": "^CNXREALTY",
    "Infra":  "^CNXINFRA",
}

SMALLCAP_FALLBACKS = [
    ("NIFTY SMLCAP 100", "^CNXSC"),
    ("NIFTY SMLCAP 250", "NIFTYSMLCAP250.NS"),
    ("BSE SMALLCAP",     "BSE-SMLCAP.BO"),
]

PLOTLY_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(6,13,20,0.8)",
    font=dict(family="Share Tech Mono", color="#7ab3cc", size=11),
    legend=dict(bgcolor="rgba(6,13,20,0.9)", bordercolor="#0d2535", borderwidth=1),
    margin=dict(l=10, r=10, t=36, b=10),
    hoverlabel=dict(bgcolor="#060d14", bordercolor="#00f5ff", font_color="#e2f4ff"),
)
AXIS_STYLE = dict(gridcolor="#0d2535", zerolinecolor="#0d2535", showgrid=True)
NEON = ["#00f5ff","#ff6b35","#00ff88","#ff3366","#a855f7","#fbbf24","#06b6d4"]

# ─── ALL AVAILABLE TECHNICAL INDICATORS ───────────────────────────────────────
ALL_INDICATORS = [
    "MA 20", "MA 50", "MA 100", "MA 200",
    "Bollinger Bands", "VWAP",
    "RSI (14)", "MACD", "Stochastic",
    "ADX", "ATR", "OBV",
    "Fibonacci Levels", "Pivot Points",
    "Volume"
]

# ─── DATA FETCHING ─────────────────────────────────────────────────────────────
def _clean_df(df):
    """Flatten MultiIndex columns, forward-fill, strip timezone."""
    if df is None or df.empty:
        return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.loc[:, ~df.columns.duplicated()]
    df = df.dropna(how='all').ffill()
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)
    return df if not df.empty else None


def fetch_single_range(ticker, start_date="2020-01-01"):
    """Download a single ticker robustly."""
    try:
        df = yf.download(ticker, start=start_date, auto_adjust=True,
                         progress=False, group_by="ticker")
        df = _clean_df(df)
        return df if df is not None and len(df) >= 5 else None
    except Exception:
        return None


@st.cache_data(ttl=1800)
def fetch_data_range(ticker_dict, start_date="2020-01-01"):
    """Download each ticker individually — avoids MultiIndex keying bugs in newer yfinance."""
    data_dict = {}
    for name, ticker in ticker_dict.items():
        df = fetch_single_range(ticker, start_date)
        if df is not None:
            data_dict[name] = df
    return data_dict


# ─── EMBEDDED ETF DATA ────────────────────────────────────────────────────────
_ETF_B64 = (
    "UEsDBBQAAAAIAAdzWFwYTIddAQEAALoBAAAPABwAeGwvd29ya2Jvb2sueG1sIKIYACigFAAAAAAAAAAAAAAAAAAAAAAAAAAAAI2QwW4CIRCGX4XMvbJuYttsRC+9eGma1LRnhMElLrBhUPfdeugj9RUKqxtNTz3xDzPfPz/8fH0v14Pr2Akj2eAFzGcVMPQqaOv3Ao7JPDzDerUcmnOIh10IB5bnPTVRQJtS33BOqkUnaRZ69LlnQnQy5TLueTDGKnwJ6ujQJ15X1SOP2MmUd1Fre4Kr2/AfN+ojSk0tYnLdxcxJ6+E+3VtkOTu+SocCtq2lz2sDGC9zRX5YPNM9VC6YsZHSezEXkP9AqmRPuJW7scos/wOPOW6K+XHlqOfAxnOjBdTAYmOziBtdT0Y3VqOxHnXJS5eESnaqvCIfhZ/Xi6d6MYFT4tUvUEsDBAoAAAAAAAdzWFwrZ4o7nAIAAJwCAAALABwAX3JlbHMvLnJlbHMgohgAKKAUAAAAAAAAAAAAAAAAAAAAAAAAAAAA77u/PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0idXRmLTgiPz48UmVsYXRpb25zaGlwcyB4bWxucz0iaHR0cDovL3NjaGVtYXMub3BlbnhtbGZvcm1hdHMub3JnL3BhY2thZ2UvMjAwNi9yZWxhdGlvbnNoaXBzIj48UmVsYXRpb25zaGlwIFR5cGU9Imh0dHA6Ly9zY2hlbWFzLm9wZW54bWxmb3JtYXRzLm9yZy9vZmZpY2VEb2N1bWVudC8yMDA2L3JlbGF0aW9uc2hpcHMvb2ZmaWNlRG9jdW1lbnQiIFRhcmdldD0iL3hsL3dvcmtib29rLnhtbCIgSWQ9IlI4YjBkMjY1NjAyNTA0YTI2IiAvPjxSZWxhdGlvbnNoaXAgVHlwZT0iaHR0cDovL3NjaGVtYXMub3BlbnhtbGZvcm1hdHMub3JnL29mZmljZURvY3VtZW50LzIwMDYvcmVsYXRpb25zaGlwcy9leHRlbmRlZC1wcm9wZXJ0aWVzIiBUYXJnZXQ9Ii9kb2NQcm9wcy9hcHAueG1sIiBJZD0icklkMSIgLz48UmVsYXRpb25zaGlwIFR5cGU9Imh0dHA6Ly9zY2hlbWFzLm9wZW54bWxmb3JtYXRzLm9yZy9wYWNrYWdlLzIwMDYvcmVsYXRpb25zaGlwcy9tZXRhZGF0YS9jb3JlLXByb3BlcnRpZXMiIFRhcmdldD0iL3BhY2thZ2Uvc2VydmljZXMvbWV0YWRhdGEvY29yZS1wcm9wZXJ0aWVzLzY5OWU0YTc1NjdlYjRlZWQ5ODZhMjZmMzZjMWJkODA0LnBzbWRjcCIgSWQ9IlI0NDQyODczYTA2MTE0N2EwIiAvPjwvUmVsYXRpb25zaGlwcz5QSwMEFAAAAAgAB3NYXLYZvy9eAQAAOgMAABAAHABkb2NQcm9wcy9hcHAueG1sIKIYACigFAAAAAAAAAAAAAAAAAAAAAAAAAAAAJ2TTU7DMBCFrxK8b92WCqEocVUBEhsgohUskXEmrUViW/Y0arkaC47EFXAcKGn5E+zGb77MvHlSXp6ek8m6KqMarJNapWTYH5AIlNC5VIuUrLDoHZMJS7iJM6sNWJTgIv+JcnGNKVkimphSJ5ZQcdf3hPLNQtuKo3/aBdVFIQWcarGqQCEdDQZHNNeimeZu5hsDjrzN4+a/82CNoHLIe2brkQTPU2NKKTj629iFFFY7XWB0thZQJnSv3/B+7AzEykrcsEEgukpDzAQv4cSvYQUvHQTmQ2uIc+BNeBmX1rGkxrgGgdpG99xBc29Kam4lV0giJx/9c0xarFVDXRqHlt1q++CWAOgSuhVD2WW7tRyzYQB88SPYzrrkFeTRNVcL+MuK0dcr6PZWFmLZDcILc4kluKsi4xa/iSYYeA/mkHS8hiCGXZd7rYPMSoV3Uwv8d6q18unmjvs9s3TnD2CvUEsDBBQAAAAIAAdzWFweDqTwVgIAAGwEAAAUABwAeGwvc2hhcmVkU3RyaW5ncy54bWwgohgAKKAUAAAAAAAAAAAAAAAAAAAAAAAAAAAAdVTRbhMxEPyV1T2gVmpzAakIhSZVlFJAgqoCCZ5de5Mz3NlX7/qafBsPfBK/wK5zrVpQHnI6x7szOzOb/Pn1+/xi27UwYCIfw7x6OZlWgMFG58NmXmVen76pLhbn2xkRg4058Lw6qyAHf5dx9XgWkECz7bxqmPtZXZNtsDM0iT0GuVvH1BmWY9rU1Cc0jhpE7tr61XT6uu6MD1Uh8fpkhZtRbyzOK6kmTANWC3ix4bf6uV5+g0vD5ryW2oU+931j92K59QTXfs07+NqZtrWmh7MpfAwOt3CVgzt6f3x66RNahpvWhEM4Iw8e5HE/MjE60MLrGFYx9TFJw9EXOj7YZG1MDq58YLQN3AwMn9hBYwjY/MQAMjBwgxDQIpFJOxCOnsAEBx0aymII+CBhdL1vDUtuENelRU2BYlhg0Br9crl6B5+vJvAdhWRA4ORl5JgTtDhgC7coyXKUvjh4h+AUZJ1iBwlbb25bBJJqixP4EO+lJZ3AAREuymghCvcmm2TkEssIxtqcjN2dgHF4l+UNYioCWmQMIlMVmLDbK3g2eNHt97CirI+BvM4kK1U6MKWYSPFi50m3mEBPeq8o0pNbloJbli0T5UWa3mRCpaUsCpR38q8sYUPrJQ+NQGKVhBrD4LmkFSKsfTBBK0CN8q2XjYN7qaGoPqmrI1EqCh+iGHlGBXLhZUBXFlK01IBiTNwhymvCMU8JepAJHi0WT7HnAvCE/MGVPdie5UDiuSCUOaN4bZIn+Xn/58TjCknPaNbzKB7AtQY2Epwu+xNHR33PV78u/x2Lv1BLAwQUAAAACAAHc1hcDNxIs+MAAAC+AgAAGgAcAHhsL19yZWxzL3dvcmtib29rLnhtbC5yZWxzIKIYACigFAAAAAAAAAAAAAAAAAAAAAAAAAAAALWSQU7DMBBFr2LNnkxaUIVQ3W666bb0ApYziaMmtuWZ0vZsLDgSV8AECWHEgk02tvzH8/TG8vvr23p7HQf1Qon74DUsqhoUeRua3ncaztLePcJ2sz7QYCTfYNdHVrnFswYnEp8Q2ToaDVchks+VNqTRSD6mDqOxJ9MRLut6heknA0qmOt4i/YcY2ra3tAv2PJKXP8DIziRqniXlCRjU0aSORANeh7JUZTKofaMh7Zt7UDifkdwG+q0yZYXDw5wOl5BO7Iik1PiOP98tb4vCaDmnkeReKm2m6GstRVaTCBa/cPMBUEsDBBQAAAAIAAdzWFxVT8ei9wIAACkSAAANABwAeGwvc3R5bGVzLnhtbCCiGAAooBQAAAAAAAAAAAAAAAAAAAAAAAAAAADtWN1O2zAUfhXL3A6SdAJtFQFtTJWQgE2DSbt1EyfxcOzIdiHh1XaxR9orzH9J2qp0DStsTOQm9sn57M+ffc5x+/P7j8PjuqTgBgtJOIthtBdCgFnCU8LyGM5UtvsGHh8d1mOpGoovC4wV0Agmx3UMC6WqcRDIpMAlknu8wkx/y7gokdJdkQeyEhil0sBKGozC8CAoEWHQjMhm5aRUEiR8xlQMX88ZgXudpjHUfNyAJzzFMYQgWOkWHewvOqbp7vn5+W6jn/sxB4uYnVc7O+FeqB8LCTqOBp5xtkzWmMxby6feUZIzcINoDKdIYkoY9vPKO2eOIm9IOOUCiHwaw8kkDLv59HSoxM75BFEyFcTbM1QS2rgvo5ZbO/s2WLjn6Vi8fQwpfMPtFqF0ebe0ybwrpBQWbKK7wLevmkpvP+OeZ9A7/xaUC9REo/3BOMkpSR2v/GRZBb8VwQJ+bnzfsCudcpHq8G3XOoK9EaQE5Zwh+qWygdR2P/BbZgzGk+JMARvcXoB12xI4f+MiSF4MAlqA8VG8GoLT7m5FSvFyCNAhjFO77iHoFuOHMnI+XFhV+Jw3VNhNgKuE3QS3UthNgI8gbNe0RzrBlF6aEb9m3bnet+PW2XJpYF1TB4RvuqF8B1UVbS5m5RSLic31Ogd6q4mqvvfeonqMzWIlZnOAT4IrnChXKi2hqrMAypNrnFrngqQptifBL7rO1rGPevajoezDv8Pe19tnq76v/c+W/9zpGd3DPnoA++iR2AeLQd0G+Tbiu86eZKtQ6wQKLsid5mVuIDlmWCAKzQ1akcTeeGx2hEDhWn3mCrlB9Fy3AlVX2mg7hKV2Qt0UmGqnG3zam77NpCJZc4akOtOXJ2uThSDs+opPSAtD5pL+sVtL8BT5aHO1/ygx/fdqb5o/X073tvTeLN+/6L31bLKmPj1c7UGFarXa5sI9L7W+D6/VOfondA66yrlwU+7qqFtxZwfmd3QML4yodE7w6YxQRZjvBYsVWtpu/4/P0S9QSwMEFAAAAAgAB3NYXODGZ5hrQQAA2OoBABgAHAB4bC93b3Jrc2hlZXRzL3NoZWV0MS54bWwgohgAKKAUAAAAAAAAAAAAAAAAAAAAAAAAAAAAjd3frl1Hct/xVxF0n63Vf6q7WvCMMWPDSIAENuwguaalI4kYiRQOqZHtV8tFHimvkO4jksuqqq9KN/ZQPNx19t5r/da/+lT/v//zf//mb//th+8/++vT87vXb9/84fPyuD7/7OnNV2+/fv3m2z98/tP7b/6Lfv63f/ybf/vy57fPf3n33dPT+8/2P3jz7svnP3z+3fv3P375xRfvvvru6YdX7x5vf3x6s//um7fPP7x6v//4/O0Xb7/55vVXT3//9quffnh68/6Lel3ji+en71+938Xefff6x3eff3i1f/s9r/bux+enV1+//BI/fP/Li/3w6vWbz8+v9/Jf/+n5/M+3P73//vWbp396/uzdTz/88Or53//89P3bn/d7+/zjf/jn199+9/7lP3zxx7/54lf/+OvX+zc9n8Vnz0/f/OHzP5Uv/7xWe/nBDz/3v14//fzuV3/67Hw2//r27V/OH/7b13/4/PrVC//6H/zDyxvav9zXT9+8+un79//89uf/+vTh95H/XOfvX71/df7w/Pbnz55/+e1/fPXm3f5fX9aXt/zV+c9/Ov/9peJ+gXcv//2vf7xO7b++/AZfvfzf/Rr/6aUavFR7eany4aV++VVe/ubPv/6bX4qU3y7SoUgPXqr+6qU+Fo1+sv12UYGi8vJS9cOL9D7aFZb85efaS8k3H99n8mkOqDlcTQlrjqDmeiy55LfrTqg7Xd0R1p3he31cWn+7rkJddXVnWFfjumUlG9SCusvW7SWsu+K6tZb+24XLRbve5UrHW/KHH/S150xK415fXOkWly5UuiX7UqlUu7raPa5d49qtqia1KaJKc7XjverDDwbvO6lMuVW6q6xx5Y4beLJHF4qv4vKrr7h2HGCPMlr2iVOMFZdjEmdniYLslx1sJLUpyorLMon37QJhVpuspDbFWXF5JrBzQ6D1bP+iQCsu0QS2cYi0kW1olRKtukST+OBRIdFm0+QDrxRp1UWaxAeQCpE2R83eN0VadZEm8c5dIdKGrOQoUinSqos0iXfuCpE2xkwO2ZVCrbpQG/FGXiHUxihZbQq16kJtxIewCqHWZSWhVinUqgu1ER/CKoSaXNnXTZlWXaYN+Loh01qbyZlSpUyrLtNmnOWVTtJmEuWVQq26UJtxlFcItTJq8m03SrXmUm3GW3mDVGuSbOSNQq25UJvxRt4g1Fq/stoUas2F2ozDvEGolaJJoDa8lHShNuMwb3SedtVkU2sUas2F2ozDvNGZ2ky/bwq15kJtxnt3ozO1lR3EGoVac6Gm8d7dINSueWW7GKVac6mmsJ1HqbYeuiQJ1Eah1lyoaXy61KJQW/vQnX7iFGrNhZrCHhaF2i6dXeN3irTuIk3j/atHkbYebSanaZ0SrbtEW/FW1qNEWzvHV3Ji3CnQugu0FR9DehRo+tjbWFaa8qy7PFtw0yrKM32MlUVKxxtmLs5WvGv1KM70IVWTXatTmnWXZis+TepRmu133dINnMKsuzBbsIFHYaaPefXsXVOWdZdlKz5+9CjL9ma2sjtKnbKsuyxb8eGjR1m2S9tDnS9NWdZtls0L9usoy84HXpMtXCjMxIbZvOL9WqIw033wyM5ThNJMbJrNK97CJUqzXbpk37VQmolNs3nFxy2J02zs2klpSjOxaTav+LglcZrtk9LkNppQmolNs3nF+7XEabb/QbaZ4UMAm2b2dOdTaUiz0rIPnNJMbJrNAlt4nGaaXuILpZnYNJslPnIJpJlKEilCaSY2zWaJj1xCaZYdNIXSTFyaFdiv4zOzq17JCdKgNBsuzQo8+InTbEmybw0Ks+HCrMQb+IAwk5GcHw0Ks+HCrMQHrhGHWZ6jg8JsuDCr8YFrxGGmJbvCHhRmw4VZjXfrEYeZVsk+cAqz4cKsxrv1iMNsx262geODTRdmFTbwOMxaG1lpCrPhwqzGB64Rh1mdmkT4oDAbLsxqfOAacZi1lu3WlGXDZVmF3To+M7v6Sj7vSVk2XZbVeLeeUZbNfSqcHbcmhdl0YdbiDXxGYTYfc6alKcymC7MWH7dmHGZXS0tTmE0XZi0+bs0ozPYHLjVJlElhNl2YQcPCjMPs0pKcKEwKs+nCjHoW4jCrLbsvPSnMpguzBls4hNnIrq4nNmq4MOvxgWvGYdZaz1pEKMymCzNomphxmO0czb5rSrPp0gyaJmacZlWy71opzdSlGTRNaHxmVjV7yKeUZurSrMdbuManZs0+8felKc3UpVmHxpw4zbI+EaUsU5dl0DGhcJUpLdm+lbJMXZZBw4TCPbMr6xNRyjJ1WQb9EhpnWV/Z9ZZSlqnLMoHtO84y0axLRCnL1GWZxMctjbNM2sh2Lew7c1kG7RIaZ5n07HmqUpapyzJol9A4y3raNbAoy5bLMuiWWHGWyZVdeizKsuWybMRb+IqzbIzsWc+iLFsuywY0+8VZZqPPV6YwWy7MoFNiwVVmzxpjFoXZcmEGjRIrDrOV3ZhdlGXLZRm0Saw4y1bXbCOjLFsuywZs33DHbK7sXVOWLZdlIz5urTjLpr0o9aUpy5bLMmgOWXGWaelJgi9so3VZBr0hK84yXdkds3JxI61LM+gO+fiT7n5dS5sML+ylvVygTWioveCZZvb8oVzYTHu5SJvQ7XdFmbYetaTdtBe2014u1qBH5ONP+reedpZe2FJ7uWSDLpGPP+mqp9t7ubCp9nLpBn0iH3/SV8/uT5cL22ovF3BKm3wsBIrk3zs21l4u46Bf4+NPuupXdte0XNhae7mYU9rh4p6Neo10d8f22sslHTSMfPxJV12y3Z3JgDMDU6GVO0QDa18VZd/6b6ABF3TQu1FCNrAe/UqTjtmAcwMT2jdKCAd29ZqdLheGA04O2BOEu3qcdNXeYQ+qY9I5PTAXbHMhH9gHOM1OmgvzAecH5oKUDwHByZqe7W8MCJwgmNDKUUJCsD/5NbNeeiYEzhBM6OYoISLYO9zInrMXRgROEUxo6CghI9jbfFnpHodJ5ySBXrTNx0mXPrQoSAmKswR6wSEmxAT7rfeUUCAmKE4TKHRXlJAT7OrZzaeCmqA4TqDQX1FCT3C+9fTYjp6gOFCgF2xzoShYDynZA6OCoqA4UqAFjjGhKdjVa2q00BQUhwpsk8xdPU66cWmWdKgKimMFCr0WJXQF6zFL9gylICwoThYotFuUkBbs6jU3gZh0zhZooW0+Tjpt2QEOcUFxukALHGJCXrCLS/q1Iy8ozhfYJ2GfqofA4Lz1TNEUFAbFEQOF1osSGoNdvWQN0AWNQXHIQKH7ooTKYO/uvafvHaPOMQOtsMmHzmAHrbYs6tAZFAcNtMJlTCgN9nu3/yCojlHnqIFCG0YJrcGufq10m8eoc9hAoROjhNrgvPesN7igNiiOGyg0YxTwBs3uJEF1jDonDhTGCRQgB5eMFEBj1jl0oA0OcaAOruyxcUF2UJw7UOjKKCE8OO2EWW9EQXpQnD1QaMwogA+ulrVwFtQHxfEDe8S6q8dRV3KNjAChOIGgMF+hhARhv3c7GCGozvjdRV0j/R5HXe25vMeocw5BoVOihBDhXMNpWh2jzlEEhWaJElqEl+rpNo9R5zSC0rSFkCOca7jsoVdBj1AcSFCatxCKhHN/OHsOU5AkFGcSFLomSogS9lY3sqduBVVCcSxBoXGihC7h3JnPju7oEoqDCUrjJkKZsIvX9JYN0oTibILS4IUQJ5y3ngmBgjqhOJ6gNHoh9Am7uuajNjDqnFBQ6KIoIVF4uT2cbnQ86cNFHTRSlFApnNuU+feOUeecgtLoiRAqvNwkzS4hUSoURxUUJiGU0CrsqCtZA3tBrFCcVlDoLSghV9jVr6yvuaBXKA4sKPQXFBAL9cqO7igWiiMLOuBrD83CLt7Se6SoFopjCzog5UO3cDY6Satj1Dm5oNBoUEK6cHb3NObRLhSHFxR6DUqoF857T4+vyBeK8wsK7QYlBAxnk88/eYw6RxjspcFdHc7qbPdPUJ3HGrmoo4f+IWM47z09r0LHUBxkUHrqH0qGfV5lHyQE1THqnGVQeuofYoZzeG/pVodR5zyDwoyEEoKGc3hPbxWiaCiONChMSSihaTjV0z0OUUNxqkHpqX/IGs5pXXqQQddQHGxQhT0ulA3nbD69jkLaUJxtUOo5CHHDGR2QPhBC3VAcb1CY1VBC3/DSb5EVx6hzwMF+jndxeACbj+tD4lCccVCFg0yIHM7hfaY7HM9wc1FHHQ+hc9hBW9OTC4QOxUkHpZaHkDqcpoN8k8eoc9hBYXZDCbXDeRiWtekW5A7FeQfrFz5VD8HDuUOc3h1H8VAceVBqeQjNw66eSo+C6KE49aDU8hCyh/UY+RUsyofi6INSy0NoH3Z12xsTVMeoc/phwSiHEvKH8xgym6xW0D8UByAWTHMooYDY772lJ1ZIIIozEItaHkIEcb739PoZFURxDGJRz0PoIM4wovS0DiFEcRJiwTCLElKIs8fl3ztmncMQCyY7lFBD7OorfQqKHKI4D7FguEMJQcRL9XRgJ2adIxG2GfquHmfdaJn6L4giilMRi1ouQhZxnsWljwYQRhQnIxa1XIQ04mx16d06tBHF4Qg7fOeuTs9g0+fP6COKAxJ2xu9dHZ7B1pV+75h1zkgsarkIkcS5gE43eYw6pyQWtVyETOLcN0kffqOTKA5KLGq5ICnRsgmeBalEcVZiwdyHEmKJ8yQwew5ZEUtUhyUs8PlYvQKWqC0dlItYojossaDTogKWqNnFe0UsUR2WWNBxUQlL1JHs7RWxRHVYws5qvKvHSdfSpvmKWKI6LLFgDEQFLNFWlvIVsUR1WGLBJIgKWCK/jqqIJarDEgs6LipgiZbdr6poJaqzEgsaLipYiZYe3CtaieqsxIKOi0pWIus1qUglqqMSC2ZCVKASe4tPDjEVrUR1VmLBWIgKVqKmA40qYonqsMSChosKWKKmw5LRSlRnJRb0W1SwEjWdBFjRSlRnJRYMxahkJVZ2w6iilajOSiyYEFHBSlR7KhJUx6BzVmLBkIgKVqJqOpYcrUR1VmJBt0dFK5HdLKtoJaqzEgu6PSpYidrT8xq0EtVZiQXdHhWsREmNTEUrUZ2VWDAyooKVqC2TkJXXXXBYYsHUiApYYm8PWdrwygsOSyxo96iAJUrJnj7X31h7wWUdNFzUUEucOYEZM6+8+oLTEouWvAi1xO+Y11d5+QWHJeyL3cUh6q4MwFZegMFhCTt65K4eR92l2T3SykswOCyxaN0LwBJlpGfTvAqDwxILhlhUwBLlyu7UVV6HwWGJRWtfAJYodoGSoDpGndMSi1a/AC1x2WT21VFLVKclFjSbVNASRdKgRS1RnZZY0GxSQUsUO84zqI5R57TEgmaTClqi5mfzqCWq0xKLlv8ALVFqutoLaonqtMSiFUBAS1z2iBxUx6xzWsJOJryrwxPYli2OUFFLVKclrGi9q8NpXQqvK2qJ6rSEPTu/q0PW9azFqaKWqE5LLBjyUElLpOO9K2qJ6rTEgiEPlbSEXbnEV0cuUR2XWNDqUolL9PQiErlEdVxiQatLDbnEwRrZ145aojotsaDTpdJqDem3jliiOixh38ldPD6pU8m/dV5UyyUdDJiosGTDrp6+d0w6hyUWNLpUWLVhpfOLKmKJ6rDEgk6XCgs3rPSpf0UsUR2WWNDpUgFLXOlsj4pYojossWDARSUs0dIbF4glqsMSC3pNKmCJ0tNbRoglqsMSC3pNKmCJki7YUVFLVKclFvSaVNASV01vEKOWqE5LLBgxUWEpB61Xts2jlqhOSywYMVFhNYcp2eysilqiWi0hF/SaVFjQQdNVFSpqiWq1xK4OexCs6TBnum4jaolqtYTYxzt3dRhSJ9nUy4paolotsavTNg9z6tLh3BW1RLVaYleHowws7qBzZEmLWqJaLbGrw1Em1BL7KNOyp/4VuUS1XGJXh/2dlni40uM7coolqgWTcgmo1HmfTBq2zqBKWNhBrD4LmkFSKsfTBBK0CN8q2XjYN7qaGoPqmrI1EqCh+iGHlGBXLhZUBXFlK01IBiTNwhymvCMU8JepAJHi0WT7HnAvCE/MGVPdie5UDiuSCUOaN4bZIn+Xn/58TjCknPaNbzKB7AtQY2Epwu+xNHR33PV78u/x2Lv1BLAwQUAAAACAAHc1hcdbGRXqsFAAC7GwAAEwAcAHhsL3RoZW1lL3RoZW1lMS54bWwgohgAKKAUAAAAAAAAAAAAAAAAAAAAAAAAAAAA7VlNj9tEGP4rI99bx0mcZldNq202aaHddrUbinqcOBN7mrHHmpnsNjfUHpGQEAVxQeLGAQGVWokDRfyYhSIo0v4FXjtee5yMu9l2EUVsDoln/LzfH37HOf7pl6vXH4YMHRAhKY86lnO5ZiESeXxMI79jzdTkUtu6fu0q3lQBCQkCcCQ3cccKlIo3bVt6sI3lZR6TCO5NuAixgqXw7bHAh8AkZHa9VmvZIaaRhSIcko51dzKhHkHDhKWVM+8z+IqUTDY8Jva9VKJOkWLHUyf5kXPZYwIdYNaxQM6YHw7JQ2UhhqWCGx2rln4sZF+7audUTFUQa4SD9HNCmFGMp/WUUPijnNIZNDeubBcS6gsJq8B+v9/rOwXHFIE9D6x1VsDNQdvp5lw11OJylXuv5taaSwSahMYKwUa323U3ygSNgqC5QtCutZpb9TJBsyBwV23obvV6rTKBWxC0VggGVzZazSWCFBUwGk1X4ElkixDlmAlnN434NuDbeS4UMFvLtAWDSFXlXYgfcDEAQBplrGiE1DwmE+wBrofDkaA4lYA3CdZuZXueXN1LxCHpCRqrjvV+jKFACszxi++OXzxDxy+eHj16fvTox6PHj48e/WCivIkjX6d89c2nf339Uf3z2devnnxeQSB1gt++//jXnz+rQCod+fKLp78/f/ryy0/++PaJCb8l8EjHD2lIJLpDDtEeDxP7DCLISJyRZBhgWiLBAUBNyL4KSsg7c8yMwC4p+/CegLZgRN6YPSjpux+ImaIm5K0gLCF3OGddLsw23UrFaTbNIr9CvpjpwD2MD4zie0tR7s9iyGxqZNoLSEnVXQaBxz6JiELJPT4lxER3n9KSf3eoJ7jkE4XuU9TF1OyYIR0pM9VNGkKA5kYdIeolD+3cQ13OjAK2yUEZChWCmZEpYSVv3sAzhUOz1jhkOvQ2VoFR0f258EqOlwqC7hPGUX9MpDQS3RXzksq3MLQocwbssHlYhgpFp0bobcy5Dt3m016Aw9isN40CHfyenELGYrTLlVkPXq6ZZA0BwVF15O9Ros5Y7B9QPzAnS3JnJk66eqk/hzR6XbNmFLr1RbNeatZb8AQzFslyi64E/kcb8zaeRbskSf6LvnzRly/68msqfO1uXDRgW5+rU4Zh5ZA9oYztqzkjt2XauiXoPR7AZrpIifKhPg7g8kReCegLnF4jwdWHVAX7AY5BjpOK8GXG25co5hIOE1Yl8/RsSsH8dM/ND5QAx2qHjxf7jdJJM2eUrnypi2okLNYV17jytuKcBXJNeY5bIc99vTxb8ynUBsLJmwOnVc/UlB5mZJx4P+NwEp1zj5QM8JhkoXLMtjiNdX3XPt11mryNxtvKWydWusBmlUD3PIJVWw2WvVqdLCqv0CEo5tZdC3k47lgTGLzgMoyBoUxaEmZ+1LE8lVlzam0v21yRoE6t2uaSkFhItY1lsCBLb+UvZaLChLrbTNidjw2m/rSmHo2286/qYS9HmEwmxFMVO8Uyu8dnioj9YHyIRmwm9jBo3lxk2ZhKeJTUTxYC6rWZJWC5D2T1sPzqJ6sTzOIAZz2qrWfAAp9e50qkK00/u0L5N7SlcY62uP9nW5L0hfG2MU7PYTAfCIySPO1YXKiAQz+KA+oNBEwUqTBQDEFtpC2LJa+wE2XJgdbCFkwWDc8P1B71kaDQ9VQgCNlVmaWncHNOOmRWHhmnrOPkCst48TsiB4QNkyJuJS6wUJC3lcwXKXA5cLapxkb+4F2eippVU9EpY0MhqnmWKaWpPwS0Z8PG22pxxgdwvcLsurv+AziGkwpKvqCRU+GxYgYe8j3IAlQMnZCSl9pZKeabI9C6rduX8PpnZ6wiEO2quJ/reKp5vFHl8VMEvrnHXYPD3VP8ba8WrK0dedLVyt9dfPQAhG/DmWrGlMzeSz2E02nv5N8JYJTJTImv/Q1QSwMECgAAAAAAB3NYXD+YAjbaAQAA2gEAAFEAHABwYWNrYWdlL3NlcnZpY2VzL21ldGFkYXRhL2NvcmUtcHJvcGVydGllcy82OTllNGE3NTY3ZWI0ZWVkOTg2YTI2ZjM2YzFiZDgwNC5wc21kY3AgohgAKKAUAAAAAAAAAAAAAAAAAAAAAAAAAAAA77u/PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0idXRmLTgiPz48Y29yZVByb3BlcnRpZXMgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIiB4bWxuczpkY3Rlcm1zPSJodHRwOi8vcHVybC5vcmcvZGMvdGVybXMvIiB4bWxuczp4c2k9Imh0dHA6Ly93d3cudzMub3JnLzIwMDEvWE1MU2NoZW1hLWluc3RhbmNlIiB4bWxucz0iaHR0cDovL3NjaGVtYXMub3BlbnhtbGZvcm1hdHMub3JnL3BhY2thZ2UvMjAwNi9tZXRhZGF0YS9jb3JlLXByb3BlcnRpZXMiPjxkY3Rlcm1zOmNyZWF0ZWQgeHNpOnR5cGU9ImRjdGVybXM6VzNDRFRGIj4yMDI2LTAyLTI0VDA4OjU0OjE0LjA2MjQxNzFaPC9kY3Rlcm1zOmNyZWF0ZWQ+PGRjdGVybXM6bW9kaWZpZWQgeHNpOnR5cGU9ImRjdGVybXM6VzNDRFRGIj4yMDI2LTAyLTI0VDA4OjU0OjE0LjA2MjQxNzFaPC9kY3Rlcm1zOm1vZGlmaWVkPjwvY29yZVByb3BlcnRpZXM+UEsDBAoAAAAAAAdzWFwRlMAINwQAADcEAAATABwAW0NvbnRlbnRfVHlwZXNdLnhtbCCiGAAooBQAAAAAAAAAAAAAAAAAAAAAAAAAAADvu788P3htbCB2ZXJzaW9uPSIxLjAiIGVuY29kaW5nPSJ1dGYtOCI/PjxUeXBlcyB4bWxucz0iaHR0cDovL3NjaGVtYXMub3BlbnhtbGZvcm1hdHMub3JnL3BhY2thZ2UvMjAwNi9jb250ZW50LXR5cGVzIj48RGVmYXVsdCBFeHRlbnNpb249InhtbCIgQ29udGVudFR5cGU9ImFwcGxpY2F0aW9uL3ZuZC5vcGVueG1sZm9ybWF0cy1vZmZpY2Vkb2N1bWVudC5zcHJlYWRzaGVldG1sLnNoZWV0Lm1haW4reG1sIiAvPjxEZWZhdWx0IEV4dGVuc2lvbj0icmVscyIgQ29udGVudFR5cGU9ImFwcGxpY2F0aW9uL3ZuZC5vcGVueG1sZm9ybWF0cy1wYWNrYWdlLnJlbGF0aW9uc2hpcHMreG1sIiAvPjxEZWZhdWx0IEV4dGVuc2lvbj0icHNtZGNwIiBDb250ZW50VHlwZT0iYXBwbGljYXRpb24vdm5kLm9wZW54bWxmb3JtYXRzLXBhY2thZ2UuY29yZS1wcm9wZXJ0aWVzK3htbCIgLz48T3ZlcnJpZGUgUGFydE5hbWU9Ii9kb2NQcm9wcy9hcHAueG1sIiBDb250ZW50VHlwZT0iYXBwbGljYXRpb24vdm5kLm9wZW54bWxmb3JtYXRzLW9mZmljZWRvY3VtZW50LmV4dGVuZGVkLXByb3BlcnRpZXMreG1sIiAvPjxPdmVycmlkZSBQYXJ0TmFtZT0iL3hsL3NoYXJlZFN0cmluZ3MueG1sIiBDb250ZW50VHlwZT0iYXBwbGljYXRpb24vdm5kLm9wZW54bWxmb3JtYXRzLW9mZmljZWRvY3VtZW50LnNwcmVhZHNoZWV0bWwuc2hhcmVkU3RyaW5ncyt4bWwiIC8+PE92ZXJyaWRlIFBhcnROYW1lPSIveGwvc3R5bGVzLnhtbCIgQ29udGVudFR5cGU9ImFwcGxpY2F0aW9uL3ZuZC5vcGVueG1sZm9ybWF0cy1vZmZpY2Vkb2N1bWVudC5zcHJlYWRzaGVldG1sLnN0eWxlcyt4bWwiIC8+PE92ZXJyaWRlIFBhcnROYW1lPSIveGwvd29ya3NoZWV0cy9zaGVldDEueG1sIiBDb250ZW50VHlwZT0iYXBwbGljYXRpb24vdm5kLm9wZW54bWxmb3JtYXRzLW9mZmljZWRvY3VtZW50LnNwcmVhZHNoZWV0bWwud29ya3NoZWV0K3htbCIgLz48T3ZlcnJpZGUgUGFydE5hbWU9Ii94bC90aGVtZS90aGVtZTEueG1sIiBDb250ZW50VHlwZT0iYXBwbGljYXRpb24vdm5kLm9wZW54bWxmb3JtYXRzLW9mZmljZWRvY3VtZW50LnRoZW1lK3htbCIgLz48L1R5cGVzPlBLAQItABQAAAAIAAdzWFwYTIddAQEAALoBAAAPAAAAAAAAAAAAAAAAAAAAAAB4bC93b3JrYm9vay54bWxQSwECLQAKAAAAAAAHc1hcK2eKO5wCAACcAgAACwAAAAAAAAAAAAAAAABKAQAAX3JlbHMvLnJlbHNQSwECLQAUAAAACAAHc1hcthm/L14BAAA6AwAAEAAAAAAAAAAAAAAAAAArBAAAZG9jUHJvcHMvYXBwLnhtbFBLAQItABQAAAAIAAdzWFweDqTwVgIAAGwEAAAUAAAAAAAAAAAAAAAAANMFAAB4bC9zaGFyZWRTdHJpbmdzLnhtbFBLAQItABQAAAAIAAdzWFwM3Eiz4wAAAL4CAAAaAAAAAAAAAAAAAAAAAHcIAAB4bC9fcmVscy93b3JrYm9vay54bWwucmVsc1BLAQItABQAAAAIAAdzWFxVT8ei9wIAACkSAAANAAAAAAAAAAAAAAAAAK4JAAB4bC9zdHlsZXMueG1sUEsBAi0AFAAAAAgAB3NYXODGZ5hrQQAA2OoBABgAAAAAAAAAAAAAAAAA7AwAAHhsL3dvcmtzaGVldHMvc2hlZXQxLnhtbFBLAQItABQAAAAIAAdzWFx1sZFeqwUAALsbAAATAAAAAAAAAAAAAAAAAKlOAAB4bC90aGVtZS90aGVtZTEueG1sUEsBAi0ACgAAAAAAB3NYXD+YAjbaAQAA2gEAAFEAAAAAAAAAAAAAAAAAoVQAAHBhY2thZ2Uvc2VydmljZXMvbWV0YWRhdGEvY29yZS1wcm9wZXJ0aWVzLzY5OWU0YTc1NjdlYjRlZWQ5ODZhMjZmMzZjMWJkODA0LnBzbWRjcFBLAQItAAoAAAAAAAdzWFwRlMAINwQAADcEAAATAAAAAAAAAAAAAAAAAAZXAABbQ29udGVudF9UeXBlc10ueG1sUEsFBgAAAAAKAAoAwAIAAIpbAAAAAA=="
)


def parse_etf_bytes(raw_bytes):
    import io
    raw  = pd.read_excel(io.BytesIO(raw_bytes), header=None)
    data = raw.iloc[4:, :2].copy()
    data.columns = ["Date", "NAV"]
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    data["NAV"]  = pd.to_numeric(data["NAV"],   errors="coerce")
    data = data.dropna(subset=["Date", "NAV"]).sort_values("Date")
    data.set_index("Date", inplace=True)
    df = pd.DataFrame(
        {"Open": data["NAV"], "High": data["NAV"],
         "Low":  data["NAV"], "Close": data["NAV"], "Volume": 0},
        index=data.index,
    )
    return df if len(df) >= 5 else None


def resolve_smallcap(start_date="2020-01-01", uploaded_file=None):
    cutoff = pd.Timestamp(start_date)

    def trim(df, name, source):
        filtered = df[df.index >= cutoff]
        return name, (filtered if len(filtered) >= 5 else df), source

    # Embedded base64
    try:
        raw_bytes = base64.b64decode(_ETF_B64)
        df = parse_etf_bytes(raw_bytes)
        if df is not None:
            return trim(df, "NIFTY SMALLCAP 50 ETF", "📦 Embedded")
    except Exception:
        pass

    # Sidebar upload
    if uploaded_file is not None:
        try:
            df = parse_etf_bytes(uploaded_file.read())
            if df is not None:
                return trim(df, "NIFTY SMALLCAP 50 ETF", "📤 Uploaded")
        except Exception:
            pass

    # Yahoo fallback
    for display_name, ticker in SMALLCAP_FALLBACKS:
        df = fetch_single_range(ticker, start_date)
        if df is not None:
            return display_name, df, f"🌐 Yahoo ({ticker})"

    return None, None, "❌ No smallcap data"


# ─── TECHNICAL INDICATORS ──────────────────────────────────────────────────────
def calc_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calc_macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calc_bollinger(series, period=20, std_dev=2):
    sma = series.rolling(period).mean()
    std = series.rolling(period).std()
    upper = sma + std_dev * std
    lower = sma - std_dev * std
    pct_b = (series - lower) / (upper - lower)
    return upper, sma, lower, pct_b

def calc_atr(df, period=14):
    hl  = df['High'] - df['Low']
    hc  = (df['High'] - df['Close'].shift()).abs()
    lc  = (df['Low']  - df['Close'].shift()).abs()
    tr  = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.rolling(period).mean()

def calc_stochastic(df, k_period=14, d_period=3):
    low_min  = df['Low'].rolling(k_period).min()
    high_max = df['High'].rolling(k_period).max()
    k = 100 * (df['Close'] - low_min) / (high_max - low_min)
    d = k.rolling(d_period).mean()
    return k, d

def calc_adx(df, period=14):
    plus_dm  = df['High'].diff()
    minus_dm = df['Low'].diff()
    plus_dm[plus_dm < 0]   = 0
    minus_dm[minus_dm > 0] = 0
    tr  = calc_atr(df, period)
    plus_di  = 100 * (plus_dm.ewm(alpha=1/period, adjust=False).mean() / tr)
    minus_di = 100 * (minus_dm.abs().ewm(alpha=1/period, adjust=False).mean() / tr)
    dx  = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    adx_val = dx.ewm(alpha=1/period, adjust=False).mean()
    return adx_val, plus_di, minus_di

def calc_obv(df):
    direction = df['Close'].diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    return (direction * df['Volume']).cumsum()

def calc_vwap(df):
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    return (tp * df['Volume']).cumsum() / df['Volume'].cumsum()

def fibonacci_levels(series):
    high = series.max()
    low  = series.min()
    diff = high - low
    return {
        "0.0% (Low)":   low,
        "23.6%":        low + 0.236 * diff,
        "38.2%":        low + 0.382 * diff,
        "50.0%":        low + 0.500 * diff,
        "61.8%":        low + 0.618 * diff,
        "78.6%":        low + 0.786 * diff,
        "100% (High)":  high,
    }

def pivot_points(df):
    last = df.iloc[-2] if len(df) > 1 else df.iloc[-1]
    H, L, C = last['High'], last['Low'], last['Close']
    P  = (H + L + C) / 3
    return {"R3": H+2*(P-L), "R2": P+(H-L), "R1": 2*P-L,
            "Pivot": P, "S1": 2*P-H, "S2": P-(H-L), "S3": L-2*(H-P)}

def calculate_drawdown(series):
    return ((series / series.cummax()) - 1) * 100


# ─── CHART BUILDER — PURE + OPTIONAL OVERLAYS ─────────────────────────────────
def build_chart(df, name, selected_indicators, chart_type="Candlestick"):
    """
    Build a dynamic chart.
    - Base: candlestick or line (clean by default)
    - Optional sub-panels: RSI, MACD, Stochastic, ADX, ATR, OBV, Volume
    - Optional overlays: MAs, BB, VWAP, Fibonacci, Pivot Points
    """
    # Determine which sub-panels are needed
    sub_indicators = [i for i in selected_indicators if i in
                      ["RSI (14)", "MACD", "Stochastic", "ADX", "ATR", "OBV", "Volume"]]
    n_sub = len(sub_indicators)

    if n_sub == 0:
        fig = go.Figure()
        has_subplots = False
    else:
        heights = [0.55] + [round(0.45 / n_sub, 3)] * n_sub
        fig = make_subplots(
            rows=1 + n_sub, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.018,
            row_heights=heights,
        )
        has_subplots = True

    # ── MAIN PRICE ROW ──────────────────────────────────────────────────────
    r = 1
    if chart_type == "Candlestick":
        trace = go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'],
            low=df['Low'], close=df['Close'], name=name,
            increasing_line_color="#00ff88", decreasing_line_color="#ff3366",
            increasing_fillcolor="rgba(0,255,136,0.75)",
            decreasing_fillcolor="rgba(255,51,102,0.75)",
        )
    else:
        trace = go.Scatter(x=df.index, y=df['Close'], name=name,
            line=dict(color="#00f5ff", width=1.8))

    if has_subplots:
        fig.add_trace(trace, row=r, col=1)
    else:
        fig.add_trace(trace)

    def add_trace(t, **kwargs):
        if has_subplots:
            fig.add_trace(t, **kwargs)
        else:
            fig.add_trace(t)

    def add_hline(y, **kwargs):
        if has_subplots:
            fig.add_hline(y=y, **kwargs)
        else:
            fig.add_hline(y=y, **{k:v for k,v in kwargs.items() if k not in ['row','col']})

    # ── OVERLAY INDICATORS on row 1 ─────────────────────────────────────────
    ma_colors = {"MA 20": "#ff6b35", "MA 50": "#fbbf24", "MA 100": "#a855f7", "MA 200": "#06b6d4"}
    for ma_label, color in ma_colors.items():
        if ma_label in selected_indicators:
            period = int(ma_label.split()[1])
            ma_vals = df['Close'].rolling(period).mean()
            t = go.Scatter(x=df.index, y=ma_vals, name=ma_label,
                line=dict(color=color, width=1.5))
            add_trace(t, row=r, col=1)

    if "Bollinger Bands" in selected_indicators:
        bb_u, bb_m, bb_l, _ = calc_bollinger(df['Close'])
        add_trace(go.Scatter(x=df.index, y=bb_u, name="BB Upper",
            line=dict(color="rgba(0,245,255,0.45)", width=1, dash='dot'), showlegend=False), row=r, col=1)
        add_trace(go.Scatter(x=df.index, y=bb_l, name="BB Lower",
            line=dict(color="rgba(0,245,255,0.45)", width=1, dash='dot'),
            fill='tonexty', fillcolor='rgba(0,245,255,0.04)', showlegend=False), row=r, col=1)
        add_trace(go.Scatter(x=df.index, y=bb_m, name="BB Mid",
            line=dict(color="rgba(0,245,255,0.22)", width=1), showlegend=False), row=r, col=1)

    has_vol = 'Volume' in df.columns and df['Volume'].sum() > 0

    if "VWAP" in selected_indicators and has_vol:
        vwap_vals = calc_vwap(df)
        add_trace(go.Scatter(x=df.index, y=vwap_vals, name="VWAP",
            line=dict(color="#fbbf24", width=1.5, dash='dash')), row=r, col=1)

    if "Fibonacci Levels" in selected_indicators:
        fibs = fibonacci_levels(df['Close'])
        fib_colors = ["#ff3366","#ff6b35","#fbbf24","#00f5ff","#a855f7","#06b6d4","#00ff88"]
        for i, (label, level) in enumerate(fibs.items()):
            kw = dict(line_dash="dot", line_color=fib_colors[i], line_width=0.9,
                      annotation_text=f"  {label}: {level:,.0f}",
                      annotation_font_color=fib_colors[i], annotation_font_size=9)
            if has_subplots:
                kw['row'] = r; kw['col'] = 1
            fig.add_hline(y=level, **kw)

    if "Pivot Points" in selected_indicators:
        pivots = pivot_points(df)
        pc = {"R3":"#ff3366","R2":"#ff6b35","R1":"#fbbf24","Pivot":"#00f5ff","S1":"#a855f7","S2":"#06b6d4","S3":"#00ff88"}
        for label, level in pivots.items():
            kw = dict(line_dash="dot", line_color=pc[label], line_width=0.9,
                      annotation_text=f"  {label}: {level:,.0f}",
                      annotation_font_color=pc[label], annotation_font_size=9)
            if has_subplots:
                kw['row'] = r; kw['col'] = 1
            fig.add_hline(y=level, **kw)

    # ── SUB-PANEL INDICATORS ────────────────────────────────────────────────
    for sub_i, ind in enumerate(sub_indicators):
        sub_row = 2 + sub_i

        if ind == "RSI (14)":
            rsi_vals = calc_rsi(df['Close'])
            fig.add_trace(go.Scatter(x=df.index, y=rsi_vals, name="RSI",
                line=dict(color="#a855f7", width=1.8),
                fill='tozeroy', fillcolor='rgba(168,85,247,0.05)'), row=sub_row, col=1)
            fig.add_hrect(y0=70, y1=100, fillcolor="rgba(255,51,102,0.05)", line_width=0, row=sub_row, col=1)
            fig.add_hrect(y0=0,  y1=30,  fillcolor="rgba(0,255,136,0.05)",  line_width=0, row=sub_row, col=1)
            fig.add_hline(y=70, line_color="#ff3366", line_dash="dash", line_width=0.7, row=sub_row, col=1)
            fig.add_hline(y=30, line_color="#00ff88", line_dash="dash", line_width=0.7, row=sub_row, col=1)
            fig.update_yaxes(range=[0,100], title_text="RSI", title_font=dict(size=9,color="#3a5a70"), row=sub_row, col=1, **AXIS_STYLE)

        elif ind == "MACD":
            m, s, h_vals = calc_macd(df['Close'])
            colors_h = ['rgba(0,255,136,0.7)' if v >= 0 else 'rgba(255,51,102,0.7)' for v in h_vals]
            fig.add_trace(go.Bar(x=df.index, y=h_vals, name="MACD Hist",
                marker_color=colors_h, showlegend=False), row=sub_row, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=m, name="MACD",
                line=dict(color="#00f5ff", width=1.5)), row=sub_row, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=s, name="Signal",
                line=dict(color="#ff6b35", width=1.5)), row=sub_row, col=1)
            fig.add_hline(y=0, line_color="#0d2535", line_width=1, row=sub_row, col=1)
            fig.update_yaxes(title_text="MACD", title_font=dict(size=9,color="#3a5a70"), row=sub_row, col=1, **AXIS_STYLE)

        elif ind == "Stochastic":
            k, d = calc_stochastic(df)
            fig.add_trace(go.Scatter(x=df.index, y=k, name="%K",
                line=dict(color="#00f5ff", width=1.5)), row=sub_row, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=d, name="%D",
                line=dict(color="#ff6b35", width=1.5, dash='dot')), row=sub_row, col=1)
            fig.add_hline(y=80, line_color="#ff3366", line_dash="dash", line_width=0.7, row=sub_row, col=1)
            fig.add_hline(y=20, line_color="#00ff88", line_dash="dash", line_width=0.7, row=sub_row, col=1)
            fig.update_yaxes(range=[0,100], title_text="STOCH", title_font=dict(size=9,color="#3a5a70"), row=sub_row, col=1, **AXIS_STYLE)

        elif ind == "ADX":
            adx_v, di_p, di_n = calc_adx(df)
            fig.add_trace(go.Scatter(x=df.index, y=adx_v, name="ADX",
                line=dict(color="#fbbf24", width=1.8)), row=sub_row, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=di_p, name="+DI",
                line=dict(color="#00ff88", width=1.2, dash='dot')), row=sub_row, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=di_n.abs(), name="-DI",
                line=dict(color="#ff3366", width=1.2, dash='dot')), row=sub_row, col=1)
            fig.add_hline(y=25, line_color="#fbbf24", line_dash="dash", line_width=0.7, row=sub_row, col=1)
            fig.update_yaxes(title_text="ADX", title_font=dict(size=9,color="#3a5a70"), row=sub_row, col=1, **AXIS_STYLE)

        elif ind == "ATR":
            atr_vals = calc_atr(df)
            fig.add_trace(go.Scatter(x=df.index, y=atr_vals, name="ATR(14)",
                line=dict(color="#06b6d4", width=1.5),
                fill='tozeroy', fillcolor='rgba(6,182,212,0.06)'), row=sub_row, col=1)
            fig.update_yaxes(title_text="ATR", title_font=dict(size=9,color="#3a5a70"), row=sub_row, col=1, **AXIS_STYLE)

        elif ind == "OBV":
            if has_vol:
                obv_vals = calc_obv(df)
                fig.add_trace(go.Scatter(x=df.index, y=obv_vals, name="OBV",
                    line=dict(color="#00ff88", width=1.5),
                    fill='tozeroy', fillcolor='rgba(0,255,136,0.05)'), row=sub_row, col=1)
                fig.update_yaxes(title_text="OBV", title_font=dict(size=9,color="#3a5a70"), row=sub_row, col=1, **AXIS_STYLE)

        elif ind == "Volume":
            if has_vol:
                vol_colors = ['rgba(0,255,136,0.6)' if df['Close'].iloc[i] >= df['Open'].iloc[i]
                              else 'rgba(255,51,102,0.6)' for i in range(len(df))]
                fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Volume",
                    marker_color=vol_colors, showlegend=False), row=sub_row, col=1)
                fig.update_yaxes(title_text="VOL", title_font=dict(size=9,color="#3a5a70"), row=sub_row, col=1, **AXIS_STYLE)

    # ── LAYOUT ──────────────────────────────────────────────────────────────
    chart_h = 520 + n_sub * 140

    # Disable rangeslider and apply axis styles
    if has_subplots:
        for row_idx in range(1, 2 + n_sub):
            fig.update_xaxes(rangeslider_visible=False, row=row_idx, col=1, **AXIS_STYLE)
        fig.update_yaxes(title_text="PRICE", title_font=dict(size=9, color="#3a5a70"),
                         row=1, col=1, **AXIS_STYLE)
    else:
        fig.update_xaxes(rangeslider_visible=False, **AXIS_STYLE)
        fig.update_yaxes(title_text="PRICE", title_font=dict(size=9, color="#3a5a70"), **AXIS_STYLE)

    fig.update_layout(
        height=chart_h,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(6,13,20,0.8)",
        font=dict(family="Share Tech Mono", color="#7ab3cc", size=11),
        hoverlabel=dict(bgcolor="#060d14", bordercolor="#00f5ff", font_color="#e2f4ff"),
        margin=dict(l=10, r=10, t=40, b=10),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1,
                    bgcolor="rgba(6,13,20,0.9)", bordercolor="#0d2535", borderwidth=1),
        hovermode="x unified",
    )
    return fig


# ─── CORRELATION HEATMAP ───────────────────────────────────────────────────────
def build_corr_heatmap(index_data):
    price_dict = {k: v['Close'] for k, v in index_data.items() if not v.empty}
    df_close = pd.DataFrame(price_dict).pct_change().dropna()
    corr = df_close.corr()
    fig = px.imshow(corr, text_auto=".2f",
        color_continuous_scale=[[0,"#ff3366"],[0.5,"#060d14"],[1,"#00ff88"]],
        zmin=-1, zmax=1, aspect="auto")
    fig.update_layout(height=380, **PLOTLY_THEME,
        title=dict(text="RETURNS CORRELATION MATRIX",
                   font=dict(family="Orbitron", size=12, color="#00f5ff")))
    fig.update_traces(textfont=dict(color="#e2f4ff", family="Share Tech Mono"))
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE)
    return fig


def build_sector_treemap(sector_data):
    rows = []
    for name, df in sector_data.items():
        if not df.empty and len(df) > 1:
            ret = ((df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100
            rows.append({"Sector": name, "Return": round(ret, 2), "Abs": abs(ret) + 0.1})
    if not rows:
        return None
    df_tree = pd.DataFrame(rows)
    fig = px.treemap(df_tree, path=['Sector'], values='Abs', color='Return',
        color_continuous_scale=[[0,"#ff3366"],[0.5,"#1a2a3a"],[1,"#00ff88"]],
        color_continuous_midpoint=0, custom_data=['Return'])
    fig.update_traces(
        texttemplate="<b>%{label}</b><br>%{customdata[0]:+.2f}%",
        textfont=dict(family="Share Tech Mono", size=13),
    )
    fig.update_layout(height=380, **PLOTLY_THEME,
        title=dict(text="SECTOR RETURNS HEATMAP",
                   font=dict(family="Orbitron", size=12, color="#00f5ff")),
        coloraxis_showscale=False)
    return fig


def build_drawdown_chart(index_data, selected):
    fig = go.Figure()
    for i, name in enumerate(selected):
        if name in index_data and not index_data[name].empty:
            dd = calculate_drawdown(index_data[name]['Close'])
            fig.add_trace(go.Scatter(x=dd.index, y=dd, name=name, fill='tozeroy',
                fillcolor=f"rgba({int(NEON[i%len(NEON)][1:3],16)},{int(NEON[i%len(NEON)][3:5],16)},{int(NEON[i%len(NEON)][5:7],16)},0.07)",
                line=dict(color=NEON[i%len(NEON)], width=1.5)))
    fig.update_layout(height=280, yaxis_title="Drawdown %",
        title=dict(text="PEAK-TO-TROUGH DRAWDOWN",
                   font=dict(family="Orbitron", size=12, color="#00f5ff")), **PLOTLY_THEME)
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE)
    return fig


def build_vol_chart(index_data, selected):
    fig = go.Figure()
    for i, name in enumerate(selected):
        if name in index_data and not index_data[name].empty:
            rets = index_data[name]['Close'].pct_change().dropna()
            roll_vol = rets.rolling(21).std() * np.sqrt(252) * 100
            fig.add_trace(go.Scatter(x=roll_vol.index, y=roll_vol, name=name,
                line=dict(color=NEON[i%len(NEON)], width=1.5)))
    fig.update_layout(height=280, yaxis_title="Ann. Vol (%)",
        title=dict(text="21-DAY ROLLING VOLATILITY",
                   font=dict(family="Orbitron", size=12, color="#00f5ff")), **PLOTLY_THEME)
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE)
    return fig


def build_returns_dist(df, name):
    rets = df['Close'].pct_change().dropna() * 100
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=rets, nbinsx=60, name="Daily Returns",
        marker_color="rgba(0,245,255,0.6)", marker_line_color="#00f5ff", marker_line_width=0.5))
    var_95 = np.percentile(rets, 5)
    var_99 = np.percentile(rets, 1)
    fig.add_vline(x=var_95, line_dash="dash", line_color="#ff6b35",
        annotation_text=f"VaR 95%: {var_95:.2f}%", annotation_font_color="#ff6b35", annotation_font_size=10)
    fig.add_vline(x=var_99, line_dash="dash", line_color="#ff3366",
        annotation_text=f"VaR 99%: {var_99:.2f}%", annotation_font_color="#ff3366", annotation_font_size=10)
    fig.add_vline(x=0, line_color="#3a5a70", line_width=1)
    fig.update_layout(height=280, xaxis_title="Daily Return (%)", yaxis_title="Frequency",
        title=dict(text=f"{name} — RETURN DISTRIBUTION",
                   font=dict(family="Orbitron", size=12, color="#00f5ff")), **PLOTLY_THEME)
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE)
    return fig


# ─── SIGNAL BADGE HTML ─────────────────────────────────────────────────────────
def signal_summary_html(df):
    close = df['Close'].dropna()
    r = calc_rsi(close).iloc[-1]
    m, s_line, h_vals = calc_macd(close)
    m_val, h_val = m.iloc[-1], h_vals.iloc[-1]
    _, _, _, pb = calc_bollinger(close)
    pb_val = pb.iloc[-1]
    adx_v, _, _ = calc_adx(df)
    adx_val = adx_v.iloc[-1]
    k, _ = calc_stochastic(df)
    k_val = k.iloc[-1]

    def rsi_sig(v):
        if v >= 70: return "OVERBOUGHT", "signal-sell"
        if v >= 60: return "BULLISH",    "signal-buy"
        if v >= 40: return "NEUTRAL",    "signal-neutral"
        if v >= 30: return "BEARISH",    "signal-sell"
        return "OVERSOLD", "signal-buy"

    def macd_sig(mv, hv):
        if mv > 0 and hv > 0: return "BULLISH CROSS", "signal-buy"
        if mv > 0 and hv <= 0: return "WEAKENING",    "signal-caution"
        if mv < 0 and hv < 0: return "BEARISH CROSS", "signal-sell"
        return "RECOVERING", "signal-caution"

    def bb_sig(pb):
        if pb > 1.0: return "ABOVE UPPER", "signal-sell"
        if pb > 0.8: return "NEAR UPPER",  "signal-caution"
        if pb < 0.0: return "BELOW LOWER", "signal-buy"
        if pb < 0.2: return "NEAR LOWER",  "signal-buy"
        return "MID BAND", "signal-neutral"

    ma50  = close.rolling(50).mean().iloc[-1]
    ma200 = close.rolling(200).mean().iloc[-1]
    trend_sig = "BULL MARKET" if ma50 > ma200 else "BEAR MARKET"
    trend_cls = "signal-buy"  if ma50 > ma200 else "signal-sell"

    rows = [
        ("RSI (14)",        f"{r:.1f}",      *rsi_sig(r)),
        ("MACD",            f"{m_val:.2f}",  *macd_sig(m_val, h_val)),
        ("Bollinger %B",    f"{pb_val:.2f}", *bb_sig(pb_val)),
        ("ADX (14)",        f"{adx_val:.1f}","STRONG" if adx_val > 25 else "WEAK", "signal-buy" if adx_val > 25 else "signal-neutral"),
        ("50/200 MA",       "",              trend_sig, trend_cls),
        ("Stoch %K",        f"{k_val:.1f}",  "OVERBOUGHT" if k_val > 80 else ("OVERSOLD" if k_val < 20 else "NEUTRAL"),
                                              "signal-sell" if k_val > 80 else ("signal-buy" if k_val < 20 else "signal-neutral")),
    ]

    html = '<div class="metric-panel">'
    for label, val, sig, cls in rows:
        html += f"""
        <div class="metric-row">
          <span class="metric-key">{label}</span>
          <span style="display:flex;align-items:center;gap:8px;">
            <span class="metric-val cyan" style="font-size:11px;">{val}</span>
            <span class="signal-badge {cls}">{sig}</span>
          </span>
        </div>"""
    html += '</div>'
    return html


def stats_panel_html(df, label):
    c = df['Close'].dropna()
    ret = ((c.iloc[-1] - c.iloc[0]) / c.iloc[0]) * 100
    rets_d = c.pct_change().dropna()
    ann_vol = rets_d.std() * np.sqrt(252) * 100
    sharpe  = (rets_d.mean() / rets_d.std()) * np.sqrt(252)
    max_dd  = calculate_drawdown(c).min()
    high52  = c.rolling(min(252, len(c))).max().iloc[-1]
    low52   = c.rolling(min(252, len(c))).min().iloc[-1]
    var95   = np.percentile(rets_d * 100, 5)
    current = c.iloc[-1]
    from_high = ((current - high52) / high52) * 100
    from_low  = ((current - low52)  / low52)  * 100

    rows = [
        (f"Return ({label})", f"{ret:+.2f}%",    "green" if ret>0 else "red"),
        ("Ann. Volatility",   f"{ann_vol:.2f}%",  "orange"),
        ("Sharpe Ratio",      f"{sharpe:.2f}",    "green" if sharpe>0 else "red"),
        ("Max Drawdown",      f"{max_dd:.2f}%",   "red"),
        ("VaR 95% (Daily)",   f"{var95:.2f}%",    "orange"),
        ("52W High",          f"{high52:,.2f}",   "green"),
        ("52W Low",           f"{low52:,.2f}",    "red"),
        ("% From 52W High",   f"{from_high:.2f}%","red" if from_high<0 else "green"),
        ("% From 52W Low",    f"{from_low:.2f}%", "green"),
        ("Daily Return Skew", f"{rets_d.skew():.2f}", "cyan"),
        ("Kurtosis",          f"{rets_d.kurt():.2f}","purple"),
    ]
    html = '<div class="metric-panel">'
    for row_label, val, cls in rows:
        html += f"""<div class="metric-row">
          <span class="metric-key">{row_label}</span>
          <span class="metric-val {cls}">{val}</span>
        </div>"""
    html += '</div>'
    return html


# ─── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    START_DATE = "2020-01-01"

    # ── SIDEBAR ─────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown('<p style="font-family:Orbitron;font-size:13px;color:#00f5ff;letter-spacing:3px;margin-bottom:12px;">⚙ SETTINGS</p>', unsafe_allow_html=True)

        if st.button("🔄 REFRESH DATA", use_container_width=True):
            st.cache_data.clear()

        st.markdown("---")
        st.markdown('<p style="font-family:Share Tech Mono;font-size:10px;color:#3a5a70;letter-spacing:1px;">DATE RANGE</p>', unsafe_allow_html=True)
        st.markdown(f'<p style="font-family:Share Tech Mono;font-size:11px;color:#00f5ff;">1 Jan 2020 → Today</p>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<p style="font-family:Share Tech Mono;font-size:10px;color:#3a5a70;letter-spacing:1px;">SMALLCAP ETF (FALLBACK)</p>', unsafe_allow_html=True)
        with st.expander("📂 Upload axis_niftyetf.xlsx"):
            uploaded_etf = st.file_uploader("ETF file", type=["xlsx"], label_visibility="collapsed")
        sc_status_placeholder = st.empty()

        st.markdown("---")
        st.markdown('<p style="font-family:Share Tech Mono;font-size:9px;color:#3a5a70;letter-spacing:1px;">DATA: YAHOO FINANCE + EMBEDDED ETF</p>', unsafe_allow_html=True)

    # ── LOAD DATA ───────────────────────────────────────────────────────────
    with st.spinner("FETCHING MARKET DATA..."):
        index_data  = fetch_data_range(INDEX_TICKERS, start_date=START_DATE)
        sector_data = fetch_data_range(SECTOR_TICKERS, start_date=START_DATE)

    sc_name, sc_df, sc_source = resolve_smallcap(start_date=START_DATE, uploaded_file=uploaded_etf)
    if sc_df is not None:
        index_data[sc_name] = sc_df
        sc_status_placeholder.markdown(
            f'<p style="font-family:Share Tech Mono;font-size:9px;color:#00ff88;">{sc_source}</p>',
            unsafe_allow_html=True
        )
    else:
        sc_status_placeholder.markdown(
            '<p style="font-family:Share Tech Mono;font-size:9px;color:#ff3366;">⚠️ SMALLCAP: no data</p>',
            unsafe_allow_html=True
        )

    if not index_data:
        st.error("NO DATA FETCHED. CHECK CONNECTION.")
        return

    # ── HEADER ──────────────────────────────────────────────────────────────
    now = datetime.now().strftime("%d %b %Y  //  %H:%M:%S")
    st.markdown(f"""
    <div class="terminal-header">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <div>
          <p class="terminal-title">BHARAT MARKETS // TERMINAL</p>
          <p class="terminal-subtitle">🇮🇳 NSE / BSE ANALYTICS SUITE  ·  DATA FROM 1 JAN 2020  ·  {now}</p>
        </div>
        <div style="text-align:right;font-family:'Share Tech Mono';font-size:10px;color:#3a5a70;">
          <div style="color:#00ff88;font-size:13px;font-weight:700;">● LIVE</div>
          <div>STREAM ACTIVE</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI CARDS ───────────────────────────────────────────────────────────
    preferred_kpi = ["NIFTY 50","NIFTY BANK","NIFTY MIDCAP","NIFTY IT","SENSEX","INDIA VIX"]
    sc_variants = [n for n in index_data if "SMALLCAP" in n.upper() or "SMLCAP" in n.upper()]
    kpi_names = [n for n in preferred_kpi if n in index_data]
    if sc_variants and sc_variants[0] not in kpi_names:
        kpi_names.append(sc_variants[0])
    kpi_names = kpi_names[:7]

    kpi_cards = ""
    for name in kpi_names:
        val_str = delta_str = "N/A"
        direction = "neu"
        card_cls = ""
        if name in index_data and not index_data[name].empty:
            df = index_data[name]
            cur = float(df['Close'].iloc[-1])
            val_str = f"{cur:,.2f}"
            if len(df) >= 2:
                prev = float(df['Close'].iloc[-2])
                pct  = ((cur - prev) / prev) * 100
                delta_str = f"{'▲' if pct >= 0 else '▼'} {abs(pct):.2f}%"
                direction = "pos" if pct >= 0 else "neg"
                card_cls  = "vix" if name == "INDIA VIX" else ("up" if pct >= 0 else "down")
        kpi_cards += f"""
        <div class="kpi-card {card_cls}">
          <div class="kpi-label">{name}</div>
          <div class="kpi-value">{val_str}</div>
          <div class="kpi-delta {direction}">{delta_str}</div>
        </div>"""

    st.markdown(f'<div class="kpi-grid" style="grid-template-columns:repeat({len(kpi_names)},1fr)">{kpi_cards}</div>', unsafe_allow_html=True)

    # ── TABS ────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🕯️  CHART & TECHNICALS",
        "📊  INDEX COMPARISON",
        "🏢  SECTORS",
        "📉  RISK",
        "🔬  STATISTICS",
    ])

    available_indices = list(index_data.keys())

    # ════════════════════════════════════════════════════════════════════════
    # TAB 1 — CLEAN CHART + OPTIONAL TECHNICAL INDICATORS
    # ════════════════════════════════════════════════════════════════════════
    with tab1:
        all_assets  = {**index_data, **sector_data}
        valid_assets = {k: v for k, v in all_assets.items() if not v.empty}

        # Controls row
        ctrl1, ctrl2, ctrl3 = st.columns([1.5, 3.5, 1])

        with ctrl1:
            selected_asset = st.selectbox(
                "ASSET",
                list(valid_assets.keys()),
                label_visibility="visible",
                key="tab1_asset"
            )
            chart_type = st.radio("CHART TYPE", ["Candlestick", "Line"], horizontal=True, key="tab1_ctype")

        with ctrl2:
            st.markdown('<p style="font-family:Share Tech Mono;font-size:10px;color:#3a5a70;letter-spacing:1px;margin-bottom:4px;">ADD INDICATORS (optional — chart is clean by default)</p>', unsafe_allow_html=True)
            selected_indicators = st.multiselect(
                "Indicators",
                ALL_INDICATORS,
                default=[],
                placeholder="Select indicators to overlay...",
                label_visibility="collapsed",
                key="tab1_indicators"
            )

        with ctrl3:
            st.markdown('<p style="font-family:Share Tech Mono;font-size:10px;color:#3a5a70;letter-spacing:1px;margin-bottom:4px;">ACTIVE</p>', unsafe_allow_html=True)
            if selected_indicators:
                pills = "".join([f'<span class="indicator-pill">{i}</span>' for i in selected_indicators])
                st.markdown(f'<div style="padding-top:2px">{pills}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<span style="font-family:Share Tech Mono;font-size:10px;color:#3a5a70;">PURE CHART</span>', unsafe_allow_html=True)

        # THE CHART
        df_asset = valid_assets[selected_asset].copy()
        fig = build_chart(df_asset, selected_asset, selected_indicators, chart_type)
        st.plotly_chart(fig, use_container_width=True, key="main_chart")

        # Bottom panels — only show if indicators are selected
        if selected_indicators:
            c1, c2, c3 = st.columns(3)

            with c1:
                st.markdown('<div class="section-head">SIGNAL DASHBOARD</div>', unsafe_allow_html=True)
                st.markdown(signal_summary_html(df_asset), unsafe_allow_html=True)

            with c2:
                st.markdown('<div class="section-head">PIVOT POINTS</div>', unsafe_allow_html=True)
                pivots = pivot_points(df_asset)
                cur_price = float(df_asset['Close'].iloc[-1])
                piv_color_map = {"R3":"red","R2":"red","R1":"orange","Pivot":"cyan","S1":"purple","S2":"cyan","S3":"green"}
                piv_html = '<div class="metric-panel">'
                for label, level in pivots.items():
                    dist = ((cur_price - level) / level) * 100
                    piv_html += f"""<div class="metric-row">
                      <span class="metric-key">{label}</span>
                      <span style="display:flex;gap:8px;align-items:center;">
                        <span class="metric-val {piv_color_map.get(label,'cyan')}">{level:,.2f}</span>
                        <span style="font-size:10px;color:#3a5a70;">{dist:+.2f}%</span>
                      </span>
                    </div>"""
                piv_html += '</div>'
                st.markdown(piv_html, unsafe_allow_html=True)

            with c3:
                st.markdown('<div class="section-head">FIBONACCI LEVELS</div>', unsafe_allow_html=True)
                fibs = fibonacci_levels(df_asset['Close'])
                fib_cls = ["red","orange","orange","cyan","purple","cyan","green"]
                fib_html = '<div class="metric-panel">'
                for i, (label, level) in enumerate(fibs.items()):
                    dist = ((cur_price - level) / level) * 100
                    fib_html += f"""<div class="metric-row">
                      <span class="metric-key">{label}</span>
                      <span style="display:flex;gap:8px;align-items:center;">
                        <span class="metric-val {fib_cls[i]}">{level:,.2f}</span>
                        <span style="font-size:10px;color:#3a5a70;">{dist:+.2f}%</span>
                      </span>
                    </div>"""
                fib_html += '</div>'
                st.markdown(fib_html, unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    # TAB 2 — INDEX COMPARISON
    # ════════════════════════════════════════════════════════════════════════
    with tab2:
        default_sel = [x for x in ["NIFTY 50","NIFTY BANK","NIFTY MIDCAP"] if x in available_indices]
        indices_to_plot = st.multiselect("SELECT INDICES", available_indices, default=default_sel, key="tab2_sel")
        normalize = st.checkbox("NORMALIZE (Base=100)", value=True, key="tab2_norm")

        c_chart, c_corr = st.columns([3, 1])

        with c_chart:
            fig_cmp = go.Figure()
            for i, name in enumerate(indices_to_plot):
                if name not in index_data or index_data[name].empty: continue
                df = index_data[name].copy()
                y  = df['Close']
                if normalize:
                    sv = y.iloc[0] or 1
                    y  = (y / sv) * 100
                fig_cmp.add_trace(go.Scatter(x=df.index, y=y, name=name,
                    line=dict(color=NEON[i%len(NEON)], width=2)))
            fig_cmp.update_layout(height=420, hovermode="x unified",
                yaxis_title="Normalized (Base=100)" if normalize else "Price", **PLOTLY_THEME)
            fig_cmp.update_xaxes(**AXIS_STYLE)
            fig_cmp.update_yaxes(**AXIS_STYLE)
            st.plotly_chart(fig_cmp, use_container_width=True, key="chart_cmp")

        with c_corr:
            if len(indices_to_plot) >= 2:
                st.plotly_chart(build_corr_heatmap(
                    {k: index_data[k] for k in indices_to_plot if k in index_data}
                ), use_container_width=True, key="chart_corr")
            else:
                st.info("Select ≥ 2 indices for correlation.")

        # Returns bar
        if indices_to_plot:
            ret_rows = []
            for name in indices_to_plot:
                if name not in index_data or index_data[name].empty: continue
                c = index_data[name]['Close']
                ret_rows.append({"Index": name, "Return": ((c.iloc[-1]-c.iloc[0])/c.iloc[0])*100})
            if ret_rows:
                df_ret = pd.DataFrame(ret_rows).sort_values("Return", ascending=True)
                colors = ["#00ff88" if r>=0 else "#ff3366" for r in df_ret["Return"]]
                fig_ret = go.Figure(go.Bar(
                    y=df_ret["Index"], x=df_ret["Return"], orientation="h",
                    marker_color=colors,
                    text=df_ret["Return"].apply(lambda x: f"{x:+.2f}%"),
                    textposition="outside", textfont=dict(color="#e2f4ff", family="Share Tech Mono"),
                ))
                fig_ret.update_layout(height=180 + len(ret_rows)*22, xaxis_title="Return % (since Jan 2020)", **PLOTLY_THEME,
                    title=dict(text="TOTAL RETURN SINCE JAN 2020",
                               font=dict(family="Orbitron", size=12, color="#00f5ff")))
                fig_ret.update_xaxes(**AXIS_STYLE)
                fig_ret.update_yaxes(**AXIS_STYLE)
                st.plotly_chart(fig_ret, use_container_width=True, key="chart_ret")

    # ════════════════════════════════════════════════════════════════════════
    # TAB 3 — SECTORS
    # ════════════════════════════════════════════════════════════════════════
    with tab3:
        if not sector_data:
            st.warning("Sector data unavailable.")
        else:
            c_tree, c_line = st.columns([1, 2])

            with c_tree:
                st.markdown('<div class="section-head">SECTOR HEATMAP</div>', unsafe_allow_html=True)
                fig_tree = build_sector_treemap(sector_data)
                if fig_tree:
                    st.plotly_chart(fig_tree, use_container_width=True, key="chart_tree")

            with c_line:
                st.markdown('<div class="section-head">RELATIVE STRENGTH</div>', unsafe_allow_html=True)
                avail_sec = list(sector_data.keys())
                sel_sec   = st.multiselect("Sectors", avail_sec,
                    default=avail_sec[:5] if len(avail_sec)>5 else avail_sec,
                    label_visibility="collapsed", key="tab3_sec")
                fig_sec = go.Figure()
                for i, name in enumerate(sel_sec):
                    if name not in sector_data or sector_data[name].empty: continue
                    sv = sector_data[name]['Close'].iloc[0] or 1
                    norm = (sector_data[name]['Close'] / sv) * 100
                    fig_sec.add_trace(go.Scatter(x=sector_data[name].index, y=norm, name=name,
                        line=dict(color=NEON[i%len(NEON)], width=2)))
                fig_sec.update_layout(height=380, yaxis_title="Rebased to 100",
                    hovermode="x unified", **PLOTLY_THEME)
                fig_sec.update_xaxes(**AXIS_STYLE)
                fig_sec.update_yaxes(**AXIS_STYLE)
                st.plotly_chart(fig_sec, use_container_width=True, key="chart_sec")

            # Returns bar for sectors
            sec_rows = []
            for name, df in sector_data.items():
                if not df.empty and len(df) > 1:
                    c = df['Close']
                    ret = ((c.iloc[-1]-c.iloc[0])/c.iloc[0])*100
                    sec_rows.append({"Sector": name, "Return (%)": round(ret,2)})
            if sec_rows:
                df_sec = pd.DataFrame(sec_rows).sort_values("Return (%)", ascending=True)
                cols_sec = ["#00ff88" if r>=0 else "#ff3366" for r in df_sec["Return (%)"]]
                fig_sb = go.Figure(go.Bar(
                    y=df_sec["Sector"], x=df_sec["Return (%)"], orientation="h",
                    marker_color=cols_sec,
                    text=df_sec["Return (%)"].apply(lambda x: f"{x:+.1f}%"),
                    textposition="outside", textfont=dict(color="#e2f4ff", family="Share Tech Mono"),
                ))
                fig_sb.update_layout(height=360, xaxis_title="Return % (since Jan 2020)", **PLOTLY_THEME,
                    title=dict(text="SECTOR TOTAL RETURNS SINCE JAN 2020",
                               font=dict(family="Orbitron", size=12, color="#00f5ff")))
                fig_sb.update_xaxes(**AXIS_STYLE)
                fig_sb.update_yaxes(**AXIS_STYLE)
                st.plotly_chart(fig_sb, use_container_width=True, key="chart_sb")

    # ════════════════════════════════════════════════════════════════════════
    # TAB 4 — RISK
    # ════════════════════════════════════════════════════════════════════════
    with tab4:
        default_risk = [x for x in ["NIFTY 50","NIFTY BANK","NIFTY MIDCAP"] if x in available_indices]
        risk_indices = st.multiselect("SELECT FOR RISK ANALYSIS", available_indices, default=default_risk, key="tab4_sel")

        c_dd, c_vol = st.columns(2)
        with c_dd:
            st.plotly_chart(build_drawdown_chart(index_data, risk_indices), use_container_width=True, key="chart_dd")
        with c_vol:
            st.plotly_chart(build_vol_chart(index_data, risk_indices), use_container_width=True, key="chart_vol")

        if risk_indices and risk_indices[0] in index_data:
            st.plotly_chart(build_returns_dist(index_data[risk_indices[0]], risk_indices[0]), use_container_width=True, key="chart_dist_risk")

        st.markdown('<div class="section-head">RISK METRICS TABLE</div>', unsafe_allow_html=True)
        risk_rows = []
        for name in risk_indices:
            if name not in index_data or index_data[name].empty: continue
            df = index_data[name]
            c  = df['Close']
            rets = c.pct_change().dropna()
            ann_vol = rets.std() * np.sqrt(252) * 100
            sharpe  = (rets.mean() / rets.std()) * np.sqrt(252)
            max_dd  = calculate_drawdown(c).min()
            var95   = np.percentile(rets*100, 5)
            var99   = np.percentile(rets*100, 1)
            calmar  = (((c.iloc[-1]-c.iloc[0])/c.iloc[0]*100) / abs(max_dd)) if max_dd != 0 else float('nan')
            risk_rows.append({
                "Index": name,
                "Ann. Vol (%)": f"{ann_vol:.2f}",
                "Sharpe": f"{sharpe:.2f}",
                "Max DD (%)": f"{max_dd:.2f}",
                "VaR 95% (%)": f"{var95:.2f}",
                "VaR 99% (%)": f"{var99:.2f}",
                "Calmar": f"{calmar:.2f}" if not np.isnan(calmar) else "N/A",
            })
        if risk_rows:
            st.dataframe(pd.DataFrame(risk_rows), use_container_width=True, hide_index=True)

    # ════════════════════════════════════════════════════════════════════════
    # TAB 5 — STATISTICS
    # ════════════════════════════════════════════════════════════════════════
    with tab5:
        all_assets_stat = {**index_data, **sector_data}
        valid_stat = {k: v for k, v in all_assets_stat.items() if not v.empty}
        sel_stat   = st.selectbox("SELECT ASSET", list(valid_stat.keys()), key="tab5_sel")
        df_stat    = valid_stat[sel_stat].copy()

        c_stats, c_dist = st.columns([1, 2])
        with c_stats:
            st.markdown('<div class="section-head">QUANTITATIVE STATS</div>', unsafe_allow_html=True)
            st.markdown(stats_panel_html(df_stat, "Since Jan 2020"), unsafe_allow_html=True)

        with c_dist:
            st.plotly_chart(build_returns_dist(df_stat, sel_stat), use_container_width=True, key="chart_dist_stat")

            rets = df_stat['Close'].pct_change().dropna()
            roll_sharpe = (rets.rolling(63).mean() / rets.rolling(63).std()) * np.sqrt(252)
            fig_rs = go.Figure(go.Scatter(x=roll_sharpe.index, y=roll_sharpe,
                line=dict(color="#00f5ff", width=1.5), fill='tozeroy',
                fillcolor='rgba(0,245,255,0.05)', name="63D Rolling Sharpe"))
            fig_rs.add_hline(y=0, line_color="#3a5a70", line_width=1)
            fig_rs.add_hline(y=1, line_color="#00ff88", line_dash="dash", line_width=0.8)
            fig_rs.add_hline(y=-1, line_color="#ff3366", line_dash="dash", line_width=0.8)
            fig_rs.update_layout(height=240, yaxis_title="Sharpe Ratio",
                title=dict(text="63-DAY ROLLING SHARPE",
                           font=dict(family="Orbitron", size=12, color="#00f5ff")), **PLOTLY_THEME)
            fig_rs.update_xaxes(**AXIS_STYLE)
            fig_rs.update_yaxes(**AXIS_STYLE)
            st.plotly_chart(fig_rs, use_container_width=True, key="chart_rs")

        # Monthly heatmap
        st.markdown('<div class="section-head">MONTHLY RETURNS HEATMAP</div>', unsafe_allow_html=True)
        monthly = df_stat['Close'].resample('ME').last().pct_change().dropna() * 100
        if not monthly.empty:
            monthly_df = pd.DataFrame({'Date': monthly.index, 'Return': monthly.values})
            monthly_df['Year']  = monthly_df['Date'].dt.year
            monthly_df['Month'] = monthly_df['Date'].dt.strftime('%b')
            month_order = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
            pivot = monthly_df.pivot(index='Year', columns='Month', values='Return')
            pivot = pivot.reindex(columns=[m for m in month_order if m in pivot.columns])
            fig_mhm = px.imshow(pivot, text_auto=".1f",
                color_continuous_scale=[[0,"#ff3366"],[0.5,"#060d14"],[1,"#00ff88"]],
                color_continuous_midpoint=0, aspect="auto")
            fig_mhm.update_traces(textfont=dict(color="#e2f4ff", family="Share Tech Mono", size=11))
            fig_mhm.update_layout(height=280, **PLOTLY_THEME,
                title=dict(text=f"{sel_stat} — MONTHLY RETURNS (%)",
                           font=dict(family="Orbitron", size=12, color="#00f5ff")),
                coloraxis_showscale=False)
            fig_mhm.update_xaxes(**AXIS_STYLE)
            fig_mhm.update_yaxes(**AXIS_STYLE)
            st.plotly_chart(fig_mhm, use_container_width=True, key="chart_mhm")


if __name__ == "__main__":
    main()
