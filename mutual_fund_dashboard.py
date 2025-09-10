import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

# ========== SCRAPING HELPERS ==========

@st.cache_data(ttl=3600)  # Cache for 1 hour
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

    # Convert numeric columns
    for col in combined.columns:
        if any(period in col for period in ['1W', '1M', '3M', '6M', '1Y', '2Y', '3Y', '5Y', '10Y', 'Ytd', 'Return', 'Change']):
            combined[col] = pd.to_numeric(combined[col].astype(str).str.rstrip('%'), errors='coerce')
        elif combined[col].dtype == 'object' and combined[col].str.contains(',').any():
            combined[col] = pd.to_numeric(combined[col].str.replace(',', ''), errors='ignore')

    if not combined.empty:
        combined["Category"] = category_label

        # ✅ Standardize return column names
        rename_map = {
            '1W': 'Return_1W', '1M': 'Return_1M', '3M': 'Return_3M', '6M': 'Return_6M',
            'Ytd': 'Return_YTD', '1Y': 'Return_1Y', '2Y': 'Return_2Y', '3Y': 'Return_3Y',
            '5Y': 'Return_5Y', '10Y': 'Return_10Y'
        }
        combined.rename(columns=lambda c: rename_map.get(c.replace('_x', '').replace('_y', ''), c), inplace=True)

        # Drop duplicate columns
        combined = combined.loc[:, ~combined.columns.duplicated()]

        # Drop columns that are fully None/NaN
        combined = combined.dropna(axis=1, how='all')

        return combined

    return pd.DataFrame()


# ========== MAIN DASHBOARD ==========

def main():
    st.title("📊 Mutual Fund Dashboard")
    st.write("Fetching live mutual fund data from Moneycontrol...")

    categories = {
        "All Funds": "all",
        "Flexi Cap": "flexi-cap-fund",
        "Small Cap": "small-cap-fund",
        "Mid Cap": "mid-cap-fund",
        "Large Cap": "large-cap-fund",
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

                # Remove duplicates and None-only columns
                df = df.loc[:, ~df.columns.duplicated()]
                df = df.dropna(axis=1, how='all')

                # ✅ Final cleaned set of columns
                keep_cols = [
                    'Scheme Name', 'Category', 'NAV', 'AUM', 'Expense Ratio',
                    'Return_1W', 'Return_1M', 'Return_3M', 'Return_6M',
                    'Return_YTD', 'Return_1Y', 'Return_2Y', 'Return_3Y',
                    'Return_5Y', 'Return_10Y',
                    'Crisil Rank', 'Risk Level', 'Exit Load',
                    'Min SIP', 'Min Lumpsum', 'Launch Date'
                ]
                df = df[[c for c in keep_cols if c in df.columns]]
            else:
                df = pd.DataFrame()
    else:
        with st.spinner(f"Fetching {selected_category} funds data..."):
            df = scrape_category(categories[selected_category], selected_category)

            if not df.empty:
                # Keep only relevant columns
                keep_cols = [
                    'Scheme Name', 'Category', 'NAV', 'AUM', 'Expense Ratio',
                    'Return_1W', 'Return_1M', 'Return_3M', 'Return_6M',
                    'Return_YTD', 'Return_1Y', 'Return_2Y', 'Return_3Y',
                    'Return_5Y', 'Return_10Y',
                    'Crisil Rank', 'Risk Level', 'Exit Load',
                    'Min SIP', 'Min Lumpsum', 'Launch Date'
                ]
                df = df[[c for c in keep_cols if c in df.columns]]

    if df is not None and not df.empty:
        st.success(f"✅ Showing {selected_category} Funds ({len(df)} schemes)")
        st.dataframe(df, use_container_width=True, height=600, hide_index=True)

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
