import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import numpy as np

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

    # Clean numeric columns
    for col in combined.columns:
        if any(period in col for period in ['1W', '1M', '3M', '6M', '1Y', '3Y', '5Y', 'Return', 'Change']):
            combined[col] = pd.to_numeric(combined[col].astype(str).str.rstrip('%'), errors='coerce')
        elif combined[col].dtype == 'object' and combined[col].str.contains(',').any():
            combined[col] = pd.to_numeric(combined[col].str.replace(',', ''), errors='ignore')

    if not combined.empty:
        combined["Category"] = category_label
        important_columns = [
            'Scheme Name', 'Plan', 'Category', 'NAV', 'AUM', 'Expense Ratio',
            '1W', '1M', '3M', '6M', '1Y', '3Y', '5Y', 'Crisil Rank',
            'Risk Level', 'Exit Load', 'Min SIP', 'Min Lumpsum', 'Launch Date'
        ]
        available_columns = [col for col in important_columns if col in combined.columns]
        other_columns = [col for col in combined.columns if col not in important_columns]
        combined = combined[available_columns + other_columns]
        combined.columns = [col.replace('_', ' ').title() for col in combined.columns]
        combined = combined.dropna(subset=['Scheme Name'])
        return combined

    return pd.DataFrame()


def scrape_category_ranks(category):
    try:
        url = f"https://www.moneycontrol.com/mutual-funds/performance-tracker/ranks/{category}.html"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'mctable1'})
        if not table:
            return None

        headers = [th.get_text(strip=True) for th in table.find('thead').find_all('th')]
        rows = []
        for tr in table.find('tbody').find_all('tr'):
            row = [td.get_text(strip=True) for td in tr.find_all('td')]
            if len(row) == len(headers):
                rows.append(row)
        if not rows:
            return None

        df = pd.DataFrame(rows, columns=headers)
        if 'Plan' in df.columns and 'Scheme Name' in df.columns:
            df = df[df['Plan'] == 'Regular']
            df = df[df['Scheme Name'].str.contains('Growth', case=False, na=False)]

        rank_columns = [col for col in df.columns if 'rank' in col.lower()]
        for col in rank_columns:
            df[col] = pd.to_numeric(df[col].str.extract(r'(\d+)', expand=False), errors='coerce')

        return df[['Scheme Name'] + rank_columns].dropna(how='all', axis=1)
    except Exception as e:
        st.error(f"Error fetching ranking data: {str(e)}")
        return None


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
                    df = scrape_category(cat_slug, cat_name)
                    if df is not None and not df.empty:
                        dfs.append(df)
            df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
    else:
        with st.spinner(f"Fetching {selected_category} funds data..."):
            df = scrape_category(categories[selected_category], selected_category)

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

