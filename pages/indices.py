import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np

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
  --accent-1:   #00f5ff;   /* cyan */
  --accent-2:   #ff6b35;   /* orange */
  --accent-3:   #00ff88;   /* green */
  --accent-4:   #ff3366;   /* red */
  --accent-5:   #a855f7;   /* purple */
  --text-pri:   #e2f4ff;
  --text-sec:   #7ab3cc;
  --text-dim:   #3a5a70;
  --border:     #0d2535;
  --border-glow:#00f5ff33;
}

html, body, .stApp {
  background: var(--bg-base) !important;
  font-family: 'Exo 2', sans-serif;
  color: var(--text-pri);
}

/* Scanline overlay */
.stApp::before {
  content: '';
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0, 245, 255, 0.012) 2px,
    rgba(0, 245, 255, 0.012) 4px
  );
  pointer-events: none;
  z-index: 9999;
}

/* Sidebar */
section[data-testid="stSidebar"] {
  background: var(--bg-panel) !important;
  border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] * { color: var(--text-sec) !important; }
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stMultiSelect label,
section[data-testid="stSidebar"] .stCheckbox label { color: var(--accent-1) !important; font-family: 'Share Tech Mono', monospace; font-size: 11px; }

/* Header */
.terminal-header {
  background: linear-gradient(135deg, var(--bg-panel) 0%, #0a1628 100%);
  border: 1px solid var(--border);
  border-top: 2px solid var(--accent-1);
  border-radius: 0 0 8px 8px;
  padding: 18px 28px;
  margin-bottom: 20px;
  position: relative;
  overflow: hidden;
}
.terminal-header::after {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, transparent, var(--accent-1), transparent);
  animation: scanH 3s ease-in-out infinite;
}
@keyframes scanH {
  0%,100% { opacity:0.3; } 50% { opacity:1; }
}
.terminal-title {
  font-family: 'Orbitron', monospace;
  font-size: 22px;
  font-weight: 900;
  letter-spacing: 4px;
  color: var(--accent-1);
  text-shadow: 0 0 20px var(--accent-1);
  margin: 0;
}
.terminal-subtitle {
  font-family: 'Share Tech Mono', monospace;
  font-size: 11px;
  color: var(--text-dim);
  letter-spacing: 2px;
  margin-top: 4px;
}

/* KPI Cards */
.kpi-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 10px; margin-bottom: 20px; }
.kpi-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 14px 16px;
  position: relative;
  overflow: hidden;
  transition: border-color 0.3s;
}
.kpi-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; height: 2px;
}
.kpi-card.up::before   { background: var(--accent-3); box-shadow: 0 0 8px var(--accent-3); }
.kpi-card.down::before { background: var(--accent-4); box-shadow: 0 0 8px var(--accent-4); }
.kpi-card.vix::before  { background: var(--accent-5); box-shadow: 0 0 8px var(--accent-5); }
.kpi-label  { font-family:'Share Tech Mono',monospace; font-size:10px; color:var(--text-dim); letter-spacing:1px; margin-bottom:6px; }
.kpi-value  { font-family:'Orbitron',monospace; font-size:18px; font-weight:700; color:var(--text-pri); }
.kpi-delta  { font-family:'Share Tech Mono',monospace; font-size:11px; margin-top:4px; }
.kpi-delta.pos { color: var(--accent-3); }
.kpi-delta.neg { color: var(--accent-4); }
.kpi-delta.neu { color: var(--text-dim); }

/* Section headers */
.section-head {
  font-family: 'Orbitron', monospace;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 3px;
  color: var(--accent-1);
  border-left: 3px solid var(--accent-1);
  padding-left: 12px;
  margin: 20px 0 14px;
  text-transform: uppercase;
}

/* Signal badge */
.signal-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 4px;
  font-family: 'Share Tech Mono', monospace;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1px;
}
.signal-buy      { background: rgba(0,255,136,0.15); color: var(--accent-3); border: 1px solid var(--accent-3); }
.signal-sell     { background: rgba(255,51,102,0.15);  color: var(--accent-4); border: 1px solid var(--accent-4); }
.signal-neutral  { background: rgba(168,85,247,0.15);  color: var(--accent-5); border: 1px solid var(--accent-5); }
.signal-caution  { background: rgba(255,107,53,0.15);  color: var(--accent-2); border: 1px solid var(--accent-2); }

/* Metric panels */
.metric-panel {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px 20px;
}
.metric-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--border);
  font-family: 'Share Tech Mono', monospace;
  font-size: 12px;
}
.metric-row:last-child { border-bottom: none; }
.metric-key  { color: var(--text-dim); }
.metric-val  { color: var(--text-pri); font-weight: 600; }
.metric-val.green { color: var(--accent-3); }
.metric-val.red   { color: var(--accent-4); }
.metric-val.cyan  { color: var(--accent-1); }
.metric-val.orange{ color: var(--accent-2); }
.metric-val.purple{ color: var(--accent-5); }

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
  background: var(--bg-panel) !important;
  border-bottom: 1px solid var(--border) !important;
  gap: 4px;
}
.stTabs [data-baseweb="tab"] {
  font-family: 'Share Tech Mono', monospace !important;
  font-size: 11px !important;
  letter-spacing: 1px !important;
  color: var(--text-dim) !important;
  padding: 10px 20px !important;
  border: none !important;
  background: transparent !important;
}
.stTabs [aria-selected="true"] {
  color: var(--accent-1) !important;
  border-bottom: 2px solid var(--accent-1) !important;
}

/* Plotly charts bg */
.js-plotly-plot .plotly { background: transparent !important; }

/* Sidebar selectbox */
.stSelectbox > div > div { background: var(--bg-card) !important; border-color: var(--border) !important; }

/* Hide streamlit cruft */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1rem !important; }

/* Gauge container */
.gauge-row { display: flex; gap: 10px; margin-bottom: 16px; }

/* Alert banners */
.alert-banner {
  background: linear-gradient(90deg, rgba(255,107,53,0.1), transparent);
  border-left: 3px solid var(--accent-2);
  padding: 8px 16px;
  border-radius: 0 6px 6px 0;
  font-family: 'Share Tech Mono', monospace;
  font-size: 11px;
  color: var(--accent-2);
  margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)

# ─── TICKERS ───────────────────────────────────────────────────────────────────
INDEX_TICKERS = {
    "NIFTY 50":         "^NSEI",
    "NIFTY BANK":       "^NSEBANK",
    "NIFTY MIDCAP":     "^NSMIDCP",
    "NIFTY IT":         "^CNXIT",
    "SENSEX":           "^BSESN",
    "INDIA VIX":        "^INDIAVIX",
    # SMALLCAP is loaded separately from axis_niftyetf.xlsx (see resolve_smallcap)
}

# Yahoo Finance fallbacks — only used if axis_niftyetf.xlsx is not found
SMALLCAP_FALLBACKS = [
    ("NIFTY SMLCAP 100",  "^CNXSC"),
    ("NIFTY SMLCAP 250",  "NIFTYSMLCAP250.NS"),
    ("NIFTY SMLCAP 50",   "NIFTYSMLCAP50.NS"),
    ("BSE SMALLCAP",      "BSE-SMLCAP.BO"),
    ("BSE SMLCAP 250",    "SML250.BO"),
]

SECTOR_TICKERS = {
    "Bank":    "^NSEBANK",
    "IT":      "^CNXIT",
    "Auto":    "^CNXAUTO",
    "Pharma":  "^CNXPHARMA",
    "FMCG":    "^CNXFMCG",
    "Metal":   "^CNXMETAL",
    "Energy":  "^CNXENERGY",
    "Realty":  "^CNXREALTY",
    "Infra":   "^CNXINFRA",
}

