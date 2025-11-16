import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import datetime

# -------------------------------------------------------
#  🔄 AUTO-REFRESH LOGIC (SAFE VERSION — NO infinite rerun)
# -------------------------------------------------------
def auto_refresh_if_needed():
    """Refresh only ONCE per day after 9 AM."""
    now = datetime.datetime.now()
    today = now.date()

    if "last_extract" not in st.session_state:
        st.session_state["last_extract"] = None

    if "auto_refresh_done" not in st.session_state:
        st.session_state["auto_refresh_done"] = False

    # If already refreshed today after 9AM → do nothing
    if st.session_state["auto_refresh_done"] is True:
        return False

    # If current time >= 9AM and we have not refreshed yet today
    today_9am = now.replace(hour=9, minute=0, second=0, microsecond=0)
    
    if now >= today_9am:
        st.cache_data.clear()
        st.session_state["auto_refresh_done"] = True
        return True  # trigger manual rerun by caller

    return False


# -------------------------------------------------------
#   🧹 Fetch Table
# -------------------------------------------------------
@st.cache_data(ttl=3600)
def fetch_table(url, rename_map=None):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", class_="mctable1")

        if not table:
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
        st.error(f"Error fetching: {url} → {str(e)}")
        return None


# -------------------------------------------------------
#  🏷 Category Scraper
# -------------------------------------------------------
def scrape_category(category, category_label):
    base = "https://www.moneycontrol.com/mutual-funds/performance-tracker"
    urls = {
        "returns": f"{base}/returns/{category}.html",
        "rank": f"{base}/ranks/{category}.html",
    }

    with ThreadPoolExecutor() as executor:
        fut_ret = executor.submit(fetch_table, urls["returns"])
        fut_rank = executor.submit(fetch_table, urls["rank"], {"Crisil Rank": "Crisil Rating"})

    df_returns = fut_ret.result()
    df_rank = fut_rank.result()

    if df_returns is None:
        return pd.DataFrame()

    # Drop common cols from ranks
    def drop_common(df, common_cols):
        if df is None:
            return None
        return df.drop(columns=[c for c in common_cols if c in df.columns], errors="ignore")

    rank_df = drop_common(df_rank, ["Category Name", "Crisil Rating"])

    combined = df_returns

    if (
        rank_df is not None
        and not rank_df.empty
        and "Scheme Name" in rank_df.columns
        and "Plan" in rank_df.columns
    ):
        combined = combined.merge(rank_df, on=["Scheme Name", "Plan"], how="left")

    # Filter only Regular + Growth
    if "Plan" not in combined.columns or "Scheme Name" not in combined.columns:
        return pd.DataFrame()

    combined = combined[combined["Plan"] == "Regular"]
    combined = combined[combined["Scheme Name"].str.contains("Growth", case=False, na=False)]

    # Convert return fields
    for col in combined.columns:
        if any(period in col for period in ["1W", "1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "10Y", "YTD"]):
            combined[col] = (
                combined[col]
                .astype(str)
                .str.replace("%", "", regex=False)
                .str.replace(",", "")
            )
            combined[col] = pd.to_numeric(combined[col], errors="coerce")

    combined["Category"] = category_label
    combined = combined.dropna(subset=["Scheme Name"])
    combined = combined.dropna(axis=1, how="all")

    return combined


# -------------------------------------------------------
#  🎯 MAIN APP
# -------------------------------------------------------
def main():

    # 🔄 Auto refresh check
    if auto_refresh_if_needed():
        st.experimental_rerun()

    # ----------------------------
    #  🏁 HEADER WITH TIMESTAMP
    # ----------------------------
    st.title("📊 Mutual Fund Dashboard")

    last_extracted = st.session_state.get("last_extract", None)

    if last_extracted:
        st.markdown(
            f"🟢 **Last Extracted:** {last_extracted.strftime('%d-%m-%Y %I:%M %p')}"
        )
    else:
        st.markdown("🟠 **Last Extracted:** Not yet extracted")

    # ----------------------------
    #  🔄 Refresh Button
    # ----------------------------
    refresh = st.button("🔄 Refresh Data")

    if refresh:
        st.cache_data.clear()
        st.session_state["auto_refresh_done"] = True
        st.session_state["last_extract"] = datetime.datetime.now()
        st.experimental_rerun()

    # ----------------------------
    #  🧭 Sidebar Category
    # ----------------------------
    categories = {
        "All Funds": "all",
        "Flexi Cap": "flexi-cap-fund",
        "Small Cap": "small-cap-fund",
        "Mid Cap": "mid-cap-fund",
        "Large Cap": "large-cap-fund",
        "Multi Cap": "multi-cap-fund",
        "ELSS": "elss",
        "Sectoral": "sectoral-fund",
        "Index": "index-fund",
    }

    st.sidebar.header("🔍 Filters")
    selected_category = st.sidebar.selectbox("Select Fund Category:", list(categories.keys()))

    # ----------------------------
    #  📥 Fetch Data
    # ----------------------------
    if categories[selected_category] == "all":
        dfs = []
        st.info("Fetching all categories…")

        for cat_name, slug in categories.items():
            if slug == "all":
                continue

            df_cat = scrape_category(slug, cat_name)
            if df_cat is not None and not df_cat.empty:
                dfs.append(df_cat)

        if dfs:
            df = pd.concat(dfs, ignore_index=True)
        else:
            df = pd.DataFrame()

    else:
        df = scrape_category(categories[selected_category], selected_category)

    # ----------------------------
    #  📊 Display Results
    # ----------------------------
    if df is not None and not df.empty:
        st.success(f"Showing **{selected_category}** — {len(df)} schemes")
        st.dataframe(df, use_container_width=True, hide_index=True, height=600)

        # Download CSV
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"{selected_category.replace(' ', '_')}.csv",
            mime="text/csv",
        )

        # Update last extract time
        st.session_state["last_extract"] = datetime.datetime.now()

    else:
        st.error("⚠️ No data available for this category.")


# Run App
if __name__ == "__main__":
    main()
