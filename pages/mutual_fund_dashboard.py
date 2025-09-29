import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

import datetime
import time

# --- Utility for quick web scraping ---
def get_live_gold_price():
    """Scrape current India and US gold prices."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        # India Gold Price (source: bullions.co.in)
        response = requests.get("https://bullions.co.in", headers=headers, timeout=8)
        soup = BeautifulSoup(response.text, "html.parser")
        ind_gold_tag = soup.find("div", {"id": "gold24"})
        us_gold_tag = soup.find("div", {"id": "us_gold"})
        india_gold = ind_gold_tag.text.strip() if ind_gold_tag else "N/A"
        us_gold = us_gold_tag.text.strip() if us_gold_tag else "N/A"
    except Exception:
        india_gold = "Error"
        us_gold = "Error"
    return india_gold, us_gold

def get_us_indices():
    """Scrape Dow Jones, S&P500, Nasdaq live values."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        # US Indices (source: moneycontrol.com)
        response = requests.get("https://www.moneycontrol.com/markets/global-indices/", headers=headers, timeout=8)
        soup = BeautifulSoup(response.text, "html.parser")
        # Example parsing (adapt as necessary):
        # Find index values using actual selectors
        indices = {"Dow Jones": "N/A", "S&P 500": "N/A", "Nasdaq": "N/A"}
        rows = soup.find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) > 1:
                name = cols[0].text.strip()
                price = cols[1].text.strip()
                if "Dow" in name:
                    indices["Dow Jones"] = price
                elif "S&P" in name:
                    indices["S&P 500"] = price
                elif "Nasdaq" in name:
                    indices["Nasdaq"] = price
    except Exception:
        indices = {"Dow Jones": "Error", "S&P 500": "Error", "Nasdaq": "Error"}
    return indices

# --- Auto refresh logic ---
def should_refresh():
    """Check if data should refresh (every day after 9 AM)."""
    now = datetime.datetime.now()
    today_9am = now.replace(hour=9, minute=0, second=0, microsecond=0)
    if now >= today_9am:
        if "last_refresh_date" not in st.session_state or st.session_state["last_refresh_date"] != now.date():
            st.session_state["last_refresh_date"] = now.date()
            st.cache_data.clear()
            return True
    return False

@st.cache_data(ttl=3600)
def fetch_table(url, rename_map=None):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/91.0.4472.124 Safari/537.36'
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
        st.error(f"Error fetching data from {url}: {str(e)}")
        return None

def scrape_category(category, category_label):
    base = "https://www.moneycontrol.com/mutual-funds/performance-tracker"
    urls = {
        "returns": f"{base}/returns/{category}.html",
        "rank": f"{base}/ranks/{category}.html"
    }
    with ThreadPoolExecutor() as executor:
        futures = {
            "returns": executor.submit(fetch_table, urls["returns"]),
            "rank": executor.submit(fetch_table, urls["rank"], {"Crisil Rank": "Crisil Rating"})
        }
        df_returns = futures["returns"].result()
        df_rank = futures["rank"].result()
    if df_returns is None:
        return pd.DataFrame()
    def drop_common(df, common_cols):
        if df is not None:
            return df.drop(columns=[c for c in common_cols if c in df.columns], errors="ignore")
        return None
    rank_df = drop_common(df_rank, ["Category Name", "Crisil Rating"]) if df_rank is not None else None
    combined = df_returns
    if rank_df is not None and not rank_df.empty and 'Scheme Name' in rank_df.columns and 'Plan' in rank_df.columns:
        combined = combined.merge(rank_df, on=["Scheme Name", "Plan"], how="left")
    if 'Plan' in combined.columns and 'Scheme Name' in combined.columns:
        combined = combined[combined["Plan"] == "Regular"]
        combined = combined[combined["Scheme Name"].str.contains("Growth", case=False, na=False)]
    else:
        return pd.DataFrame()
    for col in combined.columns:
        if any(period in col for period in ['1W', '1M', '3M', '6M', '1Y', '2Y', '3Y', '5Y', '10Y', 'YTD', 'Return', 'Change']):
            combined[col] = pd.to_numeric(
                combined[col].astype(str).str.replace('%', '', regex=False),
                errors='coerce'
            )
        elif combined[col].dtype == 'object':
            if combined[col].str.contains(',').any():
                combined[col] = pd.to_numeric(
                    combined[col].str.replace(',', ''),
                    errors='ignore'
                )
    if not combined.empty:
        combined["Category"] = category_label
        combined = combined.dropna(subset=['Scheme Name'])
        combined = combined.dropna(axis=1, how='all')
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
        return combined
    return pd.DataFrame()

def main():
    if should_refresh():
        st.experimental_rerun()
    st.title("📊 Mutual Fund Dashboard")
    

    # MARKET HIGHLIGHTS SECTION
    india_gold, us_gold = get_live_gold_price()
    us_indices = get_us_indices()
    st.markdown("## 🟨 Market Highlights")
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Gold (India, 24K/g)", value=india_gold)
        st.metric(label="Gold (US, $/oz)", value=us_gold)
    with col2:
        st.metric(label="US Dow Jones", value=us_indices.get("Dow Jones", "N/A"))
        st.metric(label="S&P 500", value=us_indices.get("S&P 500", "N/A"))
        st.metric(label="NASDAQ", value=us_indices.get("Nasdaq", "N/A"))

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
    st.sidebar.header("🔍 Filters")
    selected_category = st.sidebar.selectbox("Select Fund Category:", list(categories.keys()))
    if categories[selected_category] == "all":
        with st.spinner("Fetching all categories..."):
            dfs = []
            for cat_name, cat_slug in categories.items():
                if cat_slug != "all":
                    df_cat = scrape_category(cat_slug, cat_name)
                    if df_cat is not None and not df_cat.empty:
                        dfs.append(df_cat)
            if dfs:
                df = pd.concat(dfs, ignore_index=True)
                df = df.dropna(axis=1, how='all')
            else:
                df = pd.DataFrame()
    else:
        with st.spinner(f"Fetching {selected_category} funds data..."):
            df = scrape_category(categories[selected_category], selected_category)
            if not df.empty:
                df = df.dropna(axis=1, how='all')
    if df is not None and not df.empty:
        st.success(f"✅ Showing {selected_category} Funds ({len(df)} schemes)")
        st.dataframe(
            df,
            use_container_width=True,
            height=600,
            hide_index=True
        )
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"{selected_category.lower().replace(' ', '_')}_funds.csv",
            mime="text/csv"
        )
    else:
        st.error("⚠️ Could not fetch data. Please try again later.")

if __name__ == "__main__":
    main()