# ─── CHART THEME ───────────────────────────────────────────────────────────────
PLOTLY_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(6,13,20,0.8)",
    font=dict(family="Share Tech Mono", color="#7ab3cc", size=11),
    legend=dict(bgcolor="rgba(6,13,20,0.9)", bordercolor="#0d2535", borderwidth=1),
    margin=dict(l=10, r=10, t=30, b=10),
    hoverlabel=dict(bgcolor="#060d14", bordercolor="#00f5ff", font_color="#e2f4ff"),
)

# Applied via update_xaxes/update_yaxes to avoid subplot key conflicts
AXIS_STYLE = dict(gridcolor="#0d2535", zerolinecolor="#0d2535", showgrid=True)

NEON = ["#00f5ff", "#ff6b35", "#00ff88", "#ff3366", "#a855f7", "#fbbf24", "#06b6d4"]

# ─── DATA FETCHING ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800)
def fetch_data(ticker_dict, period="2y"):
    data_dict = {}
    ticker_list = list(ticker_dict.values())
    try:
        raw = yf.download(ticker_list, period=period, group_by='ticker', auto_adjust=True, progress=False)
    except Exception:
        return {}

    for name, ticker in ticker_dict.items():
        try:
            df = raw.copy() if len(ticker_list) == 1 else raw[ticker].copy()
            if df.empty: continue

            # Flatten multi-level columns that newer yfinance versions return
            # e.g. ('Close', '^NSEI') → 'Close'
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            df = df.dropna(how='all').ffill()
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            if df.empty: continue
            data_dict[name] = df
        except:
            continue
    return data_dict


def fetch_single_ticker(ticker, period):
    """Fetch a single ticker robustly, returns cleaned DataFrame or None."""
    try:
        df = yf.download(ticker, period=period, auto_adjust=True, progress=False)
        if df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.dropna(how='all').ffill()
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        return df if len(df) >= 5 else None
    except:
        return None


ETF_FILENAME = "axis_niftyetf.xlsx"

# ETF NAV data embedded directly — always available, no file path needed.
# Source: Axis Nifty Smallcap 50 Index Fund (Direct-Growth), data up to Feb 2026.
# Regenerate with: base64.b64encode(open("axis_niftyetf.xlsx","rb").read()).decode()
_ETF_B64 = (
    "UEsDBBQAAAAIAAdzWFwYTIddAQEAALoBAAAPABwAeGwvd29ya2Jvb2sueG1sIKIYACigFAAAAAAAAAAAAAAAAAAAAAAAAAAAAI2QwW4CIRCGX4XMvbJuYttsRC+9eGma1LRnhMElLrBhUPfdeugj9RUKqxtNTz3xDzPfPz/8fH0v14Pr2Akj2eAFzGcVMPQqaOv3Ao7JPDzDerUcmnOIh10IB5bnPTVRQJtS33BOqkUnaRZ69LlnQnQy5TLueTDGKnwJ6ujQJ15X1SOP2MmUd1Fre4Kr2/AfN+ojSk0tYnLdxcxJ6+E+3VtkOTu+SocCtq2lz2sDGC9zRX5YPNM9VC6YsZHSezEXkP9AqmRPuJW7scos/wOPOW6K+XHlqOfAxnOjBdTAYmOziBtdT0Y3VqOxHnXJS5eESnaqvCIfhZ/Xi6d6MYFT4tUvUEsDBAoAAAAAAAdzWFwrZ4o7nAIAAJwCAAALABwAX3JlbHMvLnJlbHMgohgAKKAUAAAAAAAAAAAAAAAAAAAAAAAAAAAA77u/PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0idXRmLTgiPz48UmVsYXRpb25zaGlwcyB4bWxucz0iaHR0cDovL3NjaGVtYXMub3BlbnhtbGZvcm1hdHMub3JnL3BhY2thZ2UvMjAwNi9yZWxhdGlvbnNoaXBzIj48UmVsYXRpb25zaGlwIFR5cGU9Imh0dHA6Ly9zY2hlbWFzLm9wZW54bWxmb3JtYXRzLm9yZy9vZmZpY2VEb2N1bWVudC8yMDA2L3JlbGF0aW9uc2hpcHMvb2ZmaWNlRG9jdW1lbnQiIFRhcmdldD0iL3hsL3dvcmtib29rLnhtbCIgSWQ9IlI4YjBkMjY1NjAyNTA0YTI2IiAvPjxSZWxhdGlvbnNoaXAgVHlwZT0iaHR0cDovL3NjaGVtYXMub3BlbnhtbGZvcm1hdHMub3JnL29mZmljZURvY3VtZW50LzIwMDYvcmVsYXRpb25zaGlwcy9leHRlbmRlZC1wcm9wZXJ0aWVzIiBUYXJnZXQ9Ii9kb2NQcm9wcy9hcHAueG1sIiBJZD0icklkMSIgLz48UmVsYXRpb25zaGlwIFR5cGU9Imh0dHA6Ly9zY2hlbWFzLm9wZW54bWxmb3JtYXRzLm9yZy9wYWNrYWdlLzIwMDYvcmVsYXRp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EO2quJ/reKp5vFHl8VMEvrnHXYPD3VP8ba8WrK0dedLVyt9dfPQAhG/DmWrGlMzeSz2E02nv5N8JYJTJTImv/Q1QSwMECgAAAAAAB3NYXD+YAjbaAQAA2gEAAFEAHABwYWNrYWdlL3NlcnZpY2VzL21ldGFkYXRhL2NvcmUtcHJvcGVydGllcy82OTllNGE3NTY3ZWI0ZWVkOTg2YTI2ZjM2YzFiZDgwNC5wc21kY3AgohgAKKAUAAAAAAAAAAAAAAAAAAAAAAAAAAAA77u/PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0idXRmLTgiPz48Y29yZVByb3BlcnRpZXMgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIiB4bWxuczpkY3Rlcm1zPSJodHRwOi8vcHVybC5vcmcvZGMvdGVybXMvIiB4bWxuczp4c2k9Imh0dHA6Ly93d3cudzMub3JnLzIwMDEvWE1MU2NoZW1hLWluc3RhbmNlIiB4bWxucz0iaHR0cDovL3NjaGVtYXMub3BlbnhtbGZvcm1hdHMub3JnL3BhY2thZ2UvMjAwNi9tZXRhZGF0YS9jb3JlLXByb3BlcnRpZXMiPjxkY3Rlcm1zOmNyZWF0ZWQgeHNpOnR5cGU9ImRjdGVybXM6VzNDRFRGIj4yMDI2LTAyLTI0VDA4OjU0OjE0LjA2MjQxNzFaPC9kY3Rlcm1zOmNyZWF0ZWQ+PGRjdGVybXM6bW9kaWZpZWQgeHNpOnR5cGU9ImRjdGVybXM6VzNDRFRGIj4yMDI2LTAyLTI0VDA4OjU0OjE0LjA2MjQxNzFaPC9kY3Rlcm1zOm1vZGlmaWVkPjwvY29yZVByb3BlcnRpZXM+UEsDBAoAAAAAAAdzWFwRlMAINwQAADcEAAATABwAW0NvbnRlbnRfVHlwZXNdLnhtbCCiGAAooBQAAAAAAAAAAAAAAAAAAAAAAAAAAADvu788P3htbCB2ZXJzaW9uPSIxLjAiIGVuY29kaW5nPSJ1dGYtOCI/PjxUeXBlcyB4bWxucz0iaHR0cDovL3NjaGVtYXMub3BlbnhtbGZvcm1hdHMub3JnL3BhY2thZ2UvMjAwNi9jb250ZW50LXR5cGVzIj48RGVmYXVsdCBFeHRlbnNpb249InhtbCIgQ29udGVudFR5cGU9ImFwcGxpY2F0aW9uL3ZuZC5vcGVueG1sZm9ybWF0cy1vZmZpY2Vkb2N1bWVudC5zcHJlYWRzaGVldG1sLnNoZWV0Lm1haW4reG1sIiAvPjxEZWZhdWx0IEV4dGVuc2lvbj0icmVscyIgQ29udGVudFR5cGU9ImFwcGxpY2F0aW9uL3ZuZC5vcGVueG1sZm9ybWF0cy1wYWNrYWdlLnJlbGF0aW9uc2hpcHMreG1sIiAvPjxEZWZhdWx0IEV4dGVuc2lvbj0icHNtZGNwIiBDb250ZW50VHlwZT0iYXBwbGljYXRpb24vdm5kLm9wZW54bWxmb3JtYXRzLXBhY2thZ2UuY29yZS1wcm9wZXJ0aWVzK3htbCIgLz48T3ZlcnJpZGUgUGFydE5hbWU9Ii9kb2NQcm9wcy9hcHAueG1sIiBDb250ZW50VHlwZT0iYXBwbGljYXRpb24vdm5kLm9wZW54bWxmb3JtYXRzLW9mZmljZWRvY3VtZW50LmV4dGVuZGVkLXByb3BlcnRpZXMreG1sIiAvPjxPdmVycmlkZSBQYXJ0TmFtZT0iL3hsL3NoYXJlZFN0cmluZ3MueG1sIiBDb250ZW50VHlwZT0iYXBwbGljYXRpb24vdm5kLm9wZW54bWxmb3JtYXRzLW9mZmljZWRvY3VtZW50LnNwcmVhZHNoZWV0bWwuc2hhcmVkU3RyaW5ncyt4bWwiIC8+PE92ZXJyaWRlIFBhcnROYW1lPSIveGwvc3R5bGVzLnhtbCIgQ29udGVudFR5cGU9ImFwcGxpY2F0aW9uL3ZuZC5vcGVueG1sZm9ybWF0cy1vZmZpY2Vkb2N1bWVudC5zcHJlYWRzaGVldG1sLnN0eWxlcyt4bWwiIC8+PE92ZXJyaWRlIFBhcnROYW1lPSIveGwvd29ya3NoZWV0cy9zaGVldDEueG1sIiBDb250ZW50VHlwZT0iYXBwbGljYXRpb24vdm5kLm9wZW54bWxmb3JtYXRzLW9mZmljZWRvY3VtZW50LnNwcmVhZHNoZWV0bWwud29ya3NoZWV0K3htbCIgLz48T3ZlcnJpZGUgUGFydE5hbWU9Ii94bC90aGVtZS90aGVtZTEueG1sIiBDb250ZW50VHlwZT0iYXBwbGljYXRpb24vdm5kLm9wZW54bWxmb3JtYXRzLW9mZmljZWRvY3VtZW50LnRoZW1lK3htbCIgLz48L1R5cGVzPlBLAQItABQAAAAIAAdzWFwYTIddAQEAALoBAAAPAAAAAAAAAAAAAAAAAAAAAAB4bC93b3JrYm9vay54bWxQSwECLQAKAAAAAAAHc1hcK2eKO5wCAACcAgAACwAAAAAAAAAAAAAAAABKAQAAX3JlbHMvLnJlbHNQSwECLQAUAAAACAAHc1hcthm/L14BAAA6AwAAEAAAAAAAAAAAAAAAAAArBAAAZG9jUHJvcHMvYXBwLnhtbFBLAQItABQAAAAIAAdzWFweDqTwVgIAAGwEAAAUAAAAAAAAAAAAAAAAANMFAAB4bC9zaGFyZWRTdHJpbmdzLnhtbFBLAQItABQAAAAIAAdzWFwM3Eiz4wAAAL4CAAAaAAAAAAAAAAAAAAAAAHcIAAB4bC9fcmVscy93b3JrYm9vay54bWwucmVsc1BLAQItABQAAAAIAAdzWFxVT8ei9wIAACkSAAANAAAAAAAAAAAAAAAAAK4JAAB4bC9zdHlsZXMueG1sUEsBAi0AFAAAAAgAB3NYXODGZ5hrQQAA2OoBABgAAAAAAAAAAAAAAAAA7AwAAHhsL3dvcmtzaGVldHMvc2hlZXQxLnhtbFBLAQItABQAAAAIAAdzWFx1sZFeqwUAALsbAAATAAAAAAAAAAAAAAAAAKlOAAB4bC90aGVtZS90aGVtZTEueG1sUEsBAi0ACgAAAAAAB3NYXD+YAjbaAQAA2gEAAFEAAAAAAAAAAAAAAAAAoVQAAHBhY2thZ2Uvc2VydmljZXMvbWV0YWRhdGEvY29yZS1wcm9wZXJ0aWVzLzY5OWU0YTc1NjdlYjRlZWQ5ODZhMjZmMzZjMWJkODA0LnBzbWRjcFBLAQItAAoAAAAAAAdzWFwRlMAINwQAADcEAAATAAAAAAAAAAAAAAAAAAZXAABbQ29udGVudF9UeXBlc10ueG1sUEsFBgAAAAAKAAoAwAIAAIpbAAAAAA=="
)


