import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import datetime
import time

# -------------------------
# Config / small utilities
# -------------------------
st.set_page_config(page_title="Mutual Fund Dashboard", layout="wide")

DATA_TTL_SECONDS = 3600  # cache TTL for fetch_table

def now_str():
    return datetime.datetime.now().strftime("%d-%b-%Y %I:%M %p")

# -------------------------
# Auto-refresh helper
# -------------------------
def should_daily_auto_refresh():
    """
    Auto-refresh once per day after 9:00 AM local time.
    Returns True if we should refresh now (and updates session state to avoid repeating).
    """
    now = datetime.datetime.now()
    today_9am = now.replace(hour=9, minute=0, second=0, microsecond=0)
    last_auto = st.session_state.get("_last_auto_refresh_date", None)

    if now >= today_9am:
        if last_auto != now.date():
            st.session_state["_last_auto_refresh_date"] = now.date()
            # clear cached fetches so next scraping is fresh
            try:
                st.cache_data.clear()
            except Exception:
                pass
            return True
    return False

# -------------------------
# HTTP fetch + parsing (cached)
# -------------------------
@st.cache_data(ttl=DATA_TTL_SECONDS)
def fetch_table(url, rename_map=None):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        resp = requests.get(url, headers=headers, timeout=12)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table", class_="mctable1")
        if not table:
            # structure changed or no table present
            return None

        rows = table.find_all("tr")
        data = []
        for row in rows:
            cols = row.find_all(["td", "th"])
            cols = [ele.get_text(strip=True) for ele in cols]
            data.append(cols)

        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            if rename_map:
                df.rename(columns=rename_map, inplace=True)
            return df
        return None
    except Exception as e:
        # return the exception message for debugging upstream
        return {"error": str(e)}

# -------------------------
# Scraper per category
# -------------------------
def scrape_category(category_slug, category_label):
    """
    Returns: (df, status, message)
      - df: DataFrame or None
      - status: "ok" / "partial" / "error" / "empty"
      - message: helpful text
    """
    base = "https://www.moneycontrol.com/mutual-funds/performance-tracker"
    urls = {
        "returns": f"{base}/returns/{category_slug}.html",
        "rank": f"{base}/ranks/{category_slug}.html"
    }

    with ThreadPoolExecutor(max_workers=2) as executor:
        fut_returns = executor.submit(fetch_table, urls["returns"])
        fut_rank = executor.submit(fetch_table, urls["rank"], {"Crisil Rank": "Crisil Rating"})
        df_returns = fut_returns.result()
        df_rank = fut_rank.result()

    # handle fetch_table returning an exception dict
    def interpret_fetch_result(res):
        if res is None:
            return None, None
        if isinstance(res, dict) and "error" in res:
            return None, res["error"]
        return res, None

    df_returns, err_returns = interpret_fetch_result(df_returns)
    df_rank, err_rank = interpret_fetch_result(df_rank)

    # If returns table is missing -> fail
    if df_returns is None:
        msg = "Returns table not found"
        if err_returns:
            msg += f": {err_returns}"
        return None, "error", msg

    # Merge rank if available
    combined = df_returns.copy()
    if df_rank is not None:
        # drop some duplicate columns if necessary (handled downstream)
        try:
            combined = combined.merge(df_rank, on=["Scheme Name", "Plan"], how="left")
        except Exception:
            # merging failed due to unexpected schemas; proceed with returns only
            pass

    # Keep only Regular Growth plans (if present)
    if "Plan" in combined.columns and "Scheme Name" in combined.columns:
        try:
            combined = combined[combined["Plan"] == "Regular"]
            combined = combined[combined["Scheme Name"].str.contains("Growth", case=False, na=False)]
        except Exception:
            # if filtering fails, continue but mark partial
            return combined, "partial", "Could not fully filter Plan/Scheme Name (structure changed)"
    else:
        # missing expected columns => can't reliably filter
        return combined, "partial", "Missing Plan or Scheme Name columns; returning unfiltered table"

    # Clean percent and numeric columns
    for col in combined.columns:
        if any(k in col for k in ['1W', '1M', '3M', '6M', '1Y', '2Y', '3Y', '5Y', '10Y', 'YTD', 'Return', 'Change']):
            combined[col] = pd.to_numeric(combined[col].astype(str).str.replace('%', '', regex=False), errors='coerce')
        elif combined[col].dtype == 'object':
            if combined[col].str.contains(',').any():
                combined[col] = pd.to_numeric(combined[col].str.replace(',', ''), errors='ignore')

    # final cleanup
    if combined is None or combined.empty:
        return None, "empty", "No rows after filtering/cleanup"

    combined["Category"] = category_label
    combined = combined.dropna(subset=['Scheme Name'])
    combined = combined.dropna(axis=1, how='all')

    # rename return-like columns for clarity
    def rename_return_col(col):
        col_clean = col.replace("_x", "").replace("_y", "").upper()
        mapping = {
            "1W": "Return 1W",
            "1M": "Return 1M",
            "3M": "Return 3M",
            "6M": "Return 6M",
            "YTD": "Return YTD",
            "1Y": "Return 1Y",
            "2Y": "Return 2Y",
            "3Y": "Return 3Y",
            "5Y": "Return 5Y",
            "10Y": "Return 10Y"
        }
        return mapping.get(col_clean, col_clean)

    combined.columns = [rename_return_col(c) for c in combined.columns]

    return combined, "ok", "Success"

