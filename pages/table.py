import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import pandas.tseries.offsets as offsets

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
</style>
""", unsafe_allow_html=True)

# ─── TICKERS ───────────────────────────────────────────────────────────────────
INDICES = {
    "NIFTY 50":        "^NSEI",
    "NIFTY NEXT 50":   "NIFTYJR.NS",
    "NIFTY BANK":      "^NSEBANK",
    "NIFTY MIDCAP 100":"^CRSMID",
    "SENSEX":          "^BSESN"
}

SECTORS = {
    "Defence":      "NIFTYINDIADEFENCE.NS",   # ← fixed ticker
    "Auto":         "^CNXAUTO",
    "Pharma":       "^CNXPHARMA",
    "Consumption":  "^CNXCONSUMP",
    "Energy":       "^CNXENERGY",
    "Infrastructure":"^CNXINFRA",
    "Realty":       "^CNXREALTY",
    "FMCG":         "^CNXFMCG",
    "Metal":        "^CNXMETAL"
}

# ─── DATA FETCHING ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def get_market_data(tickers: dict) -> dict:
    output = {}
    for name, ticker in tickers.items():
        try:
            data = yf.download(
                ticker, period="2y", interval="1d",
                auto_adjust=True, progress=False
            )
            if data.empty:
                continue
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            series = data["Close"] if "Close" in data.columns else data.iloc[:, 0]
            if isinstance(series, pd.DataFrame):
                series = series.iloc[:, 0]
            series = series.squeeze().dropna()
            series.index = pd.to_datetime(series.index).tz_localize(None)
            output[name] = series
        except Exception:
            continue
    return output


def prev_trading_close(series: pd.Series, date) -> float | None:
    """
    Return the last available closing price on or before `date`.
    This mirrors how NSE calculates point-to-point returns —
    using .asof() avoids the calendar-day vs trading-day mismatch.
    """
    ts = pd.Timestamp(date)
    val = series.asof(ts)
    return float(val) if pd.notna(val) else None


def calc_pct(series: pd.Series, start_date, end_date) -> float:
    """
    Percentage return between two dates using the last available
    trading close on or before each date (NSE convention).
    """
    if series is None or series.empty:
        return 0.0
    p_start = prev_trading_close(series, start_date)
    p_end   = prev_trading_close(series, end_date)
    if p_start is None or p_end is None or p_start == 0:
        return 0.0
    return ((p_end - p_start) / p_start) * 100


def get_last_friday() -> datetime.date:
    d = datetime.now().date()
    while d.weekday() != 4:          # 4 = Friday
        d -= timedelta(days=1)
    return d


def prev_week_friday(reference_friday) -> datetime.date:
    """Friday one week before the reference Friday."""
    return reference_friday - timedelta(days=7)


# ─── MAIN UI ──────────────────────────────────────────────────────────────────
def main():
    st.markdown(
        '<h1 style="font-family:Orbitron; color:#00f5ff;">BHARAT PERFORMANCE TERMINAL</h1>',
        unsafe_allow_html=True
    )

    last_friday    = get_last_friday()
    prev_friday    = prev_week_friday(last_friday)
    one_month_ago  = last_friday - timedelta(days=30)
    lf_str         = last_friday.strftime("%d-%b")

    # ── DATE CONTROLS ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-head">SET PARAMETERS (FOR MAJOR INDICES)</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        s_dt = st.date_input("START DATE", datetime.now() - timedelta(days=30))
    with col2:
        e_dt = st.date_input("END DATE", datetime.now())
    with col3:
        st.info(
            f"Sector table is locked week-over-week: "
            f"{prev_friday.strftime('%d-%b')} → {lf_str}  |  "
            f"1 Month base: {one_month_ago.strftime('%d-%b')}"
        )

    # ── FETCH DATA ────────────────────────────────────────────────────────────
    with st.spinner("Accessing Real-time Market Data..."):
        idx_dict = get_market_data(INDICES)
        sec_dict = get_market_data(SECTORS)

    today = datetime.now().date()

    # ── MAJOR INDICES TABLE ───────────────────────────────────────────────────
    st.markdown('<div class="section-head">MAJOR INDICES</div>', unsafe_allow_html=True)
    idx_rows = []
    display_order = ["NIFTY 50", "NIFTY NEXT 50", "NIFTY BANK", "NIFTY MIDCAP 100", "SENSEX"]

    for name in display_order:
        series = idx_dict.get(name)
        if series is None or series.empty:
            continue

        current = prev_trading_close(series, today)
        if current is None:
            continue

        one_week_start  = today - timedelta(days=7)
        one_month_start = today - timedelta(days=30)

        idx_rows.append({
            "Index":         name,
            "Current Level": f"{current:,.2f}",
            # ── FIX: anchor = last trading close on/before N days ago ────────
            "1 Week":        f"{calc_pct(series, one_week_start,  today):+.2f}%",
            "1 Month":       f"{calc_pct(series, one_month_start, today):+.2f}%",
            # ── FIX: custom range uses .asof() on both ends ──────────────────
            "Custom Range":  f"{calc_pct(series, s_dt, e_dt):+.2f}%",
        })

    if idx_rows:
        st.table(pd.DataFrame(idx_rows))
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
        p_week = prev_trading_close(series, prev_friday)    # ← clean Friday-to-Friday
        p_1m   = prev_trading_close(series, one_month_ago)

        if p_now is None:
            continue

        def safe_ret(curr, prev):
            if curr is None or prev is None or prev == 0:
                return "N/A"
            return f"{((curr - prev) / prev) * 100:+.2f}%"

        sec_rows.append({
            "Sector":              name,
            lf_str:                f"{p_now:,.2f}",
            "1 Week (Fri-Fri)":    safe_ret(p_now, p_week),
            "1 Month":             safe_ret(p_now, p_1m),
        })

    if sec_rows:
        df_sec = pd.DataFrame(sec_rows)

        df_sec["_sort"] = df_sec["1 Week (Fri-Fri)"].apply(
            lambda x: float(x.replace("%", "").replace("+", ""))
            if x != "N/A" else -999
        )
        df_sec = df_sec.sort_values("_sort", ascending=False).drop(columns=["_sort"])

        # Build custom HTML table
        html = '<table class="custom-table"><thead><tr>'
        for col in df_sec.columns:
            html += f"<th>{col}</th>"
        html += "</tr></thead><tbody>"

        for _, row in df_sec.iterrows():
            html += "<tr>"
            for i, col in enumerate(df_sec.columns):
                val = row[col]
                if i == 0 or col == lf_str:
                    html += f"<td>{val}</td>"
                else:
                    css = "val-neu"
                    if val != "N/A":
                        try:
                            num = float(val.replace("%", "").replace("+", ""))
                            css = "val-pos" if num > 0 else ("val-neg" if num < 0 else "val-neu")
                        except Exception:
                            pass
                    html += f'<td class="{css}">{val}</td>'
            html += "</tr>"
        html += "</tbody></table>"

        st.markdown(html, unsafe_allow_html=True)
    else:
        st.warning("No sector data found.")


if __name__ == "__main__":
    main()
