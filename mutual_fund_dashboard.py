import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import time

# Configure Streamlit page
st.set_page_config(
    page_title="Mutual Fund Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS for better styling
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stDataFrame {
        width: 100%;
    }
    .stDownloadButton button {
        width: 100%;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Cache the data to prevent re-fetching on every interaction
@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_table(url, rename_map=None):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
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
        "nav": f"{base}/navs/{category}.html",
        "portfolio": f"{base}/portfolioassets/{category}.html",
        "risk": f"{base}/risk-ratios/{category}.html",
        "rank": f"{base}/ranks/{category}.html"
    }

    # Fetch all tables in parallel
    with ThreadPoolExecutor() as executor:
        futures = {
            "returns": executor.submit(fetch_table, urls["returns"]),
            "nav": executor.submit(fetch_table, urls["nav"]),
            "portfolio": executor.submit(fetch_table, urls["portfolio"]),
            "risk": executor.submit(fetch_table, urls["risk"]),
            "rank": executor.submit(fetch_table, urls["rank"], {"Crisil Rank": "Crisil Rating"})
        }
        
        # Get results
        df_returns = futures["returns"].result()
        df_nav = futures["nav"].result()
        df_portfolio = futures["portfolio"].result()
        df_risk = futures["risk"].result()
        df_rank = futures["rank"].result()

    if df_returns is None:
        return None

    # Function to drop common columns
    def drop_common(df, common_cols):
        if df is not None:
            return df.drop(columns=[c for c in common_cols if c in df.columns], 
                         errors="ignore")
        return None

    # Process each dataframe
    nav_df = drop_common(df_nav, ["Category Name", "Crisil Rating", "AuM (Cr)"])
    portfolio_df = drop_common(df_portfolio, ["Category Name", "Crisil Rating"])
    risk_df = drop_common(df_risk, ["Category Name", "Crisil Rating"])
    rank_df = drop_common(df_rank, ["Category Name", "Crisil Rating"])

    # Merge all dataframes
    combined = df_returns
    for df in [nav_df, portfolio_df, risk_df, rank_df]:
        if df is not None and not df.empty and 'Scheme Name' in df.columns and 'Plan' in df.columns:
            combined = combined.merge(df, on=["Scheme Name", "Plan"], how="left")

    # Filter only Regular + Growth plans
    if 'Plan' in combined.columns and 'Scheme Name' in combined.columns:
        combined = combined[combined["Plan"] == "Regular"]
        combined = combined[combined["Scheme Name"].str.contains("Growth", case=False, na=False)]
    else:
        return None

    # Clean numeric columns
    numeric_columns = {
        "1W": ("%", "", float),
        "AuM (Cr)": (",", "", float),
        "3M": ("%", "", float),
        "6M": ("%", "", float),
        "1Y": ("%", "", float),
        "3Y": ("%", "", float),
        "5Y": ("%", "", float),
        "Crisil Rating Num": (r"(\d+)", "", float)
    }

    for col, (old, new, dtype) in numeric_columns.items():
        if col in combined.columns:
            try:
                if col == "Crisil Rating Num":
                    combined[col] = combined["Crisil Rating"].str.extract(r"(\d+)").astype(float)
                else:
                    combined[col] = combined[col].str.replace(old, new, regex=False).astype(dtype)
            except:
                pass

    # Add category info
    combined["Category"] = category_label
    return combined

def main():
    st.title("📊 Mutual Fund Dashboard")
    st.write("Fetching live mutual fund data from Moneycontrol...")

    # Category mapping
    categories = {
        "Small Cap": "small-cap-fund",
        "Mid Cap": "mid-cap-fund",
        "Large Cap": "large-cap-fund",
        "Flexi Cap": "flexi-cap-fund",
        "ELSS": "elss",
        "Sectoral": "sectoral-fund",
        "Index": "index-fund"
    }

    # Sidebar for filters
    st.sidebar.header("🔍 Filters")
    
    # Category selection
    selected_category = st.sidebar.selectbox(
        "Select Fund Category:",
        list(categories.keys())
    )

    # Scrape data with loading indicator
    with st.spinner(f"Fetching {selected_category} funds data..."):
        df = scrape_category(categories[selected_category], selected_category)

    if df is not None and not df.empty:
        st.success(f"✅ Showing {selected_category} Funds ({len(df)} schemes)")

        # Additional filters
        st.sidebar.subheader("Refine Results")
        
        # AUM Filter
        if "AuM (Cr)" in df.columns:
            min_aum, max_aum = df["AuM (Cr)"].min(), df["AuM (Cr)"].max()
            aum_range = st.sidebar.slider(
                "AUM (in Cr)", 
                min_value=float(min_aum), 
                max_value=float(max_aum), 
                value=(float(min_aum), float(max_aum))
            )
            df = df[(df["AuM (Cr)"] >= aum_range[0]) & (df["AuM (Cr)"] <= aum_range[1])]

        # CRISIL Rating Filter
        if "Crisil Rating" in df.columns:
            crisil_ratings = df["Crisil Rating"].dropna().unique()
            selected_ratings = st.sidebar.multiselect(
                "CRISIL Rating",
                options=sorted(crisil_ratings),
                default=sorted(crisil_ratings)
            )
            df = df[df["Crisil Rating"].isin(selected_ratings)]

        # Display the dataframe
        st.dataframe(
            df,
            use_container_width=True,
            height=600,
            hide_index=True,
            column_config={
                "Scheme Name": st.column_config.TextColumn("Scheme Name", width="large"),
                "1W": st.column_config.NumberColumn("1W Return (%)", format="%.2f%%"),
                "AuM (Cr)": st.column_config.NumberColumn("AUM (Cr)", format="₹%.2f")
            }
        )

        # Download button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"{selected_category.lower().replace(' ', '_')}_funds.csv",
            mime="text/csv"
        )

        # Show some statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Funds", len(df))
        with col2:
            if "AuM (Cr)" in df.columns:
                st.metric("Total AUM (Cr)", f"₹{df['AuM (Cr)'].sum():,.2f}")
        with col3:
            if "1W" in df.columns:
                avg_return = df["1W"].mean()
                st.metric("Avg 1W Return", f"{avg_return:.2f}%")
    else:
        st.error("⚠️ Could not fetch data. Please try again later.")

if __name__ == "__main__":
    main()