# -------------------------
# Main app
# -------------------------
def main():
    st.title("📊 Mutual Fund Dashboard")

    # Manual refresh button (always available)
    col_refresh, col_status = st.columns([1, 4])
    with col_refresh:
        if st.button("⟳ Refresh Data (manual)"):
            # clear cached fetches and mark for refresh
            try:
                st.cache_data.clear()
            except Exception:
                pass
            st.session_state["_manual_refresh"] = True
            # small wait to ensure cache cleared
            time.sleep(0.3)
            st.experimental_rerun()

    # Show last extracted badge (green if today's extraction, red if older)
    last_extracted = st.session_state.get("last_extracted_at", None)
    last_extracted_date = st.session_state.get("_last_extracted_date", None)

    if last_extracted is not None:
        # if last extracted today -> green, otherwise orange
        badge_color = "🟢" if last_extracted_date == datetime.date.today() else "🟠"
        st.markdown(f"**{badge_color} Last Extracted:** {last_extracted}")
    else:
        st.markdown("**🔴 Last Extracted:** _Not yet extracted_")

    st.sidebar.header("🔍 Filters / Options")
    categories = {
        "All Funds": "all",
        "Flexi Cap": "flexi-cap-fund",
        "Small Cap": "small-cap-fund",
        "Mid Cap": "mid-cap-fund",
        "Large Cap": "large-cap-fund",
        "Multi Cap": "multi-cap-fund",
        "ELSS": "elss",
        "Sectoral": "sectoral-fund",
        "Index": "index-fund"
    }

    selected_category_label = st.sidebar.selectbox("Select Fund Category:", list(categories.keys()))
    run_auto = should_daily_auto_refresh()
    manual_triggered = st.session_state.pop("_manual_refresh", False)

    # If auto refresh triggered or manual triggered, we will re-scrape
    do_scrape = run_auto or manual_triggered or ("cached_scrape_done" not in st.session_state)

    # Result containers
    df_final = pd.DataFrame()
    scrape_status = {}  # category_label -> (status, message)

    if do_scrape:
        st.sidebar.info("🔄 Fetching fresh data...")
        dfs = []
        failures = {}
        for cat_label, cat_slug in categories.items():
            if cat_slug == "all":
                continue
            with st.spinner(f"Fetching {cat_label}..."):
                try:
                    df_cat, status, msg = scrape_category(cat_slug, cat_label)
                except Exception as e:
                    df_cat = None
                    status = "error"
                    msg = f"Exception: {str(e)}"

                # Record status
                scrape_status[cat_label] = (status, msg)

                if df_cat is not None and isinstance(df_cat, pd.DataFrame) and not df_cat.empty:
                    dfs.append(df_cat)
                else:
                    failures[cat_label] = (status, msg)

        # Combine all categories that returned data
        if dfs:
            df_final = pd.concat(dfs, ignore_index=True).dropna(axis=1, how='all')
            # Save extraction timestamp since at least some data was fetched
            st.session_state["last_extracted_at"] = now_str()
            st.session_state["_last_extracted_date"] = datetime.date.today()
            st.session_state["cached_scrape_done"] = True
            st.success("✅ Data fetched (partial or full). See category statuses below.")
        else:
            df_final = pd.DataFrame()
            st.session_state["cached_scrape_done"] = False
            st.error("❌ No data could be fetched for any category. See statuses below.")

        # store scrape_status for display (even if previously cached)
        st.session_state["_scrape_status"] = scrape_status

    else:
        # Use cached results if available: call scrape_category for display purposes but rely on cached fetch_table
        st.sidebar.info("🗂️ Using cached data (refresh to fetch new).")
        # If we have a cached scrape_status from previous run, reuse it
        scrape_status = st.session_state.get("_scrape_status", {})
        # Attempt to reconstruct df_final from cached fetches (if previously stored)
        # We'll try to fetch categories but these calls are cached by fetch_table
        dfs = []
        for cat_label, cat_slug in categories.items():
            if cat_slug == "all":
                continue
            try:
                df_cat, status, msg = scrape_category(cat_slug, cat_label)
            except Exception as e:
                df_cat = None
                status = "error"
                msg = f"Exception: {str(e)}"
            scrape_status[cat_label] = (status, msg)
            if df_cat is not None and not df_cat.empty:
                dfs.append(df_cat)
        if dfs:
            df_final = pd.concat(dfs, ignore_index=True).dropna(axis=1, how='all')
        st.session_state["_scrape_status"] = scrape_status

    # Sidebar: show per-category statuses (helpful)
    st.sidebar.markdown("### Category fetch status")
    for cat_label in categories.keys():
        if cat_label == "All Funds":
            continue
        status, msg = st.session_state.get("_scrape_status", {}).get(cat_label, ("unknown", "Not attempted"))
        if status == "ok":
            st.sidebar.success(f"{cat_label}: OK")
        elif status == "partial":
            st.sidebar.warning(f"{cat_label}: Partial ({msg})")
        elif status == "empty":
            st.sidebar.info(f"{cat_label}: No rows ({msg})")
        elif status == "error":
            st.sidebar.error(f"{cat_label}: Error ({msg})")
        else:
            st.sidebar.write(f"{cat_label}: {status} - {msg}")

    # Main area: show the data if we have it
    if df_final is not None and not df_final.empty:
        st.session_state["last_extracted_at"] = st.session_state.get("last_extracted_at", now_str())
        st.session_state["_last_extracted_date"] = st.session_state.get("_last_extracted_date", datetime.date.today())
        st.success(f"✅ Showing {selected_category_label} Funds ({len(df_final)} schemes total across fetched categories)")
        st.dataframe(df_final, use_container_width=True, height=650, hide_index=True)

        csv = df_final.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Download as CSV", data=csv,
                           file_name=f"{selected_category_label.lower().replace(' ', '_')}_funds.csv", mime="text/csv")
    else:
        st.warning("⚠️ No combined data to show. Check category statuses in the sidebar and try Refresh.")

    # Footer - small help text
    st.markdown("---")
    st.markdown(
        "ℹ️ The app auto-refreshes once daily after 9:00 AM (local time). Use the Refresh button to force a reload. "
        "If Moneycontrol changes their page structure, category fetch may fail — check the sidebar for details."
    )

if __name__ == "__main__":
    main()