@st.cache_data(ttl=3600)
def load_etf_from_path(path: str):
    """Read axis_niftyetf.xlsx from an absolute path → yfinance-shaped OHLCV DataFrame."""
    try:
        raw  = pd.read_excel(path, header=None)
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
    except Exception:
        return None


def find_etf_path():
    """
    Return the first existing path to axis_niftyetf.xlsx, or None.
    Streamlit Cloud mounts the repo at  /mount/src/<repo>/
    This script lives at               /mount/src/<repo>/pages/indices.py
    So the file (committed to repo root) is at /mount/src/<repo>/axis_niftyetf.xlsx
    """
    import os
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        script_dir = os.getcwd()

    candidates = [
        # Relative to this script (covers pages/ subfolder layout)
        os.path.join(script_dir, ETF_FILENAME),            # same folder as script
        os.path.join(script_dir, "..", ETF_FILENAME),      # one level up (repo root)
        os.path.join(script_dir, "..", "..", ETF_FILENAME),
        os.path.join(os.getcwd(), ETF_FILENAME),
    ]

    # Also scan every repo under /mount/src/ (Streamlit Cloud)
    if os.path.isdir("/mount/src"):
        for repo in os.listdir("/mount/src"):
            candidates.append(f"/mount/src/{repo}/{ETF_FILENAME}")
            candidates.append(f"/mount/src/{repo}/pages/{ETF_FILENAME}")

    for p in candidates:
        try:
            p = os.path.normpath(p)
            if os.path.isfile(p):
                return p
        except Exception:
            continue
    return None


def resolve_smallcap(period, uploaded_file=None):
    """
    Load smallcap ETF data. Priority:
      1. Embedded base64 data (_ETF_B64) — always available, no file needed
      2. axis_niftyetf.xlsx on disk (repo root / pages/)
      3. Sidebar uploaded file
      4. Yahoo Finance fallback tickers (last resort)
    Returns (display_name, dataframe, source_label).
    """
    period_days = {"1mo": 30, "3mo": 91, "6mo": 182,
                   "1y": 365, "2y": 730, "5y": 1825, "max": 99999}
    days = period_days.get(period, 365)

    def trim(df, name, source):
        cutoff   = df.index.max() - pd.Timedelta(days=days)
        filtered = df[df.index >= cutoff]
        return name, (filtered if len(filtered) >= 5 else df), source

    def parse_excel_bytes(raw_bytes):
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

    # ── 1. Embedded base64 (always works) ───────────────────────────────────
    try:
        import base64
        raw_bytes = base64.b64decode(_ETF_B64)
        df = parse_excel_bytes(raw_bytes)
        if df is not None:
            return trim(df, "NIFTY SMALLCAP 50 ETF", "📦 Embedded data")
    except Exception:
        pass

    # ── 2. File on disk (repo mount) ────────────────────────────────────────
    etf_path = find_etf_path()
    if etf_path:
        df = load_etf_from_path(etf_path)
        if df is not None:
            return trim(df, "NIFTY SMALLCAP 50 ETF", f"📁 {etf_path}")

    # ── 3. Sidebar upload ───────────────────────────────────────────────────
    if uploaded_file is not None:
        try:
            df = parse_excel_bytes(uploaded_file.read())
            if df is not None:
                return trim(df, "NIFTY SMALLCAP 50 ETF", "📤 Uploaded")
        except Exception:
            pass

    # ── 4. Yahoo Finance fallback ───────────────────────────────────────────
    for display_name, ticker in SMALLCAP_FALLBACKS:
        df = fetch_single_ticker(ticker, period)
        if df is not None:
            return display_name, df, f"🌐 Yahoo ({ticker})"

    return None, None, "❌ No smallcap data available"




