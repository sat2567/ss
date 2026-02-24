import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime
import numpy as np

# ─── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    layout="wide",
    page_title="GLOBAL MARKETS // TERMINAL",
    page_icon="🌍",
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
  --accent-6:   #fbbf24;
  --text-pri:   #e2f4ff;
  --text-sec:   #7ab3cc;
  --text-dim:   #3a5a70;
  --border:     #0d2535;
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
    0deg, transparent, transparent 2px,
    rgba(0,245,255,0.012) 2px, rgba(0,245,255,0.012) 4px
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
section[data-testid="stSidebar"] .stCheckbox label {
  color: var(--accent-1) !important;
  font-family: 'Share Tech Mono', monospace;
  font-size: 11px;
  letter-spacing: 1px;
}

/* Terminal header */
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
@keyframes scanH { 0%,100%{opacity:.3} 50%{opacity:1} }
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
  margin: 4px 0 0 0;
}

/* KPI grid */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 10px;
  margin-bottom: 20px;
}
.kpi-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 12px 14px;
  position: relative;
  overflow: hidden;
  transition: all .2s;
}
.kpi-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; height: 2px;
}
.kpi-card.up::before   { background: var(--accent-3); box-shadow: 0 0 8px var(--accent-3); }
.kpi-card.down::before { background: var(--accent-4); box-shadow: 0 0 8px var(--accent-4); }
.kpi-card.com::before  { background: var(--accent-6); box-shadow: 0 0 8px var(--accent-6); }
.kpi-card.neu::before  { background: var(--accent-1); box-shadow: 0 0 8px var(--accent-1); }
.kpi-label {
  font-family: 'Share Tech Mono', monospace;
  font-size: 9px;
  color: var(--text-dim);
  letter-spacing: 1px;
  text-transform: uppercase;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.kpi-value {
  font-family: 'Orbitron', monospace;
  font-size: 15px;
  font-weight: 700;
  color: var(--text-pri);
  white-space: nowrap;
}
.kpi-delta { font-family: 'Share Tech Mono', monospace; font-size: 11px; margin-top: 3px; }
.kpi-delta.pos { color: var(--accent-3); }
.kpi-delta.neg { color: var(--accent-4); }
.kpi-delta.neu { color: var(--text-dim); }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
  background: var(--bg-panel) !important;
  border-bottom: 1px solid var(--border) !important;
  gap: 0;
}
.stTabs [data-baseweb="tab"] {
  font-family: 'Share Tech Mono', monospace !important;
  font-size: 11px !important;
  letter-spacing: 2px !important;
  color: var(--text-dim) !important;
  padding: 10px 20px !important;
  border-radius: 0 !important;
  border-bottom: 2px solid transparent !important;
}
.stTabs [aria-selected="true"] {
  color: var(--accent-1) !important;
  border-bottom: 2px solid var(--accent-1) !important;
  background: rgba(0,245,255,.05) !important;
}

/* Metric region cards */
.region-header {
  font-family: 'Orbitron', monospace;
  font-size: 11px;
  letter-spacing: 3px;
  color: var(--accent-2);
  border-bottom: 1px solid var(--border);
  padding-bottom: 6px;
  margin-bottom: 12px;
}

