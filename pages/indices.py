import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime
import numpy as np
import base64

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    layout="wide",
    page_title="Bharat Markets",
    page_icon="🇮🇳",
    initial_sidebar_state="expanded",
)

# ─── CSS (same design system as the global dashboard) ────────────────────────
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

.hdr { padding: 8px 0 2px 0; border-bottom: 1px solid var(--line); margin-bottom: 18px; }
.hdr-title { font-size: 20px; font-weight: 600; color: var(--ink); margin: 0; }
.hdr-sub { font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: var(--sub); margin: 2px 0 8px 0; }

.kpi-grid { display: grid; gap: 10px; margin-bottom: 18px; }
.kpi { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 10px 12px; }
.kpi-label { font-family: 'IBM Plex Mono', monospace; font-size: 10px; color: var(--sub); letter-spacing: .5px; text-transform: uppercase; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.kpi-value { font-family: 'IBM Plex Mono', monospace; font-size: 15px; font-weight: 500; color: var(--ink); margin-top: 2px; white-space: nowrap; }
.kpi-delta { font-family: 'IBM Plex Mono', monospace; font-size: 11px; margin-top: 2px; }
.kpi-delta.pos { color: var(--up); }
.kpi-delta.neg { color: var(--down); }

.stTabs [data-baseweb="tab"] { font-size: 13px; color: var(--sub) !important; }
.stTabs [aria-selected="true"] { color: var(--accent) !important; border-bottom: 2px solid var(--accent) !important; }

.sec { font-family: 'IBM Plex Mono', monospace; font-size: 11px; letter-spacing: 1px; text-transform: uppercase; color: var(--sub); border-bottom: 1px solid var(--line); padding-bottom: 4px; margin: 14px 0 10px 0; }

[data-testid="stMetricValue"] { font-family: 'IBM Plex Mono', monospace !important; font-size: 18px !important; }
[data-testid="stMetricLabel"] { color: var(--sub) !important; font-size: 12px !important; }
</style>
""", unsafe_allow_html=True)

# ─── TICKERS ──────────────────────────────────────────────────────────────────
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

# ─── DATA FETCHING (kept from your working version) ──────────────────────────
OHLCV_COLS = ["Open", "High", "Low", "Close", "Volume"]

def _clean_df(df):
    if df is None or df.empty:
        return None
    if isinstance(df.columns, pd.MultiIndex):
        lvl0 = list(df.columns.get_level_values(0))
        lvl1 = list(df.columns.get_level_values(1))
        if any(c in lvl0 for c in OHLCV_COLS):
            df.columns = lvl0
        elif any(c in lvl1 for c in OHLCV_COLS):
            df.columns = lvl1
        else:
            df.columns = lvl0
    df.columns = [str(c).strip() for c in df.columns]
    df = df.loc[:, ~df.columns.duplicated()]
    keep = [c for c in OHLCV_COLS if c in df.columns]
    if "Close" not in keep:
        return None
    df = df[keep].copy()
    df = df.dropna(subset=["Close"]).ffill()
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)
    return df if len(df) >= 5 else None

def fetch_single_range(ticker, start_date="2020-01-01"):
    try:
        df = _clean_df(yf.Ticker(ticker).history(start=start_date, auto_adjust=True))
        if df is not None:
            return df
    except Exception:
        pass
    try:
        df = _clean_df(yf.download(ticker, start=start_date, auto_adjust=True,
                                   progress=False, threads=False))
        if df is not None:
            return df
    except Exception:
        pass
    return None

@st.cache_data(ttl=1800)
def fetch_data_range(ticker_dict, start_date="2020-01-01"):
    data_dict = {}
    for name, ticker in ticker_dict.items():
        df = fetch_single_range(ticker, start_date)
        if df is not None:
            data_dict[name] = df
    return data_dict

# ─── EMBEDDED SMALLCAP ETF DATA (unchanged) ───────────────────────────────────
_ETF_B64 = (
    "UEsDBBQAAAAIAAdzWFwYTIddAQEAALoBAAAPABwAeGwvd29ya2Jvb2sueG1sIKIYACigFAAAAAAAAAAAAAAAAAAAAAAAAAAAAI2QwW4CIRCGX4XMvbJuYttsRC+9eGma1LRnhMElLrBhUPfdeugj9RUKqxtNTz3xDzPfPz/8fH0v14Pr2Akj2eAFzGcVMPQqaOv3Ao7JPDzDerUcmnOIh10IB5bnPTVRQJtS33BOqkUnaRZ69LlnQnQy5TLueTDGKnwJ6ujQJ15X1SOP2MmUd1Fre4Kr2/AfN+ojSk0tYnLdxcxJ6+E+3VtkOTu+SocCtq2lz2sDGC9zRX5YPNM9VC6YsZHSezEXkP9AqmRPuJW7scos/wOPOW6K+XHlqOfAxnOjBdTAYmOziBtdT0Y3VqOxHnXJS5eESnaqvCIfhZ/Xi6d6MYFT4tUvUEsDBAoAAAAAAAdzWFwrZ4o7nAIAAJwCAAALABwAX3JlbHMvLnJlbHMgohgAKKAUAAAAAAAAAAAAAAAAAAAAAAAAAAAA77u/PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0idXRmLTgiPz48UmVsYXRpb25zaGlwcyB4bWxucz0iaHR0cDovL3NjaGVtYXMub3BlbnhtbGZvcm1hdHMub3JnL3BhY2thZ2UvMjAwNi9yZWxhdGlvbnNoaXBzIj48UmVsYXRpb25zaGlwIFR5cGU9Imh0dHA6Ly9zY2hlbWFzLm9wZW54bWxmb3JtYXRzLm9yZy9vZmZpY2VEb2N1bWVudC8yMDA2L3JlbGF0aW9uc2hpcHMvb2ZmaWNlRG9jdW1lbnQiIFRhcmdldD0iL3hsL3dvcmtib29rLnhtbCIgSWQ9IlI4YjBkMjY1NjAyNTA0YTI2IiAvPjxSZWxhdGlvbnNoaXAgVHlwZT0iaHR0cDovL3NjaGVtYXMub3BlbnhtbGZvcm1hdHMub3JnL29mZmljZURvY3VtZW50LzIwMDYvcmVsYXRpb25zaGlwcy9leHRlbmRlZC1wcm9wZXJ0aWVzIiBUYXJnZXQ9Ii9kb2NQcm9wcy9hcHAueG1sIiBJZD0icklkMSIgLz48UmVsYXRpb25zaGlwIFR5cGU9Imh0dHA6Ly9zY2hlbWFzLm9wZW54bWxmb3JtYXRzLm9yZy9wYWNrYWdlLzIwMDYvcmVsYXRp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57/mNd5+883rr57+/u1XP/3w9Ob9hxd5fvr+1fv97t999/rHd5//cr3Xb96/ff785be/e/32L//69MP+M/3wl1c/PP2X//zt89PT/vf/8h/hi5f/8i8v9nc/PX/78rf9uq/e/H9v/vE3X3zxq//4xd9+8Yf9Bz98/tXb79//Mun+afc//u2//su//O7Nn/70/Ok//Iv+9uUKv3nz9Zunr18u9PGjX3z8y4svPvzXn3+FDy/+8Yf9m//59Ob905//+9O3r9+9f371fv+4//7Pn3/45/z8+bfvvnr1/dOfy+Ov/uOvfvHy6cXjb372xW9e/eHV+1cvL/rTm9fv//zx88svfvbb/X//7f9887v9F1++/8t3r794eV8v9tvdf/z7l+t99+r7b/7l038Ff/j85V/8P3z44uOl/vDh3fzs397e//DTZ/j913/4vDx+9U/vX16u+n/8dt3fPX24yq/+D5f593/59vXb98//8ubtu++e9lf/8ep6vN3919+//vbNP7+8/yj712X/6+9fPT99+Onl99+8/OrLZ3n5N/mrX7/7+de/lm9ffvHV23dPX//pT//09Pz65UN9+MPT+1cvXvzhV++ffvjs+dV+ny//+ubfvv2Xn3/vP31+/PWvfvHxdb+8+/rl72/e/O//69//7ct3v/g1/Pz7T/8N3v3l3fun/aP99tXzt3//5o+/+vD8/OGf/9tf/svfvvv61Y8v/71ff/PyXtabf372//jm3z7842f/6R/2C7749d/9lPTdb35+/i9v3zx9CO/8+/1//Pk/9//7L2z/mF+//uHv377526evfvrxxx9e/vTh89rD3//7Xp7f7T96evrx/aT99f89e/rTfvSlonz2/n99+PBv9y//p/33H//Qb/W/frj/72TvXn5Se/f2p+evXt7Ay1V++/T87dP7v3+z/5MYuvvhi/DjfvHnV99//4d/++Zf9tf9dcNr/vzr9//96S8vv7w8/uHDb17+8Ol/+/Cn/e37p1//7cP//u2H/wDbXsHf/vTNN/tf/8vTm/2vX7387d33f/nqu6ffvvzq3//jm5//9usPr/n56/70pw8/vP/8s+ff//7Nb98+ffx8f97+9uUvT2/+8vRPT9+8/eLp+3/en+HDb9//5fun3//09YfP+9/98vXf/vTt/mn/8Kd/evvT/qNvXn3/7uk/vNTn9//4T0/vX758+eHl33z8m0//8t3T09fvv3v58cWH/8AXH375+3d/8+7Hp6/e//jyEV/+9M3+F//w7vv+7fMPX7969/T7/UN8ff/xR3//9pt/+M0Lft8//eab119999t3T9/++PJhP3y23739+u23n/34/PbHp+f3//Zff/vjy6t9+P7/AVBLAwQUAAAACAAHc1hc"
)


def parse_etf_bytes(raw_bytes):
    import io
    raw = pd.read_excel(io.BytesIO(raw_bytes), header=None)
    data = raw.iloc[4:, :2].copy()
    data.columns = ["Date", "NAV"]
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    data["NAV"] = pd.to_numeric(data["NAV"], errors="coerce")
    data = data.dropna(subset=["Date", "NAV"]).sort_values("Date")
    data.set_index("Date", inplace=True)
    df = pd.DataFrame(
        {"Open": data["NAV"], "High": data["NAV"],
         "Low": data["NAV"], "Close": data["NAV"], "Volume": 0},
        index=data.index,
    )
    return df if len(df) >= 5 else None


def resolve_smallcap(start_date="2020-01-01", uploaded_file=None):
    cutoff = pd.Timestamp(start_date)

    def trim(df, name, source):
        filtered = df[df.index >= cutoff]
        return name, (filtered if len(filtered) >= 5 else df), source

    try:
        df = parse_etf_bytes(base64.b64decode(_ETF_B64))
        if df is not None:
            return trim(df, "NIFTY SMALLCAP 50 ETF", "Embedded")
    except Exception:
        pass

    if uploaded_file is not None:
        try:
            df = parse_etf_bytes(uploaded_file.read())
            if df is not None:
                return trim(df, "NIFTY SMALLCAP 50 ETF", "Uploaded")
        except Exception:
            pass

    for display_name, ticker in SMALLCAP_FALLBACKS:
        df = fetch_single_range(ticker, start_date)
        if df is not None:
            return display_name, df, f"Yahoo ({ticker})"

    return None, None, "No smallcap data"

# ─── INDICATORS ───────────────────────────────────────────────────────────────
def calc_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    return 100 - (100 / (1 + gain / loss))

def calculate_drawdown(series):
    return (series / series.cummax() - 1) * 100

# ─── CHARTS ───────────────────────────────────────────────────────────────────
def build_deepdive_chart(df, name, ma_windows, chart_type="Candlestick"):
    """Price + MAs / RSI / Volume — three rows."""
    has_vol = "Volume" in df.columns and df["Volume"].sum() > 0
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                        row_heights=[0.62, 0.20, 0.18], vertical_spacing=0.03,
                        subplot_titles=("", "RSI (14)", "Volume" if has_vol else ""))
    close = df["Close"]

    if chart_type == "Candlestick":
        fig.add_trace(go.Candlestick(
            x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=close,
            increasing_line_color="#1b8a5a", decreasing_line_color="#c4453c",
            name="OHLC"), row=1, col=1)
    else:
        fig.add_trace(go.Scatter(x=df.index, y=close, name=name,
                                 line=dict(color="#34558b", width=1.6)), row=1, col=1)

    ma_colors = ["#34558b", "#b07a2a", "#6b4fa0", "#2a8c9c"]
    for i, w in enumerate(ma_windows):
        fig.add_trace(go.Scatter(x=df.index, y=close.rolling(w).mean(),
                                 line=dict(color=ma_colors[i % 4], width=1.4),
                                 name=f"MA {w}"), row=1, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=calc_rsi(close), name="RSI",
                             line=dict(color="#6b4fa0", width=1.4), showlegend=False),
                  row=2, col=1)
    for level, color in [(70, "#c4453c"), (30, "#1b8a5a")]:
        fig.add_hline(y=level, line_dash="dot", line_color=color, line_width=0.8, row=2, col=1)

    if has_vol:
        vol_colors = ["#1b8a5a" if c >= o else "#c4453c" for c, o in zip(close, df["Open"])]
        fig.add_trace(go.Bar(x=df.index, y=df["Volume"], marker_color=vol_colors,
                             name="Volume", showlegend=False), row=3, col=1)

    for row in range(1, 4):
        fig.update_xaxes(rangeslider_visible=False, row=row, col=1, **AXIS_STYLE)
        fig.update_yaxes(row=row, col=1, **AXIS_STYLE)
    fig.update_layout(height=620, title=chart_title(f"{name} — technicals"), **PLOTLY_THEME)
    return fig


def build_trend_chart(data_dict, names, title="Rebased performance"):
    fig = go.Figure()
    for i, name in enumerate(names):
        if name not in data_dict or data_dict[name].empty:
            continue
        y = data_dict[name]["Close"]
        start = y.iloc[0] or 1
        fig.add_trace(go.Scatter(x=data_dict[name].index, y=(y / start) * 100,
                                 name=name, mode="lines",
                                 line=dict(color=PALETTE[i % len(PALETTE)], width=1.8)))
    fig.update_layout(height=400, hovermode="x unified", yaxis_title="Rebased to 100",
                      title=chart_title(title), **PLOTLY_THEME)
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE)
    return fig


def build_corr_heatmap(data_dict):
    closes = pd.DataFrame({k: v["Close"] for k, v in data_dict.items() if not v.empty})
    if closes.shape[1] < 2:
        return go.Figure()
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
        if name not in data_dict or data_dict[name].empty:
            continue
        dd = calculate_drawdown(data_dict[name]["Close"])
        fig.add_trace(go.Scatter(x=dd.index, y=dd, name=name, mode="lines",
                                 line=dict(color=PALETTE[i % len(PALETTE)], width=1.5)))
    fig.update_layout(height=340, yaxis_title="Drawdown (%)", hovermode="x unified",
                      title=chart_title("Drawdown from peak"), **PLOTLY_THEME)
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE)
    return fig


def build_sector_treemap(sector_data):
    rows = []
    for name, df in sector_data.items():
        if not df.empty and len(df) > 1:
            c = df["Close"]
            ret = (c.iloc[-1] / c.iloc[0] - 1) * 100
            rows.append({"Sector": name, "Return": round(ret, 2), "Abs": abs(ret) + 0.1})
    if not rows:
        return None
    df_tree = pd.DataFrame(rows)
    fig = px.treemap(df_tree, path=["Sector"], values="Abs", color="Return",
                     color_continuous_scale=[[0, "#c4453c"], [0.5, "#f2f3f0"], [1, "#1b8a5a"]],
                     color_continuous_midpoint=0, custom_data=["Return"])
    fig.update_traces(texttemplate="<b>%{label}</b><br>%{customdata[0]:+.1f}%",
                      textfont=dict(family="IBM Plex Mono", size=12))
    fig.update_layout(height=380, title=chart_title("Sector returns since Jan 2020"),
                      coloraxis_showscale=False, **PLOTLY_THEME)
    return fig


def build_sector_bar(sector_data):
    rows = []
    for name, df in sector_data.items():
        if not df.empty and len(df) > 1:
            c = df["Close"]
            rows.append({"Sector": name, "Return": (c.iloc[-1] / c.iloc[0] - 1) * 100})
    if not rows:
        return go.Figure()
    df_s = pd.DataFrame(rows).sort_values("Return")
    colors = ["#1b8a5a" if r >= 0 else "#c4453c" for r in df_s["Return"]]
    fig = go.Figure(go.Bar(y=df_s["Sector"], x=df_s["Return"], orientation="h",
                           marker_color=colors,
                           text=df_s["Return"].apply(lambda x: f"{x:+.1f}%"),
                           textposition="outside",
                           textfont=dict(family="IBM Plex Mono", size=10)))
    fig.update_layout(height=380, xaxis_title="Total return (%)",
                      title=chart_title("Sector ranking"), **PLOTLY_THEME)
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(showgrid=False, color="#5c6673")
    return fig


def build_returns_dist(df, name):
    rets = df["Close"].pct_change().dropna() * 100
    fig = go.Figure(go.Histogram(x=rets, nbinsx=60, name="Daily returns",
                                 marker_color="rgba(52,85,139,.55)",
                                 marker_line_color="#34558b", marker_line_width=0.5))
    var_95, var_99 = np.percentile(rets, 5), np.percentile(rets, 1)
    fig.add_vline(x=var_95, line_dash="dash", line_color="#b07a2a",
                  annotation_text=f"VaR 95%: {var_95:.2f}%", annotation_font_size=10)
    fig.add_vline(x=var_99, line_dash="dash", line_color="#c4453c",
                  annotation_text=f"VaR 99%: {var_99:.2f}%", annotation_font_size=10)
    fig.update_layout(height=300, xaxis_title="Daily return (%)", yaxis_title="Frequency",
                      title=chart_title(f"{name} — return distribution"), **PLOTLY_THEME)
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE)
    return fig


def build_monthly_heatmap(df, name):
    monthly = df["Close"].resample("ME").last().pct_change().dropna() * 100
    if monthly.empty:
        return None
    m = pd.DataFrame({"Date": monthly.index, "Return": monthly.values})
    m["Year"] = m["Date"].dt.year
    m["Month"] = m["Date"].dt.strftime("%b")
    order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    pivot = m.pivot(index="Year", columns="Month", values="Return")
    pivot = pivot.reindex(columns=[x for x in order if x in pivot.columns])
    fig = px.imshow(pivot, text_auto=".1f", aspect="auto",
                    color_continuous_scale=[[0, "#c4453c"], [0.5, "#ffffff"], [1, "#1b8a5a"]],
                    color_continuous_midpoint=0)
    fig.update_traces(textfont=dict(family="IBM Plex Mono", size=10))
    fig.update_layout(height=280, title=chart_title(f"{name} — monthly returns (%)"),
                      coloraxis_showscale=False, **PLOTLY_THEME)
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE)
    return fig

# ─── STATS TABLE ──────────────────────────────────────────────────────────────
def compute_risk_table(data_dict, names, label):
    rows = []
    for name in names:
        if name not in data_dict or data_dict[name].empty:
            continue
        c = data_dict[name]["Close"]
        rets = c.pct_change().dropna()
        if len(rets) < 20:
            continue
        ann_vol = rets.std() * np.sqrt(252) * 100
        sharpe = (rets.mean() / rets.std()) * np.sqrt(252) if rets.std() else 0
        max_dd = calculate_drawdown(c).min()
        var95 = np.percentile(rets * 100, 5)
        total = (c.iloc[-1] / c.iloc[0] - 1) * 100
        rows.append({
            "Index": name,
            f"Return ({label})": f"{total:+.1f}%",
            "Ann. vol": f"{ann_vol:.1f}%",
            "Sharpe": f"{sharpe:.2f}",
            "Max DD": f"{max_dd:.1f}%",
            "VaR 95% (daily)": f"{var95:.2f}%",
        })
    return pd.DataFrame(rows)

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    START_DATE = "2020-01-01"

    with st.sidebar:
        st.markdown("### Settings")
        if st.button("Refresh data", use_container_width=True):
            st.cache_data.clear()
        ma_windows = st.multiselect("Moving averages", [20, 50, 100, 200], default=[50, 200])
        with st.expander("Smallcap ETF file (fallback)"):
            uploaded_etf = st.file_uploader("Upload axis_niftyetf.xlsx", type=["xlsx"],
                                            label_visibility="collapsed")
        sc_status = st.empty()
        st.caption("Data: Yahoo Finance + embedded ETF · from 1 Jan 2020 · cached 30 min")

    with st.spinner("Fetching market data..."):
        index_data = fetch_data_range(INDEX_TICKERS, start_date=START_DATE)
        sector_data = fetch_data_range(SECTOR_TICKERS, start_date=START_DATE)

    sc_name, sc_df, sc_source = resolve_smallcap(start_date=START_DATE, uploaded_file=uploaded_etf)
    if sc_df is not None:
        index_data[sc_name] = sc_df
        sc_status.caption(f"Smallcap source: {sc_source}")
    else:
        sc_status.caption("Smallcap: no data available")

    if not index_data:
        st.error("No data fetched. Check connection and try Refresh.")
        return

    # Header
    now = datetime.now().strftime("%d %b %Y, %H:%M")
    st.markdown(f"""
    <div class="hdr">
      <p class="hdr-title">Bharat Markets</p>
      <p class="hdr-sub">NSE / BSE analytics &nbsp;·&nbsp; since Jan 2020 &nbsp;·&nbsp; {now}</p>
    </div>
    """, unsafe_allow_html=True)

    # KPI strip
    preferred = ["NIFTY 50", "NIFTY BANK", "NIFTY MIDCAP", "NIFTY IT", "SENSEX", "INDIA VIX"]
    kpi_names = [n for n in preferred if n in index_data]
    sc_variants = [n for n in index_data if "SMALLCAP" in n.upper() or "SMLCAP" in n.upper()]
    if sc_variants and sc_variants[0] not in kpi_names:
        kpi_names.append(sc_variants[0])
    kpi_names = kpi_names[:7]

    kpi_cards = ""
    for name in kpi_names:
        val_str, delta_str, direction = "N/A", "", "pos"
        df = index_data.get(name)
        if df is not None and len(df) >= 2 and "Close" in df.columns:
            cur, prev = float(df["Close"].iloc[-1]), float(df["Close"].iloc[-2])
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
    st.markdown(f'<div class="kpi-grid" style="grid-template-columns:repeat({len(kpi_names)},1fr)">{kpi_cards}</div>',
                unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Overview", "Compare", "Deep dive"])
    available_indices = list(index_data.keys())

    # ── TAB 1: OVERVIEW ─────────────────────────────────────────────────────
    with tab1:
        col_tree, col_bar = st.columns(2)
        with col_tree:
            fig_tree = build_sector_treemap(sector_data)
            if fig_tree:
                st.plotly_chart(fig_tree, use_container_width=True, key="t1_tree")
            else:
                st.info("Sector data unavailable.")
        with col_bar:
            st.plotly_chart(build_sector_bar(sector_data), use_container_width=True, key="t1_bar")

        st.markdown('<p class="sec">Index risk & return (since Jan 2020)</p>', unsafe_allow_html=True)
        df_risk = compute_risk_table(index_data, available_indices, "since 2020")
        if not df_risk.empty:
            st.dataframe(df_risk.set_index("Index"), use_container_width=True)

    # ── TAB 2: COMPARE ──────────────────────────────────────────────────────
    with tab2:
        default_sel = [x for x in ["NIFTY 50", "NIFTY BANK", "NIFTY MIDCAP"] if x in available_indices]
        sel = st.multiselect("Indices", available_indices, default=default_sel, key="t2_sel")
        if sel:
            st.plotly_chart(build_trend_chart(index_data, sel), use_container_width=True, key="t2_trend")
            col_corr, col_dd = st.columns(2)
            with col_corr:
                if len(sel) > 1:
                    st.plotly_chart(build_corr_heatmap({k: index_data[k] for k in sel}),
                                    use_container_width=True, key="t2_corr")
                else:
                    st.info("Select 2+ indices for correlation.")
            with col_dd:
                st.plotly_chart(build_drawdown_chart(index_data, sel),
                                use_container_width=True, key="t2_dd")

    # ── TAB 3: DEEP DIVE ────────────────────────────────────────────────────
    with tab3:
        all_assets = {**index_data, **sector_data}
        valid = {k: v for k, v in all_assets.items() if not v.empty}
        c_sel, c_type = st.columns([3, 1])
        with c_sel:
            sel_asset = st.selectbox("Asset", list(valid.keys()), key="t3_asset")
        with c_type:
            chart_type = st.radio("Chart", ["Candlestick", "Line"], horizontal=True, key="t3_type")

        df_td = valid[sel_asset]
        close = df_td["Close"]
        cur = float(close.iloc[-1])
        pct_1d = (cur / float(close.iloc[-2]) - 1) * 100 if len(close) >= 2 else 0
        hi52 = float(close.rolling(252, min_periods=1).max().iloc[-1])
        rsi_v = float(calc_rsi(close).iloc[-1])
        ann_vol = float(close.pct_change().std()) * np.sqrt(252) * 100

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Price", f"{cur:,.2f}", f"{pct_1d:+.2f}%")
        k2.metric("RSI (14)", f"{rsi_v:.1f}",
                  "Overbought" if rsi_v > 70 else "Oversold" if rsi_v < 30 else "Neutral",
                  delta_color="off")
        k3.metric("vs 52W high", f"{(cur / hi52 - 1) * 100:+.1f}%")
        k4.metric("Ann. volatility", f"{ann_vol:.1f}%")

        st.plotly_chart(build_deepdive_chart(df_td, sel_asset, ma_windows or [50, 200], chart_type),
                        use_container_width=True, key="t3_chart")

        col_hm, col_dist = st.columns(2)
        with col_hm:
            fig_hm = build_monthly_heatmap(df_td, sel_asset)
            if fig_hm:
                st.plotly_chart(fig_hm, use_container_width=True, key="t3_hm")
        with col_dist:
            st.plotly_chart(build_returns_dist(df_td, sel_asset),
                            use_container_width=True, key="t3_dist")


if __name__ == "__main__":
    main()