# ─── TECHNICAL INDICATORS ──────────────────────────────────────────────────────
def rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def bollinger_bands(series, period=20, std_dev=2):
    sma = series.rolling(period).mean()
    std = series.rolling(period).std()
    upper = sma + std_dev * std
    lower = sma - std_dev * std
    pct_b = (series - lower) / (upper - lower)
    bandwidth = (upper - lower) / sma * 100
    return upper, sma, lower, pct_b, bandwidth

def atr(df, period=14):
    hl  = df['High'] - df['Low']
    hc  = (df['High'] - df['Close'].shift()).abs()
    lc  = (df['Low']  - df['Close'].shift()).abs()
    tr  = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.rolling(period).mean()

def stochastic(df, k_period=14, d_period=3):
    low_min  = df['Low'].rolling(k_period).min()
    high_max = df['High'].rolling(k_period).max()
    k = 100 * (df['Close'] - low_min) / (high_max - low_min)
    d = k.rolling(d_period).mean()
    return k, d

def adx(df, period=14):
    plus_dm  = df['High'].diff()
    minus_dm = df['Low'].diff()
    plus_dm[plus_dm < 0]   = 0
    minus_dm[minus_dm > 0] = 0

    tr  = atr(df, period)
    plus_di  = 100 * (plus_dm.ewm(alpha=1/period, adjust=False).mean() / tr)
    minus_di = 100 * (minus_dm.abs().ewm(alpha=1/period, adjust=False).mean() / tr)
    dx  = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    adx_val = dx.ewm(alpha=1/period, adjust=False).mean()
    return adx_val, plus_di, minus_di

def obv(df):
    direction = df['Close'].diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    return (direction * df['Volume']).cumsum()

def vwap(df):
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    return (tp * df['Volume']).cumsum() / df['Volume'].cumsum()

def fibonacci_levels(series):
    high = series.max()
    low  = series.min()
    diff = high - low
    levels = {
        "0.0%  (Low)":  low,
        "23.6%":        low + 0.236 * diff,
        "38.2%":        low + 0.382 * diff,
        "50.0%":        low + 0.500 * diff,
        "61.8%":        low + 0.618 * diff,
        "78.6%":        low + 0.786 * diff,
        "100% (High)":  high,
    }
    return levels

def calculate_drawdown(series):
    rolling_max = series.cummax()
    return ((series / rolling_max) - 1) * 100

def pivot_points(df):
    """Classic pivot points from last completed session."""
    last = df.iloc[-2] if len(df) > 1 else df.iloc[-1]
    H, L, C = last['High'], last['Low'], last['Close']
    P  = (H + L + C) / 3
    R1 = 2*P - L
    R2 = P + (H - L)
    R3 = H + 2*(P - L)
    S1 = 2*P - H
    S2 = P - (H - L)
    S3 = L - 2*(H - P)
    return {"R3": R3, "R2": R2, "R1": R1, "Pivot": P, "S1": S1, "S2": S2, "S3": S3}

def interpret_rsi(v):
    if v >= 80:   return "EXTREME OB", "signal-sell"
    if v >= 70:   return "OVERBOUGHT", "signal-sell"
    if v >= 60:   return "BULLISH",    "signal-buy"
    if v >= 40:   return "NEUTRAL",    "signal-neutral"
    if v >= 30:   return "BEARISH",    "signal-sell"
    return "OVERSOLD", "signal-buy"

def interpret_macd(macd_val, hist):
    if macd_val > 0 and hist > 0:   return "BULLISH CROSS", "signal-buy"
    if macd_val > 0 and hist <= 0:  return "WEAKENING",     "signal-caution"
    if macd_val < 0 and hist < 0:   return "BEARISH CROSS", "signal-sell"
    return "RECOVERING", "signal-caution"

def interpret_bb(pct_b):
    if pct_b > 1.0:   return "ABOVE UPPER", "signal-sell"
    if pct_b > 0.8:   return "NEAR UPPER",  "signal-caution"
    if pct_b < 0.0:   return "BELOW LOWER", "signal-buy"
    if pct_b < 0.2:   return "NEAR LOWER",  "signal-buy"
    return "MID BAND", "signal-neutral"

def interpret_adx(v):
    if v >= 50: return "VERY STRONG TREND", "signal-sell"
    if v >= 25: return "STRONG TREND",      "signal-buy"
    if v >= 20: return "TRENDING",          "signal-caution"
    return "RANGING / WEAK", "signal-neutral"

