import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime
import re
import random
import time

st.set_page_config(page_title="Mutual Fund Dashboard", page_icon="📊", layout="wide")

BASE = "https://www.moneycontrol.com/mutual-funds/performance-tracker"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Referer": "https://www.moneycontrol.com/",
    "sec-ch-ua": '"Chromium";v="124", "Not=A?Brand";v="99", "Google Chrome";v="124"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-User": "?1",
    "Sec-Fetch-Dest": "document",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}

UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edg/125.0 Chrome/125.0 Safari/537.36",
]

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
    "Large & Midcap": "large-and-midcap-fund"
}

RETURN_COLS = ["1W", "1M", "3M", "6M", "YTD", "1Y", "2Y", "3Y", "5Y", "10Y"]


def _requests_session():
    retry = Retry(
        total=3,
        backoff_factor=0.8,
        status_forcelist=[403, 429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    # Try cloudscraper first (better at bypassing 403/Cloudflare)
    try:
        import cloudscraper  # type: ignore

        scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "mobile": False}
        )
        hdrs = dict(HEADERS)
        hdrs["User-Agent"] = random.choice(UA_LIST)
        scraper.headers.update(hdrs)
        scraper.mount("http://", adapter)
        scraper.mount("https://", adapter)
        # Seed cookies via homepage visit
        try:
            scraper.get("https://www.moneycontrol.com/", timeout=10)
            time.sleep(random.uniform(0.2, 0.6))
        except Exception:
            pass
        return scraper
    except Exception:
        pass
    # Fallback to plain requests session
    s = requests.Session()
    hdrs = dict(HEADERS)
    hdrs["User-Agent"] = random.choice(UA_LIST)
    s.headers.update(hdrs)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    # Seed cookies via homepage visit
    try:
        s.get("https://www.moneycontrol.com/", timeout=10)
        time.sleep(random.uniform(0.2, 0.6))
    except Exception:
        pass
    return s


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_table(url: str, rename_map: dict | None = None) -> pd.DataFrame | None:
    try:
        s = _requests_session()
        # Small jitter to avoid sending many concurrent requests
        time.sleep(random.uniform(0.3, 0.9))
        r = s.get(url, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find("table", class_="mctable1")
        parsed_df: pd.DataFrame | None = None
        if table:
            rows = table.find_all("tr")
            data = []
            for row in rows:
                cols = row.find_all(["td", "th"])
                cols = [ele.get_text(strip=True) for ele in cols]
                if cols:
                    data.append(cols)
            if len(data) > 1:
                parsed_df = pd.DataFrame(data[1:], columns=data[0])
        if parsed_df is None or parsed_df.empty:
            candidates = []
            try:
                for df in pd.read_html(r.text, flavor=["lxml", "bs4"], displayed_only=False):
                    candidates.append(_flatten_columns(df))
            except Exception:
                candidates = []
            best = None
            score_best = -1
            for df in candidates:
                cols_upper = [str(c).strip().upper() for c in df.columns]
                score = 0
                if "SCHEME NAME" in cols_upper:
                    score += 3
                if "PLAN" in cols_upper:
                    score += 2
                score += sum(1 for c in cols_upper if c in ["1W","1M","3M","6M","YTD","1Y","2Y","3Y","5Y","10Y"]) 
                if score > score_best and df.shape[1] >= 3:
                    best = df
                    score_best = score
            parsed_df = best
        if parsed_df is not None and not parsed_df.empty:
            parsed_df = _flatten_columns(parsed_df)
            if rename_map:
                parsed_df.rename(columns=rename_map, inplace=True)
            return parsed_df
        return None
    except Exception:
        return None


def _drop_common(df: pd.DataFrame | None, common_cols: list[str]) -> pd.DataFrame | None:
    if df is None:
        return None
    return df.drop(columns=[c for c in common_cols if c in df.columns], errors="ignore")


def _clean_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        if any(period in col for period in RETURN_COLS + ["Return", "Change", "YTD"]):
            df[col] = pd.to_numeric(
                df[col]
                .astype(str)
                .str.replace("%", "", regex=False)
                .str.replace(r"[^0-9+\-.]", "", regex=True),
                errors="coerce",
            )
        elif df[col].dtype == "object":
            s = df[col].astype(str)
            if s.str.contains(",").any():
                df[col] = pd.to_numeric(s.str.replace(",", ""), errors="ignore")
    return df


def _standardize_return_headers(cols: list[str]) -> list[str]:
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
    out = []
    for c in cols:
        cc = c.replace("_x", "").replace("_y", "").strip()
        key = cc.upper()
        out.append(mapping.get(key, cc))
    return out


def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        new_cols: list[str] = []
        for tup in df.columns:
            parts = [str(x) for x in tup if str(x).lower() != "nan" and str(x) != "None"]
            name = " ".join(parts).strip()
            new_cols.append(name if name else "")
        df.columns = new_cols
    return df


def _normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    def to_clean(s: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()

    rename: dict[str, str] = {}
    for c in list(df.columns):
        cc = to_clean(c)
        new_c = None
        # Return windows
        m = re.match(r"^(\d+)\s*(w|wk|wks|week|weeks)\b", cc)
        if m:
            new_c = f"{m.group(1).upper()}W"
        m = m or re.match(r"^(\d+)\s*(m|mo|mon|mons|month|months)\b", cc)
        if not new_c and m:
            new_c = f"{m.group(1).upper()}M"
        m = None
        if not new_c and ("ytd" in cc or "year to date" in cc):
            new_c = "YTD"
        if not new_c:
            my = re.match(r"^(\d+)\s*(y|yr|yrs|year|years)\b", cc)
            if my:
                new_c = f"{my.group(1).upper()}Y"
        # Core keys
        if not new_c:
            if cc in {"scheme name", "schemename", "scheme", "fund name", "fund"}:
                new_c = "Scheme Name"
            elif cc in {"plan", "plan type", "plantype", "plan name", "planname"}:
                new_c = "Plan"
            elif cc in {"option", "scheme option", "option name"}:
                new_c = "Option"
            elif ("crisil" in cc) and ("rank" in cc or "rating" in cc):
                new_c = "Crisil Rating"
            elif cc.startswith("unnamed") or cc in {"sr no", "s no", "s. no", "serial no"}:
                # drop obvious index columns
                new_c = None
        if new_c and new_c != c:
            rename[c] = new_c
    if rename:
        df = df.rename(columns=rename)
    # Drop duplicate or empty-named columns if any
    if "" in df.columns:
        df = df.drop(columns=[""], errors="ignore")
    return df


def _normalize_plan_values(df: pd.DataFrame) -> pd.DataFrame:
    if "Plan" in df.columns:
        def norm(v: object) -> str:
            s = str(v).strip().lower()
            if ("regular" in s) or s.startswith("reg"):
                return "Regular"
            if ("direct" in s) or s.startswith("dir"):
                return "Direct"
            return str(v)
        df["Plan"] = df["Plan"].map(norm)
    return df


def _use_headless() -> bool:
    try:
        return bool(st.session_state.get("use_headless", False))
    except Exception:
        return False


def fetch_table_headless(url: str, rename_map: dict | None = None) -> pd.DataFrame | None:
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception:
        return None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=random.choice(UA_LIST),
                extra_http_headers=HEADERS,
                locale="en-US",
            )
            page = context.new_page()
            # Warm-up home to seed cookies
            try:
                page.goto("https://www.moneycontrol.com/", wait_until="networkidle", timeout=25000)
                time.sleep(random.uniform(0.2, 0.6))
            except Exception:
                pass
            page.goto(url, wait_until="networkidle", timeout=30000)
            # Wait for any table to appear, but cap wait
            try:
                page.wait_for_selector("table", timeout=8000)
            except Exception:
                pass
            html = page.content()
            context.close()
            browser.close()
        soup = BeautifulSoup(html, "html.parser")
        # Prefer Moneycontrol table class if present
        table = soup.find("table", class_="mctable1") or soup.find("table")
        parsed_df: pd.DataFrame | None = None
        candidates = []
        if table:
            try:
                candidates = [
                    _flatten_columns(x) for x in pd.read_html(str(table), flavor=["lxml", "bs4"], displayed_only=False)
                ]
            except Exception:
                candidates = []
        if not candidates:
            try:
                candidates = [
                    _flatten_columns(x) for x in pd.read_html(html, flavor=["lxml", "bs4"], displayed_only=False)
                ]
            except Exception:
                candidates = []
        best = None
        score_best = -1
        for df in candidates:
            cols_upper = [str(c).strip().upper() for c in df.columns]
            score = 0
            if "SCHEME NAME" in cols_upper:
                score += 3
            if "PLAN" in cols_upper:
                score += 2
            score += sum(1 for c in cols_upper if c in ["1W","1M","3M","6M","YTD","1Y","2Y","3Y","5Y","10Y"]) 
            if score > score_best and df.shape[1] >= 3:
                best = df
                score_best = score
        parsed_df = best
        if parsed_df is not None and not parsed_df.empty:
            parsed_df = _flatten_columns(parsed_df)
            parsed_df = _normalize_headers(parsed_df)
            parsed_df = _normalize_plan_values(parsed_df)
            if rename_map:
                parsed_df.rename(columns=rename_map, inplace=True)
            return parsed_df
        return None
    except Exception:
        return None
@st.cache_data(ttl=3600, show_spinner=False)
def scrape_category(category_slug: str, category_label: str) -> pd.DataFrame:
    urls = {
        "returns": urljoin(BASE + "/", f"returns/{category_slug}.html"),
        "rank": urljoin(BASE + "/", f"ranks/{category_slug}.html"),
    }
    with ThreadPoolExecutor(max_workers=2) as ex:
        fut_returns = ex.submit(fetch_table, urls["returns"], None)
        fut_rank = ex.submit(fetch_table, urls["rank"], {"Crisil Rank": "Crisil Rating"})
        df_returns = fut_returns.result()
        df_rank = fut_rank.result()
    # Headless fallback if allowed and either frame is missing
    if _use_headless():
        if (df_returns is None or df_returns.empty):
            df_returns = fetch_table_headless(urls["returns"], None)
        if (df_rank is None or df_rank.empty):
            df_rank = fetch_table_headless(urls["rank"], {"Crisil Rank": "Crisil Rating"})
    # Normalize headers and plan values for robustness
    if df_returns is not None and not df_returns.empty:
        df_returns = _normalize_headers(df_returns)
        df_returns = _normalize_plan_values(df_returns)
    if df_rank is not None and not df_rank.empty:
        df_rank = _normalize_headers(df_rank)
        df_rank = _normalize_plan_values(df_rank)
    if df_returns is None or df_returns.empty:
        return pd.DataFrame()
    rank_df = _drop_common(df_rank, ["Category Name", "Crisil Rating"]) if df_rank is not None else None
    combined = df_returns.copy()
    # Merge by available keys
    if rank_df is not None and not rank_df.empty:
        keys: list[str] = []
        if "Scheme Name" in combined.columns and "Scheme Name" in rank_df.columns:
            keys.append("Scheme Name")
        if "Plan" in combined.columns and "Plan" in rank_df.columns:
            keys.append("Plan")
        if keys:
            combined = combined.merge(rank_df, on=keys, how="left")
    # Filter Regular plan when possible
    if "Plan" in combined.columns:
        mask_reg = combined["Plan"].astype(str).str.contains("regular", case=False, na=False)
        if mask_reg.any():
            combined = combined[mask_reg]
    # Prefer Option == Growth; else fall back to Scheme Name contains Growth; else skip this filter
    if "Option" in combined.columns and combined["Option"].astype(str).str.contains("growth", case=False, na=False).any():
        combined = combined[combined["Option"].astype(str).str.contains("growth", case=False, na=False)]
    elif "Scheme Name" in combined.columns and combined["Scheme Name"].astype(str).str.contains("growth", case=False, na=False).any():
        combined = combined[combined["Scheme Name"].astype(str).str.contains("growth", case=False, na=False)]
    if combined.empty:
        return pd.DataFrame()
    combined = _clean_numeric_columns(combined)
    combined["Category"] = category_label
    combined = combined.dropna(subset=["Scheme Name"]).dropna(axis=1, how="all")
    combined.columns = _standardize_return_headers(list(combined.columns))
    return combined.reset_index(drop=True)


def _aggregate_categories(selected: list[str]) -> pd.DataFrame:
    slugs = [(name, slug) for name, slug in CATEGORIES.items() if slug != "all" and name in selected]
    dfs: list[pd.DataFrame] = []
    with ThreadPoolExecutor(max_workers=min(3, len(slugs) or 1)) as ex:
        futures = {ex.submit(scrape_category, slug, name): name for name, slug in slugs}
        for fut in as_completed(futures):
            df = fut.result()
            if df is not None and not df.empty:
                dfs.append(df)
    if not dfs:
        return pd.DataFrame()
    df = pd.concat(dfs, ignore_index=True)
    df = df.dropna(axis=1, how="all")
    return df


def main():
    st.title("📊 Mutual Fund Dashboard")

    st.sidebar.header("🔍 Filters")
    st.sidebar.button("♻️ Refresh data", on_click=st.cache_data.clear, help="Clear cached results and refetch")
    debug = st.sidebar.checkbox("Diagnostics", value=False)
    st.sidebar.checkbox("Use headless browser fallback (Playwright)", value=False, key="use_headless", help="Enable this if the site blocks scraping (403) or tables don’t load. Requires Playwright installed.")
    category = st.sidebar.selectbox("Select Fund Category", list(CATEGORIES.keys()))

    if category == "All Funds":
        multiselect = st.sidebar.multiselect(
            "Choose categories to include",
            [k for k in CATEGORIES.keys() if k != "All Funds"],
            default=["Flexi Cap", "Large Cap", "Mid Cap"],
        )
        with st.spinner("Fetching all selected categories..."):
            df = _aggregate_categories(multiselect)
    else:
        with st.spinner(f"Fetching {category} funds data..."):
            df = scrape_category(CATEGORIES[category], category)
            if not df.empty:
                df = df.dropna(axis=1, how="all")

    # Diagnostics: show fetch status and candidate table columns
    if debug:
        slug = CATEGORIES[category] if category != "All Funds" else "large-cap-fund"
        ret_url = urljoin(BASE + "/", f"returns/{slug}.html")
        rank_url = urljoin(BASE + "/", f"ranks/{slug}.html")
        def probe_url(url: str) -> dict:
            try:
                s = _requests_session()
                r = s.get(url, timeout=10)
                soup = BeautifulSoup(r.text, "html.parser")
                mc = soup.find("table", class_="mctable1") is not None
                try:
                    dfs = [
                        _normalize_headers(_flatten_columns(x))
                        for x in pd.read_html(r.text, flavor=["lxml", "bs4"], displayed_only=False)
                    ]
                except Exception:
                    dfs = []
                preview = [list(x.columns)[:12] for x in dfs[:3]]
                return {
                    "status": r.status_code,
                    "url": url,
                    "has_mc_table": mc,
                    "tables_found": len(dfs),
                    "sample_columns": preview,
                }
            except Exception as e:
                return {"url": url, "error": str(e)}
        colA, colB = st.columns(2)
        with colA:
            st.caption("Returns page probe")
            st.json(probe_url(ret_url))
        with colB:
            st.caption("Rank page probe")
            st.json(probe_url(rank_url))

    if df is not None and not df.empty:
        st.success(f"✅ Showing {category} ({len(df)} schemes)")
        left, right = st.columns([3, 1])
        with right:
            q = st.text_input("Search scheme", "")
            min_1y = st.slider("Min 1Y Return (%)", -50.0, 100.0, -50.0, 0.5)
        if q:
            df = df[df["Scheme Name"].str.contains(q, case=False, na=False)]
        if "Return 1Y" in df.columns:
            df = df[df["Return 1Y"].fillna(-1e9) >= min_1y]
        st.dataframe(df, use_container_width=True, height=600, hide_index=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"{category.lower().replace(' ', '_')}_funds.csv",
            mime="text/csv",
        )
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        st.error("⚠️ Could not fetch data. Please try again later.")


if __name__ == "__main__":
    main()
