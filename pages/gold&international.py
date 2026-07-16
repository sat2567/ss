import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime
import numpy as np

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    layout="wide",
    page_title="Global Markets",
    page_icon="🌍",
    initial_sidebar_state="expanded",
)

# ─── CSS (light, quiet, data-first) ───────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
  --bg:      #f6f7f5;
  --panel:   #ffffff;
  --ink:     #1c2430;
  --sub:     #5c6673;
  --line:    #e3e6e2;
  --accent:  #34558b;
  --up:      #1b8a5a;
  --down:    #c4453c;
}

html, body, .stApp { background: var(--bg) !important; color: var(--ink); font-family: 'IBM Plex Sans', sans-serif; }

section[data-testid="stSidebar"] { background: var(--panel) !important; border-right: 1px solid var(--line) !important; }

h1, h2, h3 { font-family: 'IBM Plex Sans', sans-serif; font-weight: 600; }

/* Header */
.hdr { padding: 8px 0 2px 0; border-bottom: 1px solid var(--line); margin-bottom: 18px; }
.hdr-title { font-size: 20px; font-weight: 600; color: var(--ink); margin: 0; }
.hdr-sub { font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: var(--sub); margin: 2px 0 8px 0; }

/* KPI strip */
.kpi-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 10px; margin-bottom: 18px; }
.kpi { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 10px 12px; }
.kpi-label { font-family: 'IBM Plex Mono', monospace; font-size: 10px; color: var(--sub); letter-spacing: .5px; text-transform: uppercase; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.kpi-value { font-family: 'IBM Plex Mono', monospace; font-size: 15px; font-weight: 500; color: var(--ink); margin-top: 2px; white-space: nowrap; }
.kpi-delta { font-family: 'IBM Plex Mono', monospace; font-size: 11px; margin-top: 2px; }
.kpi-delta.pos { color: var(--up); }
.kpi-delta.neg { color: var(--down); }

/* Tabs */
.stTabs [data-baseweb="tab"] { font-size: 13px; color: var(--sub) !important; }
.stTabs [aria-selected="true"] { color: var(--accent) !important; border-bottom: 2px solid var(--accent) !important; }

/* Section label */
.sec { font-family: 'IBM Plex Mono', monospace; font-size: 11px; letter-spacing: 1px; text-transform: uppercase; color: var(--sub); border-bottom: 1px solid var(--line); padding-bottom: 4px; margin: 14px 0 10px 0; }

[data-testid="stMetricValue"] { font-family: 'IBM Plex Mono', monospace !important; font-size: 18px !important; }
[data-testid="stMetricLabel"] { color: var(--sub) !important; font-size: 12px !important; }
</style>
""", unsafe_allow_html=True)

# ─── TICKERS (trimmed to majors) ──────────────────────────────────────────────
EQUITY_TICKERS = {
    "S&P 500":     "^GSPC",
    "NASDAQ 100":  "^NDX",
    "FTSE 100":    "^FTSE",
    "DAX":         "^GDAXI",
    "NIKKEI 225":  "^N225",
    "HANG SENG":   "^HSI",
    "SHANGHAI":    "000001.SS",
    "NIFTY 50":    "^NSEI",
    "SENSEX":      "^BSESN",
}

COMMODITY_TICKERS = {
    "GOLD":       "GC=F",
    "SILVER":     "SI=F",
    "CRUDE (WTI)":"CL=F",
    "COPPER":     "HG=F",
}

FOREX_TICKERS = {
    "USD/INR": "INR=X",
    "EUR/USD": "EURUSD=X",
    "USD/JPY": "JPY=X",
    "USD/CNY": "CNY=X",
}

REGIONS = {
    "Americas":  ["S&P 500", "NASDAQ 100"],
    "Europe":    ["FTSE 100", "DAX"],
    "Asia-Pac":  ["NIKKEI 225", "HANG SENG", "SHANGHAI"],
    "India":     ["NIFTY 50", "SENSEX"],
}

KPI_NAMES = ["S&P 500", "NASDAQ 100", "NIKKEI 225", "NIFTY 50", "GOLD", "CRUDE (WTI)", "USD/INR"]

# ─── PLOTLY THEME ─────────────────────────────────────────────────────────────
PLOTLY_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#ffffff",
    font=dict(family="IBM Plex Sans", color="#5c6673", size=11),
    legend=dict(bgcolor="rgba(255,255,255,.9)", bordercolor="#e3e6e2", borderwidth=1),
    margin=dict(l=10, r=10, t=36, b=10),
    hoverlabel=dict(bgcolor="#ffffff", bordercolor="#34558b", font_color="#1c2430"),
)
AXIS_STYLE = dict(gridcolor="#eef0ec", zerolinecolor="#e3e6e2", showgrid=True, color="#8a93a0")
PALETTE = ["#34558b", "#c4453c", "#1b8a5a", "#b07a2a", "#6b4fa0", "#2a8c9c",
           "#8a5a44", "#4f6d7a", "#a04f6b"]

def chart_title(text):
    return dict(text=text, font=dict(family="IBM Plex Sans", size=13, color="#1c2430"))

# ─── DATA ─────────────────────────────────────────────────────────────────────
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
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df.dropna(how="all").ffill()
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            if not df.empty:
                data_dict[name] = df
        except Exception:
            continue
    return data_dict

def safe_float(val):
    try:
        v = val.iloc[0] if hasattr(val, "iloc") else val
        return float(v)
    except Exception:
        return float("nan")

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    return 100 - (100 / (1 + gain / loss))

# ─── CHARTS ───────────────────────────────────────────────────────────────────
def build_trend_chart(data_dict, names, normalize=True):
    fig = go.Figure()
    for i, name in enumerate(names):
        if name not in data_dict:
            continue
        df = data_dict[name]
        y = df["Close"]
        if normalize:
            start = y.iloc[0]
            y = (y / start) * 100 if start != 0 else y
        fig.add_trace(go.Scatter(x=df.index, y=y, name=name, mode="lines",
                                 line=dict(color=PALETTE[i % len(PALETTE)], width=1.8)))
    fig.update_layout(height=400, hovermode="x unified",
                      yaxis_title="Rebased to 100" if normalize else "Price",
                      title=chart_title("Price trend"), **PLOTLY_THEME)
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE)
    return fig

def build_returns_bar(data_dict, period_label):
    rows = []
    for name, df in data_dict.items():
        if len(df) < 2:
            continue
        first, last = safe_float(df["Close"].iloc[0]), safe_float(df["Close"].iloc[-1])
        rows.append({"Asset": name, "Return": (last - first) / first * 100})
    if not rows:
        return go.Figure()
    df_ret = pd.DataFrame(rows).sort_values("Return")
    colors = ["#1b8a5a" if r >= 0 else "#c4453c" for r in df_ret["Return"]]
    fig = go.Figure(go.Bar(
        y=df_ret["Asset"], x=df_ret["Return"], orientation="h", marker_color=colors,
        text=df_ret["Return"].apply(lambda x: f"{x:+.1f}%"), textposition="outside",
        textfont=dict(family="IBM Plex Mono", size=10),
    ))
    fig.update_layout(height=max(320, len(rows) * 30), xaxis_title="Total return (%)",
                      title=chart_title(f"Performance — {period_label}"), **PLOTLY_THEME)
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(showgrid=False, color="#5c6673")
    return fig

def build_corr_heatmap(data_dict, names):
    valid = [n for n in names if n in data_dict and not data_dict[n].empty]
    if len(valid) < 2:
        return go.Figure()
    closes = pd.DataFrame({n: data_dict[n]["Close"] for n in valid})
    corr = closes.pct_change().corr()
    fig = px.imshow(corr, text_auto=".2f", zmin=-1, zmax=1, aspect="auto",
                    color_continuous_scale=[[0, "#c4453c"], [0.5, "#ffffff"], [1, "#34558b"]])
    fig.update_layout(height=400, title=chart_title("Return correlation"),
                      coloraxis_showscale=False, **PLOTLY_THEME)
    fig.update_xaxes(tickfont=dict(size=9))
    fig.update_yaxes(tickfont=dict(size=9))
    return fig

def build_drawdown_chart(data_dict, names):
    fig = go.Figure()
    for i, name in enumerate(names):
        if name not in data_dict:
            continue
        close = data_dict[name]["Close"]
        dd = (close / close.cummax() - 1) * 100
        fig.add_trace(go.Scatter(x=data_dict[name].index, y=dd, name=name, mode="lines",
                                 line=dict(color=PALETTE[i % len(PALETTE)], width=1.5)))
    fig.update_layout(height=340, yaxis_title="Drawdown (%)", hovermode="x unified",
                      title=chart_title("Drawdown from peak"), **PLOTLY_THEME)
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE)
    return fig

def build_region_heatmap(data_dict):
    rows = []
    for region, names in REGIONS.items():
        for name in names:
            if name not in data_dict or len(data_dict[name]) < 2:
                continue
            c = data_dict[name]["Close"]
            chg = (safe_float(c.iloc[-1]) / safe_float(c.iloc[-2]) - 1) * 100
            rows.append({"Region": region, "Index": name, "Change": chg})
    if not rows:
        return go.Figure()
    df_h = pd.DataFrame(rows)
    fig = px.treemap(
        df_h, path=["Region", "Index"], values=[1] * len(df_h), color="Change",
        color_continuous_scale=[[0, "#c4453c"], [0.5, "#f2f3f0"], [1, "#1b8a5a"]],
        color_continuous_midpoint=0, custom_data=["Change"],
    )
    fig.update_traces(texttemplate="<b>%{label}</b><br>%{customdata[0]:+.2f}%",
                      textfont=dict(family="IBM Plex Mono", size=12))
    fig.update_layout(height=360, title=chart_title("Daily change by region"),
                      coloraxis_showscale=False, **PLOTLY_THEME)
    return fig

def build_deepdive_chart(df, name, ma_windows):
    """Price + MAs / RSI / Volume — three rows, no clutter."""
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                        row_heights=[0.62, 0.20, 0.18], vertical_spacing=0.03,
                        subplot_titles=("", "RSI (14)", "Volume"))
    close = df["Close"]

    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=close,
        increasing_line_color="#1b8a5a", decreasing_line_color="#c4453c",
        name="OHLC",
    ), row=1, col=1)

    ma_colors = ["#34558b", "#b07a2a", "#6b4fa0", "#2a8c9c"]
    for i, w in enumerate(ma_windows):
        fig.add_trace(go.Scatter(x=df.index, y=close.rolling(w).mean(),
                                 line=dict(color=ma_colors[i % 4], width=1.4),
                                 name=f"MA {w}"), row=1, col=1)

    rsi_vals = rsi(close)
    fig.add_trace(go.Scatter(x=df.index, y=rsi_vals, name="RSI",
                             line=dict(color="#6b4fa0", width=1.4), showlegend=False),
                  row=2, col=1)
    for level, color in [(70, "#c4453c"), (30, "#1b8a5a")]:
        fig.add_hline(y=level, line_dash="dot", line_color=color, line_width=0.8, row=2, col=1)

    if "Volume" in df.columns:
        vol_colors = ["#1b8a5a" if c >= o else "#c4453c" for c, o in zip(close, df["Open"])]
        fig.add_trace(go.Bar(x=df.index, y=df["Volume"], marker_color=vol_colors,
                             name="Volume", showlegend=False), row=3, col=1)

    for row in range(1, 4):
        fig.update_xaxes(rangeslider_visible=False, row=row, col=1, **AXIS_STYLE)
        fig.update_yaxes(row=row, col=1, **AXIS_STYLE)
    fig.update_layout(height=620, title=chart_title(f"{name} — technicals"), **PLOTLY_THEME)
    return fig

# ─── STATS ────────────────────────────────────────────────────────────────────
def compute_stats(data_dict, names):
    rows = []
    for name in names:
        if name not in data_dict:
            continue
        close = data_dict[name]["Close"]
        if len(close) < 20:
            continue
        rets = close.pct_change().dropna()
        cur = safe_float(close.iloc[-1])
        hi52 = safe_float(close.rolling(252, min_periods=1).max().iloc[-1])
        ann_r = safe_float(rets.mean()) * 252 * 100
        ann_v = safe_float(rets.std()) * np.sqrt(252) * 100
        mdd = safe_float((close / close.cummax() - 1).min() * 100)
        rows.append({
            "Asset": name,
            "Price": f"{cur:,.2f}",
            "Ann. return": f"{ann_r:+.1f}%",
            "Volatility": f"{ann_v:.1f}%",
            "Sharpe": f"{ann_r / ann_v:.2f}" if ann_v else "—",
            "Max DD": f"{mdd:.1f}%",
            "vs 52W high": f"{(cur / hi52 - 1) * 100:+.1f}%",
        })
    return pd.DataFrame(rows)

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    with st.sidebar:
        st.markdown("### Settings")
        if st.button("Refresh data", use_container_width=True):
            st.cache_data.clear()
        period_options = {"1 Month": "1mo", "3 Months": "3mo", "6 Months": "6mo",
                          "1 Year": "1y", "2 Years": "2y", "5 Years": "5y"}
        sel_label = st.selectbox("Lookback period", list(period_options.keys()), index=3)
        sel_period = period_options[sel_label]
        ma_windows = st.multiselect("Moving averages", [20, 50, 100, 200], default=[50, 200])
        st.caption("Data: Yahoo Finance · cached 30 min")

    with st.spinner("Fetching market data..."):
        equity_data = fetch_data(EQUITY_TICKERS, period=sel_period)
        commodity_data = fetch_data(COMMODITY_TICKERS, period=sel_period)
        forex_data = fetch_data(FOREX_TICKERS, period=sel_period)

    all_data = {**equity_data, **commodity_data, **forex_data}
    if not equity_data and not commodity_data:
        st.error("No data fetched. Check connection and try Refresh.")
        return

    # Header
    now = datetime.now().strftime("%d %b %Y, %H:%M")
    st.markdown(f"""
    <div class="hdr">
      <p class="hdr-title">Global Markets</p>
      <p class="hdr-sub">Equities · Commodities · FX &nbsp;·&nbsp; {sel_label} &nbsp;·&nbsp; {now}</p>
    </div>
    """, unsafe_allow_html=True)

    # KPI strip
    kpi_cards = ""
    for name in KPI_NAMES:
        val_str, delta_str, direction = "N/A", "", "pos"
        if name in all_data and len(all_data[name]) >= 2:
            c = all_data[name]["Close"]
            cur, prev = safe_float(c.iloc[-1]), safe_float(c.iloc[-2])
            pct = (cur / prev - 1) * 100
            val_str = f"{cur:,.2f}"
            delta_str = f"{'▲' if pct >= 0 else '▼'} {abs(pct):.2f}%"
            direction = "pos" if pct >= 0 else "neg"
        kpi_cards += f"""
        <div class="kpi">
          <div class="kpi-label">{name}</div>
          <div class="kpi-value">{val_str}</div>
          <div class="kpi-delta {direction}">{delta_str}</div>
        </div>"""
    st.markdown(f'<div class="kpi-grid">{kpi_cards}</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Overview", "Compare", "Deep dive"])

    # ── TAB 1: OVERVIEW ─────────────────────────────────────────────────────
    with tab1:
        col_map, col_perf = st.columns([3, 2])
        with col_map:
            st.plotly_chart(build_region_heatmap(equity_data), use_container_width=True, key="t1_map")
        with col_perf:
            st.plotly_chart(build_returns_bar(equity_data, sel_label), use_container_width=True, key="t1_perf")

        col_com, col_fx = st.columns(2)
        with col_com:
            st.markdown('<p class="sec">Commodities</p>', unsafe_allow_html=True)
            st.plotly_chart(build_returns_bar(commodity_data, sel_label), use_container_width=True, key="t1_com")
        with col_fx:
            st.markdown('<p class="sec">FX</p>', unsafe_allow_html=True)
            for fname, fdf in forex_data.items():
                if len(fdf) < 2:
                    continue
                c = fdf["Close"]
                cur, prev = safe_float(c.iloc[-1]), safe_float(c.iloc[-2])
                pct = (cur / prev - 1) * 100
                cols = st.columns(3)
                cols[0].markdown(f"**{fname}**")
                cols[1].markdown(f"`{cur:,.4f}`")
                color = "#1b8a5a" if pct >= 0 else "#c4453c"
                cols[2].markdown(f'<span style="color:{color};font-family:IBM Plex Mono;">{pct:+.2f}%</span>',
                                 unsafe_allow_html=True)

        st.markdown('<p class="sec">Key stats</p>', unsafe_allow_html=True)
        df_stats = compute_stats(equity_data, list(equity_data.keys()))
        if not df_stats.empty:
            st.dataframe(df_stats.set_index("Asset"), use_container_width=True)

    # ── TAB 2: COMPARE ──────────────────────────────────────────────────────
    with tab2:
        sel_compare = st.multiselect(
            "Assets", list(all_data.keys()),
            default=[n for n in ["S&P 500", "NIKKEI 225", "NIFTY 50", "GOLD"] if n in all_data],
            key="t2_sel",
        )
        if sel_compare:
            st.plotly_chart(build_trend_chart(all_data, sel_compare), use_container_width=True, key="t2_trend")
            col_corr, col_dd = st.columns(2)
            with col_corr:
                if len(sel_compare) > 1:
                    st.plotly_chart(build_corr_heatmap(all_data, sel_compare),
                                    use_container_width=True, key="t2_corr")
                else:
                    st.info("Select 2+ assets for correlation.")
            with col_dd:
                st.plotly_chart(build_drawdown_chart(all_data, sel_compare),
                                use_container_width=True, key="t2_dd")

    # ── TAB 3: DEEP DIVE ────────────────────────────────────────────────────
    with tab3:
        sel_asset = st.selectbox("Asset", list(all_data.keys()), key="t3_asset")
        if sel_asset in all_data:
            df_td = all_data[sel_asset]
            close = df_td["Close"]
            cur = safe_float(close.iloc[-1])
            pct_1d = (cur / safe_float(close.iloc[-2]) - 1) * 100 if len(close) >= 2 else 0
            hi52 = safe_float(close.rolling(252, min_periods=1).max().iloc[-1])
            rsi_v = safe_float(rsi(close).iloc[-1])
            ann_vol = safe_float(close.pct_change().std()) * np.sqrt(252) * 100

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Price", f"{cur:,.2f}", f"{pct_1d:+.2f}%")
            k2.metric("RSI (14)", f"{rsi_v:.1f}",
                      "Overbought" if rsi_v > 70 else "Oversold" if rsi_v < 30 else "Neutral",
                      delta_color="off")
            k3.metric("vs 52W high", f"{(cur / hi52 - 1) * 100:+.1f}%")
            k4.metric("Ann. volatility", f"{ann_vol:.1f}%")

            st.plotly_chart(build_deepdive_chart(df_td, sel_asset, ma_windows or [50, 200]),
                            use_container_width=True, key="t3_chart")


if __name__ == "__main__":
    main()