# ─── PLOTLY CANDLESTICK + FULL INDICATORS CHART ────────────────────────────────
def build_full_chart(df, name, ma_windows):
    df = df.copy()
    df['RSI']      = rsi(df['Close'])
    df['MACD'], df['Signal'], df['Hist'] = macd(df['Close'])
    df['BB_U'], df['BB_M'], df['BB_L'], df['PctB'], df['BW'] = bollinger_bands(df['Close'])
    df['ATR']      = atr(df)
    df['STK_K'], df['STK_D'] = stochastic(df)
    df['ADX'], df['DI_P'], df['DI_N'] = adx(df)
    if 'Volume' in df.columns and df['Volume'].sum() > 0:
        df['OBV']  = obv(df)
        df['VWAP'] = vwap(df)
        has_vol = True
    else:
        has_vol = False

    for ma in ma_windows:
        df[f'MA_{ma}'] = df['Close'].rolling(ma).mean()

    # 5 rows: Price+BB, MACD, RSI, Stoch, Volume
    row_heights = [0.42, 0.15, 0.15, 0.14, 0.14]
    specs = [[{"secondary_y": False}]] * 5
    fig = make_subplots(
        rows=5, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=row_heights,
    )

    # ── Row 1: Candlestick + BB + MAs ──────────────────────────────────────
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'], name="Price",
        increasing_line_color="#00ff88", decreasing_line_color="#ff3366",
        increasing_fillcolor="rgba(0,255,136,0.7)",
        decreasing_fillcolor="rgba(255,51,102,0.7)",
    ), row=1, col=1)

    # BB bands
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_U'], name="BB Upper",
        line=dict(color="rgba(0,245,255,0.4)", width=1, dash='dot'), showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_L'], name="BB Lower",
        line=dict(color="rgba(0,245,255,0.4)", width=1, dash='dot'),
        fill='tonexty', fillcolor='rgba(0,245,255,0.04)', showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_M'], name="BB Mid",
        line=dict(color="rgba(0,245,255,0.25)", width=1), showlegend=False), row=1, col=1)

    # VWAP
    if has_vol:
        fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'], name="VWAP",
            line=dict(color="#fbbf24", width=1.5, dash='dash')), row=1, col=1)

    # MAs
    ma_colors = ["#ff6b35", "#a855f7", "#06b6d4", "#fbbf24"]
    for i, ma in enumerate(ma_windows):
        if f'MA_{ma}' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df[f'MA_{ma}'],
                name=f"{ma}D MA", line=dict(color=ma_colors[i % 4], width=1.5)), row=1, col=1)

    # Pivot points
    pivots = pivot_points(df)
    piv_colors = {"R3":"#ff3366","R2":"#ff6b35","R1":"#fbbf24",
                  "Pivot":"#00f5ff","S1":"#a855f7","S2":"#06b6d4","S3":"#00ff88"}
    for label, level in pivots.items():
        fig.add_hline(y=level, line_dash="dot", line_color=piv_colors.get(label, "#fff"),
                      line_width=0.8, row=1, col=1,
                      annotation_text=f"  {label}: {level:,.0f}",
                      annotation_font_color=piv_colors.get(label, "#fff"),
                      annotation_font_size=9)

    # ── Row 2: MACD ─────────────────────────────────────────────────────────
    colors_hist = ['rgba(0,255,136,0.7)' if v >= 0 else 'rgba(255,51,102,0.7)' for v in df['Hist']]
    fig.add_trace(go.Bar(x=df.index, y=df['Hist'], name="MACD Hist",
        marker_color=colors_hist, showlegend=False), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], name="MACD",
        line=dict(color="#00f5ff", width=1.5)), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Signal'], name="Signal",
        line=dict(color="#ff6b35", width=1.5)), row=2, col=1)
    fig.add_hline(y=0, line_color="#0d2535", line_width=1, row=2, col=1)

    # ── Row 3: RSI ──────────────────────────────────────────────────────────
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI",
        line=dict(color="#a855f7", width=2),
        fill='tozeroy', fillcolor='rgba(168,85,247,0.06)'), row=3, col=1)
    fig.add_hrect(y0=70, y1=100, fillcolor="rgba(255,51,102,0.06)",
                  line_width=0, row=3, col=1)
    fig.add_hrect(y0=0,  y1=30,  fillcolor="rgba(0,255,136,0.06)",
                  line_width=0, row=3, col=1)
    fig.add_hline(y=70, line_color="#ff3366", line_dash="dash", line_width=0.8, row=3, col=1)
    fig.add_hline(y=30, line_color="#00ff88", line_dash="dash", line_width=0.8, row=3, col=1)
    fig.update_yaxes(range=[0, 100], row=3, col=1)

    # ── Row 4: Stochastic ───────────────────────────────────────────────────
    fig.add_trace(go.Scatter(x=df.index, y=df['STK_K'], name="%K",
        line=dict(color="#00f5ff", width=1.5)), row=4, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['STK_D'], name="%D",
        line=dict(color="#ff6b35", width=1.5, dash='dot')), row=4, col=1)
    fig.add_hline(y=80, line_color="#ff3366", line_dash="dash", line_width=0.8, row=4, col=1)
    fig.add_hline(y=20, line_color="#00ff88", line_dash="dash", line_width=0.8, row=4, col=1)
    fig.update_yaxes(range=[0, 100], row=4, col=1)

    # ── Row 5: Volume + OBV ─────────────────────────────────────────────────
    if has_vol:
        vol_colors = ['rgba(0,255,136,0.6)' if df['Close'].iloc[i] >= df['Open'].iloc[i]
                      else 'rgba(255,51,102,0.6)' for i in range(len(df))]
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Volume",
            marker_color=vol_colors, showlegend=False), row=5, col=1)

    # ── Axis labels ─────────────────────────────────────────────────────────
    for row, label in zip([1,2,3,4,5], ["PRICE", "MACD", "RSI", "STOCH", "VOLUME"]):
        fig.update_yaxes(title_text=label, title_font=dict(size=9, color="#3a5a70"),
                         row=row, col=1, gridcolor="#0d2535", zerolinecolor="#0d2535", showgrid=True)

    # Disable rangeslider on all x-axes
    for row in [1, 2, 3, 4, 5]:
        fig.update_xaxes(rangeslider_visible=False, row=row, col=1,
                         gridcolor="#0d2535", zerolinecolor="#0d2535", showgrid=True)

    fig.update_layout(
        height=820,
        title=dict(text=f"<b>{name}</b> — TECHNICAL ANALYSIS",
                   font=dict(family="Orbitron", size=14, color="#00f5ff")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(6,13,20,0.8)",
        font=dict(family="Share Tech Mono", color="#7ab3cc", size=11),
        hoverlabel=dict(bgcolor="#060d14", bordercolor="#00f5ff", font_color="#e2f4ff"),
        margin=dict(l=10, r=10, t=50, b=10),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1,
                    bgcolor="rgba(6,13,20,0.9)", bordercolor="#0d2535", borderwidth=1),
    )
    return fig, df

# ─── SIGNAL SUMMARY HTML ───────────────────────────────────────────────────────
def signal_summary_html(df):
    close = df['Close'].dropna()
    r = rsi(close).iloc[-1]
    m, s, h = macd(close)
    m_val, h_val = m.iloc[-1], h.iloc[-1]
    _, _, _, pb, bw = bollinger_bands(close)
    pb_val = pb.iloc[-1]
    adx_val, di_p, di_n = adx(df)
    adx_v = adx_val.iloc[-1]
    stk_k, stk_d = stochastic(df)
    k_val = stk_k.iloc[-1]

    r_sig,    r_cls  = interpret_rsi(r)
    m_sig,    m_cls  = interpret_macd(m_val, h_val)
    bb_sig,   bb_cls = interpret_bb(pb_val)
    adx_sig,  adx_cls= interpret_adx(adx_v)

    ma50  = close.rolling(50).mean().iloc[-1]
    ma200 = close.rolling(200).mean().iloc[-1]
    trend_sig = "BULL MARKET" if ma50 > ma200 else "BEAR MARKET"
    trend_cls = "signal-buy"  if ma50 > ma200 else "signal-sell"

    rows = [
        ("RSI (14)",          f"{r:.1f}",     r_sig,    r_cls),
        ("MACD",              f"{m_val:.2f}", m_sig,    m_cls),
        ("Bollinger %B",      f"{pb_val:.2f}",bb_sig,   bb_cls),
        ("ADX (14)",          f"{adx_v:.1f}", adx_sig,  adx_cls),
        ("50/200 MA Cross",   "",             trend_sig,trend_cls),
        ("Stoch %K",          f"{k_val:.1f}", "OVERBOUGHT" if k_val > 80 else ("OVERSOLD" if k_val < 20 else "NEUTRAL"),
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

# ─── STATS PANEL HTML ──────────────────────────────────────────────────────────
def stats_panel_html(df, period_label):
    close = df['Close'].dropna()
    ret_pct = ((close.iloc[-1] - close.iloc[0]) / close.iloc[0]) * 100
    returns_daily = close.pct_change().dropna()
    ann_vol = returns_daily.std() * np.sqrt(252) * 100
    sharpe  = (returns_daily.mean() / returns_daily.std()) * np.sqrt(252)
    max_dd  = calculate_drawdown(close).min()
    skew    = returns_daily.skew()
    kurt    = returns_daily.kurt()
    atr_v   = atr(df).iloc[-1]
    high52  = close.rolling(252).max().iloc[-1]
    low52   = close.rolling(252).min().iloc[-1]

    current = close.iloc[-1]
    from_high = ((current - high52) / high52) * 100
    from_low  = ((current - low52)  / low52)  * 100

    def col(v, positive_green=True):
        if v > 0: return "green" if positive_green else "red"
        if v < 0: return "red"   if positive_green else "green"
        return "cyan"

    rows = [
        (f"Return ({period_label})", f"{ret_pct:+.2f}%",    col(ret_pct)),
        ("Ann. Volatility",          f"{ann_vol:.2f}%",      "orange"),
        ("Sharpe Ratio",             f"{sharpe:.2f}",        col(sharpe)),
        ("Max Drawdown",             f"{max_dd:.2f}%",       "red"),
        ("ATR (14)",                 f"{atr_v:.2f}",         "cyan"),
        ("52W High",                 f"{high52:,.2f}",       "green"),
        ("52W Low",                  f"{low52:,.2f}",        "red"),
        ("% From 52W High",          f"{from_high:.2f}%",    col(from_high)),
        ("% From 52W Low",           f"{from_low:.2f}%",     col(from_low)),
        ("Daily Return Skew",        f"{skew:.2f}",          col(skew)),
        ("Kurtosis",                 f"{kurt:.2f}",          "purple"),
    ]

    html = '<div class="metric-panel">'
    for label, val, cls in rows:
        html += f"""
        <div class="metric-row">
          <span class="metric-key">{label}</span>
          <span class="metric-val {cls}">{val}</span>
        </div>"""
    html += '</div>'
    return html

# ─── FIBONACCI CHART ───────────────────────────────────────────────────────────
def build_fib_chart(df, name):
    close = df['Close']
    fibs  = fibonacci_levels(close)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=close, name="Price",
        line=dict(color="#00f5ff", width=1.5)))
    fib_colors = ["#ff3366","#ff6b35","#fbbf24","#00f5ff","#a855f7","#06b6d4","#00ff88"]
    for i, (label, level) in enumerate(fibs.items()):
        fig.add_hline(y=level, line_dash="dot", line_color=fib_colors[i], line_width=1,
                      annotation_text=f"  {label}: {level:,.0f}",
                      annotation_font_color=fib_colors[i], annotation_font_size=9)
    fig.update_layout(height=350, title=dict(text=f"<b>{name}</b> — FIBONACCI RETRACEMENT",
        font=dict(family="Orbitron", size=12, color="#00f5ff")), **PLOTLY_THEME)
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE)
    return fig

