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
    "NIFTY 50":       "^NSEI",
    "NIFTY BANK":     "^NSEBANK",
    "NIFTY MIDCAP":   "^NSMIDCP",
    "NIFTY IT":       "^CNXIT",
    "SENSEX":         "^BSESN",
    "INDIA VIX":      "^INDIAVIX",
}

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
    xaxis=dict(gridcolor="#0d2535", zerolinecolor="#0d2535", showgrid=True),
    yaxis=dict(gridcolor="#0d2535", zerolinecolor="#0d2535", showgrid=True),
    legend=dict(bgcolor="rgba(6,13,20,0.9)", bordercolor="#0d2535", borderwidth=1),
    margin=dict(l=10, r=10, t=30, b=10),
    hoverlabel=dict(bgcolor="#060d14", bordercolor="#00f5ff", font_color="#e2f4ff"),
)

NEON = ["#00f5ff", "#ff6b35", "#00ff88", "#ff3366", "#a855f7", "#fbbf24", "#06b6d4"]

# ─── DATA FETCHING ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800)
def fetch_data(ticker_dict, period="2y"):
    data_dict = {}
    ticker_list = list(ticker_dict.values())
    try:
        raw = yf.download(ticker_list, period=period, group_by='ticker', auto_adjust=True, progress=False)
    except Exception as e:
        return {}

    for name, ticker in ticker_dict.items():
        try:
            df = raw.copy() if len(ticker_list) == 1 else raw[ticker].copy()
            if df.empty: continue
            df = df.dropna(how='all').ffill()
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            if df.empty: continue
            data_dict[name] = df
        except:
            continue
    return data_dict

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
                         row=row, col=1, gridcolor="#0d2535", zerolinecolor="#0d2535")

    fig.update_layout(
        height=820,
        xaxis_rangeslider_visible=False,
        title=dict(text=f"<b>{name}</b> — TECHNICAL ANALYSIS",
                   font=dict(family="Orbitron", size=14, color="#00f5ff")),
        **PLOTLY_THEME,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1,
                    bgcolor="rgba(6,13,20,0.9)", bordercolor="#0d2535", borderwidth=1),
        xaxis5=dict(rangeslider_visible=False),
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
        st.markdown('<p style="font-family:Share Tech Mono;font-size:9px;color:#3a5a70;letter-spacing:1px;">DATA: YAHOO FINANCE<br>REFRESH: 30 MIN TTL</p>', unsafe_allow_html=True)

    # ── LOAD DATA ───────────────────────────────────────────────────────────
    with st.spinner("FETCHING MARKET DATA..."):
        index_data  = fetch_data(INDEX_TICKERS,  period=selected_period)
        sector_data = fetch_data(SECTOR_TICKERS, period=selected_period)

    if not index_data and not sector_data:
        st.error("NO DATA FETCHED. CHECK CONNECTION.")
        return

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
    kpi_names  = ["NIFTY 50", "NIFTY BANK", "NIFTY MIDCAP", "NIFTY IT", "SENSEX", "INDIA VIX"]
    kpi_cards  = ""
    for name in kpi_names:
        val_str = delta_str = "N/A"
        direction = "neu"
        card_cls  = ""
        if name in index_data:
            df = index_data[name]
            if not df.empty:
                cur  = df['Close'].iloc[-1]
                val_str = f"{cur:,.2f}"
                if len(df) >= 2:
                    prev = df['Close'].iloc[-2]
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

    st.markdown(f'<div class="kpi-grid">{kpi_cards}</div>', unsafe_allow_html=True)

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
        st.plotly_chart(fig_full, use_container_width=True)

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
        st.plotly_chart(build_fib_chart(df_enriched, selected_asset), use_container_width=True)

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
            st.plotly_chart(fig_cmp, use_container_width=True)

        with c_corr:
            if len(indices_to_plot) >= 2:
                st.plotly_chart(build_corr_heatmap(
                    {k: index_data[k] for k in indices_to_plot if k in index_data}
                ), use_container_width=True)
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
                st.plotly_chart(fig_ret, use_container_width=True)

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
                    st.plotly_chart(fig_tree, use_container_width=True)

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
                st.plotly_chart(fig_sec, use_container_width=True)

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
                st.plotly_chart(fig_secbar, use_container_width=True)

    # ════════════════════════════════════════════════════════════════════════
    # TAB 4 — RISK & VOLATILITY
    # ════════════════════════════════════════════════════════════════════════
    with tab4:
        default_risk = [x for x in ["NIFTY 50","NIFTY BANK","NIFTY MIDCAP"] if x in available_indices]
        risk_indices = st.multiselect("SELECT FOR RISK ANALYSIS", available_indices, default=default_risk, key="risk_sel")

        c_dd, c_vol = st.columns(2)
        with c_dd:
            st.plotly_chart(build_drawdown_chart(index_data, risk_indices), use_container_width=True)
        with c_vol:
            st.plotly_chart(build_vol_chart(index_data, risk_indices), use_container_width=True)

        # Returns distribution
        if risk_indices and risk_indices[0] in index_data:
            st.plotly_chart(build_returns_dist(index_data[risk_indices[0]], risk_indices[0]), use_container_width=True)

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
            st.plotly_chart(build_returns_dist(df_stat, sel_stat), use_container_width=True)

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
            st.plotly_chart(fig_rs, use_container_width=True)

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
            st.plotly_chart(fig_mhm, use_container_width=True)

if __name__ == "__main__":
    main()
