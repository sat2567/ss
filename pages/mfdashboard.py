import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import random
import time
import re
from datetime import datetime

# Config
BASE_URL = "https://www.moneycontrol.com/mutual-funds/performance-tracker"
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edg/125.0 Chrome/125.0 Safari/537.36",
]
HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Referer": "https://www.moneycontrol.com/",
}
CATEGORIES = {
    "All Funds": "all",
    "Flexi Cap": "flexi-cap-fund",
    "Small Cap": "small-cap-fund",
    "Mid Cap": "mid-cap-fund",
    "Large Cap": "large-cap-fund",
    "Multi Cap": "multi-cap-fund",
    "ELSS": "elss",
    "Sectoral": "sectoral-fund",
    "Index": "index-fund",
    "Large & Midcap": "large-and-midcap-fund",
}
RETURN_COLUMNS = ["1W", "1M", "3M", "6M", "YTD", "1Y", "2Y", "3Y", "5Y", "10Y"]

st.set_page_config(page_title="Mutual Fund Dashboard", page_icon="📊", layout="wide")


def create_session():
    retry_strategy = Retry(
        total=3,
        backoff_factor=0.8,
        status_forcelist=[403, 429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.headers.update(HEADERS)
    session.headers["User-Agent"] = random.choice(USER_AGENTS)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    # Seed cookies
    try:
        session.get("https://www.moneycontrol.com/", timeout=10)
        time.sleep(random.uniform(0.2, 0.6))
    except Exception:
        pass
    return session


def normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    def clean_col(name):
        name = str(name).lower()
        name = re.sub(r"[^a-z0-9]+", " ", name).strip()
        return name

    mapping = {}
    for col in df.columns:
        cclean = clean_col(col)
        if cclean in ["scheme name", "schemename", "scheme", "fund name", "fund"]:
            mapping[col] = "Scheme Name"
        elif cclean in ["plan", "plan type", "plantype", "plan name", "planname"]:
            mapping[col] = "Plan"
        elif cclean in ["option", "scheme option", "option name"]:
            mapping[col] = "Option"
        elif "crisil" in cclean and ("rank" in cclean or "rating" in cclean):
            mapping[col] = "Crisil Rating"
    df.rename(columns=mapping, inplace=True)
    return df


def clean_numeric_columns(df):
    for col in df.columns:
        if any(x in col for x in RETURN_COLUMNS + ["Return", "Change", "YTD"]):
            df[col] = (
                df[col].astype(str)
                .str.replace("%", "", regex=False)
                .str.replace(r"[^0-9+.\-]", "", regex=True)
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data(ttl=3600)
def fetch_table(url: str):
    session = create_session()
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", class_="mctable1")
        if not table:
            # fallback parse first table found
            table = soup.find("table")
        if not table:
            return pd.DataFrame()
        df_list = pd.read_html(str(table))
        if not df_list:
            return pd.DataFrame()
        df = df_list[0]
        df = normalize_headers(df)
        df = clean_numeric_columns(df)
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def scrape_category(slug: str, apply_filters=True):
    returns_url = urljoin(BASE_URL + "/", f"returns/{slug}.html")
    ranks_url = urljoin(BASE_URL + "/", f"ranks/{slug}.html")
    with ThreadPoolExecutor(max_workers=2) as executor:
        fut_ret = executor.submit(fetch_table, returns_url)
        fut_rank = executor.submit(fetch_table, ranks_url)
        df_returns = fut_ret.result()
        df_ranks = fut_rank.result()

    if df_returns.empty:
        return pd.DataFrame()
    # Merge ranks if available
    if not df_ranks.empty:
        if "Scheme Name" in df_returns.columns and "Scheme Name" in df_ranks.columns:
            keys = ["Scheme Name"]
            if "Plan" in df_returns.columns and "Plan" in df_ranks.columns:
                keys.append("Plan")
            df_returns = df_returns.merge(
                df_ranks.drop(columns=["Category Name"], errors="ignore"), on=keys, how="left"
            )

    # Conditionally apply filters based on user input and category
    if apply_filters and slug != "large-and-midcap-fund":
        if "Plan" in df_returns.columns:
            df_returns = df_returns[
                df_returns["Plan"].str.lower().str.contains("regular", na=False)
            ]
        if "Option" in df_returns.columns and df_returns["Option"].str.lower().str.contains("growth", na=False).any():
            df_returns = df_returns[
                df_returns["Option"].str.lower().str.contains("growth", na=False)
            ]
        elif "Scheme Name" in df_returns.columns and df_returns["Scheme Name"].str.lower().str.contains("growth", na=False).any():
            df_returns = df_returns[
                df_returns["Scheme Name"].str.lower().str.contains("growth", na=False)
            ]

    df_returns["Category"] = slug.replace("-", " ").title()
    df_returns = df_returns.dropna(subset=["Scheme Name"])
    df_returns.reset_index(drop=True, inplace=True)
    return df_returns


def aggregate_categories(selected_categories, apply_filters=True):
    dataframes = []
    with ThreadPoolExecutor(max_workers=len(selected_categories)) as executor:
        futures = {
            executor.submit(scrape_category, CATEGORIES[cat], apply_filters): cat for cat in selected_categories
        }
        for fut in as_completed(futures):
            df = fut.result()
            if not df.empty:
                dataframes.append(df)
    if not dataframes:
        return pd.DataFrame()
    return pd.concat(dataframes, ignore_index=True)


def main():
    st.title("📊 Mutual Fund Dashboard")

    st.sidebar.header("Filters")
    if st.sidebar.button("Refresh Data"):
        st.cache_data.clear()
    debug_mode = st.sidebar.checkbox("Show Diagnostics", False)
    use_headless = st.sidebar.checkbox("Use Headless Browser Fallback (Playwright)", False)
    st.session_state.use_headless = use_headless

    category = st.sidebar.selectbox("Fund Category", list(CATEGORIES.keys()))

    # Optional filter toggles
    if category == "Large & Midcap":
        apply_filters = st.sidebar.checkbox(
            "Apply 'Regular Plan' and 'Growth Option' filters (may filter out many funds)",
            value=False,
        )
    else:
        apply_filters = st.sidebar.checkbox(
            "Apply 'Regular Plan' and 'Growth Option' filters",
            value=True,
        )

    if category == "All Funds":
        selected_cats = st.sidebar.multiselect(
            "Select categories",
            [k for k in CATEGORIES.keys() if k != "All Funds"],
            default=["Flexi Cap", "Large Cap", "Mid Cap"],
        )
        with st.spinner("Fetching data for selected categories..."):
            data = aggregate_categories(selected_cats, apply_filters=apply_filters)
    else:
        with st.spinner(f"Fetching {category} funds data..."):
            data = scrape_category(CATEGORIES[category], apply_filters=apply_filters)

    if debug_mode:
        st.write("### Debug Information")
        st.json(
            {
                "Selected Category": category,
                "Use Headless": use_headless,
                "Funds Count": len(data),
                "Columns": list(data.columns) if not data.empty else [],
                "Sample Data": data.head(5).to_dict(orient="records") if not data.empty else [],
            }
        )

    if not data.empty:
        st.success(f"Showing {category} funds: {len(data)} results.")
        search_text = st.text_input("Search Scheme Name")
        min_return_1y = st.slider("Minimum 1 Year Return %", -50.0, 100.0, -50.0, 0.5)

        filtered_data = data
        if search_text:
            filtered_data = filtered_data[
                filtered_data["Scheme Name"].str.contains(search_text, case=False, na=False)
            ]
        if "Return 1Y" in filtered_data.columns:
            filtered_data = filtered_data[filtered_data["Return 1Y"].fillna(-1e9) >= min_return_1y]

        st.dataframe(filtered_data, height=600, use_container_width=True)

        csv_data = filtered_data.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download data as CSV",
            data=csv_data,
            file_name=f"{category.lower().replace(' ', '_')}_mutual_funds.csv",
            mime="text/csv",
        )

        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    else:
        st.error("No data could be fetched. Please try again later or adjust filters.")


if __name__ == "__main__":
    main()