# ─── CORRELATION HEATMAP ───────────────────────────────────────────────────────
def build_corr_heatmap(index_data):
    price_dict = {k: v['Close'] for k, v in index_data.items() if not v.empty}
    df_close = pd.DataFrame(price_dict).pct_change().dropna()
    corr = df_close.corr()
    fig = px.imshow(corr, text_auto=".2f", color_continuous_scale=[
        [0.0, "#ff3366"], [0.5, "#060d14"], [1.0, "#00ff88"]],
        zmin=-1, zmax=1, aspect="auto")
    fig.update_layout(height=380, **PLOTLY_THEME,
        title=dict(text="RETURNS CORRELATION MATRIX",
                   font=dict(family="Orbitron", size=12, color="#00f5ff")))
    fig.update_traces(textfont=dict(color="#e2f4ff", family="Share Tech Mono"))
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE)
    return fig

# ─── ROLLING VOLATILITY CHART ──────────────────────────────────────────────────
def build_vol_chart(index_data, selected):
    fig = go.Figure()
    for i, name in enumerate(selected):
        if name in index_data and not index_data[name].empty:
            rets = index_data[name]['Close'].pct_change().dropna()
            roll_vol = rets.rolling(21).std() * np.sqrt(252) * 100
            fig.add_trace(go.Scatter(x=roll_vol.index, y=roll_vol, name=name,
                line=dict(color=NEON[i % len(NEON)], width=1.5)))
    fig.update_layout(height=320, yaxis_title="Ann. Vol (%)",
        title=dict(text="21-DAY ROLLING VOLATILITY",
                   font=dict(family="Orbitron", size=12, color="#00f5ff")), **PLOTLY_THEME)
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE)
    return fig

# ─── DRAWDOWN CHART ────────────────────────────────────────────────────────────
def build_drawdown_chart(index_data, selected):
    fig = go.Figure()
    for i, name in enumerate(selected):
        if name in index_data and not index_data[name].empty:
            dd = calculate_drawdown(index_data[name]['Close'])
            fig.add_trace(go.Scatter(x=dd.index, y=dd, name=name, fill='tozeroy',
                fillcolor=f"rgba({int(NEON[i%len(NEON)][1:3],16)},{int(NEON[i%len(NEON)][3:5],16)},{int(NEON[i%len(NEON)][5:7],16)},0.08)",
                line=dict(color=NEON[i % len(NEON)], width=1.5)))
    fig.update_layout(height=320, yaxis_title="Drawdown %",
        title=dict(text="PEAK-TO-TROUGH DRAWDOWN",
                   font=dict(family="Orbitron", size=12, color="#00f5ff")), **PLOTLY_THEME)
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE)
    return fig

# ─── SECTOR HEATMAP ────────────────────────────────────────────────────────────
def build_sector_treemap(sector_data, period):
    rows = []
    for name, df in sector_data.items():
        if not df.empty and len(df) > 1:
            ret = ((df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100
            rows.append({"Sector": name, "Return": round(ret, 2), "Abs": abs(ret)})
    if not rows:
        return None
    df_tree = pd.DataFrame(rows)
    df_tree['Color'] = df_tree['Return']
    fig = px.treemap(df_tree, path=['Sector'], values='Abs', color='Color',
        color_continuous_scale=[[0,"#ff3366"],[0.5,"#1a2a3a"],[1,"#00ff88"]],
        color_continuous_midpoint=0,
        custom_data=['Return'])
    fig.update_traces(
        texttemplate="<b>%{label}</b><br>%{customdata[0]:+.2f}%",
        textfont=dict(family="Share Tech Mono", size=13),
    )
    fig.update_layout(height=380, **PLOTLY_THEME,
        title=dict(text=f"SECTOR HEATMAP ({period})",
                   font=dict(family="Orbitron", size=12, color="#00f5ff")),
        coloraxis_showscale=False)
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE)
    return fig

# ─── RETURNS DISTRIBUTION ──────────────────────────────────────────────────────
def build_returns_dist(df, name):
    rets = df['Close'].pct_change().dropna() * 100
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=rets, nbinsx=60, name="Daily Returns",
        marker_color="rgba(0,245,255,0.6)", marker_line_color="#00f5ff", marker_line_width=0.5))
    # VaR lines
    var_95 = np.percentile(rets, 5)
    var_99 = np.percentile(rets, 1)
    fig.add_vline(x=var_95, line_dash="dash", line_color="#ff6b35",
                  annotation_text=f"VaR 95%: {var_95:.2f}%", annotation_font_color="#ff6b35", annotation_font_size=10)
    fig.add_vline(x=var_99, line_dash="dash", line_color="#ff3366",
                  annotation_text=f"VaR 99%: {var_99:.2f}%", annotation_font_color="#ff3366", annotation_font_size=10)
    fig.add_vline(x=0, line_color="#3a5a70", line_width=1)
    fig.update_layout(height=300, xaxis_title="Daily Return (%)", yaxis_title="Frequency",
        title=dict(text=f"{name} — RETURN DISTRIBUTION",
                   font=dict(family="Orbitron", size=12, color="#00f5ff")), **PLOTLY_THEME)
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE)
    return fig