/* Signal badges */
.badge {
  display: inline-block;
  font-family: 'Share Tech Mono', monospace;
  font-size: 10px;
  letter-spacing: 1px;
  padding: 3px 8px;
  border-radius: 3px;
  font-weight: 700;
}
.badge-bull  { background: rgba(0,255,136,.15); color: #00ff88; border:1px solid rgba(0,255,136,.3); }
.badge-bear  { background: rgba(255,51,102,.15); color: #ff3366; border:1px solid rgba(255,51,102,.3); }
.badge-neu   { background: rgba(0,245,255,.10); color: #00f5ff; border:1px solid rgba(0,245,255,.2); }
.badge-warn  { background: rgba(251,191,36,.15); color: #fbbf24; border:1px solid rgba(251,191,36,.3); }

/* Table styling */
.stDataFrame { border: 1px solid var(--border) !important; }

/* Plotly container */
.stPlotlyChart { border: 1px solid var(--border); border-radius: 6px; }

/* Metric */
[data-testid="stMetricValue"] {
  font-family: 'Orbitron', monospace !important;
  color: var(--text-pri) !important;
}
[data-testid="stMetricLabel"] {
  font-family: 'Share Tech Mono', monospace !important;
  color: var(--text-dim) !important;
  font-size: 11px !important;
}

/* Spinner */
.stSpinner > div { border-top-color: var(--accent-1) !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--bg-base); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent-1); }
</style>
""", unsafe_allow_html=True)

# ─── TICKERS ───────────────────────────────────────────────────────────────────
EQUITY_TICKERS = {
    # Americas
    "S&P 500":        "^GSPC",
    "NASDAQ 100":     "^NDX",
    "DOW JONES":      "^DJI",
    "RUSSELL 2000":   "^RUT",
    # Europe
    "FTSE 100":       "^FTSE",
    "DAX":            "^GDAXI",
    "CAC 40":         "^FCHI",
    "EURO STOXX 50":  "^STOXX50E",
    # Asia-Pacific
    "NIKKEI 225":     "^N225",
    "HANG SENG":      "^HSI",
    "KOSPI":          "^KS11",
    "SHANGHAI":       "000001.SS",
    "ASX 200":        "^AXJO",
    # India (link-back)
    "NIFTY 50":       "^NSEI",
    "SENSEX":         "^BSESN",
}

COMMODITY_TICKERS = {
    "GOLD":           "GC=F",
    "SILVER":         "SI=F",
    "CRUDE OIL (WTI)":"CL=F",
    "BRENT CRUDE":    "BZ=F",
    "NATURAL GAS":    "NG=F",
    "COPPER":         "HG=F",
    "WHEAT":          "ZW=F",
}

FOREX_TICKERS = {
    "USD/INR":        "INR=X",
    "EUR/USD":        "EURUSD=X",
    "GBP/USD":        "GBPUSD=X",
    "USD/JPY":        "JPY=X",
    "AUD/USD":        "AUDUSD=X",
    "USD/CNY":        "CNY=X",
}

# Regions for grouped display
REGIONS = {
    "🌎 AMERICAS":   ["S&P 500", "NASDAQ 100", "DOW JONES", "RUSSELL 2000"],
    "🌍 EUROPE":     ["FTSE 100", "DAX", "CAC 40", "EURO STOXX 50"],
    "🌏 ASIA-PAC":   ["NIKKEI 225", "HANG SENG", "KOSPI", "SHANGHAI", "ASX 200"],
    "🇮🇳 INDIA":     ["NIFTY 50", "SENSEX"],
}

# KPI cards shown in header
KPI_NAMES = ["S&P 500", "NASDAQ 100", "NIKKEI 225", "FTSE 100", "DAX",
             "GOLD", "CRUDE OIL (WTI)"]

# ─── PLOTLY THEME ──────────────────────────────────────────────────────────────
PLOTLY_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(6,13,20,0.8)",
    font=dict(family="Share Tech Mono", color="#7ab3cc", size=11),
    legend=dict(bgcolor="rgba(6,13,20,0.9)", bordercolor="#0d2535", borderwidth=1),
    margin=dict(l=10, r=10, t=36, b=10),
    hoverlabel=dict(bgcolor="#060d14", bordercolor="#00f5ff", font_color="#e2f4ff"),
)
AXIS_STYLE = dict(gridcolor="#0d2535", zerolinecolor="#0d2535", showgrid=True, color="#3a5a70")
NEON = ["#00f5ff", "#ff6b35", "#00ff88", "#ff3366", "#a855f7", "#fbbf24",
        "#06b6d4", "#f472b6", "#34d399", "#fb923c", "#818cf8", "#facc15"]

# ─── DATA FETCHING ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800)
def fetch_data(ticker_dict, period="1y"):
    data_dict = {}
    tickers = list(ticker_dict.values())
    try:
        raw = yf.download(tickers, period=period, group_by="ticker",
                          auto_adjust=True, progress=False, threads=True)
    except Exception:
        return {}

    for name, ticker in ticker_dict.items():
        try:
            df = raw.copy() if len(tickers) == 1 else raw[ticker].copy()
            if df.empty:
                continue
            # Flatten multi-level columns (yfinance ≥0.2.18)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df.dropna(how="all").ffill()
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            if df.empty:
                continue
            data_dict[name] = df
        except Exception:
            continue
    return data_dict

# ─── TECHNICAL INDICATORS ──────────────────────────────────────────────────────
def rsi(series, period=14):
    delta = series.diff()
    gain  = delta.where(delta > 0, 0).rolling(period).mean()
    loss  = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs    = gain / loss
    return 100 - (100 / (1 + rs))

def macd(series, fast=12, slow=26, signal=9):
    ema_f = series.ewm(span=fast, adjust=False).mean()
    ema_s = series.ewm(span=slow, adjust=False).mean()
    line  = ema_f - ema_s
    sig   = line.ewm(span=signal, adjust=False).mean()
    hist  = line - sig
    return line, sig, hist

def bollinger(series, period=20, std=2):
    sma   = series.rolling(period).mean()
    sigma = series.rolling(period).std()
    upper = sma + std * sigma
    lower = sma - std * sigma
    pct_b = (series - lower) / (upper - lower)
    return upper, sma, lower, pct_b

def atr(df, period=14):
    h, l, c = df["High"], df["Low"], df["Close"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(period).mean()

def safe_float(val):
    """Extract scalar float safely from pandas Series or numpy scalar."""
    try:
        v = val.iloc[0] if hasattr(val, "iloc") else val
        return float(v)
    except Exception:
        return float("nan")

# ─── CHART BUILDERS ────────────────────────────────────────────────────────────
def build_trend_chart(data_dict, names, normalize=True):
    fig = go.Figure()
    for i, name in enumerate(names):
        if name not in data_dict:
            continue
        df = data_dict[name]
        y  = df["Close"]
        if normalize:
            start = y.iloc[0]
            y = (y / start) * 100 if start != 0 else y
        fig.add_trace(go.Scatter(
            x=df.index, y=y,
            name=name, mode="lines",
            line=dict(color=NEON[i % len(NEON)], width=1.8),
        ))
    fig.update_layout(
        height=420,
        yaxis_title="Normalised (Base=100)" if normalize else "Price",
        hovermode="x unified",
        title=dict(text="PRICE TREND COMPARISON", font=dict(family="Orbitron", size=12, color="#00f5ff")),
        **PLOTLY_THEME,
    )
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE)
    return fig


def build_returns_bar(data_dict, period_label):
    rows = []
    for name, df in data_dict.items():
        if df.empty or len(df) < 2:
            continue
        ret = ((safe_float(df["Close"].iloc[-1]) - safe_float(df["Close"].iloc[0]))
               / safe_float(df["Close"].iloc[0])) * 100
        rows.append({"Asset": name, "Return": ret})
    if not rows:
        return go.Figure()
    df_ret = pd.DataFrame(rows).sort_values("Return")
    colors = ["#00ff88" if r >= 0 else "#ff3366" for r in df_ret["Return"]]
    fig = go.Figure(go.Bar(
        y=df_ret["Asset"], x=df_ret["Return"],
        orientation="h",
        marker_color=colors,
        text=df_ret["Return"].apply(lambda x: f"{x:+.2f}%"),
        textposition="outside",
        textfont=dict(family="Share Tech Mono", size=10, color="#7ab3cc"),
    ))
    fig.update_layout(
        height=max(350, len(rows) * 28),
        xaxis_title="Total Return (%)",
        title=dict(text=f"PERFORMANCE RANKING — {period_label}",
                   font=dict(family="Orbitron", size=12, color="#00f5ff")),
        **PLOTLY_THEME,
    )
    fig.update_xaxes(**AXIS_STYLE, zeroline=True, zerolinewidth=1, zerolinecolor="#3a5a70")
    fig.update_yaxes(**AXIS_STYLE, showgrid=False)
    return fig


def build_corr_heatmap(data_dict, names):
    valid = [n for n in names if n in data_dict and not data_dict[n].empty]
    if len(valid) < 2:
        return go.Figure()
    closes = pd.DataFrame({n: data_dict[n]["Close"] for n in valid})
    corr   = closes.pct_change().corr()
    fig    = px.imshow(
        corr, text_auto=".2f",
        color_continuous_scale=[[0,"#ff3366"],[0.5,"#060d14"],[1,"#00f5ff"]],
        zmin=-1, zmax=1, aspect="auto",
    )
    fig.update_layout(
        height=420,
        title=dict(text="RETURN CORRELATION MATRIX", font=dict(family="Orbitron", size=12, color="#00f5ff")),
        **PLOTLY_THEME,
    )
    fig.update_xaxes(tickfont=dict(size=9), color="#3a5a70")
    fig.update_yaxes(tickfont=dict(size=9), color="#3a5a70")
    return fig


def build_volatility_chart(data_dict, names):
    fig = go.Figure()
    for i, name in enumerate(names):
        if name not in data_dict:
            continue
        df  = data_dict[name]
        vol = df["Close"].pct_change().rolling(21).std() * np.sqrt(252) * 100
        fig.add_trace(go.Scatter(
            x=df.index, y=vol,
            name=name, mode="lines",
            line=dict(color=NEON[i % len(NEON)], width=1.5),
        ))
    fig.update_layout(
        height=350, yaxis_title="Annualised Volatility (%)",
        title=dict(text="21-DAY ROLLING VOLATILITY", font=dict(family="Orbitron", size=12, color="#00f5ff")),
        hovermode="x unified",
        **PLOTLY_THEME,
    )
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE)
    return fig


def build_technical_chart(df, name, ma_windows):
    """5-row subplot: Candlestick + BBands + MAs / MACD / RSI / Volume / ATR."""
    row_heights = [0.42, 0.16, 0.16, 0.14, 0.12]
    fig = make_subplots(
        rows=5, cols=1, shared_xaxes=True,
        row_heights=row_heights, vertical_spacing=0.025,
        subplot_titles=("", "MACD", "RSI (14)", "VOLUME", "ATR (14)"),
    )

    close = df["Close"]

    # ── Row 1: Candles + Bollinger + MAs ────────────────────────────────────
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"], low=df["Low"], close=close,
        increasing_line_color="#00ff88", decreasing_line_color="#ff3366",
        increasing_fillcolor="rgba(0,255,136,.25)", decreasing_fillcolor="rgba(255,51,102,.25)",
        name="OHLC",
    ), row=1, col=1)

    bb_u, bb_m, bb_l, _ = bollinger(close)
    fig.add_trace(go.Scatter(x=df.index, y=bb_u, line=dict(color="rgba(0,245,255,.25)", width=1),
                             name="BB Upper", showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=bb_l, line=dict(color="rgba(0,245,255,.25)", width=1),
                             fill="tonexty", fillcolor="rgba(0,245,255,.04)",
                             name="BB Lower", showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=bb_m, line=dict(color="rgba(0,245,255,.5)", width=1, dash="dot"),
                             name="BB Mid", showlegend=False), row=1, col=1)

    ma_colors = ["#fbbf24", "#a855f7", "#ff6b35", "#06b6d4"]
    for i, w in enumerate(ma_windows):
        ma = close.rolling(w).mean()
        fig.add_trace(go.Scatter(x=df.index, y=ma,
                                 line=dict(color=ma_colors[i % 4], width=1.5),
                                 name=f"MA {w}"), row=1, col=1)

    # ── Row 2: MACD ──────────────────────────────────────────────────────────
    m_line, m_sig, m_hist = macd(close)
    hist_colors = ["rgba(0,255,136,.7)" if v >= 0 else "rgba(255,51,102,.7)" for v in m_hist.fillna(0)]
    fig.add_trace(go.Bar(x=df.index, y=m_hist, marker_color=hist_colors,
                         name="MACD Hist", showlegend=False), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=m_line, line=dict(color="#00f5ff", width=1.2),
                             name="MACD"), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=m_sig,  line=dict(color="#ff6b35", width=1.2),
                             name="Signal"), row=2, col=1)

    # ── Row 3: RSI ───────────────────────────────────────────────────────────
    rsi_vals = rsi(close)
    rsi_colors = ["#00ff88" if v < 30 else "#ff3366" if v > 70 else "#00f5ff"
                  for v in rsi_vals.fillna(50)]
    fig.add_trace(go.Scatter(x=df.index, y=rsi_vals, line=dict(color="#a855f7", width=1.5),
                             name="RSI"), row=3, col=1)
    for level, color in [(70, "#ff3366"), (30, "#00ff88"), (50, "#3a5a70")]:
        fig.add_hline(y=level, line_dash="dot", line_color=color,
                      line_width=0.8, row=3, col=1)

    # ── Row 4: Volume ────────────────────────────────────────────────────────
    if "Volume" in df.columns:
        vol_colors = ["#00ff88" if c >= o else "#ff3366"
                      for c, o in zip(df["Close"], df["Open"])]
        fig.add_trace(go.Bar(x=df.index, y=df["Volume"],
                             marker_color=vol_colors, name="Volume",
                             showlegend=False), row=4, col=1)

    # ── Row 5: ATR ───────────────────────────────────────────────────────────
    atr_vals = atr(df)
    fig.add_trace(go.Scatter(x=df.index, y=atr_vals, line=dict(color="#fbbf24", width=1.2),
                             name="ATR", fill="tozeroy",
                             fillcolor="rgba(251,191,36,.08)"), row=5, col=1)

    for row in range(1, 6):
        fig.update_xaxes(rangeslider_visible=False, row=row, col=1, **AXIS_STYLE)
        fig.update_yaxes(row=row, col=1, **AXIS_STYLE)

    fig.update_layout(
        height=700,
        title=dict(text=f"{name.upper()} // TECHNICAL ANALYSIS",
                   font=dict(family="Orbitron", size=13, color="#00f5ff")),
        **PLOTLY_THEME,
    )
    return fig


def build_region_heatmap(data_dict):
    """Daily % change heatmap by region."""
    rows = []
    for region, names in REGIONS.items():
        for name in names:
            if name not in data_dict:
                continue
            df = data_dict[name]
            if len(df) < 2:
                continue
            chg = ((safe_float(df["Close"].iloc[-1]) - safe_float(df["Close"].iloc[-2]))
                   / safe_float(df["Close"].iloc[-2])) * 100
            rows.append({"Region": region, "Index": name, "Change": chg})
    if not rows:
        return go.Figure()

    df_h = pd.DataFrame(rows)
    fig  = px.treemap(
        df_h, path=["Region", "Index"], values=[1] * len(df_h),
        color="Change",
        color_continuous_scale=[[0,"#ff3366"],[0.35,"#1a0510"],
                                 [0.5,"#060d14"],[0.65,"#011a0d"],[1,"#00ff88"]],
        color_continuous_midpoint=0,
        custom_data=["Change"],
    )
    fig.update_traces(
        texttemplate="<b>%{label}</b><br>%{customdata[0]:.2f}%",
        textfont=dict(family="Share Tech Mono", size=11),
    )
    fig.update_layout(
        height=380,
        title=dict(text="GLOBAL MARKET HEATMAP (DAILY Δ%)",
                   font=dict(family="Orbitron", size=12, color="#00f5ff")),
        coloraxis_showscale=False,
        **PLOTLY_THEME,
    )
    return fig


def build_drawdown_chart(data_dict, names):
    fig = go.Figure()
    for i, name in enumerate(names):
        if name not in data_dict:
            continue
        close   = data_dict[name]["Close"]
        peak    = close.cummax()
        dd      = ((close - peak) / peak) * 100
        fig.add_trace(go.Scatter(
            x=data_dict[name].index, y=dd,
            name=name, mode="lines",
            line=dict(color=NEON[i % len(NEON)], width=1.5),
            fill="tozeroy",
            fillcolor=f"rgba({int(NEON[i%len(NEON)][1:3],16)},"
                       f"{int(NEON[i%len(NEON)][3:5],16)},"
                       f"{int(NEON[i%len(NEON)][5:7],16)},.06)",
        ))
    fig.update_layout(
        height=340, yaxis_title="Drawdown (%)",
        title=dict(text="PEAK-TO-TROUGH DRAWDOWN",
                   font=dict(family="Orbitron", size=12, color="#00f5ff")),
        hovermode="x unified",
        **PLOTLY_THEME,
    )
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE)
    return fig


def build_forex_chart(forex_data, names, normalize=True):
    fig = go.Figure()
    for i, name in enumerate(names):
        if name not in forex_data:
            continue
        df = forex_data[name]
        y  = df["Close"]
        if normalize:
            s = y.iloc[0]
            y = (y / s) * 100 if s != 0 else y
        fig.add_trace(go.Scatter(
            x=df.index, y=y, name=name, mode="lines",
            line=dict(color=NEON[i % len(NEON)], width=1.8),
        ))
    fig.update_layout(
        height=380,
        yaxis_title="Normalised (Base=100)" if normalize else "Rate",
        title=dict(text="FOREX RATES", font=dict(family="Orbitron", size=12, color="#00f5ff")),
        hovermode="x unified",
        **PLOTLY_THEME,
    )
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE)
    return fig


# ─── SIGNAL ENGINE ─────────────────────────────────────────────────────────────
def get_signals(df):
    """Return a dict of signal name → (badge_class, label) pairs."""
    signals = {}
    close   = df["Close"]

    # RSI
    r = rsi(close)
    rv = safe_float(r.iloc[-1])
    if rv >= 70:  signals["RSI"]  = ("badge-bear", f"OVERBOUGHT ({rv:.1f})")
    elif rv <= 30: signals["RSI"] = ("badge-bull", f"OVERSOLD ({rv:.1f})")
    else:          signals["RSI"] = ("badge-neu",  f"NEUTRAL ({rv:.1f})")

    # MACD
    ml, ms, mh = macd(close)
    mv = safe_float(mh.iloc[-1])
    signals["MACD"] = ("badge-bull", "BULL CROSS") if mv > 0 else ("badge-bear", "BEAR CROSS")

    # Bollinger
    _, _, _, pct_b = bollinger(close)
    bv = safe_float(pct_b.iloc[-1])
    if bv > 1:    signals["BOLL"] = ("badge-bear", f"%B ABOVE ({bv:.2f})")
    elif bv < 0:  signals["BOLL"] = ("badge-bull", f"%B BELOW ({bv:.2f})")
    else:         signals["BOLL"] = ("badge-neu",  f"%B NEUTRAL ({bv:.2f})")

    # MA cross (50/200)
    if len(close) >= 200:
        ma50  = safe_float(close.rolling(50).mean().iloc[-1])
        ma200 = safe_float(close.rolling(200).mean().iloc[-1])
        if ma50 > ma200: signals["MA X"] = ("badge-bull", "GOLDEN CROSS")
        else:            signals["MA X"] = ("badge-bear", "DEATH CROSS")

    # Trend (price vs MA200)
    if len(close) >= 200:
        p     = safe_float(close.iloc[-1])
        m200  = safe_float(close.rolling(200).mean().iloc[-1])
        above = p > m200
        signals["TREND"] = ("badge-bull", "ABOVE MA200") if above else ("badge-bear", "BELOW MA200")

    return signals


# ─── STATS TABLE ───────────────────────────────────────────────────────────────
def compute_stats(data_dict, names):
    rows = []
    for name in names:
        if name not in data_dict:
            continue
        df    = data_dict[name]
        close = df["Close"]
        if len(close) < 20:
            continue
        rets  = close.pct_change().dropna()
        cur   = safe_float(close.iloc[-1])
        hi52  = safe_float(close.rolling(252, min_periods=1).max().iloc[-1])
        lo52  = safe_float(close.rolling(252, min_periods=1).min().iloc[-1])
        ann_r = safe_float(rets.mean()) * 252 * 100
        ann_v = safe_float(rets.std())  * np.sqrt(252) * 100
        sharpe = ann_r / ann_v if ann_v else 0
        peak  = close.cummax()
        mdd   = safe_float(((close - peak) / peak).min() * 100)
        rows.append({
            "Asset":      name,
            "Price":      f"{cur:,.2f}",
            "Ann.Ret %":  f"{ann_r:+.1f}",
            "Volatility": f"{ann_v:.1f}%",
            "Sharpe":     f"{sharpe:.2f}",
            "Max DD":     f"{mdd:.1f}%",
            "52W High":   f"{hi52:,.2f}",
            "52W Low":    f"{lo52:,.2f}",
            "vs High":    f"{((cur-hi52)/hi52*100):+.1f}%",
        })
    return pd.DataFrame(rows)


# ─── MAIN ──────────────────────────────────────────────────────────────────────
def main():

    # ── SIDEBAR ─────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown('<p style="font-family:Orbitron;font-size:14px;color:#00f5ff;letter-spacing:3px;">⚙ SETTINGS</p>',
                    unsafe_allow_html=True)
        if st.button("🔄 REFRESH", use_container_width=True):
            st.cache_data.clear()

        period_options = {"1 Month": "1mo", "3 Months": "3mo", "6 Months": "6mo",
                          "1 Year": "1y", "2 Years": "2y", "5 Years": "5y"}
        sel_label  = st.selectbox("LOOKBACK PERIOD", list(period_options.keys()), index=3)
        sel_period = period_options[sel_label]

        st.markdown("---")
        ma_windows = st.multiselect("MOVING AVERAGES", [20, 50, 100, 200], default=[50, 200])
        normalize  = st.checkbox("NORMALIZE (Base=100)", value=True)
        st.markdown("---")
        st.markdown('<p style="font-family:Share Tech Mono;font-size:9px;color:#3a5a70;'
                    'letter-spacing:1px;">DATA: YAHOO FINANCE<br>REFRESH: 30 MIN TTL</p>',
                    unsafe_allow_html=True)

    # ── LOAD DATA ───────────────────────────────────────────────────────────
    with st.spinner("FETCHING GLOBAL MARKET DATA..."):
        equity_data    = fetch_data(EQUITY_TICKERS,    period=sel_period)
        commodity_data = fetch_data(COMMODITY_TICKERS, period=sel_period)
        forex_data     = fetch_data(FOREX_TICKERS,     period=sel_period)

    all_data = {**equity_data, **commodity_data}
    if not all_data:
        st.error("NO DATA FETCHED. CHECK CONNECTION.")
        return

    # ── HEADER ──────────────────────────────────────────────────────────────
    now = datetime.now().strftime("%d %b %Y  //  %H:%M:%S")
    st.markdown(f"""
    <div class="terminal-header">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <div>
          <p class="terminal-title">GLOBAL MARKETS // TERMINAL</p>
          <p class="terminal-subtitle">🌍 EQUITIES · COMMODITIES · FOREX  ·  PERIOD: {sel_label.upper()}  ·  {now}</p>
        </div>
        <div style="text-align:right;font-family:'Share Tech Mono';font-size:10px;color:#3a5a70;">
          <div style="color:#00ff88;font-size:13px;font-weight:700;">● LIVE</div>
          <div>DATA STREAM ACTIVE</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI CARDS ───────────────────────────────────────────────────────────
    # Commodities get 'com' class, equities get up/down
    commodity_names = set(COMMODITY_TICKERS.keys())
    kpi_cards = ""
    for name in KPI_NAMES:
        val_str = delta_str = "N/A"
        direction = "neu"
        card_cls  = "neu"
        source = all_data
        if name in source and not source[name].empty:
            df_k  = source[name]
            cur   = safe_float(df_k["Close"].iloc[-1])
            val_str = f"{cur:,.2f}"
            if len(df_k) >= 2:
                prev  = safe_float(df_k["Close"].iloc[-2])
                pct   = ((cur - prev) / prev) * 100
                arrow = "▲" if pct >= 0 else "▼"
                delta_str = f"{arrow} {abs(pct):.2f}%"
                direction = "pos" if pct >= 0 else "neg"
                if name in commodity_names:
                    card_cls = "com"
                else:
                    card_cls = "up" if pct >= 0 else "down"

        kpi_cards += f"""
        <div class="kpi-card {card_cls}">
          <div class="kpi-label">{name}</div>
          <div class="kpi-value">{val_str}</div>
          <div class="kpi-delta {direction}">{delta_str}</div>
        </div>"""

    st.markdown(f'<div class="kpi-grid">{kpi_cards}</div>', unsafe_allow_html=True)

    # ── TABS ────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🗺️  GLOBAL HEATMAP",
        "📊  TREND COMPARISON",
        "🏆  PERFORMANCE",
        "🕯️  TECHNICAL DIVE",
        "💱  FOREX & COMMODITIES",
        "📉  RISK & STATS",
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — GLOBAL HEATMAP
    # ══════════════════════════════════════════════════════════════════════════
    with tab1:
        st.plotly_chart(build_region_heatmap(equity_data), use_container_width=True, key="t1_heatmap")

        # Region-by-region KPI table
        st.markdown("---")
        for region, names in REGIONS.items():
            st.markdown(f'<p class="region-header">{region}</p>', unsafe_allow_html=True)
            cols = st.columns(len(names))
            for i, name in enumerate(names):
                if name not in equity_data:
                    continue
                df_r  = equity_data[name]
                cur   = safe_float(df_r["Close"].iloc[-1])
                prev  = safe_float(df_r["Close"].iloc[-2]) if len(df_r) >= 2 else cur
                pct   = ((cur - prev) / prev) * 100 if prev else 0
                cols[i].metric(
                    label=name,
                    value=f"{cur:,.2f}",
                    delta=f"{pct:+.2f}%",
                )

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — TREND COMPARISON
    # ══════════════════════════════════════════════════════════════════════════
    with tab2:
        col_chart, col_corr = st.columns([3, 2])
        with col_chart:
            sel_compare = st.multiselect(
                "SELECT ASSETS",
                list(all_data.keys()),
                default=["S&P 500", "NIKKEI 225", "FTSE 100", "DAX", "GOLD"],
                key="t2_compare",
            )
            if sel_compare:
                st.plotly_chart(build_trend_chart(all_data, sel_compare, normalize),
                                use_container_width=True, key="t2_trend")
                st.plotly_chart(build_volatility_chart(all_data, sel_compare),
                                use_container_width=True, key="t2_vol")

        with col_corr:
            st.markdown("**CORRELATION MATRIX**")
            if len(sel_compare) > 1:
                st.plotly_chart(build_corr_heatmap(all_data, sel_compare),
                                use_container_width=True, key="t2_corr")
            else:
                st.info("Select 2+ assets to show correlation")

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 — PERFORMANCE RANKING
    # ══════════════════════════════════════════════════════════════════════════
    with tab3:
        col_eq, col_com = st.columns(2)
        with col_eq:
            st.plotly_chart(build_returns_bar(equity_data, sel_label),
                            use_container_width=True, key="t3_eq")
        with col_com:
            st.plotly_chart(build_returns_bar(commodity_data, sel_label),
                            use_container_width=True, key="t3_com")

        # Drawdown comparison
        sel_dd = st.multiselect(
            "DRAWDOWN — SELECT ASSETS",
            list(equity_data.keys()),
            default=["S&P 500", "NIKKEI 225", "NIFTY 50"],
            key="t3_dd_sel",
        )
        if sel_dd:
            st.plotly_chart(build_drawdown_chart(equity_data, sel_dd),
                            use_container_width=True, key="t3_dd")

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 4 — TECHNICAL DEEP DIVE
    # ══════════════════════════════════════════════════════════════════════════
    with tab4:
        sel_asset = st.selectbox(
            "SELECT ASSET FOR DEEP DIVE",
            list(all_data.keys()),
            key="t4_asset",
        )
        if sel_asset in all_data:
            df_td = all_data[sel_asset].copy()

            # Signal row
            sigs = get_signals(df_td)
            badge_html = "  ".join(
                f'<span class="badge {bc}">{lbl}</span>'
                for bc, lbl in sigs.values()
            )
            st.markdown(f'<div style="margin-bottom:12px;">{badge_html}</div>',
                        unsafe_allow_html=True)

            # KPI row
            close  = df_td["Close"]
            rsi_v  = safe_float(rsi(close).iloc[-1])
            cur_p  = safe_float(close.iloc[-1])
            pct_1d = ((cur_p - safe_float(close.iloc[-2])) / safe_float(close.iloc[-2]) * 100
                      if len(close) >= 2 else 0)
            hi52   = safe_float(close.rolling(252, min_periods=1).max().iloc[-1])
            lo52   = safe_float(close.rolling(252, min_periods=1).min().iloc[-1])
            ann_vol= safe_float(close.pct_change().std()) * np.sqrt(252) * 100

            k1, k2, k3, k4, k5 = st.columns(5)
            k1.metric("PRICE",     f"{cur_p:,.2f}",  f"{pct_1d:+.2f}%")
            k2.metric("RSI (14)",  f"{rsi_v:.1f}",
                      "OVERBOUGHT" if rsi_v > 70 else "OVERSOLD" if rsi_v < 30 else "NEUTRAL")
            k3.metric("52W HIGH",  f"{hi52:,.2f}",   f"{((cur_p-hi52)/hi52*100):+.1f}% vs Hi")
            k4.metric("52W LOW",   f"{lo52:,.2f}",   f"{((cur_p-lo52)/lo52*100):+.1f}% vs Lo")
            k5.metric("ANN. VOL",  f"{ann_vol:.1f}%")

            # Main chart
            st.plotly_chart(build_technical_chart(df_td, sel_asset, ma_windows or [50, 200]),
                            use_container_width=True, key="t4_chart")

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 5 — FOREX & COMMODITIES
    # ══════════════════════════════════════════════════════════════════════════
    with tab5:
        col_fx, col_cm = st.columns(2)

        with col_fx:
            st.markdown('<p class="region-header">FOREX RATES</p>', unsafe_allow_html=True)
            if forex_data:
                sel_fx = st.multiselect(
                    "SELECT PAIRS",
                    list(forex_data.keys()),
                    default=list(forex_data.keys())[:4],
                    key="t5_fx",
                )
                if sel_fx:
                    st.plotly_chart(build_forex_chart(forex_data, sel_fx, normalize),
                                    use_container_width=True, key="t5_fx_chart")

                # Forex KPIs
                for fname, fdf in forex_data.items():
                    if fdf.empty:
                        continue
                    cur  = safe_float(fdf["Close"].iloc[-1])
                    prev = safe_float(fdf["Close"].iloc[-2]) if len(fdf) >= 2 else cur
                    pct  = ((cur - prev) / prev) * 100
                    cls  = "badge-bull" if pct >= 0 else "badge-bear"
                    st.markdown(
                        f'<span style="font-family:Share Tech Mono;font-size:11px;color:#7ab3cc;">'
                        f'{fname}</span>&nbsp;&nbsp;'
                        f'<span style="font-family:Orbitron;font-size:13px;color:#e2f4ff;">{cur:,.4f}</span>'
                        f'&nbsp;&nbsp;<span class="badge {cls}">{pct:+.2f}%</span><br>',
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No forex data loaded")

        with col_cm:
            st.markdown('<p class="region-header">COMMODITIES</p>', unsafe_allow_html=True)
            if commodity_data:
                st.plotly_chart(build_trend_chart(commodity_data,
                                                   list(commodity_data.keys()), normalize),
                                use_container_width=True, key="t5_com_trend")
                st.plotly_chart(build_returns_bar(commodity_data, sel_label),
                                use_container_width=True, key="t5_com_ret")

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 6 — RISK & STATS
    # ══════════════════════════════════════════════════════════════════════════
    with tab6:
        sel_risk = st.multiselect(
            "SELECT ASSETS FOR RISK TABLE",
            list(equity_data.keys()),
            default=["S&P 500", "NASDAQ 100", "NIKKEI 225", "FTSE 100",
                     "DAX", "NIFTY 50", "SENSEX"],
            key="t6_risk",
        )

        if sel_risk:
            df_stats = compute_stats(equity_data, sel_risk)
            if not df_stats.empty:
                # Highlight best/worst
                st.dataframe(
                    df_stats.set_index("Asset"),
                    use_container_width=True,
                    height=min(500, (len(df_stats) + 1) * 40),
                )

        st.markdown("---")
        col_v, col_dd2 = st.columns(2)
        with col_v:
            st.plotly_chart(build_volatility_chart(equity_data, sel_risk[:6]),
                            use_container_width=True, key="t6_vol")
        with col_dd2:
            st.plotly_chart(build_drawdown_chart(equity_data, sel_risk[:6]),
                            use_container_width=True, key="t6_dd")

        # Commodity stats
        st.markdown("---")
        st.markdown('<p class="region-header">📦 COMMODITY RISK STATS</p>', unsafe_allow_html=True)
        df_com_stats = compute_stats(commodity_data, list(commodity_data.keys()))
        if not df_com_stats.empty:
            st.dataframe(df_com_stats.set_index("Asset"), use_container_width=True)


if __name__ == "__main__":
    main()
