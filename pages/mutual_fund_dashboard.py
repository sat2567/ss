import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import datetime

# --- Auto refresh daily after 9 AM ---
def should_refresh():
    now = datetime.datetime.now()
    refresh_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
    if now >= refresh_time:
        last_refresh = st.session_state.get("last_refresh_date")
        if last_refresh != now.date():
            st.session_state["last_refresh_date"] = now.date()
            st.cache_data.clear()
            return True
    return False

@st.cache_data(ttl=3600)
def fetch_table(url, rename_columns=None):
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
        data = [
            [cell.get_text(strip=True) for cell in row.find_all(["td", "th"])]
            for row in rows
        ]
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            if rename_columns:
                df.rename(columns=rename_columns, inplace=True)
            return df
        return None
    except Exception as e:
        st.error(f"Error fetching data from {url}: {e}")
        return None

def scrape_category(cat_slug, cat_label):
    base_url = "https://www.moneycontrol.com/mutual-funds/performance-tracker"
    urls = {
        "returns": f"{base_url}/returns/{cat_slug}.html",
        "rank": f"{base_url}/ranks/{cat_slug}.html",
    }

    with ThreadPoolExecutor() as executor:
        future_returns = executor.submit(fetch_table, urls["returns"])
        future_rank = executor.submit(fetch_table, urls["rank"], {"Crisil Rank": "Crisil Rating"})
        df_returns = future_returns.result()
        df_rank = future_rank.result()

    if df_returns is None:
        return pd.DataFrame()

    def drop_columns(df, cols_to_drop):
        if df is not None:
            return df.drop(columns=[col for col in cols_to_drop if col in df.columns], errors="ignore")
        return None

    rank_df_trimmed = drop_columns(df_rank, ["Category Name", "Crisil Rating"]) if df_rank is not None else None

    combined = df_returns
    if rank_df_trimmed is not None and not rank_df_trimmed.empty:
        if "Scheme Name" in rank_df_trimmed.columns and "Plan" in rank_df_trimmed.columns:
            combined = combined.merge(rank_df_trimmed, on=["Scheme Name", "Plan"], how="left")

    if {"Plan", "Scheme Name"}.issubset(combined.columns):
        combined = combined[combined["Plan"] == "Regular"]
        combined = combined[combined["Scheme Name"].str.contains("Growth", case=False, na=False)]
    else:
        return pd.DataFrame()

    # Convert percentage and numeric columns
    for col in combined.columns:
        if any(p in col for p in ['1W', '1M', '3M', '6M', '1Y', '2Y', '3Y', '5Y', '10Y', 'YTD', 'Return', 'Change']):
            combined[col] = pd.to_numeric(combined[col].astype(str).str.replace('%', ''), errors='coerce')
        elif combined[col].dtype == 'object' and combined[col].str.contains(',').any():
            combined[col] = pd.to_numeric(combined[col].str.replace(',', ''), errors='ignore')

    if combined.empty:
        return pd.DataFrame()

    combined["Category"] = cat_label
    combined.dropna(subset=['Scheme Name'], inplace=True)
    combined.dropna(axis=1, how='all', inplace=True)

    def clean_column_name(col_name):
        name = col_name.replace("_x", "").replace("_y", "").upper()
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
            "10Y": "Return 10Y",
        }
        return mapping.get(name, name)

    combined.columns = [clean_column_name(c) for c in combined.columns]
    return combined


def main():
    if should_refresh():
        st.session_state['needs_refresh'] = True

    if st.session_state.get('needs_refresh', False):
        st.session_state['needs_refresh'] = False
        st.experimental_rerun()

    st.title("📊 Mutual Fund Dashboard")

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

    if categories[selected_category] == "all":
        with st.spinner("Fetching all categories..."):
            all_dfs = []
            for name, slug in categories.items():
                if slug != "all":
                    df_cat = scrape_category(slug, name)
                    if df_cat is not None and not df_cat.empty:
                        all_dfs.append(df_cat)
            if all_dfs:
                df = pd.concat(all_dfs, ignore_index=True)
                df.dropna(axis=1, how='all', inplace=True)
            else:
                df = pd.DataFrame()
    else:
        with st.spinner(f"Fetching {selected_category} funds data..."):
            df = scrape_category(categories[selected_category], selected_category)
            if not df.empty:
                df.dropna(axis=1, how='all', inplace=True)

    if df is not None and not df.empty:
        st.success(f"✅ Showing {selected_category} Funds ({len(df)})")
        st.dataframe(df, use_container_width=True, height=600, hide_index=True)
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download as CSV",
            data=csv_data,
            file_name=f"{selected_category.lower().replace(' ', '_')}_funds.csv",
            mime="text/csv",
        )
    else:
        st.error("⚠️ Could not fetch data. Please try again later.")


if __name__ == "__main__":
    main()
