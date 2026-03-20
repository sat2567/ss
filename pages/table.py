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
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
        font-family: 'Share Tech Mono', monospace;
        font-size: 13px;
    }
    .custom-table th {
        background-color: #0b3d60;
        color: #ffffff;
        padding: 10px;
        text-align: right;
        border: 1px solid var(--border);
        font-weight: bold;
    }
    .custom-table th:first-child { text-align: left; }
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
    .ticker-note { font-size: 11px; color: #456070; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

# ─── TICKERS ───────────────────────────────────────────────────────────────────
# FORMAT: "Display Name": (primary_ticker, fallback_ticker_or_None)
# All symbols verified against Yahoo Finance.
# Fallbacks handle Yahoo Finance regional inconsistencies.

INDICES = {
    "NIFTY 50":           ("^NSEI",               None),
    "NIFTY NEXT 50":      ("^NSMIDCP",             "NIFTYJR.NS"),       # ^NSMIDCP is correct YF symbol
    "NIFTY BANK":         ("^NSEBANK",             None),
    "NIFTY MIDCAP 100":   ("NIFTY_MIDCAP_100.NS",  "^CRSMID"),          # NIFTY_MIDCAP_100.NS is primary
    "NIFTY SMALLCAP 100": ("^CNXSC",               "NIFTYSMLCAP100.NS"),
    "NIFTY SMALLCAP 250": ("NIFTYSMLCAP250.NS",    None),
    "SENSEX":             ("^BSESN",               None),
}

SECTORS = {
    "Defence":        ("NIFTYINDIADEFENCE.NS", None),
    "Auto":           ("^CNXAUTO",             None),
    "Pharma":         ("^CNXPHARMA",           None),
    "Consumption":    ("^CNXCONSUMP",          None),
    "Energy":         ("^CNXENERGY",           None),
    "Infrastructure": ("^CNXINFRA",            None),
    "Realty":         ("^CNXREALTY",           None),
    "FMCG":           ("^CNXFMCG",             None),
    "Metal":          ("^CNXMETAL",            None),
}

# ─── DATA FETCHING ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def _fetch_one(ticker: str):
    """Download 2y of daily closes for one ticker. Returns pd.Series or None."""
    try:
        data = yf.download(ticker, period="2y", interval="1d", auto_adjust=True, progress=False)
        if data.empty:
            return None
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        series = data["Close"] if "Close" in data.columns else data.iloc[:, 0]
        if isinstance(series, pd.DataFrame):
            series = series.iloc[:, 0]
        series = series.squeeze().dropna()
        series.index = pd.to_datetime(series.index).tz_localize(None)
        return series if not series.empty else None
    except Exception:
        return None


@st.cache_data(ttl=3600)
def get_market_data(tickers: dict) -> dict:
    """Try primary ticker; fall back to secondary if primary fails."""
    output = {}
    for name, (primary, fallback) in tickers.items():
        series = _fetch_one(primary)
        if series is None and fallback:
            series = _fetch_one(fallback)
        if series is not None:
            output[name] = series
    return output


# ─── CALCULATION HELPERS ───────────────────────────────────────────────────────
def prev_trading_close(series: pd.Series, date) -> float | None:
    """
    Last available closing price ON OR BEFORE `date` using .asof().
    This is the NSE point-to-point convention — avoids calendar/trading day mismatch.
    """
    val = series.asof(pd.Timestamp(date))
    return float(val) if pd.notna(val) else None


def calc_pct(series: pd.Series, start_date, end_date) -> str:
    """Formatted % change string between two dates, or 'N/A'."""
    p_start = prev_trading_close(series, start_date)
    p_end   = prev_trading_close(series, end_date)
    if p_start is None or p_end is None or p_start == 0:
        return "N/A"
    return f"{((p_end - p_start) / p_start) * 100:+.2f}%"


def color_class(val_str: str) -> str:
    if val_str == "N/A":
        return "val-neu"
    try:
        n = float(val_str.replace("%", "").replace("+", ""))
        return "val-pos" if n > 0 else ("val-neg" if n < 0 else "val-neu")
    except Exception:
        return "val-neu"


def get_last_friday() -> datetime.date:
    d = datetime.now().date()
    while d.weekday() != 4:
        d -= timedelta(days=1)
    return d


def build_html_table(df: pd.DataFrame, skip_color_cols: list) -> str:
    html = '<table class="custom-table"><thead><tr>'
    for col in df.columns:
        html += f"<th>{col}</th>"
    html += "</tr></thead><tbody>"
    for _, row in df.iterrows():
        html += "<tr>"
        for col in df.columns:
            val = str(row[col])
            if col in skip_color_cols:
                html += f"<td>{val}</td>"
            else:
                html += f'<td class="{color_class(val)}">{val}</td>'
        html += "</tr>"
    html += "</tbody></table>"
    return html


# ─── MAIN UI ──────────────────────────────────────────────────────────────────
def main():
    st.markdown(
        '<h1 style="font-family:Orbitron; color:#00f5ff;">BHARAT PERFORMANCE TERMINAL</h1>',
        unsafe_allow_html=True
    )

    today         = datetime.now().date()
    last_friday   = get_last_friday()
    prev_friday   = last_friday - timedelta(days=7)
    one_month_ago = last_friday - timedelta(days=30)
    lf_str        = last_friday.strftime("%d-%b")

    # ── DATE CONTROLS ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-head">SET PARAMETERS (FOR MAJOR INDICES)</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        s_dt = st.date_input("START DATE", today - timedelta(days=30))
    with col2:
        e_dt = st.date_input("END DATE", today)
    with col3:
        st.info(
            f"Sector table locked Fri→Fri:  "
            f"{prev_friday.strftime('%d-%b')} → {lf_str}  |  "
            f"1M base: {one_month_ago.strftime('%d-%b')}"
        )

    # ── FETCH ─────────────────────────────────────────────────────────────────
    with st.spinner("Fetching market data..."):
        idx_dict = get_market_data(INDICES)
        sec_dict = get_market_data(SECTORS)

    # ── MAJOR INDICES TABLE ───────────────────────────────────────────────────
    st.markdown('<div class="section-head">MAJOR INDICES</div>', unsafe_allow_html=True)

    display_order = [
        "NIFTY 50", "NIFTY NEXT 50", "NIFTY BANK",
        "NIFTY MIDCAP 100", "NIFTY SMALLCAP 100", "NIFTY SMALLCAP 250",
        "SENSEX",
    ]

    idx_rows = []
    for name in display_order:
        series = idx_dict.get(name)
        if series is None:
            idx_rows.append({
                "Index": name, "Current Level": "N/A",
                "1 Week": "N/A", "1 Month": "N/A", "Custom Range": "N/A",
            })
            continue

        current = prev_trading_close(series, today)
        if current is None:
            continue

        idx_rows.append({
            "Index":         name,
            "Current Level": f"{current:,.2f}",
            "1 Week":        calc_pct(series, today - timedelta(days=7),  today),
            "1 Month":       calc_pct(series, today - timedelta(days=30), today),
            "Custom Range":  calc_pct(series, s_dt, e_dt),
        })

    if idx_rows:
        df_idx = pd.DataFrame(idx_rows)
        st.markdown(
            build_html_table(df_idx, skip_color_cols=["Index", "Current Level"]),
            unsafe_allow_html=True
        )
    else:
        st.warning("Data connection issues. Please try refreshing.")

    # ── SECTOR ROTATION TABLE ─────────────────────────────────────────────────
    st.markdown(
        f'<div class="section-head">SECTOR ROTATION (ENDING {lf_str.upper()})</div>',
        unsafe_allow_html=True
    )

    sec_rows = []
    for name, series in sec_dict.items():
        if series.empty:
            continue

        p_now  = prev_trading_close(series, last_friday)
        p_week = prev_trading_close(series, prev_friday)
        p_1m   = prev_trading_close(series, one_month_ago)

        if p_now is None:
            continue

        def safe_ret(curr, prev):
            if curr is None or prev is None or prev == 0:
                return "N/A"
            return f"{((curr - prev) / prev) * 100:+.2f}%"

        sec_rows.append({
            "Sector":           name,
            lf_str:             f"{p_now:,.2f}",
            "1 Week (Fri→Fri)": safe_ret(p_now, p_week),
            "1 Month":          safe_ret(p_now, p_1m),
        })

    if sec_rows:
        df_sec = pd.DataFrame(sec_rows)
        df_sec["_sort"] = df_sec["1 Week (Fri→Fri)"].apply(
            lambda x: float(x.replace("%", "").replace("+", "")) if x != "N/A" else -999
        )
        df_sec = df_sec.sort_values("_sort", ascending=False).drop(columns=["_sort"])
        st.markdown(
            build_html_table(df_sec, skip_color_cols=["Sector", lf_str]),
            unsafe_allow_html=True
        )
    else:
        st.warning("No sector data found.")

    st.markdown(
        '<p class="ticker-note">Data via Yahoo Finance · Cached 1hr · '
        'Returns calculated using last available trading close on or before each date (NSE convention)</p>',
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