# ─── MAIN ──────────────────────────────────────────────────────────────────────
def main():

    # ── SIDEBAR ─────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown('<p style="font-family:Orbitron;font-size:14px;color:#00f5ff;letter-spacing:3px;">⚙ SETTINGS</p>', unsafe_allow_html=True)
        if st.button("🔄 REFRESH", use_container_width=True):
            st.cache_data.clear()

        period_options = {"1 Month": "1mo", "3 Months": "3mo", "6 Months": "6mo",
                          "1 Year": "1y", "2 Years": "2y", "5 Years": "5y"}
        selected_period_label = st.selectbox("LOOKBACK PERIOD", list(period_options.keys()), index=3)
        selected_period = period_options[selected_period_label]

        st.markdown("---")
        ma_windows = st.multiselect("MOVING AVERAGES", [20, 50, 100, 200], default=[50, 200])
        normalize  = st.checkbox("NORMALIZE (Base=100)", value=True)
        st.markdown("---")

        # Smallcap ETF — loaded from GitHub. Uploader shown only as emergency fallback.
        st.markdown('<p style="font-family:Share Tech Mono;font-size:9px;color:#3a5a70;letter-spacing:1px;">DATA: YAHOO FINANCE<br>SMALLCAP: GITHUB RAW URL</p>', unsafe_allow_html=True)
        with st.expander("📂 Manual ETF upload (fallback)"):
            uploaded_etf = st.file_uploader("axis_niftyetf.xlsx", type=["xlsx"], label_visibility="collapsed")
        sc_status_placeholder = st.empty()

    # ── LOAD DATA ───────────────────────────────────────────────────────────
    with st.spinner("FETCHING MARKET DATA..."):
        index_data  = fetch_data(INDEX_TICKERS,  period=selected_period)
        sector_data = fetch_data(SECTOR_TICKERS, period=selected_period)

    if not index_data and not sector_data:
        st.error("NO DATA FETCHED. CHECK CONNECTION.")
        return

    # ── SMALLCAP RESOLUTION ─────────────────────────────────────────────────
    # Smallcap is NOT in INDEX_TICKERS — always loaded from ETF file or fallback
    sc_name, sc_df, sc_source = resolve_smallcap(selected_period, uploaded_file=uploaded_etf)
    if sc_df is not None:
        index_data[sc_name] = sc_df
        sc_status_placeholder.markdown(
            f'<p style="font-family:Share Tech Mono;font-size:9px;color:#00ff88;letter-spacing:1px;">{sc_source}<br>{sc_name}</p>',
            unsafe_allow_html=True
        )
    else:
        sc_status_placeholder.markdown(
            '<p style="font-family:Share Tech Mono;font-size:9px;color:#ff3366;letter-spacing:1px;">⚠️ SMALLCAP: no data<br>Add axis_niftyetf.xlsx to repo</p>',
            unsafe_allow_html=True
        )

    # ── HEADER ──────────────────────────────────────────────────────────────
    now = datetime.now().strftime("%d %b %Y  //  %H:%M:%S")
    st.markdown(f"""
    <div class="terminal-header">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <div>
          <p class="terminal-title">BHARAT MARKETS // TERMINAL</p>
          <p class="terminal-subtitle">🇮🇳 NSE / BSE ANALYTICS SUITE  ·  PERIOD: {selected_period_label.upper()}  ·  {now}</p>
        </div>
        <div style="text-align:right;font-family:'Share Tech Mono';font-size:10px;color:#3a5a70;">
          <div style="color:#00ff88;font-size:13px;font-weight:700;">● LIVE</div>
          <div>DATA STREAM ACTIVE</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI CARDS ───────────────────────────────────────────────────────────
    # Show top 6 indices — pick whichever are available (smallcap may have a different name)
    preferred_kpi = ["NIFTY 50", "NIFTY BANK", "NIFTY MIDCAP", "NIFTY IT", "SENSEX", "INDIA VIX"]
    # Insert whichever smallcap variant loaded
    sc_variants = [n for n in index_data if "SMALLCAP" in n.upper() or "SMLCAP" in n.upper()]
    kpi_names = []
    for name in preferred_kpi:
        if name in index_data:
            kpi_names.append(name)
        elif name == "NIFTY SMALLCAP" and sc_variants:
            kpi_names.append(sc_variants[0])
    # Fill remaining slots with any loaded index not yet shown
    for name in index_data:
        if name not in kpi_names and len(kpi_names) < 7:
            kpi_names.append(name)
    kpi_names = kpi_names[:7]  # cap at 7
    kpi_cards  = ""
    for name in kpi_names:
        val_str = delta_str = "N/A"
        direction = "neu"
        card_cls  = ""
        if name in index_data:
            df = index_data[name]
            if not df.empty:
                cur  = float(df['Close'].iloc[-1])
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
        "🕯️  TECHNICAL DEEP DIVE",
        "📊  INDEX COMPARISON",
        "🏢  SECTOR ANALYSIS",
        "📉  RISK & VOLATILITY",
        "🔬  STATISTICS",
    ])

    available_indices = list(index_data.keys())

    # ════════════════════════════════════════════════════════════════════════
    # TAB 1 — TECHNICAL DEEP DIVE
    # ════════════════════════════════════════════════════════════════════════
    with tab1:
        all_assets   = {**index_data, **sector_data}
        valid_assets = {k: v for k, v in all_assets.items() if not v.empty}

        col_sel, col_info = st.columns([1, 3])
        with col_sel:
            st.markdown('<div class="section-head">SELECT ASSET</div>', unsafe_allow_html=True)
            selected_asset = st.selectbox("", list(valid_assets.keys()), label_visibility="collapsed")

        df_asset = valid_assets[selected_asset].copy()

        # Build full chart
        fig_full, df_enriched = build_full_chart(df_asset, selected_asset, ma_windows)
        st.plotly_chart(fig_full, use_container_width=True, key="chart_full")

        # Bottom panels
        c1, c2, c3 = st.columns([1, 1, 1])

        with c1:
            st.markdown('<div class="section-head">SIGNAL DASHBOARD</div>', unsafe_allow_html=True)
            st.markdown(signal_summary_html(df_enriched), unsafe_allow_html=True)

        with c2:
            st.markdown('<div class="section-head">PIVOT POINTS</div>', unsafe_allow_html=True)
            pivots = pivot_points(df_enriched)
            cur_price = df_enriched['Close'].iloc[-1]
            piv_html = '<div class="metric-panel">'
            piv_color_map = {"R3":"red","R2":"red","R1":"orange","Pivot":"cyan","S1":"purple","S2":"cyan","S3":"green"}
            for label, level in pivots.items():
                dist = ((cur_price - level) / level) * 100
                piv_html += f"""
                <div class="metric-row">
                  <span class="metric-key">{label}</span>
                  <span style="display:flex;gap:10px;align-items:center;">
                    <span class="metric-val {piv_color_map.get(label,'cyan')}">{level:,.2f}</span>
                    <span style="font-size:10px;color:#3a5a70;">{dist:+.2f}%</span>
                  </span>
                </div>"""
            piv_html += '</div>'
            st.markdown(piv_html, unsafe_allow_html=True)

        with c3:
            st.markdown('<div class="section-head">FIBONACCI LEVELS</div>', unsafe_allow_html=True)
            fibs = fibonacci_levels(df_enriched['Close'])
            fib_html = '<div class="metric-panel">'
            fib_color_list = ["red","orange","orange","cyan","purple","cyan","green"]
            for i, (label, level) in enumerate(fibs.items()):
                dist = ((cur_price - level) / level) * 100
                fib_html += f"""
                <div class="metric-row">
                  <span class="metric-key">{label}</span>
                  <span style="display:flex;gap:10px;align-items:center;">
                    <span class="metric-val {fib_color_list[i]}">{level:,.2f}</span>
                    <span style="font-size:10px;color:#3a5a70;">{dist:+.2f}%</span>
                  </span>
                </div>"""
            fib_html += '</div>'
            st.markdown(fib_html, unsafe_allow_html=True)

        # Fibonacci chart
        st.plotly_chart(build_fib_chart(df_enriched, selected_asset), use_container_width=True, key="chart_fib")

    # ════════════════════════════════════════════════════════════════════════
    # TAB 2 — INDEX COMPARISON
    # ════════════════════════════════════════════════════════════════════════
    with tab2:
        st.markdown('<div class="section-head">RELATIVE PERFORMANCE</div>', unsafe_allow_html=True)

        default_sel = [x for x in ["NIFTY 50", "NIFTY BANK", "NIFTY MIDCAP"] if x in available_indices]
        indices_to_plot = st.multiselect("SELECT INDICES", available_indices, default=default_sel)

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
                    line=dict(color=NEON[i % len(NEON)], width=2)))
            fig_cmp.update_layout(height=450, hovermode="x unified",
                yaxis_title="Normalized (Base=100)" if normalize else "Price",
                **PLOTLY_THEME)
            fig_cmp.update_xaxes(**AXIS_STYLE)
            fig_cmp.update_yaxes(**AXIS_STYLE)
            st.plotly_chart(fig_cmp, use_container_width=True, key="chart_cmp")

        with c_corr:
            if len(indices_to_plot) >= 2:
                st.plotly_chart(build_corr_heatmap(
                    {k: index_data[k] for k in indices_to_plot if k in index_data}
                ), use_container_width=True, key="chart_corr")
            else:
                st.info("Select ≥2 indices for correlation.")

        # Multi-index returns comparison bar
        if indices_to_plot:
            ret_rows = []
            for name in indices_to_plot:
                if name not in index_data or index_data[name].empty: continue
                c = index_data[name]['Close']
                ret_rows.append({"Index": name, "Return": ((c.iloc[-1]-c.iloc[0])/c.iloc[0])*100})
            if ret_rows:
                df_ret = pd.DataFrame(ret_rows).sort_values("Return", ascending=True)
                colors = ["#00ff88" if r >= 0 else "#ff3366" for r in df_ret["Return"]]
                fig_ret = go.Figure(go.Bar(
                    y=df_ret["Index"], x=df_ret["Return"], orientation="h",
                    marker_color=colors,
                    text=df_ret["Return"].apply(lambda x: f"{x:+.2f}%"),
                    textposition="outside", textfont=dict(color="#e2f4ff", family="Share Tech Mono"),
                ))
                fig_ret.update_layout(height=200, xaxis_title="Return %", **PLOTLY_THEME,
                    title=dict(text=f"TOTAL RETURN COMPARISON ({selected_period_label.upper()})",
                               font=dict(family="Orbitron", size=12, color="#00f5ff")))
                fig_ret.update_xaxes(**AXIS_STYLE)
                fig_ret.update_yaxes(**AXIS_STYLE)
                st.plotly_chart(fig_ret, use_container_width=True, key="chart_ret")

    # ════════════════════════════════════════════════════════════════════════
    # TAB 3 — SECTOR ANALYSIS
    # ════════════════════════════════════════════════════════════════════════
    with tab3:
        if not sector_data:
            st.warning("Sector data unavailable.")
        else:
            c_tree, c_line = st.columns([1, 2])
            with c_tree:
                st.markdown('<div class="section-head">SECTOR HEATMAP</div>', unsafe_allow_html=True)
                fig_tree = build_sector_treemap(sector_data, selected_period_label)
                if fig_tree:
                    st.plotly_chart(fig_tree, use_container_width=True, key="chart_tree")

            with c_line:
                st.markdown('<div class="section-head">RELATIVE STRENGTH</div>', unsafe_allow_html=True)
                avail_sec = list(sector_data.keys())
                sel_sec   = st.multiselect("", avail_sec,
                    default=avail_sec[:5] if len(avail_sec) > 5 else avail_sec,
                    label_visibility="collapsed")
                fig_sec = go.Figure()
                for i, name in enumerate(sel_sec):
                    if name not in sector_data or sector_data[name].empty: continue
                    sv = sector_data[name]['Close'].iloc[0] or 1
                    norm = (sector_data[name]['Close'] / sv) * 100
                    fig_sec.add_trace(go.Scatter(x=sector_data[name].index, y=norm, name=name,
                        line=dict(color=NEON[i % len(NEON)], width=2)))
                fig_sec.update_layout(height=380, yaxis_title="Rebased to 100",
                    hovermode="x unified", **PLOTLY_THEME)
                fig_sec.update_xaxes(**AXIS_STYLE)
                fig_sec.update_yaxes(**AXIS_STYLE)
                st.plotly_chart(fig_sec, use_container_width=True, key="chart_sec")

            # Sector bar
            sec_rows = []
            for name, df in sector_data.items():
                if not df.empty and len(df) > 1:
                    c = df['Close']
                    ret = ((c.iloc[-1]-c.iloc[0])/c.iloc[0])*100
                    vol = c.pct_change().std()*np.sqrt(252)*100
                    sec_rows.append({"Sector": name, "Return (%)": round(ret,2), "Ann. Vol (%)": round(vol,2)})
            if sec_rows:
                df_sec = pd.DataFrame(sec_rows).sort_values("Return (%)", ascending=True)
                cols_sec = ["#00ff88" if r >= 0 else "#ff3366" for r in df_sec["Return (%)"]]
                fig_secbar = go.Figure(go.Bar(
                    y=df_sec["Sector"], x=df_sec["Return (%)"], orientation="h",
                    marker_color=cols_sec,
                    text=df_sec["Return (%)"].apply(lambda x: f"{x:+.1f}%"),
                    textposition="outside", textfont=dict(color="#e2f4ff", family="Share Tech Mono"),
                ))
                fig_secbar.update_layout(height=380, xaxis_title="Return %", **PLOTLY_THEME,
                    title=dict(text="SECTOR TOTAL RETURNS",
                               font=dict(family="Orbitron", size=12, color="#00f5ff")))
                fig_secbar.update_xaxes(**AXIS_STYLE)
                fig_secbar.update_yaxes(**AXIS_STYLE)
                st.plotly_chart(fig_secbar, use_container_width=True, key="chart_secbar")

    # ════════════════════════════════════════════════════════════════════════
    # TAB 4 — RISK & VOLATILITY
    # ════════════════════════════════════════════════════════════════════════
    with tab4:
        default_risk = [x for x in ["NIFTY 50","NIFTY BANK","NIFTY MIDCAP"] if x in available_indices]
        risk_indices = st.multiselect("SELECT FOR RISK ANALYSIS", available_indices, default=default_risk, key="risk_sel")

        c_dd, c_vol = st.columns(2)
        with c_dd:
            st.plotly_chart(build_drawdown_chart(index_data, risk_indices), use_container_width=True, key="chart_dd")
        with c_vol:
            st.plotly_chart(build_vol_chart(index_data, risk_indices), use_container_width=True, key="chart_vol")

        # Returns distribution
        if risk_indices and risk_indices[0] in index_data:
            st.plotly_chart(build_returns_dist(index_data[risk_indices[0]], risk_indices[0]), use_container_width=True, key="chart_dist_risk")

        # Risk metrics table
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
            var95   = np.percentile(rets * 100, 5)
            var99   = np.percentile(rets * 100, 1)
            calmar  = ((c.iloc[-1]-c.iloc[0])/c.iloc[0]*100) / abs(max_dd) if max_dd != 0 else np.nan
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
        sel_stat   = st.selectbox("SELECT ASSET FOR STATISTICS", list(valid_stat.keys()), key="stat_sel")
        df_stat    = valid_stat[sel_stat].copy()

        c_stats, c_dist = st.columns([1, 2])
        with c_stats:
            st.markdown('<div class="section-head">QUANTITATIVE STATS</div>', unsafe_allow_html=True)
            st.markdown(stats_panel_html(df_stat, selected_period_label), unsafe_allow_html=True)
        with c_dist:
            st.plotly_chart(build_returns_dist(df_stat, sel_stat), use_container_width=True, key="chart_dist_stat")

            # Rolling Sharpe
            rets = df_stat['Close'].pct_change().dropna()
            roll_sharpe = (rets.rolling(63).mean() / rets.rolling(63).std()) * np.sqrt(252)
            fig_rs = go.Figure(go.Scatter(x=roll_sharpe.index, y=roll_sharpe,
                line=dict(color="#00f5ff", width=1.5), fill='tozeroy',
                fillcolor='rgba(0,245,255,0.05)', name="63D Rolling Sharpe"))
            fig_rs.add_hline(y=0, line_color="#3a5a70", line_width=1)
            fig_rs.add_hline(y=1, line_color="#00ff88", line_dash="dash", line_width=0.8)
            fig_rs.add_hline(y=-1, line_color="#ff3366", line_dash="dash", line_width=0.8)
            fig_rs.update_layout(height=250, yaxis_title="Sharpe Ratio",
                title=dict(text="63-DAY ROLLING SHARPE RATIO",
                           font=dict(family="Orbitron", size=12, color="#00f5ff")), **PLOTLY_THEME)
            fig_rs.update_xaxes(**AXIS_STYLE)
            fig_rs.update_yaxes(**AXIS_STYLE)
            st.plotly_chart(fig_rs, use_container_width=True, key="chart_rs")

        # Monthly returns heatmap
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
            fig_mhm.update_layout(height=300, **PLOTLY_THEME,
                title=dict(text=f"{sel_stat} — MONTHLY RETURNS (%)",
                           font=dict(family="Orbitron", size=12, color="#00f5ff")),
                coloraxis_showscale=False)
            fig_mhm.update_xaxes(**AXIS_STYLE)
            fig_mhm.update_yaxes(**AXIS_STYLE)
            st.plotly_chart(fig_mhm, use_container_width=True, key="chart_mhm")

if __name__ == "__main__":
    main()
